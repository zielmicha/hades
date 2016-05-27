import tempfile
import os
import subprocess

from . import core

DISPLAY_ID = ':0'

def update_container(self):
    config = self.get_config()

    try:
        localtime = os.readlink('/etc/localtime')
    except OSError:
         print('Failed to read timezone. Please run dpkg-reconfigure tzdata on host.')
         return
    self.run_command(['ln', '-sf', localtime, '/etc/localtime'])
