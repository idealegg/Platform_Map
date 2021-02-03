# -*- coding: utf-8 -*-

from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import display_machine
from django.db.models import Q
from GetPlatformInfo.machine import Machine


class DisplayMachine(Machine, SQLOperator):
  def __init__(self, login):
    SQLOperator.__init__(self)
    Machine.__init__(self, login)
    self.attr = {'Name': self.name,
                 'IP': '',
                 'Host_name': '',
                 'Thalix': '11.0',
                 'Resolution': '',
                 'X_ver': '',
                 'Login': login,
                 }
    self.set_filter_function(display_machine.objects.filter)

  def save(self, is_init=False):
    self.db_inst = display_machine(**self.attr)
    if not is_init:
      self.insert_or_update(self.db_inst, filters={'Name': self.attr['Name']}, kept={'Owner'})
    else:
      self.insert_or_update(self.db_inst, filters={'Name': self.attr['Name']}, kept={'IP', 'Host_name', 'Thalix', 'Owner', 'Resolution', 'X_ver', 'Login'})

  def set_ip(self, ip):
    self.attr['IP'] = ip

  def set_hostname(self, hostname):
    self.attr['Host_name'] = hostname

  def set_thalix(self, thalix):
    self.attr['Thalix'] = thalix

  def set_resolution(self, resolution):
    self.attr['Resolution'] = resolution

  def set_x_ver(self, ver):
    self.attr['X_ver'] = ver

  @classmethod
  def get_inst_by_ip(cls, ip):
    dm_set = display_machine.objects.filter(Q(IP__contains="%s "%ip) | Q(IP=ip) | Q(IP__endswith=" %s"%ip))
    if dm_set.count():
      return dm_set[0]
    else:
      return None
