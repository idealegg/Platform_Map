# -*- coding: utf-8 -*-

import ssh
from GetPlatformInfo.parseUtil import parse_cmd
import myLogging


class Machine(object):
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

  def set_user(self, user):
    self.user = user

  @myLogging.log("Machine")
  def init_ssh(self):
    if not self.ssh_client:
      myLogging.logger.info( "Init ssh client [%s@%s:%d]." % (self.user, self.host, self.port))
      self.ssh_client = ssh.SSHClient()
      self.ssh_client.set_missing_host_key_policy(ssh.AutoAddPolicy())
      myLogging.logger.info( "Begin to connect to [%s@%s:%d]." % (self.user, self.host, self.port))
      self.ssh_client.connect(self.host, port=self.port, username=self.user, password=self.passwd)
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
  def execute_cmd(self, cmd):
    myLogging.logger.info( "Run cmd '%s' in %s:%d" % (cmd, self.host, self.port))
    self.last_cmd = cmd
    self.stdin, self.stdout, self.stderr=self.ssh_client.exec_command("%s 2>&1" % cmd)
    #print self.stdout.read()

  @myLogging.log("Machine")
  def execute_script(self, script):
    myLogging.logger.info("Run script %s in %s" % (self.SCRIPT_PATH, self.host))
    with open(self.SCRIPT_PATH, 'w') as f:
      f.write(script)
    f_path = "$HOME/%s" % self.SCRIPT_PATH
    self.tx_file(self.SCRIPT_PATH, self.SCRIPT_PATH)
    self.stdin, self.stdout, self.stderr = self.ssh_client.exec_command("chmod u+x %s" % f_path)
    self.stdin, self.stdout, self.stderr = self.ssh_client.exec_command("dos2unix %s" % f_path)
    self.stdin, self.stdout, self.stderr = self.ssh_client.exec_command("%s 2>&1" % (f_path))
    # print self.stdout.read()

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
    cmd = 'ifconfig -a'
    self.execute_cmd(cmd)
    out = parse_cmd(cmd, self.stdout.read().split('\n'))
    return out['IP']

  @myLogging.log("Machine")
  def is_ping_reachable(self, target_host):
    cmd = self.PING_CMD % target_host
    self.execute_cmd(cmd)
    tmp = parse_cmd(cmd, self.stdout.read().split('\n'))
    myLogging.logger.debug(tmp)
    return tmp['Ping_reachable'] == "Y"