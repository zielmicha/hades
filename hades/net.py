import tempfile
import os
import subprocess

from . import core
from . import driver_lxc

MAC_BASE = '76:91:df:b8:e4:'

@core.update_profile.register
def update_container(profile: core.Profile):
    config = profile.config

    net = config.get('net', {})

    for phy in net.get('wireless-phy', []):
        profile.driver.attach_wireless_phy(phy)

    if not net.get('master'):
        master_profile = get_net_master(profile)

        if not master_profile.driver.is_running():
            master_profile.update()

        if interface_exists(veth_for(profile)):
            master_profile.driver.attach_link('profile%d' % config['id'], veth_for(profile))
        master_profile.run_command(['hades-net-update'])

@core.update_configuration.register
def update_configuration(profile, configuration):
    config = profile.config

    net = config.get('net', {})

    if net.get('master'):
        assert isinstance(profile.driver, driver_lxc.LxcDriver), 'net master must be using LXC driver'

        try:
            del configuration.definition['devices']['eth0']
        except KeyError:
            pass

        configuration.add_p2p_netdev(name='host', source='upstream', mac=MAC_BASE + '0')
    else:
        # TODO: moving interfaces should happen in update_container
        dev_name = veth_for(profile)
        configuration.add_p2p_netdev(name='eth0', source=dev_name, mac=MAC_BASE + str(hex(config['id']))[2:])

    for iface in net.get('raw', []):
        configuration.add_host_netdev(iface, iface, mac=None)

def veth_for(p):
    return 'c%d-%d' % (p.user.uid, p.config['id'])

def interface_exists(name):
    return os.path.exists('/sys/class/net/' + name)

def get_net_master(profile):
    for profile in core.all_profiles(None):
        if profile.config.get('net', {}).get('master'):
            return profile

    raise ValueError('no net master!')
