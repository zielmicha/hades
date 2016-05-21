import os
import subprocess
import pipes
from . import core

def update_container(self):
    config = self.get_config()

    if not config.get('gui'):
        return

    run_path = core.RUN_PATH + '/profile-' + self.container_name
    socket_path = run_path + '/shell.socket'

    if not os.path.exists(socket_path):
        unit_name = 'hades-shell-%s-%s.service' % (self.user.name, self.name)
        with open('/etc/systemd/system/%s' % unit_name, 'w') as f:
            f.write('''[Unit]
Description=HadesOS shell server

[Service]
Type=simple
ExecStart=/usr/local/bin/hades shell-server %s %s

[Install]
WantedBy=multi-user.target
''' % (pipes.quote(self.user.name), pipes.quote(self.name)))
        subprocess.check_call(['systemctl', 'start', unit_name])

def update_container_def(self, definition):
    src_path = core.RUN_PATH + '/profile-' + self.container_name
    if not os.path.exists(src_path):
        os.mkdir(src_path)
    definition['devices']['host'] = {
        'type': 'disk', 'path': '/hades/run/host',
        'source': src_path
    }
    definition['devices']['clienttools'] = {
        'type': 'disk', 'path': '/hades/tools',
        'source': os.path.dirname(__file__) + '/../clienttools',
        'readonly': True
    }
