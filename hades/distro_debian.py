from . import distro
from . import core

@core.create_distro.register
def _create_distro(name, profile):
    if name == 'debian':
        return DebianDistro(profile)

class DebianDistro(distro.CommonDistro):
    pass
