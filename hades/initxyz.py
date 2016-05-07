
def update_container(self):
    config = self.get_config()
    config = config.get('initxyz')

    if config:
        bin = self.user.home + '/init.xyz/bin/initxyz'
        self.execute([bin, 'init', self.user.home + '/configs.xyz'])
        for profile in config['profiles']: # TODO: disable
            self.execute([bin, 'enable', profile])
        self.execute([bin, 'reload', '--silent'])

def update_container_def(self, definition):
    config = self.get_config()
    if config.get('initxyz'):
        definition['devices']['configsxyz'] = {
            'type': 'disk',
            'path': self.user.home + '/configs.xyz',
            'source': self.user.home + '/configs.xyz',
            'readonly': 'true',
        }
        definition['devices']['initxyz'] = {
            'type': 'disk',
            'path': self.user.home + '/init.xyz',
            'source': self.user.home + '/init.xyz',
            'readonly': 'true',
        }
