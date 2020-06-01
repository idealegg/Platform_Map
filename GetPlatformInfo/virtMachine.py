# -*- coding: utf-8 -*-

from GetPlatformInfo.machine import Machine
from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import node, X_server, host_machine, platform_node_list, platform
from GetPlatformInfo.sqlDisplayMachine import SQLDisplayMachine
import re
import myLogging
import Platform_Map.settings
import os
import platform as os_pf
import time


class VirMachine(Machine, SQLOperator):
  def __init__(self, vm_host, running='Y', id_in_host=-1, is_orphan=False):
    super(VirMachine, self).__init__(vm_host)
    self.script = ''
    self.vm_state = {'Name': vm_host,
                     'Id_in_host': id_in_host,
                     'Running': running,
                     'Orphan': 'Y' if is_orphan else 'N',
                     }
    self.cmdList = None
    self.cmdOut = {}
    self.attr = self.vm_state
    self.conf_name = self.vm_state['Name']
    self.set_filter_function(node.objects.filter)

  def set_conf_name(self, name):
    self.conf_name = name
    self.attr['Name'] = name

  def set_name(self, name):
    self.attr['Name'] = name

  def save(self):
    if self.conf_name != self.attr['Name']:
      self.attr['Name'] = self.conf_name
    self.db_inst = node(**self.attr)
    self.insert_or_update(self.db_inst, filters={'Name': self.attr['Name']}, kept={'Restarting'})

  def save_restarting(self, restarting):
    if self.conf_name != self.attr['Name']:
      self.attr['Name'] = self.conf_name
    self.db_inst = node(**self.attr)
    self.db_inst.Restarting = restarting
    self.insert_or_update(self.db_inst, filters={'Name': self.attr['Name']},
                          kept={'Os', 'OPS_Name', 'Structure', 'Host', 'Host_Machine', 'Ping_reachable', 'Reachable',
                                'Controlled', 'Orphan', 'Id_in_host', 'Running', 'IP', 'Interface', 'Thalix', 'Display',
                                'X_server', 'Config', 'CSCI', 'Platform'})

  def get_vm_db_inst(self):
    return self.get_db_inst(filters={'Name': self.attr['Name']})

  def get_x_server(self):
    if 'Display' in self.attr:
      if self.attr['Display']:
        if 'X_server' in self.attr and self.attr['X_server']:
          return self.attr['X_server']
        host, port = re.split('\s+', self.attr['Display'])
        if host.replace('.', '').isdigit():  # is ip address
          dm = SQLDisplayMachine.get_inst_by_ip(host)
          x_set = X_server.objects.filter(Display_machine=dm, Port=port)
        else:
          x_set = X_server.objects.filter(Host=host, Port=port)
          if host.endswith('t') or host.endswith('s') or host.endswith('x'):
            if not x_set.count():
              x_set = X_server.objects.filter(Host=host[:-1], Port=port)
        if x_set.count():
          return x_set[0]
    return None

  @myLogging.log('VirMachine')
  def set_x_server(self, x):
    myLogging.logger.info("Host: %s, Port: %d" % (x.Host, x.Port))
    self.db_inst = node.objects.get(Name=self.attr['Name'])
    self.db_inst.X_server = x
    self.db_inst.Display = '%s %d' %(x.Host, x.Port)
    self.db_inst.save()

  def get_host_machine(self):
    if 'Host' in self.attr:
      if self.attr['Host']:
        if 'Host_Machine' in self.attr and self.attr['Host_Machine']:
          return self.attr['Host_Machine']
        hm_set = host_machine.objects.filter(Host_name=self.attr['Host'])
        if hm_set.count():
          return hm_set[0]
    return None

  def get_ops_name(self):
    if 'OPS_Name' in self.attr:
      if self.attr['OPS_Name']:
        return self.attr['OPS_Name']
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
    self.execute_cmd(cmd)
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
    self.execute_cmd(cmd)
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
      if self.check_stderr():
        if os_pf.system() == "Windows":
          self.tx_file(os.path.join(Platform_Map.settings.BASE_DIR, 'static', 'map_g', template),
                     "/".join(['/usr/system', template]))
          self.execute_cmd(
            'ksh -lc "cp %s %s"' % ("/".join(['/usr/system', template]), "/".join([source_dir, template])))
        else:
          self.tx_file("\\".join([Platform_Map.settings.BASE_DIR, 'static', 'map_g', template]), os.path.join('/usr/system', template))
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

  @myLogging.log('VirMachine')
  def stop_node(self, time_out=120, check_interval=3, first_sleep=5):
    self.init_ssh()
    cmd='''
export HOME=/usr/system
. $HOME/.profile > /dev/null 2>&1
run_tools_path=$HOME/INTEG/run_tools/$RUN_TOOLS_VERS/bin

${run_tools_path}/stop node

sleep %d

wait_seconds=$((%d - %d ))
stopped=0
hostname=`hostname`

while [ ${wait_seconds} -gt 0 ]
do
  ps -o pid,comm -A | grep npm_main > /dev/null 2>&1
  if [ $? -ne 0 ]
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
 echo "Node is not real exit!"
 exit 1
fi

echo "Stop node successfully!"
exit 0
''' % (first_sleep, time_out, first_sleep, check_interval, check_interval)
    self.execute_cmd(cmd)
    tmp_out = self.stdout.read()
    self.close_ssh()
    myLogging.logger.info(tmp_out)
    return tmp_out.count('Stop node successfully') != 0

  @myLogging.log('VirMachine')
  def start_node(self, time_out=120, check_interval=5, first_sleep=20):
    self.init_ssh()
    self.execute_cmd('ksh -lc "start node -silent"')
    time.sleep(10.0)
    cmd = '''
  export HOME=/usr/system
  . $HOME/.profile > /dev/null 2>&1
  run_tools_path=$HOME/INTEG/run_tools/$RUN_TOOLS_VERS/bin
  hostname=`hostname`

  # > /usr/system/huangd_touch.log

  # ${run_tools_path}/start node -silent

  sleep %d
  wait_seconds=$((%d - %d))
  lscm_started=0
  check_num=10
  started=0
  pid=''

 #echo "start while ps lscm" > /usr/system/huangd_touch.log

  while [ ${wait_seconds} -gt 0 ]
  do
    #echo "ps lscm" >> /usr/system/huangd_touch.log
    lscm_pid=`ps -o pid,comm -A | grep lscm`
    if [ -n "${lscm_pid}" ]
    then
      if [ ${check_num} -gt 0 ]
      then
        if [ -n "${pid}" -a "${pid}" != "${lscm_pid}" ]
        then
          echo "lscm is abnormal!"
          exit 1
        fi
        pid="${lscm_pid}"
        check_num=$((check_num - 1))
        wait_seconds=$((wait_seconds-1))
        sleep 1
        continue
      fi
  	  lscm_started=1
      break
    else
      wait_seconds=$((wait_seconds-%d))
      sleep %d
    fi
    #echo "${wait_seconds}  ${lscm_pid}" >> /usr/system/huangd_touch.log
  done

  #echo "end while ps lscm" >> /usr/system/huangd_touch.log

  if [ ${lscm_started} -eq 1 ]
  then
    #echo "start show system " >> /usr/system/huangd_touch.log
    #echo "${wait_seconds}" >> /usr/system/huangd_touch.log
    while [ ${wait_seconds} -gt 0 ]
    do
      #echo "show system " >> /usr/system/huangd_touch.log
      ${run_tools_path}/lsc show system|grep $hostname|grep BS_NODEONLINE  > /dev/null 2>&1
      if [ $? -eq 0 ]
      then
        started=1
        break
      else
        wait_seconds=$((wait_seconds-%d))
        sleep %d
      fi
    done
  fi

  #echo "end while show system " >> /usr/system/huangd_touch.log

  if [ ${started} -eq 0 ]
  then
   #echo "Node is not real started!" >> /usr/system/huangd_touch.log
   echo "Node is not real started!"
   exit 2
  fi

  echo "Start node successfully!"
  #echo "Start node successfully!" >> /usr/system/huangd_touch.log
  exit 0
  ''' % (first_sleep, time_out, first_sleep,
         check_interval, check_interval, check_interval, check_interval)
    myLogging.logger.info("cmd: %s" % cmd)
    self.execute_cmd(cmd)
    tmp_out = self.stdout.read()
    self.close_ssh()
    myLogging.logger.info(tmp_out)
    return tmp_out.count('Start node successfully') != 0

