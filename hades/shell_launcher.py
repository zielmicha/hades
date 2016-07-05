import os
import subprocess
import pipes
from . import core

@core.update_profile.register
def update_profile(profile):
    config = profile.config

    run_path = core.RUN_PATH + '/profile-' + profile.full_name
    socket_path = run_path + '/shell.socket'
    unit_name = 'hades-shell-%s-%s.service' % (profile.user.name, profile.name)

    if not config.get('gui'):
        if os.path.exists(socket_path):
            os.unlink(socket_path)
            if subprocess.call(['systemctl', '-q', 'is-active', unit_name]):
                subprocess.check_call(['systemctl', 'stop', unit_name])
        return

    if not os.path.exists(socket_path):
        with open('/etc/systemd/system/%s' % unit_name, 'w') as f:
            f.write('''[Unit]
Description=HadesOS shell server

[Service]
Type=simple
ExecStart=/usr/local/bin/hades shell-server %s %s
''' % (pipes.quote(profile.user.name), pipes.quote(profile.name)))
        subprocess.check_call(['systemctl', 'start', unit_name])

@core.update_configuration.register
def update_configuration(profile, configuration):
    src_path = core.RUN_PATH + '/profile-' + profile.full_name
    if not os.path.exists(src_path):
        os.mkdir(src_path)

    configuration.add_mount('/hades/run/host', src_path)
    configuration.add_mount('/hades/tools', os.path.dirname(__file__) + '/../clienttools', readonly=True)
