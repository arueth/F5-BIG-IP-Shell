from cloudshell.shell.core.context_utils import get_attribute_by_name
from f5.big_ip.auto_load.auto_load import AutoLoad
from f5.big_ip.cli import Cli
from log_helper import LogHelper
from re import sub


class Shell:
    def __init__(self, context):
        self.context = context
        self.logger = LogHelper.get_logger(self.context)

    def run_command(self, command):
        cli = Cli(self.context)

        with cli.get_session() as default_session:
            output = default_session.send_command(command)

        return sub(cli.prompt_regex, '', output)

    def get_inventory(self):
        enable_snmp = True
        set_snmp_allowed_addresses = True

        retry = True
        while retry:
            try:
                retry = False
                auto_load = AutoLoad(self.context)
            except Exception as e:
                self.logger.debug('Exception message: "%s"' % e.message)
                if e.message == 'Snmp attributes or host IP are not valid\nNo SNMP response received before timeout':
                    if enable_snmp:
                        enable_snmp = False
                        set_snmp_allowed_addresses = False
                        self.enable_snmp()

                        retry = True
                    elif set_snmp_allowed_addresses:
                        set_snmp_allowed_addresses = False
                        self.set_snmp_allowed_addresses()

                        retry = True
                    else:
                        raise e
                else:
                    raise e
            else:
                break

        return_value = auto_load.auto_load()

        return return_value

    def enable_snmp(self):
        self.set_snmp_allowed_addresses()
        pass

    def set_snmp_allowed_addresses(self, allowed_address_string=None):
        if allowed_address_string is None:
            allowed_address_string = get_attribute_by_name(context=self.context, attribute_name='SNMP Allowed Addresses')

        allowed_address_list = filter(None, [address.strip() for address in allowed_address_string.split(',')])

        output = ''
        if allowed_address_list:
            cli = Cli(self.context)

            with cli.get_session() as session:
                command = 'tmsh modify sys snmp allowed-addresses add { %s }' % ' '.join(allowed_address_list)
                output = '%s\n' % sub(cli.prompt_regex, '', session.send_command(command))

                command = 'tmsh show running-config sys snmp allowed-addresses'
                output += sub(cli.prompt_regex, '', session.send_command(command))

        self.logger.debug('output: %s' % output)
        return output
