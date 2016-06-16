from . import core
import subprocess
import binascii
import os
import time
import pipes

DISPLAY_ID = ':0'

def rand_cookie():
    return binascii.hexlify(os.urandom(16)).decode()

def wait_for_x():
    path = '/tmp/.X11-unix/X' + DISPLAY_ID[1:]
    for i in range(30):
        if os.path.exists(path):
            break
        time.sleep(0.1)
    else:
        raise OSError('X failed to start (%r not found)' % path)

def main(user):
    subprocess.call(['mkdir', '/run/hades'])
    xauth_path = core.RUN_PATH + '/xauth.' + DISPLAY_ID
    x_command = ['python3', '-m', 'hades.main', 'exec', '--update', user.name, 'gui', 'hades-run-gui']
    print(x_command)
    subprocess.call(['rm', xauth_path])
    subprocess.check_call(['xauth', '-f', xauth_path, 'add',
                     DISPLAY_ID, 'MIT-MAGIC-COOKIE-1', rand_cookie()])
    xorg = subprocess.Popen(['X', DISPLAY_ID, 'vt2', '-auth', xauth_path, '-nolisten', 'tcp', '-novtswitch'])
    wait_for_x()
    with open(core.RUN_PATH + '/x11-user', 'w') as f:
        f.write(user.name + '\n')
    subprocess.check_call(x_command)

def start(user):
    unit_name = 'hades-x11-%s.service' % user.name
    with open('/etc/systemd/system/%s' % unit_name, 'w') as f:
        f.write('''[Unit]
Description=HadesOS X session

[Service]
Type=simple
ExecStart=/usr/local/bin/hades runx %s
''' % (pipes.quote(user.name)))

    subprocess.check_call(['systemctl', 'start', unit_name])

if __name__ == '__main__':
    import sys
    main(core.User(sys.argv[1]))
