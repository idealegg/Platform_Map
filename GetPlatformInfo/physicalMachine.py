# -*- coding: utf-8 -*-

import re
from GetPlatformInfo.machine import Machine
from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import host_machine
import myLogging
import parseUtil
import os


class HostMachine(Machine, SQLOperator):
  def __init__(self, login):
    SQLOperator.__init__(self)
    Machine.__init__(self, login)
    self.VMListPattern = re.compile('^\s*(\d+|-)\s+(\w+)\s+([\w ]+)')
    self.START_VM = 'virsh start %s'
    self.STOP_VM = 'virsh shutdown %s'
    self.vmInfo = []
    self.VmList = []
    self.attr = {'Login': login,
                 'Name': self.name}
    self.set_filter_function(host_machine.objects.filter)

  @myLogging.log('HostMachine')
  def get_vm_ist(self):
    cmd = "virsh list --all"
    try:
      self.execute_cmd(cmd)
      self.VmList = []
      for line in self.stdout:
        # print line
        res = re.search(self.VMListPattern, line)
        if res:
          id_tmp = res.group(1)
          vm = {'Id_in_host': int(id_tmp) if id_tmp != '-' else 0,
                'Name': res.group(2),
                'Running': 'Y' if res.group(3) == 'running' else 'N',
                'Host': self.get_hostname(),
                }
          self.VmList.append(vm)
      self.close_open_file()
      return True
    except:
      myLogging.logger.exception( "Execute cmd '%s' in %s error!" % (cmd, self.name))
      return False

  def start_vm(self, vm):
    cmd = self.START_VM % vm.vm_name
    self.execute_cmd(cmd)
    tmp = parseUtil.parse_cmd(cmd, self.stdout.read().split('\n'))
    return tmp

  def stop_vm(self, vm):
    cmd = self.STOP_VM % vm.vm_name
    self.execute_cmd(cmd)
    tmp = parseUtil.parse_cmd(cmd, self.stdout.read().split('\n'))
    return tmp['Controlled'] == 'Y'

  def wait_vm_start(self, vm, times):
    cmd = "ping -c 1 -W 1 %s" % vm.host
    while times > 0:
      self.execute_cmd(cmd)
      tmp = parseUtil.parse_cmd(cmd, self.stdout.read().split('\n'))
      if tmp['Ping_reachable'] == 'Y':
        return True
      times -= 1
    return False

  def save(self):
    self.db_inst = host_machine(**self.attr)
    self.insert_or_update(self.db_inst, filters={'Name': self.attr['Name']})

  def update_hostname(self):
    self.attr['Host_name'] = self.get_hostname()
    self.save()

  # only update status, ignore other diff
  def update_vm_status(self, vm_state):
    self.get_vm_ist()
    for vm in self.VmList:
      if parseUtil.node_equal(vm['Name'], vm_state['Name']):
        return vm['Running']
    return vm_state['Running']
