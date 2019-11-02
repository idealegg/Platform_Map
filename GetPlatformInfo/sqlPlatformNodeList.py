# -*- coding: utf-8 -*-

from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import platform_node_list


class SQLPlatformNodeList(SQLOperator):
  def __init__(self, pf, n):
    super(SQLPlatformNodeList, self).__init__()
    self.platform = pf
    self.node = n
    self.attr = {'Platform': pf,
                 'Node': n,
                 }
    self.set_filter_function(platform_node_list.objects.filter)

  def save(self):
    self.db_inst = platform_node_list(**self.attr)
    #self.insert_or_update(self.db_inst, filters={'Platform': self.attr['Platform'], 'Node': self.attr['Node']})
    self.insert_or_update(self.db_inst, filters={'Node': self.attr['Node']})
