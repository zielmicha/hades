import tempfile
import os
import subprocess

from . import core, common

DISPLAY_ID = ':0'

def generate_xauthority(trusted):
    with tempfile.NamedTemporaryFile() as f:
        env = os.environ.copy()
        env['XAUTHORITY'] = core.RUN_PATH + '/xauth.' + DISPLAY_ID
        env['DISPLAY'] = DISPLAY_ID
        subprocess.check_call(['xauth', '-f', f.name, 'generate', DISPLAY_ID, 'MIT-MAGIC-COOKIE-1', 'trusted' if trusted else 'untrusted', 'timeout', '31536000'], env=env)
        return open(f.name, 'rb').read()

def setup_shell_env():
    os.environ['XAUTHORITY'] = core.RUN_PATH + '/xauth.' + DISPLAY_ID
    os.environ['DISPLAY'] = DISPLAY_ID

def update_container(self):
    config = self.get_config()

    if not os.path.exists('/tmp/.X11-unix/X' + DISPLAY_ID[1:]):
        # X11 not running
        return

    # TODO: restricted tokens
    if config.get('x11'):
        if config.get('x11') == 'unrestricted':
            xauthority = open(core.RUN_PATH + '/xauth.' + DISPLAY_ID, 'rb').read()
            self.run_command(['bash', '-c', 'shopt -s nullglob; chown %d:%d /dev/dri/* /dev/nvidia*' % (core.INTERNAL_UID, core.INTERNAL_GID)])
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

        if config.get('x11') == 'unrestricted':
            common.add_devices(definition, ['/dev/dri/*', '/dev/nvidia*'],
                               uid=0,
                               gid=0,
                               mode=0o660) # assigning UID is broken in LXD (for users in raw uidmaps)

def add_parsers(addf):
    sub = addf('runx')
    sub.add_argument('user')

    sub = addf('startx')
    sub.add_argument('user')

    sub = addf('guiexec')
    sub.add_argument('args', nargs='+')
    sub.add_argument('--update', action='store_true', default=False)

def get_gui_user():
    username = open(core.RUN_PATH + '/x11-user', 'r').read().strip()
    return core.User(username)

def call_main(ns):
    if ns.command == 'runx':
        from . import runx
        runx.main(core.User(name=ns.user))
    elif ns.command == 'startx':
        from . import runx
        runx.start(core.User(name=ns.user))
    elif ns.command == 'guiexec':
        profile = core.Profile(user=get_gui_user(), name='gui')
        if ns.update or not profile.is_running():
            profile.update_container()
        profile.execute(ns.args)
