# -*- coding: utf-8 -*-

import re
if __name__ == "__main__":
  import os, django
  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Platform_Map.settings")
  django.setup()
from GetPlatformInfo.machine import Machine
from GetPlatformInfo.sqlOperator import SQLOperator
from GetPlatformInfo.sqlDisplayMachine import SQLDisplayMachine
from Display_Platform_Info.models import X_server, display_machine
import myLogging


class XServer(Machine, SQLOperator):
  xs_list = set()

  def __init__(self, login):
    super(XServer, self).__init__(login)
    self.set_filter_function(X_server.objects.filter)
    self.dm_db_inst = None
    self.active_tty = -1
    self.attr = {'Host': login,
                # 'Display_machine': None,
                 'Port': 0,
                 'Tty': 0,
                 'Active': False,
                 }

  @myLogging.log('XServer')
  def get_x_servers(self, timeout=None):
    self.set_connect_timeout(timeout)
    try:
      self.init_ssh()
    except Exception,e:
      myLogging.logger.exception('Exception when init ssh to X node %s!' % self.attr['Host'])
      return
    sql_dm = SQLDisplayMachine(self.login)
    sql_dm.set_ip(self.get_ip())
    sql_dm.set_hostname(self.get_hostname())
    sql_dm.set_thalix(self.get_thalix())
    sql_dm.save()
    self.dm_db_inst = sql_dm.db_inst
    self.execute_cmd('fgconsole')
    tmp_out = self.stdout.read().strip()
    if tmp_out:
      self.active_tty = int(tmp_out)
    self.execute_cmd('ps -ef|grep Xorg')
    for line in self.stdout:
      fields = re.split('\s+', line)
      if fields[7] == '/usr/bin/Xorg' and fields[5].find('tty') != -1:
        current_tty = int(fields[5].replace('tty', ''))
        self.attr.update({
          'Host': self.get_hostname(),
          'Tty': current_tty,
          'Port': 6000 + int(fields[8].replace(':', '') if fields[8].startswith(':') else 0),
          'Display_machine': self.get_display_machine(),
          'Active': current_tty == self.active_tty,
          })
        myLogging.logger.info(self.attr)
        self.save()
        XServer.xs_list.add(self.get_id())
    self.close_open_file()
    self.close_ssh()

  def save(self):
    self.db_inst = X_server(**self.attr)
    self.insert_or_update(self.db_inst, filters={'Host': self.attr['Host'], 'Port': self.attr['Port']})

  def get_display_machine(self):
    if self.dm_db_inst:
      return self.dm_db_inst
    dm_set = display_machine.objects.filter(Node=self.host)
    if dm_set.count():
      return dm_set[0]
    dm_set = display_machine.objects.filter(Host_name=self.get_hostname())
    if dm_set.count():
      return dm_set[0]
    dm = SQLDisplayMachine.get_inst_by_ip(self.get_ip())
    if dm:
      return dm
    return None


if __name__ == "__main__":
  myLogging.setup_logging()
  xs = XServer('127.0.0.1:11160')
  xs.get_x_servers()