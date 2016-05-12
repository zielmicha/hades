import passfd
import subprocess
import os
import sys
import threading
import socket
import pwd
import pipes
import signal

def wrap_in_pty(command):
    return [
        'script', '-q', '/dev/null',
        '-c', 'exec ' + ' '.join( pipes.quote(arg) for arg in command )
    ]

def main(user, profile):
    session_id = os.urandom(12).encode('hex')

    directory = os.environ.get('HADES_RUN', 'run') + '/profile-%s-%s' % (user, profile)
    try:
        os.mkdir(directory)
    except OSError:
        pass

    path = directory + '/shell.socket'
    if os.path.exists(path):
        os.unlink(path)

    sock = socket.socket(socket.AF_UNIX)
    sock.bind(path)
    os.chmod(path, 0o600)
    pw = pwd.getpwnam(user)
    os.chown(path, pw.pw_uid, pw.pw_gid)
    sock.listen(3)

    def handle_resize(child, proc):
        child.settimeout(None)
        while True:
            ret = child.recv(1)
            if not ret:
                break

            proc.send_signal(signal.SIGWINCH)

    def handle_client(child):
        fd, msg = passfd.recvfd(child)
        command = ['python3', '-m', 'hades.main', 'shell',
                   '--session-id', session_id, user]
        def preexec():
            # make process group, script sometimes does kill(0, TERM)
            os.setpgrp()

        proc = subprocess.Popen(
            wrap_in_pty(command), stdin=fd, stdout=fd, stderr=fd, preexec_fn=preexec)
        os.close(fd)
        threading.Thread(target=handle_resize, args=[child, proc]).start()
        proc.wait()
        child.sendall('F')
        child.close()

    while True:
        child, addr = sock.accept()
        child.settimeout(5)
        threading.Thread(target=handle_client, args=[child]).start()

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
