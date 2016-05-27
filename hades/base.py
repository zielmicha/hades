from . import core
import sys
import subprocess
import os
import yaml

def add_parsers(addf):
    sub = addf('exec')
    sub.add_argument('--update', action='store_true', default=False)
    sub.add_argument('user')
    sub.add_argument('profile')
    sub.add_argument('args', nargs='*')

    sub = addf('update')
    sub.add_argument('user')
    sub.add_argument('profile')

    sub = addf('edit')
    sub.add_argument('--new', action='store_true')
    sub.add_argument('user')
    sub.add_argument('profile')

def init_config(profile):
    id = max(profile.get_config()['id'] for profile in core.all_profiles(profile.user)) + 1
    with_initxyz = True
    config = {
        'id': id,
        'template': 'images:ubuntu/xenial/amd64',
        'x11': True,
        'sudo': 'allow',
        'shell': '/bin/zsh',
    }
    if with_initxyz:
        config['initxyz'] = {'profiles': []}

    with open(profile.config_path, 'w') as f:
        f.write(yaml.dump(config))

def call_main(ns):
    if ns.command == 'update':
        core.Profile(user=core.User(name=ns.user), name=ns.profile).update_container()
    elif ns.command == 'exec':
        profile = core.Profile(user=core.User(name=ns.user), name=ns.profile)
        if ns.update or not profile.is_running():
            profile.update_container()
        exit = profile.execute(ns.args)
        sys.exit(exit)
    elif ns.command == 'edit':
        profile = core.Profile(user=core.User(name=ns.user), name=ns.profile)
        if ns.new and not os.path.exists(profile.config_path):
            init_config(profile)
        subprocess.call(['editor', profile.config_path])
        profile.update_container()
