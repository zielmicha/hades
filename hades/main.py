from . import core
from .common import Observable

import argparse
import sys
import os

call_main = Observable()
add_parsers = Observable()

def check_user(name):
    restricted = os.environ.get("HADES_AS_USER")
    if restricted and restricted != name:
        sys.exit('bad user')

def main():
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest='command')

    available_commands = []

    def _add_parser(name, **kwargs):
        available_commands.append(name)
        return subcommands.add_parser(name, **kwargs)

    add_parsers.call(_add_parser)

    ns = parser.parse_args()

    if hasattr(ns, 'user'):
        check_user(ns.user)

    if ns.command not in available_commands:
        parser.print_usage()

    call_main.call(ns)

if __name__ == '__main__':
    from . import main
    core.load_plugins()
    main.main()
