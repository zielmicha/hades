import subprocess
import yaml
import tempfile
import binascii
import time
import glob
import stat
import os

from . import core

_lxd = None

def lxd():
    global _lxd
    if _lxd == None:
        from pylxd import api
        _lxd = api.API()
    return _lxd

@core.create_driver.register
def _create_driver(name, profile):
    if name == 'lxc':
        return LxcDriver(profile)

class LxcDriver:
    def __init__(self, profile):
        self.profile = profile

    @property
    def container_name(self):
        return self.profile.user.name + '-' + self.profile.name

    def is_running(self):
        return lxd().container_running(self.container_name)

    def _ensure_exists(self):
        if not lxd().container_defined(self.container_name):
            print('Updating', self.container_name)
            self._launch_container()


    def start(self):
        self._ensure_exists()

        if not lxd().container_running(self.container_name):
            lxd().container_start(self.container_name, timeout=15)

        for i in range(40):
            if lxd().container_running(self.container_name):
                return
            time.sleep(0.5)

        raise Exception('failed to start container %s' % self.container_name)

    def get_file(self, path: str) -> bytes:
        return lxd().get_container_file(self.container_name, path)

    def put_file(self, path, data, uid=0, gid=0, mode=0o644):
        with tempfile.NamedTemporaryFile() as f:
            f.write(data.encode('utf8') if isinstance(data, str) else data)
            f.flush()
            lxd().put_container_file(self.container_name, f.name, path, uid=uid, gid=gid, mode=mode)

    def run_command(self, args):
        subprocess.check_call(['lxc', 'exec', self.container_name, '--'] + args)

    def run_command_silent(self, args):
        return subprocess.call(['lxc', 'exec', self.container_name, '--'] + args)

    def reconfigure(self) -> 'LxcReconfigurator':
        self._ensure_exists()
        return LxcReconfigurator(self)

    def attach_wireless_phy(self, name):
        info = self._get_container_info()
        if info['pid']:
            subprocess.call(['iw', 'phy', name, 'set', 'netns', str(info['pid'])])

    def attach_link(self, name, source):
        info = self._get_container_info()
        subprocess.check_call(['ip', 'link', 'set', 'dev', source, 'netns', str(info['pid']), 'name', name])

    def _launch_container(self):
        config = self.profile.config

        # FIXME: sanitize template name?
        # We use CLI LXD client, because launching using REST API is quite involved
        subprocess.check_call(['lxc', 'init', '--', config['template'], self.container_name])

        for i in range(10):
            if lxd().container_defined(self.container_name):
                return
            time.sleep(0.5)

    def _get_container_info(self):
        return lxd().container_info(self.container_name)

class LxcReconfigurator:
    def __init__(self, driver):
        self.driver = driver
        self.profile = driver.profile

        definition = lxd().get_container_config(self.driver.container_name)
        self.definition = {
            'name': definition['name'],
            'profiles': definition['profiles'],
            'config': definition['config'],
            'devices': definition['devices'],
            'ephemeral': definition['ephemeral'],
        }
        self._init_config()

    def _init_config(self):
        self.definition['config'].update({
            'raw.lxc': '''lxc.id_map = u %d %d 1\nlxc.id_map = g %d %d 1\nlxc.aa_allow_incomplete = 1''' % (core.INTERNAL_UID, self.profile.user.uid, core.INTERNAL_GID, self.profile.user.gid),
            'environment.HADES_PROFILE': self.profile.name,
            'environment.LANG': 'en_US.UTF-8', # TODO: Read /etc/default/locale? Or use PAM to set this?
            'environment.SHELL': '/bin/zsh', # TODO
            'linux.kernel_modules': 'overlay, nf_nat',
            'security.nesting': 'true'
        })

        self.definition['profiles'] = []

        self.definition['devices'] = {
            'root': {'type': 'disk', 'path': '/'},
            # 'eth0': {'name': 'eth0', 'nictype': 'bridged', 'parent': 'lxdbr0', 'type': 'nic'},

            # give container a few useful devices, they anyway won't be usable without "sudo: allow"
            'apparmorfix': {'path': '/sys/module/apparmor/parameters/enabled', 'type': 'disk', 'source': '/dev/null'},
            'tun': {'type': 'unix-char', 'path': '/dev/net/tun'},
            'kvm': {'type': 'unix-char', 'path': '/dev/kvm'},
            'fuse': {'type': 'unix-char', 'path': '/dev/fuse'}, # requires kernel patch to support user ns
        }

    def add_mount(self, path, source, readonly=False):
        name = 'mount-' + binascii.hexlify(path.encode('utf8')).decode()
        self.definition['devices'][name] = {
            'type': 'disk',
            'path': path,
            'source': source,
            'readonly': 'true' if readonly else 'false'
        }

    def add_unix_socket(self, path, source):
        self.add_mount(path, source)

    def add_env(self, k, v):
        self.definition['config']['environment.' + k] = v

    def commit(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write(yaml.safe_dump(self.definition).encode())
            f.seek(0)
            subprocess.check_call(['lxc', 'config', 'edit', '--', self.driver.container_name], stdin=f)

    def add_devices(self, patterns, uid=0, gid=0, mode=0o660):
        devices = []
        for pattern in patterns: devices += glob.glob(pattern)
        for dev in devices:
            self.definition['devices']['dev' + binascii.hexlify(dev.encode()).decode()] = {
                'type': 'unix-block' if stat.S_ISBLK(os.stat(dev).st_mode) else 'unix-char',
                'path': dev,
                'uid': uid,
                'gid': gid,
                'mode': oct(mode)[2:]
            }

    def add_block_device(self, path, source, uid=0, gid=0, mode=0o666, _type=None):
        self.definition['devices']['dev' + binascii.hexlify(path.encode()).decode()] = {
            'type': _type or 'unix-block',
            'path': path,
            # 'source': path, TODO - get minor, major
            'uid': uid,
            'gid': gid,
            'mode': oct(mode)[2:]
        }

    def add_serial_device(self, path, source, uid=0, gid=0, mode=0o666):
        self.add_block_device(path, source, uid, gid, mode, _type='unix-char')

    def add_host_netdev(self, name, source, mac):
        self.definition['devices']['netdev-' + name] = {
            'type': 'nic',
            'nictype': 'physical',
            'name': name,
            'parent': source,
            'hwaddr': mac
        }

    def add_p2p_netdev(self, name, source, mac=None):
        self.definition['devices']['netdev-' + name] = {
            'type': 'nic',
            'nictype': 'p2p',
            'name': name,
            'host_name': source,
            'hwaddr': mac
        }
