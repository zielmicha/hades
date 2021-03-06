from . import core
from . import main
from .common import Observable

import shlex
import readline
import os
import subprocess
import sys
import signal
import yaml
import traceback
import threading

setup_shell_env = Observable()

@main.call_main.register
def call_main(ns):
    if ns.command == 'shell':
        run(core.User(name=ns.user), ns.session_id)
    elif ns.command == 'shell-server':
        os.execvp('python2', ['python2', '-m', 'hades.shell_server', ns.user, ns.profile])

@main.add_parsers.register
def add_parsers(addf):
    sub = addf('shell')
    sub.add_argument('user')
    sub.add_argument('--session-id', default=None)

    sub = addf('shell-server')
    sub.add_argument('user')
    sub.add_argument('profile')

def run(user, session_id):
    os.environ['HADES_AS_USER'] = user.name
    os.environ['TERM'] = 'xterm' # TODO: get TERM from client
    setup_shell_env.call()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    signal.signal(signal.SIGTTIN, signal.SIG_IGN)
    signal.signal(signal.SIGTTOU, signal.SIG_IGN)
    signal.signal(signal.SIGQUIT, signal.SIG_IGN)

    try:
        while True:
            tick(user)
    except EOFError:
        print()

def run_main(user, args):
    # return subprocess.call(['python3', '-m', 'hades.main', args[0], user.name] + args[1:])
    try:
        from hades.main import main
        sys.argv = ['hades', args[0], user.name] + args[1:]
        main()
    except SystemExit as exc:
        return exc.args[0]
    except BaseException:
        traceback.print_exc()

def load_settings(user):
    path = core.CONF_PATH + '/shell_%s.yml' % user.name
    with open(path, 'r') as f:
        return yaml.load(f)

def check_auth(user, scope):
    return True

def tick(user):
    try:
        command_str = input('# ')
    except KeyboardInterrupt:
        print()
        return

    args = shlex.split(command_str, posix=False)

    if not args:
        return

    settings = load_settings(user)
    aliases = settings.get('aliases', {})
    root_commands = settings.get('rootcommands', {})

    command = args[0]
    builtin_profile_commands = ['update', 'exec']
    builtin_root_commands = ['edit']

    if command in aliases:
        command = aliases[command]

    if command in builtin_profile_commands:
        if check_auth(user, 'root'):
            run_main(user, [command] + args[1:])
    elif command in builtin_root_commands:
        if check_auth(user, 'root'):
            run_main(user, [command] + args[1:])
    elif command in root_commands:
        if check_auth(user, 'root'):
            cmd = root_commands[command]
            subprocess.call(['bash', '-c', cmd, '--'] + args[1:])
    else:
        print('Invalid command:', command)
