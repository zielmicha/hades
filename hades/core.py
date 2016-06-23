import os
import tempfile
import yaml
import subprocess
import time
import platform
import pwd
import time

from .common import valid_name

_lxd = None

def lxd():
    global _lxd
    if _lxd == None:
        from pylxd import api
        _lxd = api.API()
    return _lxd

CONF_PATH = os.path.abspath(os.environ.get('HADES_CONF', 'conf'))
RUN_PATH = os.path.abspath(os.environ.get('HADES_RUN', '/run/hades'))
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

begin = time.time()

def call_plugins(name, *args):
    for plugin in plugins:
        #print('[%.2f]' % (time.time() - begin), name, ' ', plugin.__name__)
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

    @property
    def config_path(self):
        return os.path.join(CONF_PATH, 'profiles_%s' % self.user.name, self.name + '.yml')

    def get_config(self):
        with open(self.config_path) as f:
            return yaml.safe_load(f.read())

    def update_container(self):
        if not lxd().container_defined(self.container_name):
            print('Updating', self.container_name)
            self.launch_container()
        self.update_definition()
        self.start_container()
        self.update_inner_user()
        self.update_hostname()

        call_plugins('update_container', self)

    def is_running(self):
        return lxd().container_running(self.container_name)

    def start_container(self):
        if not lxd().container_running(self.container_name):
            lxd().container_start(self.container_name, timeout=15)

        for i in range(20):
            if lxd().container_running(self.container_name):
                return
            time.sleep(0.5)
        raise ValueError('failed to start container %s' % self.container_name)

    def launch_container(self):
        config = self.get_config()
        # FIXME: sanitize template name?
        # We use CLI LXD client, because launching using REST API is quite involved
        subprocess.check_call(['lxc', 'init', '--', config['template'], self.container_name])

        for i in range(10):
            if lxd().container_defined(self.container_name):
                return
            time.sleep(0.5)

    def update_inner_user(self):
        config = self.get_config()

        passwd = lxd().get_container_file(self.container_name, '/etc/passwd').decode('utf8')
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
                      'Defaults !authenticate\nDefaults env_keep += "HADES_PROFILE"\n%s   ALL=(ALL:ALL) ALL' % self.user.name if config.get('sudo') == 'allow' else '')

    def update_hostname(self):
        hostname = platform.node()
        self.run_command(['hostname', '--', hostname])
        hosts = lxd().get_container_file(self.container_name, '/etc/hosts').decode('utf8')
        hosts = '\n'.join([ line for line in hosts.splitlines() if not '# HADES HOSTNAME' in line ])
        self.put_file('/etc/hosts', '127.0.0.1   ' + hostname + ' # HADES HOSTNAME\n' + hosts)

    def run_command(self, args):
        subprocess.check_call(['lxc', 'exec', self.container_name, '--'] + args)

    def put_file(self, path, data, uid=0, gid=0, mode=0o644):
        with tempfile.NamedTemporaryFile() as f:
            f.write(data.encode('utf8') if isinstance(data, str) else data)
            f.flush()
            lxd().put_container_file(self.container_name, f.name, path, uid=uid, gid=gid, mode=mode)

    def update_definition(self):
        definition = lxd().get_container_config(self.container_name)
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
            'raw.lxc': '''lxc.id_map = u %d %d 1\nlxc.id_map = g %d %d 1\nlxc.aa_allow_incomplete = 1''' % (INTERNAL_UID, self.user.uid, INTERNAL_GID, self.user.gid),
            'environment.HADES_PROFILE': self.name,
            'environment.LANG': 'en_US.UTF-8', # Read /etc/default/locale? Or use PAM to set this?
            'environment.SHELL': config.get('shell', '/bin/bash'),
            'boot.autostart': bool(config.get('autostart')),
        })

        definition['profiles'] = []

        definition['devices'] = {
            'root': {'type': 'disk', 'path': '/'},
            'eth0': {'name': 'eth0', 'nictype': 'bridged', 'parent': 'lxdbr0', 'type': 'nic'},

            # give container a few useful devices, they anyway won't be usable without "sudo: allow"
            'tun': {'type': 'unix-char', 'path': '/dev/net/tun'},
            'kvm': {'type': 'unix-char', 'path': '/dev/kvm'},
            'fuse': {'type': 'unix-char', 'path': '/dev/fuse'}, # requires kernel patch to support user ns
        }

        call_plugins('update_container_def', self, definition)

    def execute(self, args):
        # Execute command as user in the container
        cmd = ['lxc', 'exec', '--', self.container_name, '/hades/tools/bin/hades-runas', self.user.name]
        cmd += args
        return subprocess.call(cmd)

    def get_container_info(self):
        return lxd().container_info(self.container_name)

def all_profiles(user):
    dir = CONF_PATH + '/profiles_' + user.name
    names = os.listdir(dir)
    result = []
    for name in names:
        if not name.endswith('.yml'):
            continue
        profile_name = name.rsplit('.', 1)[0]
        result.append(Profile(user, profile_name))
    return result

def load_plugins():
    if plugins: return
    from . import storage
    from . import net
    from . import locale
    from . import x11
    from . import shell_launcher
    from . import sound
    from . import initxyz
    from . import shell
    from . import base
    from . import ssh
    plugins.append(storage)
    plugins.append(net)
    plugins.append(locale)
    plugins.append(x11)
    plugins.append(shell_launcher)
    plugins.append(sound)
    plugins.append(initxyz)
    plugins.append(shell)
    plugins.append(base)
    plugins.append(ssh)

if __name__ == '__main__':
    import sys
    Profile(user=User(name='michal'), name=sys.argv[1]).update_container()
