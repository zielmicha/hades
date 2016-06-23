from . import core
from .core import call_plugins

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

available_commands = []

def add_parser(name, **kwargs):
    available_commands.append(name)
    return subcommands.add_parser(name, **kwargs)

call_plugins('add_parsers', add_parser)

def main():
    ns = parser.parse_args()

    if hasattr(ns, 'user'):
        check_user(ns.user)

    call_plugins('call_main', ns)

    if ns.command not in available_commands:
        parser.print_usage()

if __name__ == '__main__':
    main()
