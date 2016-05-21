from . import core
import sys

def add_parsers(addf):
    sub = addf('exec')
    sub.add_argument('--update', action='store_true', default=False)
    sub.add_argument('user')
    sub.add_argument('profile')
    sub.add_argument('args', nargs='*')

    sub = addf('update')
    sub.add_argument('user')
    sub.add_argument('profile')

def call_main(ns):
    if ns.command == 'update':
        core.Profile(user=core.User(name=ns.user), name=ns.profile).update_container()
    elif ns.command == 'exec':
        profile = core.Profile(user=core.User(name=ns.user), name=ns.profile)
        if ns.update or not profile.is_running():
            profile.update_container()
        exit = profile.execute(ns.args)
        sys.exit(exit)
