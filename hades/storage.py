from . import core

def expanduser(self, path):
    if path.startswith('~/'):
        return self.user.home + '/' + path[2:]
    else:
        return path

@core.update_configuration.register
def update_configuration(profile, configuration):
    config = profile.config
    for i, conf in enumerate(config.get('files', [])):
        path = expanduser(profile, conf['path'])
        source = conf.get('source')
        if source:
            source = expanduser(self, source)
        else:
            source = path

        configuration.add_mount(path, source, bool(conf.get('readonly')))

    for conf in config.get('devices', []):
        configuration.add_block_device(conf['path'], conf['path'])
