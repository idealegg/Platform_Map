# -*- coding: utf-8 -*-

from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import platform


class SQLPlatform(SQLOperator):
  def __init__(self, pf, conf):
    super(SQLPlatform, self).__init__()
    self.pf = pf
    self.attr = {'Site': conf['site'],
                 'Platform': pf,
                 'Description': conf['description'],
                 'Owner': conf['owner'],
                 'Validity': conf['validity'],
                 }
    self.set_filter_function(platform.objects.filter)

  def save(self):
    self.db_inst = platform(**self.attr)
    self.insert_or_update(self.db_inst, filters={'Site': self.attr['Site'], 'Platform': self.attr['Platform']})
