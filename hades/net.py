import tempfile
import os
import subprocess

from . import core

MAC_BASE = '76:91:df:b8:e4:'

def update_container(self):
    config = self.get_config()

    net = config.get('net', {})

def ensure_veth(name, mac):
    if not os.path.exists('/sys/class/net/' + name) and not os.path.exists('/sys/class/net/' + name + 'P'):
        subprocess.check_call(['ip', 'link', 'add', 'dev', name, 'type', 'veth', 'peer', 'name', (name + 'P')])
        if mac:
            subprocess.check_call(['ip', 'link', 'set', 'dev', name, 'address', mac])

def veth_for(p):
    return 'c%d-%d' % (p.user.uid, p.get_config()['id'])

def get_net_master(self):
    for profile in core.all_profiles(self.user):
        if profile.get_config().get('net', {}).get('master'):
            return profile
    raise ValueError('no net master!')

def move_link_to(link, pid, target_name):
    subprocess.check_call(['ip', 'link', 'set', 'dev', link, 'netns', '%d' % pid, 'name', target_name])

def update_container_def(self, definition):
    config = self.get_config()

    net = config.get('net', {})

    if net.get('master'):
        del definition['devices']['eth0']
        dev_name = 'upstream'
        ensure_veth(dev_name, mac=MAC_BASE + '0')

        definition['devices']['host-dev'] = {
            'type': 'nic',
            'nictype': 'physical',
            'name': 'host',
            'parent': dev_name + 'P',
        }
    else:
        dev_name = veth_for(self)
        info = self.get_container_info()
        id = self.get_config()['id']
        if 'eth0' not in (info['network'] or {}):
            # interface may not exist yet, but if it exists it is in root namespace
            ensure_veth(dev_name, mac=MAC_BASE + str(hex(id)))

        target_dev = 'profile%d' % id
        master_profile = get_net_master(self)
        master_info = master_profile.get_container_info()
        if target_dev not in master_info['network']:
            move_link_to(dev_name + 'P', master_info['pid'], target_dev)

        definition['devices']['eth0'] = {
            'type': 'nic',
            'nictype': 'physical',
            'name': 'eth0',
            'parent': dev_name
        }

    for iface in net.get('raw', []):
        definition['devices']['host-raw-%s' % iface] = {
            'type': 'nic',
            'nictype': 'physical',
            'name': iface,
            'parent': iface
        }
