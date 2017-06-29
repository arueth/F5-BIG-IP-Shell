from f5.big_ip.snmp import Snmp
from cloudshell.shell.core.context import AutoLoadAttribute, AutoLoadDetails, AutoLoadResource
from log_helper import LogHelper


class Attribute(AutoLoadAttribute):
    def __init__(self, relative_address, attribute_name, attribute_value):
        self.relative_address = relative_address
        self.attribute_name = attribute_name
        self.attribute_value = attribute_value


class Resource(AutoLoadResource):
    def __init__(self, name, model, relative_address, unique_identifier):
        self.name = name
        self.model = model
        self.relative_address = relative_address
        self.unique_identifier = unique_identifier


class AutoLoad:
    def __init__(self, context):
        self.context = context
        self.logger = LogHelper.get_logger(self.context)
        self.snmp = Snmp(self.context, 'get')

        self.resource_address = self.context.resource.address

    def auto_load(self):
        rv = AutoLoadDetails()
        rv.resources = []
        rv.attributes = []

        rv.attributes.append(Attribute(relative_address='',
                                       attribute_name='Contact Name',
                                       attribute_value=self.snmp.handler.get_property('SNMPv2-MIB', 'sysContact', 0)))

        rv.attributes.append(Attribute(relative_address='',
                                       attribute_name='Location',
                                       attribute_value=self.snmp.handler.get_property('SNMPv2-MIB', 'sysLocation', 0)))

        rv.attributes.append(Attribute(relative_address='',
                                       attribute_name='Model',
                                       attribute_value=self.snmp.handler.get_property('F5-BIGIP-SYSTEM-MIB', 'sysPlatformInfoMarketingName', 0)))

        rv.attributes.append(Attribute(relative_address='',
                                       attribute_name='OS Version',
                                       attribute_value='%s b%s %s' % (self.snmp.handler.get_property('F5-BIGIP-SYSTEM-MIB', 'sysProductVersion', 0),
                                                                      self.snmp.handler.get_property('F5-BIGIP-SYSTEM-MIB', 'sysProductBuild', 0),
                                                                      self.snmp.handler.get_property('F5-BIGIP-SYSTEM-MIB', 'sysProductEdition', 0))))

        rv.attributes.append(Attribute(relative_address='',
                                       attribute_name='System Name',
                                       attribute_value=self.snmp.handler.get_property('SNMPv2-MIB', 'sysName', 0)))

        rv.attributes.append(Attribute(relative_address='',
                                       attribute_name='Vendor',
                                       attribute_value='F5 Networks'))

        rv.resources.append(Resource(name='Chassis',
                                     model='Generic Chassis',
                                     relative_address='chassis',
                                     unique_identifier="%s-Chassis" % self.resource_address))

        rv.attributes.append(Attribute(relative_address='chassis',
                                       attribute_name='Serial Number',
                                       attribute_value=self.snmp.handler.get_property('F5-BIGIP-SYSTEM-MIB', 'sysGeneralChassisSerialNum', 0)))

        interface_table = self.snmp.handler.get_table('F5-BIGIP-SYSTEM-MIB', 'sysInterfaceTable')
        for index, attribute in interface_table.iteritems():
            interface_name = attribute['sysInterfaceName']

            if interface_name != 'mgmt':
                port_name = 'Port %s' % interface_name
                port_relative_address = 'chassis/port%s' % interface_name
                rv.resources.append(Resource(name=port_name,
                                             model='Generic Port',
                                             relative_address=port_relative_address,
                                             unique_identifier='%s-Chassis-Port%s' % (self.resource_address, interface_name)))

                if_speed = attribute['sysInterfaceMediaMaxSpeed']
                rv.attributes.append(Attribute(relative_address=port_relative_address,
                                               attribute_name='Bandwidth',
                                               attribute_value=if_speed))

                if_duplex = attribute['sysInterfaceMediaMaxDuplex'].capitalize()
                rv.attributes.append(Attribute(relative_address=port_relative_address,
                                               attribute_name='Duplex',
                                               attribute_value=if_duplex if if_duplex in ('Half', 'Full') else 'Full'))

                if_mac_addr = attribute['sysInterfaceMacAddr']
                rv.attributes.append(Attribute(relative_address=port_relative_address,
                                               attribute_name='MAC Address',
                                               attribute_value=if_mac_addr))

                if_mtu = attribute['sysInterfaceMtu']
                rv.attributes.append(Attribute(relative_address=port_relative_address,
                                               attribute_name='MTU',
                                               attribute_value=if_mtu))

        ps_table = self.snmp.handler.get_table('F5-BIGIP-SYSTEM-MIB', 'sysChassisPowerSupplyTable')
        for index, attribute in ps_table.iteritems():
            ps_status = attribute['sysChassisPowerSupplyStatus']  # INTEGER { 'bad'(0), 'good'(1), 'notpresent'(2) }

            if ps_status != "'notpresent'":
                ps_index = attribute['sysChassisPowerSupplyIndex']
                ps_name = 'PP %s' % ps_index
                port_relative_address = 'chassis/pp%s' % ps_index
                rv.resources.append(Resource(name=ps_name,
                                             model='Generic Power Port',
                                             relative_address=port_relative_address,
                                             unique_identifier='%s-Chassis-PP%s' % (self.resource_address, ps_index)))

        return rv
