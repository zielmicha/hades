# Simple program that launches and monitors qemu instances.
# API is designed to be similar to LXD, so HadesOS driver_kvm can easily replace driver_lxc. It can also execute rootfs's of existing LXD containers.
import argparse, sys, yaml, socket, traceback, os
from . import daemon

BASE_PATH = '/run/kvmd'
SOCKET_PATH = '/run/kvmd/socket'

def _init():
    try:
        os.makedirs(SOCKET_PATH)
    except OSError:
        pass

    os.chmod(SOCKET_PATH, 0o700)

def fork_process(f):
    try:
        try:
            f()
        except:
            traceback.print_exc()
    finally:
        os._exit(0)

def configure(name, config):
    _init()
    socket_path = SOCKET_PATH + '/vm_' + name

    if not os.path.exists(socket_path):
        serv_sock = socket.socket(socket.SOCK_UNIX)
        serv_sock.bind(socket_path)
        serv_sock.listen(9)
        fork_process(lambda: run_daemon(name, serv_sock))
        serv_sock.close()

    sock = socket.socket(socket.SOCK_UNIX)
    sock.connect(socket_path)

    f = sock.makefile('rw')
    f.write(yaml.dump(config))
    f.close()

def run_daemon(name, serv_sock, init_config=None):
    print('Name', name)
    vm = daemon.VM(name)
    if init_config is not None: vm.configure(init_config)
    while True:
        child, addr = serv_sock.accept()
        conf = yaml.load(child.makefile('r'))
        try:
            vm.configure(conf)
        except Exception:
            traceback.print_exc()

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand')

    subparser = subparsers.add_parser('stop', help='Stop running VM')
    subparser.add_argument('name')

    subparser = subparsers.add_parser('config', help='Configures (and starts, if needed) a VM')
    subparser.add_argument('name')

    subparser = subparsers.add_parser('is-running', help='Checks if a domain is running')
    subparser.add_argument('name')

    subparser = subparsers.add_parser('daemon', help='Start a daemon running a VM (internal)')
    subparser.add_argument('name')

    ns = parser.parse_args()

    if ns.subcommand == 'stop':
        configure(ns.subcommand, {'state': 'off'})
    elif ns.subcommand == 'config':
        config = yaml.safe_load(sys.stdin)
        configure(ns.subcommand, config)
    elif ns.subcommand == 'daemon':
        # for debugging, normally spawned by configure
        _init()
        config = yaml.safe_load(sys.stdin)
        socket_path = SOCKET_PATH + '/vm_' + ns.name

        if os.path.exists(socket_path):
            os.unlink(socket_path)

        serv_sock = socket.socket(socket.AF_UNIX)
        serv_sock.bind(socket_path)
        serv_sock.listen(9)

        run_daemon(ns.name, serv_sock, init_config=config)
    elif ns.subcommand == 'is-running':
        socket_path = SOCKET_PATH + '/vm_' + ns.name
        serv_sock = socket.socket(socket.AF_UNIX)
        try:
            serv_sock.connect(socket_path)
        except socket.error:
            print('not running')
        else:
            print('running')
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
