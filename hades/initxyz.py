from . import core

@core.update_profile.register
def update_profile(profile):
    config = profile.config.get('initxyz')

    if config:
        bin = profile.user.home + '/init.xyz/bin/initxyz'
        profile.execute([bin, 'init', profile.user.home + '/configs.xyz'])
        for name in config['profiles']: # TODO: disable
            profile.execute([bin, 'enable', name])
        # self.execute([bin, 'reload', '--silent'])

@core.update_configuration.register
def update_configuration(profile, configuration):
    config = profile.config
    home = profile.user.home

    if config.get('initxyz'):
        configuration.add_mount(home + '/configs.xyz', home + '/configs.xyz', readonly=True)
        configuration.add_mount(home + '/init.xyz', home + '/init.xyz', readonly=True)
