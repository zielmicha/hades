from . import core

import subprocess

KVMD = ['python3', '-m', 'hades.kvmd.main']

@core.create_driver.register
def _create_driver(name, profile):
    if name == 'kvm':
        return KvmDriver(profile)

@core.ensure_not_running.register
def _ensure_not_running(except_driver, profile):
    if except_driver != 'kvm':
        profile = KvmDriver(self.profile)
        if profile.is_running():
            profile.stop()

class KvmDriver:
    def __init__(self, profile):
        self.profile = profile

    @property
    def vm_name(self):
        return self.profile.user.name + '-' + self.profile.name

    def is_running(self):
        return subprocess.check_output(KVMD + ['is-running', self.vm_name]) == 'running'

    def reconfigure(self):
        return KvmReconfigurator(self)

class KvmReconfigurator:
    def __init__(self, driver):
        self.driver = driver
        self.profile = driver.profile
        self.config = {'netdevs': [], 'disks': {}}

    def add_mount(self, path, source, readonly=False):
        self.config['disks'][path] = {
            'source': source,
            'readonly': readonly,
        }

    def add_p2p_netdev(self, name, source, mac=None):
        # name is ignored
        self.config['netdevs'].append({
            'host_name': source,
            'hwaddr': mac
        })

    def add_env(self, k, v):
        pass # TODO

    def commit(self):
        pass
