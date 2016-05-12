from . import core

def expanduser(self, path):
    if path.startswith('~/'):
        return self.user.home + '/' + path[2:]
    else:
        return path

def update_container(self):
    config = self.get_config()

def update_container_def(self, definition):
    config = self.get_config()
    for i, conf in enumerate(config.get('files', [])):
        path = expanduser(self, conf['path'])
        source = conf.get('source')
        if source:
            source = expanduser(self, source)
        else:
            source = path

        definition['devices']['files%d' % i] = {
            'type': 'disk',
            'path': path,
            'source': source,
            'readonly': 'true' if (conf.get('readonly')) else 'false'
        }
