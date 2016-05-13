import subprocess
import os

from . import core
from .common import maybe_mkdir

# TODO: create apparmor profile for PulseAudio server

def is_pulseaudio_running(self):
    pulseaudio = ['sudo', '-Hu', self.user.name, '--',
                  'pulseaudio', '--check']
    return subprocess.call(pulseaudio) == 0

def get_socket_path(self):
    return core.RUN_PATH + '/pulse-' + self.user.name + '/pulseaudio.socket'

def start_pulseaudio(self):
    subprocess.check_call(['adduser', self.user.name, 'audio'])

    conf_dir = '/etc/pulse/daemon.conf.d'
    maybe_mkdir(conf_dir)

    with open(conf_dir + '/disable-idle.conf', 'w') as f:
        f.write('exit-idle-time = -1\n')

    sock_dir = os.path.dirname(get_socket_path(self))
    maybe_mkdir(sock_dir)
    os.chown(sock_dir, self.user.uid, self.user.gid)

    with open('/etc/pulse/hades.pa', 'w') as f:
        f.write("load-module module-native-protocol-unix socket=%s auth-anonymous=1\n" % get_socket_path(self))
        # f.write("load-module module-cli-protocol-unix socket=%s-cli\n" % get_socket_path(self))

    pulseaudio = ['sudo', '-Hu', self.user.name, '--',
                  'pulseaudio', '-F', '/etc/pulse/hades.pa', '--disallow-exit', '--disallow-module-loading',
                  '--disable-shm=true', # containers can't access host shared memory
                  '--log-target=syslog']

    print('Starting pulseaudio: ', ' '.join(pulseaudio))
    subprocess.Popen(pulseaudio)

def update_container(self):
    config = self.get_config()

    if not config.get('sound'):
        return

    if not is_pulseaudio_running(self):
        start_pulseaudio(self)

    self.put_file('/etc/sudoers.d/pulse-allow',
                  'Defaults env_keep += "PULSE_SERVER"\n')

def update_container_def(self, definition):
    config = self.get_config()

    if not config.get('sound'):
        return

    maybe_mkdir(os.path.dirname(get_socket_path(self)))

    definition['devices']['pulse'] = {
        'type': 'disk',
        'path': '/opt/hadespulse',
        'source': os.path.dirname(get_socket_path(self))
    }
    definition['config']['environment.PULSE_SERVER'] = 'unix:/opt/hadespulse/pulseaudio.socket'
