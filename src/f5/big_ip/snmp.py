import os

from cloudshell.shell.core.context_utils import get_attribute_by_name
from cloudshell.snmp.quali_snmp import QualiSnmp
from cloudshell.snmp.snmp_parameters import SNMPV3Parameters, SNMPV2Parameters
from log_helper import LogHelper


class Snmp:
    def __init__(self, context, action='get'):
        action = action.lower()

        self.context = context
        self.logger = LogHelper.get_logger(context)

        self.address = self.context.resource.address
        self.community_read = get_attribute_by_name(context=self.context, attribute_name='SNMP Read Community') or 'public'
        self.community_write = get_attribute_by_name(context=self.context, attribute_name='SNMP Write Community') or 'private'
        self.password = get_attribute_by_name(context=self.context, attribute_name='SNMP Password') or '',
        self.user = get_attribute_by_name(context=self.context, attribute_name='SNMP User') or '',
        self.version = get_attribute_by_name(context=self.context, attribute_name='SNMP Version')
        self.private_key = get_attribute_by_name(context=self.context, attribute_name='SNMP Private Key')

        handler = None
        if action in ('get', 'set'):
            handler = self._get_handler(action)
        else:
            raise Exception('Unsupported SNMP action: %s' % action)

        self.handler = handler
        self._test_handler()

    def _get_handler(self, action):
        mib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mibs'))
        snmp_parameters = self._get_snmp_parameters(action)

        handler = QualiSnmp(snmp_parameters, self.logger)
        handler.update_mib_sources(mib_path)
        handler.load_mib(['F5-BIGIP-COMMON-MIB', 'F5-BIGIP-SYSTEM-MIB'])

        return handler

    def _get_snmp_parameters(self, action):
        action = action.lower()

        if '3' in self.version:
            return SNMPV3Parameters(ip=self.address,
                                    snmp_user=self.user,
                                    snmp_password=self.password,
                                    snmp_private_key=self.private_key)
        else:
            if action == 'set':
                community = self.community_write
            elif action == 'get':
                community = self.community_read
            else:
                raise Exception('Unsupported SNMP action: %s' % action)

            return SNMPV2Parameters(ip=self.address, snmp_community=community)

    def _test_handler(self):
        self.handler.get_property('SNMPv2-MIB', 'sysName', 0)
