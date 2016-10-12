from . import qemu
import subprocess, os

class VM:
    def __init__(self, name):
        self.name = name
        self.qemu_process = None
        self.rootfs_dir = '/run/kvmd/rootfs_' + self.name + '/'
        self.mounts = {}

    def setup_mounts(self, config):
        for path, info in list(self.mounts.items()):
            if config['disks'][path] != info:
                subprocess.check_call(['umount', '-l', self.rootfs_dir + path])
                del config['disks']

        for path, info in config['disks'].items():
            if self.mounts.get(path) != info:
                readonly = info.get('readonly')
                target = os.path.realpath(self.rootfs_dir + '/' + path)

                # TODO: TOCTOU
                if not target.startswith(self.rootfs_dir.rstrip('/') + '/') and target != self.rootfs_dir.rstrip('/'):
                    raise Exception('symlink check failed')

                if not os.path.exists(target):
                    os.makedirs(target)
                args = ([
                    'mount', '--bind',
                    *(['-o', 'ro'] if readonly else []),
                    info['source'], target])
                subprocess.check_call(args)

    def configure(self, config):
        print('configuring')

        self.setup_mounts(config)

        if not self.qemu_process:
            print(config['uid_map'])

            args = []

            for netdev in config['netdevs']:
                host_name = netdev['host_name']
                hwaddr = netdev['hwaddr']
                args += [
                    '-netdev', 'tap,id=netdev{0},ifname={0},script=/bin/true'.format(host_name),
                    '-device', 'virtio-net-pci,netdev=netdev{0},mac={1}'.format(host_name, hwaddr)]

            self.qemu_process = qemu.run(
                memory=config['memory'],
                uid_map=config['uid_map'],
                gid_map=config['gid_map'],
                rootfs_path=self.rootfs_dir,
                args=args,
            )
