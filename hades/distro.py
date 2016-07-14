from . import core
import platform

class CommonDistro:
    def __init__(self, profile):
        self.profile = profile
        self.driver = self.profile.driver
        self.user = self.profile.user

    def update(self):
        self.update_inner_user()
        self.update_hostname()

    def update_inner_user(self):
        config = self.profile.config

        passwd = self.profile.driver.get_file('/etc/passwd').decode('utf8')
        users = [ line.split(':')[0] for line in passwd.splitlines() ]

        if 'ubuntu' in users:
            self.profile.driver.run_command(['userdel', 'ubuntu'])
            # self.run_command(['groupdel', 'ubuntu'])

        if self.user.name not in users:
            self.profile.run_command(['groupadd', '--gid', str(core.INTERNAL_GID), self.user.name])
            self.profile.run_command(['useradd', '--create-home', '--uid', str(core.INTERNAL_UID), '--gid', str(core.INTERNAL_GID), self.user.name])

        self.profile.run_command(['chsh', '--shell', config.get('shell', '/bin/bash'), self.user.name])
        self.profile.run_command(['chown', '%d:%d' % (core.INTERNAL_UID, core.INTERNAL_GID), '--', self.user.home])

        config = self.profile.config
        self.driver.put_file('/etc/sudoers.d/hades-sudo',
                             'Defaults !authenticate\nDefaults env_keep += "HADES_PROFILE"\n%s   ALL=(ALL:ALL) ALL' % self.user.name if config.get('sudo') == 'allow' else '')

    def update_hostname(self):
        hostname = platform.node()
        self.driver.run_command(['hostname', '--', hostname])
        hosts = self.driver.get_file('/etc/hosts').decode('utf-8')
        hosts = '\n'.join([ line for line in hosts.splitlines() if not '# HADES HOSTNAME' in line ])
        self.driver.put_file('/etc/hosts', '127.0.0.1   ' + hostname + ' # HADES HOSTNAME\n' + hosts)

    def execute(self, args):
        # Execute command as user in the container
        cmd = ['/hades/tools/bin/hades-runas', self.profile.user.name]
        cmd += args
        return self.profile.driver.run_command_silent(cmd)

    def update_configuration(self, configuration):
        pass
