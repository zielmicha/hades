from . import core

core.load_plugins()

import argparse
import sys
import os

def check_user(name):
    restricted = os.environ.get("HADES_AS_USER")
    if restricted and restricted != name:
        sys.exit('bad user')

parser = argparse.ArgumentParser()
subcommands = parser.add_subparsers(dest='command')

exec_parser = subcommands.add_parser('exec')
exec_parser.add_argument('--update', action='store_true', default=False)
exec_parser.add_argument('user')
exec_parser.add_argument('profile')
exec_parser.add_argument('args', nargs='*')

update_parser = subcommands.add_parser('update')
update_parser.add_argument('user')
update_parser.add_argument('profile')

shell_parser = subcommands.add_parser('shell')
shell_parser.add_argument('user')
shell_parser.add_argument('--session-id', default=None)

shellserver_parser = subcommands.add_parser('shell-server')
shellserver_parser.add_argument('user')
shellserver_parser.add_argument('profile')

ns = parser.parse_args()
if ns.command == 'update':
    check_user(ns.user)

    core.Profile(user=core.User(name=ns.user), name=ns.profile).update_container()
elif ns.command == 'exec':
    check_user(ns.user)

    profile = core.Profile(user=core.User(name=ns.user), name=ns.profile)
    if ns.update or not profile.is_running():
        profile.update_container()
    exit = profile.execute(ns.args)
    sys.exit(exit)
elif ns.command == 'shell':
    check_user(ns.user)

    from . import shell
    shell.run(core.User(name=ns.user), ns.session_id)
elif ns.command == 'shell-server':
    os.execvp('python2', ['python2', '-m', 'hades.shell_server', ns.user, ns.profile])
else:
    parser.print_usage()
