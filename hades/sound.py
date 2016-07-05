import subprocess
import os

from . import core
from .common import maybe_mkdir

# TODO: create apparmor profile for PulseAudio server

def is_pulseaudio_running(profile):
    pulseaudio = ['sudo', '-Hu', profile.user.name, '--',
                  'pulseaudio', '--check']
    return subprocess.call(pulseaudio) == 0

def get_socket_path(profile):
    return core.RUN_PATH + '/pulse-' + profile.user.name + '/pulseaudio.socket'

def start_pulseaudio(profile):
    subprocess.check_call(['adduser', profile.user.name, 'audio'])

    conf_dir = '/etc/pulse/daemon.conf.d'
    maybe_mkdir(conf_dir)

    with open(conf_dir + '/disable-idle.conf', 'w') as f:
        f.write('exit-idle-time = -1\n')

    sock_dir = os.path.dirname(get_socket_path(profile))
    maybe_mkdir(sock_dir)
    os.chown(sock_dir, profile.user.uid, profile.user.gid)

    with open('/etc/pulse/hades.pa', 'w') as f:
        f.write("load-module module-native-protocol-unix socket=%s auth-anonymous=1\n" % get_socket_path(profile))
        # f.write("load-module module-cli-protocol-unix socket=%s-cli\n" % get_socket_path(profile))

    pulseaudio = ['sudo', '-Hu', profile.user.name, '--',
                  'pulseaudio', '-F', '/etc/pulse/hades.pa', '--disallow-exit', '--disallow-module-loading',
                  '--disable-shm=true', # containers can't access host shared memory
                  '--log-target=syslog']

    print('Starting pulseaudio: ', ' '.join(pulseaudio))
    subprocess.Popen(pulseaudio)

@core.update_profile.register
def update_profile(profile):
    config = profile.config

    if not config.get('sound'):
        return

    if not is_pulseaudio_running(profile):
        start_pulseaudio(profile)

    profile.driver.put_file('/etc/sudoers.d/pulse-allow',
                            'Defaults env_keep += "PULSE_SERVER"\n')

@core.update_configuration.register
def update_configuration(profile, configuration):
    config = profile.config

    if not config.get('sound'):
        return

    maybe_mkdir(os.path.dirname(get_socket_path(profile)))

    configuration.add_mount('/hades/run/pulse', os.path.dirname(get_socket_path(profile)))
    configuration.add_env('PULSE_SERVER', 'unix:/hades/run/pulse/pulseaudio.socket')
