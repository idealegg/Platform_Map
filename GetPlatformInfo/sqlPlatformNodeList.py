# -*- coding: utf-8 -*-

from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import platform_node_list
import parseUtil


class SQLPlatformNodeList(SQLOperator):
  def __init__(self, pf, login):
    super(SQLPlatformNodeList, self).__init__()
    self.platform = pf
    self.node = parseUtil.parse_login(login, check_name_only=True)
    self.attr = {'Platform': pf,
                 'Node': self.node,
                 }
    self.set_filter_function(platform_node_list.objects.filter)

  def save(self):
    self.db_inst = platform_node_list(**self.attr)
    #self.insert_or_update(self.db_inst, filters={'Platform': self.attr['Platform'], 'Node': self.attr['Node']})
    self.insert_or_update(self.db_inst, filters={'Node': self.attr['Node']})
