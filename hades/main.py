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

def add_parser(name):
    available_commands.append(name)
    return subcommands.add_parser(name)

call_plugins('add_parsers', add_parser)

ns = parser.parse_args()

if ns.user:
    check_user(ns.user)

call_plugins('call_main', ns)

if ns.command not in available_commands:
    parser.print_usage()
