import tempfile
import os
import subprocess

from . import core

DISPLAY_ID = ':0'

def update_container(self):
    config = self.get_config()

    localtime = os.readlink('/etc/localtime')
    self.run_command(['ln', '-sf', localtime, '/etc/localtime'])
