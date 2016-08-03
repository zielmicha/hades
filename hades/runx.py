from . import core, x11
import subprocess
import binascii
import os
import time
import pipes

def rand_cookie():
    return binascii.hexlify(os.urandom(16)).decode()

def wait_for_x(user):
    path = '/tmp/.X11-unix/X%d' % x11.get_display_num(user)
    for i in range(30):
        if os.path.exists(path):
            break
        time.sleep(0.1)
    else:
        raise OSError('X failed to start (%r not found)' % path)

def main(user):
    subprocess.call(['mkdir', '/run/hades'])
    xauth_path = core.RUN_PATH + '/xauth.' + x11.get_display_id(user)
    x_command = ['python3', '-m', 'hades.main', 'exec', '--update', user.name, 'gui', 'hades-run-gui']
    print(x_command)
    subprocess.call(['rm', xauth_path])
    subprocess.check_call(['xauth', '-f', xauth_path, 'add',
                     x11.get_display_id(user), 'MIT-MAGIC-COOKIE-1', rand_cookie()])
    xorg = subprocess.Popen(['X', x11.get_display_id(user), 'vt%d' % (x11.get_display_num(user) + 2), '-audit', '4', '-auth', xauth_path, '-nolisten', 'tcp', '-novtswitch'])
    wait_for_x(user)
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
