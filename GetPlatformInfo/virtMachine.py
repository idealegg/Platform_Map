# -*- coding: utf-8 -*-

from GetPlatformInfo.machine import Machine
from GetPlatformInfo.physicalMachine import HostMachine
from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import node, X_server, host_machine, platform_node_list, platform
from GetPlatformInfo.displayMachine import DisplayMachine
import re
import myLogging
import Platform_Map.settings
import os
import platform as os_pf
import time
import parseUtil


class VirMachine(Machine, SQLOperator):
  def __init__(self, vm_login, running='Y', id_in_host=-1, is_orphan=False, vm_name=""):
    SQLOperator.__init__(self)
    Machine.__init__(self, vm_login)
    self.script = ''
    self.vm_state = {'Name': self.name,
                     'Id_in_host': id_in_host,
                     'Running': running,
                     'Orphan': 'Y' if is_orphan else 'N',
                     'Vm_name': vm_name,
                     'Login': vm_login,
                     }
    self.vm_name = vm_name
    self.cmdList = None
    self.cmdOut = {}
    self.attr = self.vm_state
    self.set_filter_function(node.objects.filter)

  def set_vm_name(self, name):
    self.vm_name = name

  def save(self):
    self.db_inst = node(**self.attr)
    self.insert_or_update(self.db_inst, filters={'Name': self.attr['Name']}, kept={'Restarting'})

  def save_restarting(self, restarting):
    self.db_inst = node(**self.attr)
    self.db_inst.Restarting = restarting
    self.insert_or_update(self.db_inst, filters={'Name': self.attr['Name']},
                          kept={'Os', 'Ops_name', 'Structure', 'Host', 'Host_machine', 'Ping_reachable', 'Reachable',
                                'Controlled', 'Orphan', 'Id_in_host', 'Running', 'IP', 'Interface', 'Thalix', 'Display',
                                'X_server', 'Config', 'CSCI', 'Platform', 'Login', 'Vm_name'})

  def get_vm_db_inst(self):
    return self.get_db_inst(filters={'Name': self.attr['Name']})

  def get_x_server(self):
    if 'Display' in self.attr:
      if self.attr['Display']:
        if 'X_server' in self.attr and self.attr['X_server']:
          return self.attr['X_server']
        host, port = re.split('\s+', self.attr['Display'])
        if host.replace('.', '').isdigit():  # is ip address
          dm = DisplayMachine.get_inst_by_ip(host)
          x_set = X_server.objects.filter(Display_machine=dm, Port=port)
        else:
          x_set = X_server.objects.filter(Host=host, Port=port)
          if host[-1] in 'tsxd':
            if not x_set.count():
              x_set = X_server.objects.filter(Host=host[:-1], Port=port)
        if x_set.count():
          return x_set[0]
    return None

  @myLogging.log('VirMachine')
  def set_x_server(self, x):
    self.db_inst = node.objects.get(Name=self.attr['Name'])
    if x:
      myLogging.logger.info("Host: %s, Port: %d" % (x.Host, x.Port))
      self.db_inst.X_server = x
      self.db_inst.Display = '%s %d' %(x.Host, x.Port)
    else:
      myLogging.logger.info('Set x server to None!')
      self.db_inst.X_server = x
      self.db_inst.Display = ''
    self.db_inst.save()

  def get_host_machine(self):
    if 'Host' in self.attr:
      if self.attr['Host']:
        if 'Host_machine' in self.attr and self.attr['Host_machine']:
          return self.attr['Host_machine']
        hm_set = host_machine.objects.filter(Host_name=self.attr['Host'])
        if hm_set.count():
          return hm_set[0]
    return None

  def get_ops_name(self):
    if 'Ops_name' in self.attr:
      if self.attr['Ops_name']:
        return self.attr['Ops_name']
    return ''

  def get_platform(self):
    if 'Platform' in self.attr:
      if self.attr['Platform']:
        return self.attr['Platform']
    ns = platform_node_list.objects.filter(Node=self.attr['Name'])
    if ns.count():
      return ns[0].Platform
    return platform.objects.get(Site=SQLOperator.ORPHAN)

  @myLogging.log('VirMachine')
  def stop_mmi(self, time_out=120, check_interval=3, first_sleep=5):
    self.init_ssh()
    cmd='''
export HOME=/usr/system
. $HOME/.profile > /dev/null 2>&1
run_tools_path=$HOME/INTEG/run_tools/$RUN_TOOLS_VERS/bin

${run_tools_path}/lsc SYS_MNG STOP_MMI

sleep %d
wait_seconds=$((%d - %d))
stopped=0

while [ ${wait_seconds} -gt 0 ]
do
  ${run_tools_path}/lsc show sw|grep -w 'MMI...'|grep -e BS_GROUPEXITED -e BS_GROUPOFFLINE  > /dev/null 2>&1
  if [ $? -eq 0 ]
  then
	stopped=1
    break
  else
    wait_seconds=$((wait_seconds-%d))
    sleep %d
  fi
done

if [ ${stopped} -eq 0 ]
then
 echo " MMI group is not real exit!"
 exit 1
fi

echo "Stop MMI successfully!"
exit 0
''' % (first_sleep, time_out, first_sleep, check_interval, check_interval)
    self.execute_cmd(cmd, timeout=time_out)
    tmp_out = self.stdout.read()
    self.close_ssh()
    myLogging.logger.info(tmp_out)
    return tmp_out.count('Stop MMI successfully') != 0

  @myLogging.log('VirMachine')
  def start_mmi(self, time_out=120, check_interval=5, first_sleep=10):
    self.init_ssh()
    cmd = '''
  export HOME=/usr/system
  . $HOME/.profile > /dev/null 2>&1
  run_tools_path=$HOME/INTEG/run_tools/$RUN_TOOLS_VERS/bin

  ${run_tools_path}/lsc SYS_MNG START_MMI

  sleep %d
  wait_seconds=$((%d - %d))
  started=0

  while [ ${wait_seconds} -gt 0 ]
  do
    ${run_tools_path}/lsc show sw|grep -w 'MMI...'|grep BS_GROUPONLINE  > /dev/null 2>&1
    if [ $? -eq 0 ]
    then
  	  started=1
      break
    else
      wait_seconds=$((wait_seconds-%d))
      sleep %d
    fi
  done

  if [ ${started} -eq 0 ]
  then
   echo " MMI group is not real started!"
   exit 1
  fi

  echo "Start MMI successfully!"
  exit 0
  ''' % (first_sleep, time_out, first_sleep, check_interval, check_interval)
    self.execute_cmd(cmd, timeout=time_out)
    tmp_out = self.stdout.read()
    self.close_ssh()
    myLogging.logger.info(tmp_out)
    return tmp_out.count('Start MMI successfully') != 0

  def copy_key_mapping_files(self, x_os):
    try:
      targets = ['kbd_t1x_xf86.map_g', 'kbd_t2x_xf86.map_g', 'kbd_t2x_xf86_sup.map_g', 'kbd_t1x_xf86_prm.map_g']
      target_dir = '/usr/system/INTEG/mmi/\$MMI_VERS/data/MAPPING'
      source_dir = '/usr/system/INTEG/mmi/\$MMI_VERS/data/MAPPING'
      t12 = 'kbd_thalix12.map_g'
      t11 = 'kbd_tmx_xf86_thalix11.map_g'
      self.init_ssh()
      if x_os.count('11'):
        template=t11
      else:
        template=t12
      self.execute_cmd('ksh -lc "ls %s"' % os.path.join(source_dir, template))
      if self.check_stderr() or not Platform_Map.settings.USE_LOCAL_MAP_G:
        if os_pf.system() == "Windows":
          self.tx_file(os.path.join(Platform_Map.settings.BASE_DIR, 'static', 'map_g', template),
                     "/".join(['/usr/system', template]))
          self.execute_cmd(
            'ksh -lc "cp %s %s"' % ("/".join(['/usr/system', template]), "/".join([source_dir, template])))
        else:
          #self.tx_file("\\".join([Platform_Map.settings.BASE_DIR, 'static', 'map_g', template]), os.path.join('/usr/system', template))
          self.tx_file(os.path.join(Platform_Map.settings.BASE_DIR, 'static', 'map_g', template), os.path.join('/usr/system', template))
          self.execute_cmd(
          'ksh -lc "cp %s %s"' % (os.path.join('/usr/system', template), os.path.join(source_dir, template)))
      for f in targets:
        if os_pf.system() == "Windows":
          self.execute_cmd('ksh -lc "cp %s %s"' % ("/".join([source_dir, template]), "/".join([target_dir, f])))
        else:
          self.execute_cmd('ksh -lc "cp %s %s"' % (os.path.join(source_dir, template), os.path.join(target_dir, f)))
      self.close_ssh()
      return True
    except:
      return False

  def check_npm(self, proc='npm_main'):
    self.execute_cmd('/sbin/pidof %s' % proc)
    return self.stdout.read().strip()

  def check_ipcs(self):
    self.execute_cmd('ipcs')
    return self.stdout.read().count('system') > 10

  def is_online(self):
    self.execute_cmd('ksh -lc "lsc show system|grep %s"'% self.get_hostname())
    return self.stdout.read().count('BS_NODEONLINE')

  def check_npm_started(self):
    self.execute_cmd('/bin/ls -1 /tmp|/bin/grep "^node_starting$"')
    return not self.stdout.read().strip()

  @myLogging.log('VirMachine')
  def stop_node(self, time_out=120, check_interval=2, first_sleep=30):
    self.init_ssh()
    start_t = time.time()
    result = True
    if self.check_npm():
      self.execute_cmd('ksh -lc "stop node"')
      while self.check_npm() and (time.time() - start_t < first_sleep):
        time.sleep(check_interval)
      if self.check_npm():
        self.execute_cmd('pkill -9  npm_main')
    if self.check_ipcs():
      vm2 = VirMachine(self.login)
      vm2.set_user('system')
      vm2.init_ssh()
      vm2.execute_cmd('ksh -lc "start node"')
      while not self.check_npm() and (time.time() - start_t < time_out):
        time.sleep(check_interval)
      vm2.close_ssh()
      if not self.check_npm():
        self.close_ssh()
        myLogging.logger.info("Ipcs could not be cleared1!")
        return False
      while not self.check_npm_started() and (time.time() - start_t < time_out):
        time.sleep(check_interval)
      if not self.check_npm_started():
        self.close_ssh()
        myLogging.logger.info("Ipcs could not be cleared2!")
        return False
      self.execute_cmd('ksh -lc "stop node"')
      while self.check_ipcs() and (time.time() - start_t < time_out):
        time.sleep(check_interval)
      result = not self.check_ipcs()
    self.close_ssh()
    myLogging.logger.info("Result: %s"%result)
    return result

  @myLogging.log('VirMachine')
  def start_node(self, time_out=120, check_interval=2, first_sleep=30):
    self.init_ssh()
    start_t = time.time()
    vm2 = VirMachine(self.login)
    vm2.set_user('system')
    vm2.init_ssh()
    vm2.execute_cmd('ksh -lc "start node -silent"')
    while not self.check_npm() and (time.time() - start_t < first_sleep * 2):
      time.sleep(check_interval)
    vm2.close_ssh()
    if not self.check_npm():
      self.close_ssh()
      myLogging.logger.info("Npm could not start!")
      return False
    step_t = time.time()
    while not self.check_npm('LSCM') and (time.time() - step_t < time_out):
      time.sleep(check_interval)
    if not self.check_npm('LSCM'):
      self.close_ssh()
      myLogging.logger.info("LSCM could not start!")
      return False
    while not self.is_online() and (time.time() - start_t < time_out):
      time.sleep(check_interval*2)
    result = self.is_online()
    self.close_ssh()
    myLogging.logger.info("Result: %s" % result)
    return result

  @myLogging.log('VirMachine')
  def exec_comms(self, comms, pm=None, redirect_stderr=True, echo=False):
    if not parseUtil.get_conf():
      parseUtil.set_conf(self.get_conf_inst())
    ret = parseUtil.ping_a_node(self.attr['Name'])
    #ret = self.get_vm_db_inst().Reachable == 'N'
    myLogging.logger.info('Ping result: %d' % ret)
    if not ret:
      # The node could be reached directly, use ssh.
      # if c_node not equal vm_state['Name'], like 'umerod002lit' vs 'umerod002li'
      self.init_ssh()
      if echo:
        cmd = '\n'.join(map(lambda x: 'echo "%s";%s' (x, x), comms))
      else:
        cmd = '\n'.join(comms)
      self.execute_cmd(cmd, redirect_stderr=redirect_stderr, timeout=self.get_conf_inst().get_para_float('cmd_exec_timeout'))
      return True
    else:
        if pm:
          script = parseUtil.gen_script(map(lambda x: x.strip(), comms),
                                        self.attr['Name'],
                                        is_root=True,
                                        is_ssh=pm.is_ping_reachable(self.attr['Name'])
                                        #is_ssh=True
          )
          pm.execute_script(script, timeout=self.get_conf_inst().get_para_float('script_exec_timeout'))
          self.stdout = pm.stdout
          self.stderr = pm.stderr
          return True
        else:
          return False

  @myLogging.log('VirMachine')
  def change_x11_fw(self, x):
    err = 'Successful'
    pm = None
    new_status = 'N'
    x_host = ""
    if x:
      if x.Host != x.Login:
        ret = os.system('ping -c 1 -W 1 %s' % x.Host)
        x_host = x.Login if ret else x.Host
      else:
        x_host = x.Host
      cmd = '''
    cat << EOF > /etc/xinetd.d/x11-fw
service x11-fw
{
 disable = no
 type = UNLISTED
 socket_type = stream
 protocol = tcp
 wait = no
 user = root
 bind = 0.0.0.0
 port = 6000
 only_from = 0.0.0.0
 redirect = %s %d
}
EOF
    ''' % (x_host, x.Port)
    else:
      cmd = 'rm /etc/xinetd.d/x11-fw'
    if self.get_vm_db_inst().Running == 'N':
      pm_db = host_machine.objects.get(Host_name=self.get_vm_db_inst().Host)
      pm = HostMachine(pm_db.Login)
      pm.init_ssh()
      new_status = pm.update_vm_status({'Name': self.attr['Name'], 'Running': 'N'})
      if new_status == 'N':
        if pm.start_vm(self)['Controlled'] == 'N' or not pm.wait_vm_start(self, 30):
          err = 'Node failed to start!'
          myLogging.logger.error(err)
          pm.close_ssh()
          return err
    if not self.exec_comms([cmd, 'service xinetd reload'], pm=pm) and not pm:
      pm_db = host_machine.objects.get(Host_name=self.get_vm_db_inst().Host)
      pm = HostMachine(pm_db.Login)
      pm.init_ssh()
      self.exec_comms([cmd, 'service xinetd reload'], pm=pm)
    myLogging.logger.info("cmd result: %s" % self.stdout.read())
    self.close_ssh()
    if self.get_vm_db_inst().Running == 'N' and new_status == 'N':
      pm.stop_vm(self)
    if pm:
      pm.close_ssh()
    return err
