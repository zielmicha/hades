from . import core

core.load_plugins()

import argparse
import sys

parser = argparse.ArgumentParser()
subcommands = parser.add_subparsers(dest='command')

exec_parser = subcommands.add_parser('exec')
exec_parser.add_argument('user')
exec_parser.add_argument('profile')
exec_parser.add_argument('args', nargs='*')

update_parser = subcommands.add_parser('update')
update_parser.add_argument('user')
update_parser.add_argument('profile')

update_parser = subcommands.add_parser('shell')
update_parser.add_argument('user')

ns = parser.parse_args()
if ns.command == 'update':
    core.Profile(user=core.User(name=ns.user), name=ns.profile).update_container()
elif ns.command == 'exec':
    exit = core.Profile(user=core.User(name=ns.user), name=ns.profile).execute(ns.args)
    sys.exit(exit)
elif ns.command == 'shell':
    from . import shell
    shell.run(core.User(name=ns.user))
else:
    parser.print_usage()
