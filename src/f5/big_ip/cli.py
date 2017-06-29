from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.cli.cli import CLI
from cloudshell.cli.command_mode import CommandMode
from cloudshell.cli.session.ssh_session import SSHSession
from cloudshell.cli.session.telnet_session import TelnetSession
from cloudshell.shell.core.context_utils import get_attribute_by_name
from log_helper import LogHelper


class Cli:
    class UnImplementedCliConnectionType(Exception):
        pass

    class UnSupportedCliConnectionType(Exception):
        pass

    def __init__(self, context):
        self.context = context
        self.logger = LogHelper.get_logger(context)

        self.connection_type = get_attribute_by_name(context=self.context, attribute_name='CLI Connection Type')
        self.prompt_regex = get_attribute_by_name(context=self.context, attribute_name='CLI Prompt Regular Expression')
        self.mode = CommandMode(self.prompt_regex)

        self.session_types = None
        self._set_session_types()

    def get_session(self):
        return CLI().get_session(self.session_types, self.mode, self.logger)

    def _set_session_types(self):
        self._cs_session_handler()

        if self.connection_type == 'Auto':
            self.session_types = [SSHSession(host=self.address,
                                             username=self.user,
                                             password=self.cs_session.DecryptPassword(self.password_hash).Value),
                                  TelnetSession(host=self.address,
                                                username=self.user,
                                                password=self.cs_session.DecryptPassword(self.password_hash).Value)]
        elif self.connection_type == 'Console':
            message = 'Unimplemented CLI Connection Type: "%s"' % self.connection_type
            self.logger.error(message)
            raise Cli.UnImplementedCliConnectionType(message)
        elif self.connection_type == 'SSH':
            self.session_types = [SSHSession(host=self.address,
                                             username=self.user,
                                             password=self.cs_session.DecryptPassword(self.password_hash).Value)]
        elif self.connection_type == 'TCP':
            message = 'Unimplemented CLI Connection Type: "%s"' % self.connection_type
            self.logger.error(message)
            raise Cli.UnImplementedCliConnectionType(message)
        elif self.connection_type == 'Telnet':
            self.session_types = [TelnetSession(host=self.address,
                                                username=self.user,
                                                password=self.cs_session.DecryptPassword(self.password_hash).Value)]
        else:
            message = 'Unsupported CLI Connection Type: "%s"' % self.connection_type
            self.logger.error(message)
            raise Cli.UnSupportedCliConnectionType(message)

    def _cs_session_handler(self):
        self.address = self.context.resource.address
        self.user = self.context.resource.attributes['User']
        self.password_hash = self.context.resource.attributes['Password']

        domain = None
        try:
            domain = self.context.reservation.domain
        except AttributeError:
            domain = 'Global'

        self.cs_session = CloudShellAPISession(host=self.context.connectivity.server_address,
                                               token_id=self.context.connectivity.admin_auth_token,
                                               domain=domain)
