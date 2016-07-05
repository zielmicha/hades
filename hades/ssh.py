import os
import subprocess

from . import core, common

@core.update_profile.register
def update_profile(profile):
    config = profile.config

    socket_path = core.RUN_PATH + '/profile-' + profile.full_name  + '/ssh-agent/agent.socket'

    if not config.get('ssh-keys'):
        return

    if not os.path.exists(socket_path):
        dir_path = os.path.dirname(socket_path)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
            os.chown(dir_path, profile.user.uid, profile.user.gid)

        cmd = ['sudo', '-Hu', profile.user.name, '--',
               'ssh-agent', '-a', socket_path]

        print('Starting SSH agent:', ' '.join(cmd))
        subprocess.check_call(cmd, stdout=open('/dev/null', 'w'))

    pubkeys = core.RUN_PATH + '/profile-' + profile.full_name + '/ssh-pub/'
    common.maybe_mkdir(pubkeys)

    # TODO: remove keys
    for key in config.get('ssh-keys'):
        path = os.path.join(profile.user.home + '/.ssh', key)
        cmd = ['sudo', '-Hu', profile.user.name, '--', 'env', 'SSH_AUTH_SOCK=' + socket_path, 'ssh-add', '--', path]
        subprocess.check_call(cmd, stderr=open('/dev/null', 'w'))
        pubkey = subprocess.check_output(['cat', path + '.pub'])
        common.write_file(pubkeys + os.path.basename(key) + '.pub', pubkey)

@core.update_configuration.register
def update_configuration(profile, configuration):
    config = profile.config

    if not config.get('ssh-keys'):
        return

    configuration.add_env('environment.SSH_AUTH_SOCK', '/hades/run/host/ssh-agent/agent.socket')
