import tempfile
import os
import subprocess

from . import core, common, shell, main

DISPLAY_NUM = 0
DISPLAY_ID = ':%d' % DISPLAY_NUM

def generate_xauthority(trusted):
    with tempfile.NamedTemporaryFile() as f:
        env = os.environ.copy()
        env['XAUTHORITY'] = core.RUN_PATH + '/xauth.' + DISPLAY_ID
        env['DISPLAY'] = DISPLAY_ID
        subprocess.check_call(['xauth', '-f', f.name, 'generate', DISPLAY_ID, 'MIT-MAGIC-COOKIE-1', 'trusted' if trusted else 'untrusted', 'timeout', '31536000'], env=env)
        return open(f.name, 'rb').read()

@shell.setup_shell_env.register
def setup_shell_env():
    os.environ['XAUTHORITY'] = core.RUN_PATH + '/xauth.' + DISPLAY_ID
    os.environ['DISPLAY'] = DISPLAY_ID

@core.update_profile.register
def update_container(profile):
    config = profile.config

    if config.get('x11'):
        profile.run_command(['ln', '-sf', '/hades/run/x11/X%d' % DISPLAY_NUM, '/tmp/.X11-unix/X%d' % DISPLAY_NUM])

        if config.get('x11') == 'unrestricted':
            xauthority = open(core.RUN_PATH + '/xauth.' + DISPLAY_ID, 'rb').read()

            # TODO: only makes sense for LXC driver
            profile.run_command(['bash', '-c', 'shopt -s nullglob; chown %d:%d /dev/dri/* /dev/nvidia*' % (core.INTERNAL_UID, core.INTERNAL_GID)])

        if not os.path.exists('/tmp/.X11-unix/X' + DISPLAY_ID[1:]):
            # X11 not running
            return

        if config.get('x11') == 'unrestricted':
            xauthority = open(core.RUN_PATH + '/xauth.' + DISPLAY_ID, 'rb').read()
        else:
            xauthority = generate_xauthority(trusted=False)

        profile.driver.put_file('%s/.Xauthority' % (profile.user.home), xauthority, uid=core.INTERNAL_UID, gid=core.INTERNAL_GID, mode=0o644) # FIXME: permissions

@core.update_configuration.register
def update_configuration(profile, configuration):
    config = profile.config
    if config.get('x11'):
        configuration.add_mount('/hades/run/x11', '/tmp/.X11-unix')
        configuration.add_env('DISPALY', DISPLAY_ID)

        if config.get('x11') == 'unrestricted':
            configuration.add_devices(['/dev/dri/*', '/dev/nvidia*'],
                                      mode=0o660) # assigning UID is broken in LXD (for users in raw uidmaps)

@main.add_parsers.register
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

@main.call_main.register
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
