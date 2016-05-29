import os
import subprocess

from . import core, common

def update_container(self):
    config = self.get_config()

    socket_path = core.RUN_PATH + '/profile-' + self.container_name  + '/ssh-agent/agent.socket'

    if not config.get('ssh-keys'):
        return

    if not os.path.exists(socket_path):
        dir_path = os.path.dirname(socket_path)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
            os.chown(dir_path, self.user.uid, self.user.gid)

        cmd = ['sudo', '-Hu', self.user.name, '--',
               'ssh-agent', '-a', socket_path]

        print('Starting SSH agent:', ' '.join(cmd))
        subprocess.check_call(cmd, stdout=open('/dev/null', 'w'))

    pubkeys = core.RUN_PATH + '/profile-' + self.container_name + '/ssh-pub/'
    common.maybe_mkdir(pubkeys)

    # TODO: remove keys
    for key in config.get('ssh-keys'):
        path = os.path.join(self.user.home + '/.ssh', key)
        cmd = ['sudo', '-Hu', self.user.name, '--', 'env', 'SSH_AUTH_SOCK=' + socket_path, 'ssh-add', '--', path]
        subprocess.check_call(cmd, stderr=open('/dev/null', 'w'))
        pubkey = subprocess.check_output(['cat', path + '.pub'])
        common.write_file(pubkeys + os.path.basename(key) + '.pub', pubkey)

def update_container_def(self, definition):
    config = self.get_config()

    if not config.get('ssh-keys'):
        return

    definition['config']['environment.SSH_AUTH_SOCK'] = '/hades/run/host/ssh-agent/agent.socket'
