import os
import tempfile
import yaml
import subprocess
import time
import platform
import pwd
import time

from .common import valid_name
from .common import Observable, cached_property

CONF_PATH = os.path.abspath(os.environ.get('HADES_CONF', 'conf'))
RUN_PATH = os.path.abspath(os.environ.get('HADES_RUN', '/run/hades'))
INTERNAL_UID = 200000
INTERNAL_GID = 200000

class User:
    def __init__(self, name):
        entry = pwd.getpwnam(name)
        self.name = name
        self.uid = entry.pw_uid
        self.gid = entry.pw_gid
        self.home = entry.pw_dir
        assert '-' not in name and valid_name(name)

begin = time.time()

create_distro = Observable(need_return=True)
create_driver = Observable(need_return=True)
update_profile = Observable()
update_configuration = Observable()

class Profile:
    def __init__(self, user, name):
        self.user = user
        self.name = name
        assert valid_name(name)

    @cached_property
    def distro(self):
        return create_distro.call(self.config.get('distro', 'debian'), self)

    @property
    def full_name(self):
        return self.user.name + '-' + self.name

    @cached_property
    def driver(self):
        return create_driver.call(self.config.get('distro', 'lxc'), self)

    @property
    def config_path(self):
        return os.path.join(CONF_PATH, 'profiles_%s' % self.user.name, self.name + '.yml')

    @cached_property
    def config(self):
        with open(self.config_path) as f:
            return yaml.safe_load(f.read())

    def update(self):
        configuration = self.driver.reconfigure()
        self.distro.update_configuration(configuration)
        update_configuration.call(self, configuration)
        configuration.commit()

        if not self.driver.is_running():
            self.driver.start()

        self.distro.update()
        update_profile.call(self)

    def run_command(self, *args, **kwargs):
        return self.driver.run_command(*args, **kwargs)

    def execute(self, *args, **kwargs):
        return self.distro.execute(*args, **kwargs)

def all_users():
    result = []
    for name in os.listdir(CONF_PATH):
        if name.startswith('profiles_'):
            user_name = name[len('profiles_'):]
            result.append(User(user_name))
    return result

def all_profiles(user):
    if not user:
        result = []
        for user in all_users():
            result += all_profiles(user)
        return result

    dir = CONF_PATH + '/profiles_' + user.name
    names = os.listdir(dir)
    result = []
    for name in names:
        if not name.endswith('.yml'):
            continue
        profile_name = name.rsplit('.', 1)[0]
        result.append(Profile(user, profile_name))

    return result

def load_plugins():
    from . import (
        storage, net, locale, x11, shell_launcher, sound, initxyz, shell, base, ssh,
        distro_debian, driver_lxc,
    )

if __name__ == '__main__':
    import sys
    Profile(user=User(name='michal'), name=sys.argv[1]).update_container()
