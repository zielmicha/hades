import dbus

bus = dbus.SystemBus()
netd = bus.get_object('net.networkos.netd',
                       '/net/networkos/netd')
netd_core = dbus.Interface(netd, dbus_interface='net.networkos.netd.Core')
netd_fragments = dbus.Interface(netd, dbus_interface='net.networkos.netd.Fragments')
