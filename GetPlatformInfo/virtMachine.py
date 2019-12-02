# -*- coding: utf-8 -*-

from GetPlatformInfo.machine import Machine
from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import node, X_server, host_machine, platform_node_list, platform
from GetPlatformInfo.sqlDisplayMachine import SQLDisplayMachine
import re
import myLogging


class VirMachine(Machine, SQLOperator):
  def __init__(self, vm_host, running='Y', id_in_host=-1, is_orphan=False):
    super(VirMachine, self).__init__(vm_host)
    self.script = ''
    self.vm_state = {'Name': vm_host,
                     'Id_in_host': id_in_host,
                     'Running': running,
                     'Orphan': 'Y' if is_orphan else 'N',
                     }
    self.cmdList = None
    self.cmdOut = {}
    self.attr = self.vm_state
    self.set_filter_function(node.objects.filter)

  def save(self):
    self.db_inst = node(**self.attr)
    self.insert_or_update(self.db_inst, filters={'Name': self.attr['Name']})

  def get_vm_db_inst(self):
    return self.get_db_inst(filters={'Name': self.attr['Name']})

  def get_x_server(self):
    if 'Display' in self.attr:
      if self.attr['Display']:
        if 'X_server' in self.attr and self.attr['X_server']:
          return self.attr['X_server']
        host, port = re.split('\s+', self.attr['Display'])
        if host.replace('.', '').isdigit():  # is ip address
          dm = SQLDisplayMachine.get_inst_by_ip(host)
          x_set = X_server.objects.filter(Display_machine=dm, Port=port)
        else:
          x_set = X_server.objects.filter(Host=host, Port=port)
        if x_set.count():
          return x_set[0]
    return None

  @myLogging.log('VirMachine')
  def set_x_server(self, x):
    self.db_inst = node.objects.get(Name=self.attr['Name'])
    self.db_inst.X_server = x
    self.db_inst.Display = '%s %d' %(x.Host, x.Port)
    self.db_inst.save()


  def get_host_machine(self):
    if 'Host' in self.attr:
      if self.attr['Host']:
        if 'Host_Machine' in self.attr and self.attr['Host_Machine']:
          return self.attr['Host_Machine']
        hm_set = host_machine.objects.filter(Host_name=self.attr['Host'])
        if hm_set.count():
          return hm_set[0]
    return None

  def get_ops_name(self):
    if 'OPS_Name' in self.attr:
      if self.attr['OPS_Name']:
        return self.attr['OPS_Name']
    return ''

  def get_platform(self):
    if 'Platform' in self.attr:
      if self.attr['Platform']:
        return self.attr['Platform']
    ns = platform_node_list.objects.filter(Node=self.attr['Name'])
    if ns.count():
      return ns[0].Platform
    return platform.objects.get(Site=SQLOperator.ORPHAN)




