# -*- coding: utf-8 -*-

import re
import os
if __name__ == "__main__":
  import django
  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Platform_Map.settings")
  django.setup()
from GetPlatformInfo.machine import Machine
from GetPlatformInfo.sqlOperator import SQLOperator
from GetPlatformInfo.sqlDisplayMachine import SQLDisplayMachine
from Display_Platform_Info.models import X_server, display_machine
import myLogging
import platform as os_pf
import socket


class XServer(Machine, SQLOperator):
  xs_list = set()

  def __init__(self, login):
    SQLOperator.__init__(self)
    Machine.__init__(self, login)
    self.set_filter_function(X_server.objects.filter)
    self.dm_db_inst = None
    self.active_tty = -1
    self.resolution = 'invalid'
    self.attr = {'Host': login,
                # 'Display_machine': None,
                 'Port': 0,
                 'Tty': 0,
                 'Valid': True,
                 'Active': False,
                 }

  @myLogging.log('XServer')
  def get_x_servers(self, timeout=None):
    self.set_connect_timeout(timeout)
    try:
      self.init_ssh()
    except Exception, e:
      if e.message.find('timed out') != -1:
        myLogging.logger.warning('Display machine [%s] connect timeout! Skip it!' % self.host)
      else:
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
    tmp_out = self.stdout.read().split("\n")
    for line in tmp_out:
      fields = re.split('\s+', line)
      if (len(fields) > 8):
        if fields[7] == '/usr/bin/Xorg' and fields[5].find('tty') != -1:
          current_tty = int(fields[5].replace('tty', ''))
          self.attr.update({
            'Host': self.get_hostname(),
            'Tty': current_tty,
            'Port': 6000 + int(fields[8].replace(':', '') if fields[8].startswith(':') else 0),
            'Display_machine': self.get_display_machine(),
            'Valid': self.check_x_valid(timeout, "%s.0"%fields[8]),
            'Active': current_tty == self.active_tty,
            })
          myLogging.logger.info(self.attr)
          self.save()
          XServer.xs_list.add(self.get_id())
    sql_dm.set_resolution(self.resolution)
    sql_dm.save()
    self.dm_db_inst = sql_dm.db_inst
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

  def check_x_valid(self, timeout, ix):
    valid = False
    if os_pf.system() == "Windows":
      self.execute_cmd('xrandr -display %s' % (ix,), redirect_stderr=False, timeout=timeout)
      try:
        t_buf = self.stdout.read().split('\n')
      except socket.timeout:
        t_buf = ''
    else:
      fp = os.popen("timeout -s 9 %d xrandr -display %s%s" % (int(timeout), self.get_hostname(), ix))
      t_buf = fp.read().split('\n')
    t_2 = filter(lambda x: x.count('*'), t_buf)
    if t_2:
      t_buf = t_2[0].split()
      if self.get_thalix().count('11'):
        if len(t_buf) > 3:
          self.resolution = "".join(t_buf[1:4])
          valid = True
      else:
        if t_buf:
          self.resolution = t_buf[0]
          valid = True
    return valid


if __name__ == "__main__":
  myLogging.setup_logging()
  xs = XServer('127.0.0.1:11160')
  xs.get_x_servers()