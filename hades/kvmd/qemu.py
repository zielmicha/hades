import os, socket, subprocess, time, fcntl
from . import userns

def run(memory, uid_map, gid_map, rootfs_path):
    virtfs_sock, helper_pid = launch_virtfs_helper(uid_map, gid_map, rootfs_path)

    cmd = [
        'qemu-system-x86_64',
        '-m', str(memory),
        '-enable-kvm',
        '-kernel', '/opt/kvmimage',
        '-fsdev', 'proxy,id=root,sock_fd=%d,readonly,path=%s' % (
            virtfs_sock.fileno(), rootfs_path),
        '-device', 'virtio-9p-pci,fsdev=root,mount_tag=/dev/root',
        '-append', 'root=/dev/root ro rootfstype=9p rootflags=trans=virtio,version=9p2000.L console=ttyS0 init=/sbin/init',
        '-nographic']
    print(cmd)

    try:
        subprocess.check_call(cmd, pass_fds=[virtfs_sock.fileno()])
    finally:
        os.kill(helper_pid, 15)

def launch_virtfs_helper(uid_map, gid_map, path):
    sockpair = socket.socketpair(socket.AF_UNIX)

    def func():
        fd = sockpair[0].fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        fcntl.fcntl(fd, fcntl.F_SETFD, flags & (~fcntl.FD_CLOEXEC))
        os.execvp('virtfs-proxy-helper', ['virtfs-proxy-helper', '--nodaemon',
                                          '-p', path, '--fd', str(fd)])

    pid = userns.spawn_in_userns(uid_map, gid_map, func)
    return sockpair[1], pid

if __name__ == '__main__':
    map = '0 100000 65536\n200000 1000 1'
    run(1024, map, map, '/var/lib/lxd/containers/michal-misc/rootfs')
