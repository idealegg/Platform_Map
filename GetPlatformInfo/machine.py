# -*- coding: utf-8 -*-

import ssh
from GetPlatformInfo.parseUtil import parse_cmd
import myLogging
import Platform_Map.settings
import platform


class Machine(object):
  class_connect_timeout = 2.0

  def __init__(self, login):
    super(Machine, self).__init__()
    self.PING_CMD = 'ping -c 3 -W 2 %s'
    self.SCRIPT_PATH = 'vm_execute_script.sh'
    tmp = login.split(":")
    self.login = login
    self.host = tmp[0]
    self.port = 22
    self.user = "root"
    self.passwd = "abc123"
    if len(tmp) > 1:
      self.port = int(tmp[1])
    if len(tmp) > 2:
      self.user = tmp[2]
    if len(tmp) > 3:
      self.passwd = tmp[3]
    self.ssh_client = None
    self.last_cmd = ''
    self.stdout = None
    self.stderr = None
    self.stdin = None
    self.sftp = None
    self.hostname = ''
    self.IP = ''
    self.Thalix = ''
    self.connect_timeout = None

  def set_user(self, user):
    self.user = user

  def set_host(self, host):
    self.host = host

  def set_connect_timeout(self, timeout):
    self.connect_timeout = timeout

  @classmethod
  def set_class_connect_timeout(cls, timeout):
    Machine.class_connect_timeout = timeout

  @myLogging.log("Machine")
  def init_ssh(self):
    if not self.ssh_client:
      myLogging.logger.info( "Init ssh client [%s@%s:%d]." % (self.user, self.host, self.port))
      self.ssh_client = ssh.SSHClient()
      self.ssh_client.set_missing_host_key_policy(ssh.AutoAddPolicy())
      myLogging.logger.info( "Begin to connect to [%s@%s:%d] timeout:[%f]." %
                             (self.user, self.host, self.port, self.connect_timeout or Machine.class_connect_timeout))
      self.ssh_client.connect(self.host,
                              port=self.port,
                              username=self.user,
                              password=self.passwd,
                              timeout=self.connect_timeout or Machine.class_connect_timeout)
    else:
      myLogging.logger.debug("Init ssh client again [%s@%s:%d]." % (self.user, self.host, self.port))

  @myLogging.log("Machine")
  def close_ssh(self):
    self.close_open_file()
    if self.ssh_client:
      self.ssh_client.close()
      self.ssh_client = None
    else:
      myLogging.logger.warning("ssh client is already closed!")

  @myLogging.log("Machine")
  def execute_cmd(self, cmd, redirect_stderr=True):
    myLogging.logger.info( "Run cmd '%s' in %s:%d" % (cmd, self.host, self.port))
    self.last_cmd = cmd
    if redirect_stderr:
      cmd = "%s 2>&1" % cmd
    self.stdin, self.stdout, self.stderr=self.ssh_client.exec_command(cmd)
    #print self.stdout.read()

  @myLogging.log("Machine")
  def execute_script(self, script, script_name=''):
    if not script_name:
      script_name = self.SCRIPT_PATH
    myLogging.logger.info("Run script %s in %s" % (script_name, self.host))
    local_f = "%s%s%s" % (Platform_Map.settings.BASE_DIR,
                         "\\" if platform.system() == 'Windows' else "/",
                         script_name)
    with open(local_f, 'w') as f:
      f.write(script)
    f_path="$HOME/%s" % script_name
    self.tx_file(local_f, script_name)
    self.stdin, self.stdout, self.stderr = self.ssh_client.exec_command("chmod u+x %s" % f_path)
    self.stdin, self.stdout, self.stderr = self.ssh_client.exec_command("dos2unix %s" % f_path)
    self.stdin, self.stdout, self.stderr = self.ssh_client.exec_command("%s 2>&1" % (f_path))
    # print self.stdout.read()

  @myLogging.log("Machine")
  def check_stderr(self):
    tmp_out = self.stderr.read()
    if tmp_out:
      myLogging.logger.info("stderr: %s" % tmp_out)
    return tmp_out

  @myLogging.log("Machine")
  def close_open_file(self):
    if self.stdin:
      self.stdin.close()
      self.stdin=None
    else:
      myLogging.logger.warning("stdin is already closed!")
    if self.stdout:
      self.stdout.close()
      self.stdout=None
    else:
      myLogging.logger.warning("stdout is already closed!")
    if self.stderr:
      self.stderr.close()
      self.stderr=None
    else:
      myLogging.logger.warning("stderr is already closed!")

  @myLogging.log("Machine")
  def tx_file(self, src, des):
    myLogging.logger.info("Open sftp in %s ..." % self.host)
    self.sftp = self.ssh_client.open_sftp()
    myLogging.logger.info("Put [%s] to [%s] at %s..." % (src, des, self.host))
    self.sftp.put(src, des)
    self.sftp.close()

  @myLogging.log("Machine")
  def get_hostname(self):
    if not self.hostname:
      try:
        self.execute_cmd('hostname')
        self.hostname = self.stdout.read().strip()
      except Exception, e:
        myLogging.logger.exception( "get_hostname % error: %s" % (self.host, e.message))
        self.hostname = self.host
    return self.hostname

  def get_ip(self):
    if self.IP:
      return self.IP
    cmd = '/sbin/ifconfig -a'
    self.execute_cmd(cmd)
    out = parse_cmd(cmd, self.stdout.read().split('\n'))
    return out['IP']

  def get_thalix(self):
    if self.Thalix:
      return self.Thalix
    cmd = 'cat /etc/thalix-release'
    self.execute_cmd(cmd)
    out = parse_cmd(cmd, self.stdout.read().split('\n'))
    return out['Thalix']

  @myLogging.log("Machine")
  def is_ping_reachable(self, target_host):
    cmd = self.PING_CMD % target_host
    self.execute_cmd(cmd)
    tmp = parse_cmd(cmd, self.stdout.read().split('\n'))
    myLogging.logger.debug(tmp)
    return tmp['Ping_reachable'] == "Y"