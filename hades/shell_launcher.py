import os
import subprocess
from . import core

def update_container(self):
    config = self.get_config()

    if not config.get('gui'):
        return

    run_path = core.RUN_PATH + '/profile-' + self.container_name
    socket_path = run_path + '/shell.socket'

    if not os.path.exists(socket_path):
        # TODO: launch it in a better way
        null = open('/dev/null', 'r+')
        subprocess.Popen(['python3', '-m', 'hades.main', 'shell-server',
                          self.user.name, self.name],
                         stdin=null, stdout=null, stderr=null)

def update_container_def(self, definition):
    src_path = core.RUN_PATH + '/profile-' + self.container_name
    if not os.path.exists(src_path):
        os.mkdir(src_path)
    definition['devices']['host'] = {
        'type': 'disk', 'path': '/opt/hadeshost',
        'source': src_path
    }
    definition['devices']['clienttools'] = {
        'type': 'disk', 'path': '/opt/hadestools',
        'source': os.path.dirname(__file__) + '/../clienttools',
        'readonly': True
    }
