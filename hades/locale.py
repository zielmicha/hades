import tempfile
import os
import subprocess

from . import core

DISPLAY_ID = ':0'

@core.update_profile.register
def update_profile(profile):
    # TODO: move this to distro
    try:
        localtime = os.readlink('/etc/localtime')
    except OSError:
         print('Failed to read timezone. Please run dpkg-reconfigure tzdata on host.')
         return
    profile.run_command(['ln', '-sf', localtime, '/etc/localtime'])
