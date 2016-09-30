import ctypes, subprocess, os, time, traceback

libc = ctypes.CDLL('libc.so.6')
CLONE_NEWUSER = 0x10000000

def _userns_child(unshared_pipe, ready_pipe, func):
    if libc.unshare(CLONE_NEWUSER) != 0:
        raise OSError('unshare(CLONE_NEWUSER) failed')

    unshared_pipe[1].write(b'0')
    ready_pipe[0].read(1)

    os.setgid(0)
    os.setuid(0)
    func()

def pipe():
    p = os.pipe()
    return [os.fdopen(p[0], 'rb', 0), os.fdopen(p[1], 'wb', 0)]

def spawn_in_userns(uid_map, gid_map, func):
    unshared_pipe = pipe()
    ready_pipe = pipe()

    pid = os.fork()
    if pid == 0:
        try:
            try:
                _userns_child(unshared_pipe, ready_pipe, func)
            except:
                traceback.print_exc()
        finally:
            os._exit(0)
    else:
        unshared_pipe[0].read(1)

        with open('/proc/%d/uid_map' % pid, 'w') as w:
            w.write(uid_map)

        with open('/proc/%d/gid_map' % pid, 'w') as w:
            w.write(gid_map)

        ready_pipe[1].write(b'0')
        return pid

if __name__ == '__main__':
    map = '0 100000 65536\n200000 1000 1'
    pid = spawn_in_userns(map, map, lambda: subprocess.call(['bash']))
    os.wait()
