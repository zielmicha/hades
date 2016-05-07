import os
import tempfile
import yaml
import subprocess
import time
import platform
import pwd

from pylxd import api
from .common import valid_name

lxd = api.API()

CONF_PATH = os.path.abspath(os.environ.get('HADES_CONF', 'conf'))
INTERNAL_UID = 200000
INTERNAL_GID = 200000

plugins = []

class User:
    def __init__(self, name):
        entry = pwd.getpwnam(name)
        self.name = name
        self.uid = entry.pw_uid
        self.gid = entry.pw_gid
        self.home = entry.pw_dir
        assert '-' not in name and valid_name(name)

def call_plugins(name, *args):
    for plugin in plugins:
        if hasattr(plugin, name):
            getattr(plugin, name)(*args)

class Profile:
    def __init__(self, user, name):
        self.user = user
        self.name = name
        assert valid_name(name)

    @property
    def container_name(self):
        return self.user.name + '-' + self.name

    def get_config(self):
        with open(os.path.join(CONF_PATH, 'profiles_%s' % self.user.name, self.name + '.yml')) as f:
            return yaml.safe_load(f.read())

    def update_container(self):
        if not lxd.container_defined(self.container_name):
            self.launch_container()
        self.update_definition()
        self.start_container()
        self.update_inner_user()
        self.update_hostname()

        call_plugins('update_container', self)

    def start_container(self):
        if not lxd.container_running(self.container_name):
            lxd.container_start(self.container_name, timeout=15)

        for i in range(20):
            if lxd.container_running(self.container_name):
                return
            time.sleep(0.5)

    def launch_container(self):
        config = self.get_config()
        # FIXME: sanitize template name?
        # We use CLI LXD client, because launching using REST API is quite involved
        subprocess.check_call(['lxc', 'init', '--', config['template'], self.container_name])

        for i in range(10):
            if lxd.container_defined(self.container_name):
                return
            time.sleep(0.5)

    def update_inner_user(self):
        config = self.get_config()

        passwd = lxd.get_container_file(self.container_name, '/etc/passwd').decode('utf8')
        users = [ line.split(':')[0] for line in passwd.splitlines() ]

        if 'ubuntu' in users:
            self.run_command(['userdel', 'ubuntu'])
            # self.run_command(['groupdel', 'ubuntu'])

        if self.user.name not in users:
            self.run_command(['groupadd', '--gid', str(INTERNAL_GID), self.user.name])
            self.run_command(['useradd', '--create-home', '--uid', str(INTERNAL_UID), '--gid', str(INTERNAL_GID), self.user.name])

        self.run_command(['chsh', '--shell', config.get('shell', '/bin/bash'), self.user.name])
        self.run_command(['chown', '%d:%d' % (INTERNAL_UID, INTERNAL_GID), '--', self.user.home])

        config = self.get_config()
        self.put_file('/etc/sudoers.d/hades-sudo',
                      'Defaults !authenticate\n%s   ALL=(ALL:ALL) ALL' % self.user.name if config.get('sudo') == 'allow' else '')

    def update_hostname(self):
        hostname = platform.node()
        self.run_command(['hostname', '--', hostname])

    def run_command(self, args):
        subprocess.check_call(['lxc', 'exec', self.container_name, '--'] + args)

    def put_file(self, path, data, uid=0, gid=0, mode=0o644):
        with tempfile.NamedTemporaryFile() as f:
            f.write(data.encode('utf8') if isinstance(data, str) else data)
            f.flush()
            lxd.put_container_file(self.container_name, f.name, path, uid=uid, gid=gid, mode=mode)

    def update_definition(self):
        definition = lxd.get_container_config(self.container_name)
        definition = {
            'name': definition['name'],
            'profiles': definition['profiles'],
            'config': definition['config'],
            'devices': definition['devices'],
            'ephemeral': definition['ephemeral'],
        }
        self.update_container_def(definition)

        with tempfile.NamedTemporaryFile() as f:
            f.write(yaml.safe_dump(definition).encode())
            f.seek(0)
            subprocess.check_call(['lxc', 'config', 'edit', '--', self.container_name], stdin=f)

    def update_container_def(self, definition):
        config = self.get_config()
        definition['config'].update({
            'raw.lxc': '''lxc.id_map = u %d %d 1\nlxc.id_map = g %d %d 1''' % (INTERNAL_UID, self.user.uid, INTERNAL_GID, self.user.gid),
            'environment.HADES_PROFILE': self.name,
        })

        definition['devices'] = {
            'root': {'type': 'disk', 'path': '/'},
            'eth0': {'name': 'eth0', 'nictype': 'bridged', 'parent': 'lxdbr0', 'type': 'nic'},

            # give container a few useful devices, they anyway won't be usable without "sudo: allow"
            'tun': {'type': 'unix-char', 'path': '/dev/net/tun'},
            'kvm': {'type': 'unix-char', 'path': '/dev/kvm'},
        }

        call_plugins('update_container_def', self, definition)

    def execute(self, args):
        # Execute command as user in the container
        cmd = ['lxc', 'exec', '--', self.container_name, 'sudo', '-EH', '-u', self.user.name]
        if args:
            cmd += ['--'] + args
        else:
            cmd += ['-i']
        return subprocess.call(cmd)

def load_plugins():
    from . import storage
    from . import x11
    from . import initxyz
    plugins.append(storage)
    plugins.append(x11)
    plugins.append(initxyz)

if __name__ == '__main__':
    import sys
    Profile(user=User(name='michal'), name=sys.argv[1]).update_container()
