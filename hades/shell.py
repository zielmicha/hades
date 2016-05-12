import shlex
import readline
import os
import subprocess
import sys
import signal

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

def call_main(user, args):
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
        call_main(user, ['update'] + args[1:])
    elif command in ('exec', 'e'):
        if call_main(user, ['exec', '--'] + args[1:]) == 0:
            sys.exit(0)
    elif command == 'root':
        subprocess.call(['bash'], cwd='/root')
    else:
        print('Invalid command.')
