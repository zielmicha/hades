import tempfile
import os
import subprocess

from . import core

DISPLAY_ID = ':0'

def generate_xauthority():
    with tempfile.NamedTemporaryFile() as f:
        subprocess.check_call(['xauth', '-f', f.name, 'generate', DISPLAY_ID, 'MIT-MAGIC-COOKIE-1']) # + ['untrusted']
        return open(f.name, 'rb').read()

def update_container(self):
    config = self.get_config()

    # TODO: restricted tokens
    if config.get('x11'):
        xauthority = generate_xauthority()
        self.put_file('/home/%s/.Xauthority' % (self.user.name), xauthority, uid=self.user.uid, gid=self.user.gid, mode=0o600)

def update_container_def(self, definition):
    config = self.get_config()
    if config.get('x11'):
        definition['devices']['x11'] = {
            'type': 'disk',
            'path': '/tmp/.X11-unix',
            'source': '/tmp/.X11-unix'
        }
