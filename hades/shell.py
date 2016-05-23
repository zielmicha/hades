from . import core

import shlex
import readline
import os
import subprocess
import sys
import signal

def call_main(ns): # plugin
    if ns.command == 'shell':
        run(core.User(name=ns.user), ns.session_id)
    elif ns.command == 'shell-server':
        os.execvp('python2', ['python2', '-m', 'hades.shell_server', ns.user, ns.profile])

def add_parsers(addf): # plugin
    sub = addf('shell')
    sub.add_argument('user')
    sub.add_argument('--session-id', default=None)

    sub = addf('shell-server')
    sub.add_argument('user')
    sub.add_argument('profile')

def run(user, session_id):
    os.environ['HADES_AS_USER'] = user.name
    os.environ['TERM'] = 'xterm' # TODO: get TERM from client

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
    return subprocess.call(['python3', '-m', 'hades.main', args[0], user.name] + args[1:])

def tick(user):
    try:
        command_str = input('# ')
    except KeyboardInterrupt:
        print()
        return

    args = shlex.split(command_str, posix=False)

    if not args:
        return

    command = args[0]

    if command in ('update', 'upd', 'u'):
        run_main(user, ['update'] + args[1:])
    elif command in ('exec', 'e'):
        if run_main(user, ['exec', '--'] + args[1:]) == 0 and not args:
            sys.exit(0)
        else:
            print
    elif command == 'edit':
        run_main(user, ['edit'] + args[1:])
    elif command == 'root':
        subprocess.call(['bash'], cwd='/root')
    else:
        print('Invalid command.')
