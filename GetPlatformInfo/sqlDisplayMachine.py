# -*- coding: utf-8 -*-

from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import display_machine
from django.db.models import Q


class SQLDisplayMachine(SQLOperator):
  def __init__(self, n):
    super(SQLDisplayMachine, self).__init__()
    self.node = n
    self.attr = {'Node': n,
                 'IP': '',
                 'Host_name': '',
                 }
    self.set_filter_function(display_machine.objects.filter)

  def save(self):
    self.db_inst = display_machine(**self.attr)
    self.insert_or_update(self.db_inst, filters={'Node': self.attr['Node']})

  def set_ip(self, ip):
    self.attr['IP'] = ip

  def set_hostname(self, hostname):
    self.attr['Host_name'] = hostname

  @classmethod
  def get_inst_by_ip(cls, ip):
    dm_set = display_machine.objects.filter(Q(IP__contains="%s "%ip) | Q(IP__endswith=ip))
    if dm_set.count():
      return dm_set[0]
    else:
      return None
