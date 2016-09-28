import tempfile
import os
import subprocess
import ipaddress

from . import core
from . import driver_lxc

MAC_BASE = '76:91:df:b8:e4:'
IP4_BASE = ipaddress.IPv4Address('10.11.102.0')

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

    # internal IP network (TODO: migrate to netd)
    # I've tried getting IPv6 to work, but failed: https://serverfault.com/questions/805424/linux-not-sending-ndp-for-routed-packets

    ip_base = IP4_BASE + config['id']
    subprocess.check_call('ip addr flush profile{0:d} && ip addr add dev profile{0:d} {1} peer {2}'.format(
        config['id'], str(IP4_BASE + 254), ip_base
    ), shell=True)
    profile.run_command(['sh', '-c', 'ip link set dev eth1 down && ip addr flush eth1 && ip link set dev eth1 up && ip addr add dev eth1 {0} peer {2}/32 && ip route add {1}/24 via {2}'.format(str(ip_base), str(IP4_BASE), str(IP4_BASE + 254))])

@core.update_configuration.register
def update_configuration(profile, configuration):
    config = profile.config

    net = config.get('net', {})

    # internal IPv6 network
    configuration.add_p2p_netdev(name='eth1', source='profile%d' % config['id'])

    if net.get('master'):
        assert isinstance(profile.driver, driver_lxc.LxcDriver), 'net master must be using LXC driver'

        try:
            del configuration.definition['devices']['eth0']
        except KeyError:
            pass

        configuration.add_p2p_netdev(name='host', source='upstream', mac=MAC_BASE + '0')
    else:
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
