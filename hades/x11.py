import tempfile
import os
import subprocess

from . import core

DISPLAY_ID = ':0'

def generate_xauthority(trusted):
    with tempfile.NamedTemporaryFile() as f:
        env = os.environ.copy()
        env['XAUTHORITY'] = core.RUN_PATH + '/xauth.' + DISPLAY_ID
        env['DISPLAY'] = DISPLAY_ID
        subprocess.check_call(['xauth', '-f', f.name, 'generate', DISPLAY_ID, 'MIT-MAGIC-COOKIE-1', 'trusted' if trusted else 'untrusted'], env=env)
        return open(f.name, 'rb').read()

def update_container(self):
    config = self.get_config()

    if not os.path.exists('/tmp/.X11-unix/X' + DISPLAY_ID[1:]):
        # X11 not running
        return

    # TODO: restricted tokens
    if config.get('x11'):
        if config.get('x11') == 'unrestricted':
            xauthority = open(core.RUN_PATH + '/xauth.' + DISPLAY_ID, 'rb').read()
        else:
            xauthority = generate_xauthority(trusted=False)
        self.put_file('/home/%s/.Xauthority' % (self.user.name), xauthority, uid=core.INTERNAL_UID, gid=core.INTERNAL_GID, mode=0o644) # FIXME: permissions

def update_container_def(self, definition):
    config = self.get_config()
    if config.get('x11'):
        definition['devices']['x11'] = {
            'type': 'disk',
            'path': '/tmp/.X11-unix',
            'source': '/tmp/.X11-unix'
        }
        definition['config']['environment.DISPLAY'] = DISPLAY_ID
