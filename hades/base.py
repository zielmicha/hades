from . import core
from . import main
import sys
import subprocess
import os
import yaml
import getpass

@main.add_parsers.register
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


    sub = addf('foreach', help='Execute command in each profile of a given user.')
    sub.add_argument('user')
    sub.add_argument('args', nargs='+')

    sub = addf('login')

    sub = addf('init')

def init():
    if not os.path.isdir(core.RUN_PATH):
        os.mkdir(core.RUN_PATH)

    apparmor_path = os.path.dirname(__file__) + '/../misc/apparmor'
    for name in os.listdir(apparmor_path):
        path = apparmor_path + '/' + name
        if os.path.isfile(path):
            subprocess.check_call(['apparmor_parser', '-r', path])

def init_config(profile):
    id = max(profile.config['id'] for profile in core.all_profiles(profile.user)) + 1
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

def login():
    import pam

    # what handles this during normal boot?
    subprocess.call(['rm', '/run/nologin', '/etc/nologin'])

    try:
        subprocess.call(['clear'])
        print('Welcome to HadesOS!')
        print()
        session_type = input('Session type (graphical/text): ') or 'text'
        if session_type not in ('graphical', 'text'):
            print('Bad session type.')
            return

        if session_type == 'text':
            # For text sessions, use login - it sets up controlling terminals etc correctly
            os.execvp('login', ['login'])
            return

        user_name = input('Login: ')

        password = getpass.getpass()

        pamobj = pam.pam()
        pamobj.authenticate(user_name, password)
        if pamobj.code == 0:
            if session_type == 'graphical':
                os.execvp('hades', ['hades', 'startx', '--', user_name])
        else:
            print('Authentication failed.')
    except (KeyboardInterrupt, EOFError):
        pass

@main.call_main.register
def call_main(ns):
    if ns.command == 'update':
        core.Profile(user=core.User(name=ns.user), name=ns.profile).update()
    elif ns.command == 'exec':
        profile = core.Profile(user=core.User(name=ns.user), name=ns.profile)
        if ns.update or not profile.driver.is_running():
            profile.update()
        exit = profile.execute(ns.args)
        sys.exit(exit)
    elif ns.command == 'init':
        init()
    elif ns.command == 'login':
        login()
    elif ns.command == 'edit':
        profile = core.Profile(user=core.User(name=ns.user), name=ns.profile)
        if ns.new and not os.path.exists(profile.config_path):
            init_config(profile)
        subprocess.call(['editor', profile.config_path])
        profile.update()
    elif ns.command == 'foreach':
        for profile in core.all_profiles(core.User(name=ns.user)):
            print(profile.name + ':')
            if not profile.driver.is_running():
                profile.update()
            profile.execute(ns.args)
