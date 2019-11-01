# -*- coding: utf-8 -*-

import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Platform_Map.settings")
django.setup()
import virtMachine
import physicalMachine
import xServer
import parseUtil
import confUtil
import myLogging
import sqlDisplayMachine, sqlPlatform, sqlPlatformNodeList, sqlRunState, sqlOperator, sqlSiteConf, machine
from Display_Platform_Info.models import platform, platform_node_list, host_machine, display_machine, X_server, node, run_state
import Platform_Map.settings
import os
import time
import shutil
from django.db import connections


class RunCollect:
  def __init__(self):
    self.conf = confUtil.Conf()
    self.db_path = Platform_Map.settings.DATABASES['default']['NAME']
    self.vm_list = []
    self.vm = None
    self.pm = None
    self.node_ids = set()
    self.pm_login_map = {}
    self.first_run = True

  @myLogging.log('RunCollect')
  def init_data(self):
    # Back up db
    if os.path.isfile(self.db_path):
      #with open('.'.join([self.db_path, time.strftime('%y%m%d%H%M', time.localtime())]), 'wb') as fw:
      #  with open(self.db_path, 'rb') as fr:
      #    fw.write(fr.read())
      shutil.copyfile(self.db_path, '.'.join([self.db_path, time.strftime('%y%m%d%H%M%S', time.localtime())]))

    # Truncate tables
    #platform.objects.all().delete()
    #platform_node_list.objects.all().delete()
    #host_machine.objects.all().delete()
    #display_machine.objects.all().delete()
    #X_server.objects.all().delete()
    #node.objects.all().delete()

    # Init table data(platform and platform_node_list)
    platform_ids = set()
    platform_node_map_ids = set()
    for site in self.conf.get_site_list():
      for pf in self.conf.get_site_platform_list(site):
        sql_pf = sqlPlatform.SQLPlatform(pf, self.conf.get_site_platform(site, pf))
        sql_pf.save()
        platform_ids.add(sql_pf.get_id())
        for n in self.conf.get_site_platform_nodelist(site, pf):
          sql_pf_n = sqlPlatformNodeList.SQLPlatformNodeList(sql_pf.get_db_inst(), n)
          sql_pf_n.save()
          platform_node_map_ids.add(sql_pf_n.get_id())
    # Insert a platform for ORPHAN
    sql_pf = sqlPlatform.SQLPlatform('', {'site': sqlOperator.SQLOperator.ORPHAN,
                                          'description': None,
                                          'owner': None,
                                          'validity': None,
                                          })
    sql_pf.save()
    platform_ids.add(sql_pf.get_id())
    # Delete the odd data (platform and platform_node_list)
    myLogging.logger.info("platfromts id all: [%s]" % map(lambda x: x.id, platform.objects.all()))
    myLogging.logger.info("platfromts id rev: [%s]" % list(platform_ids))
    myLogging.logger.info("platfromt_node_map id all: [%s]" % map(lambda x: x.id, platform_node_list.objects.all()))
    myLogging.logger.info("platfromt_node_map id rev: [%s]" % list(platform_node_map_ids))
    platform.objects.exclude(id__in=platform_ids).delete()
    platform_node_list.objects.exclude(id__in=platform_node_map_ids).delete()

    # Init table data(host_machine)
    host_machine_ids = set()
    for hm in self.conf.get_physical_host_list():
      ph = physicalMachine.HostMachine(hm)
      ph.save()
      host_machine_ids.add(ph.get_id())
    # Delete the odd data
    myLogging.logger.info("host_machines id all: [%s]" % map(lambda x: x.id, host_machine.objects.all()))
    myLogging.logger.info("host_machines id rev: [%s]" % list(host_machine_ids))
    host_machine.objects.exclude(id__in=host_machine_ids).delete()

    # Init table data(display_machine)
    display_machine_ids = set()
    for dm in self.conf.get_display_host_list():
      sql_dm = sqlDisplayMachine.SQLDisplayMachine(dm)
      sql_dm.save()
      display_machine_ids.add(sql_dm.get_id())
    # Delete the odd data
    myLogging.logger.info("display_machines id all: [%s]" % map(lambda x: x.id, display_machine.objects.all()))
    myLogging.logger.info("display_machines id rev: [%s]" % list(display_machine_ids))
    display_machine.objects.exclude(id__in=display_machine_ids).delete()

  @myLogging.log('RunCollect')
  def process_uncontrolled_node(self):
    myLogging.logger.error("Start vm [%s] failed!" % self.vm.vm_state)
    self.vm.attr.update({'Host': self.pm.get_hostname()})
    self.vm.attr.update({'Host_Machine': self.vm.get_host_machine(),
                         'Platform': self.vm.get_platform(),
                         })
    self.vm.save()
    self.node_ids.add(self.vm.get_id())

  @myLogging.log('RunCollect')
  def process_direct_ssh_node(self, host):
    self.vm.set_user('system')
    try:
      self.vm.init_ssh()
    except Exception, e:
      if e.message.find('timed out') != -1:
        myLogging.logger.warning('Node [%s] ssh connect timeout!' % self.vm.attr['Name'])
        self.vm.attr.update({'Host': host})
        self.vm.attr.update({'Ping_reachable': "Y",
                             'Reachable': 'N',
                             'Host_Machine': self.vm.get_host_machine(),
                             'Platform': self.vm.get_platform(),
                             })
        return
      else:
        raise
    for cmd in self.conf.get_cmd_list():
      self.vm.execute_cmd(cmd)
      self.vm.attr.update(parseUtil.parse_cmd(cmd, self.vm.stdout.read().split("\n"), self.vm.get_ops_name()))
    self.vm.attr.update({'Host': host})
    self.vm.attr.update({'Ping_reachable': "Y",
                         'Reachable': 'Y',
                         'Host_Machine': self.vm.get_host_machine(),
                         'X_server': self.vm.get_x_server(),
                         'Platform': self.vm.get_platform(),
                         })

  def process_pm_only_node(self):
    #self.vm.attr.update({'Ping_reachable': "N"}) # default value.
    script = parseUtil.gen_script(map(lambda x: x.strip(), self.conf.get_cmd_list()), self.vm.vm_state['Name'],
                                  not self.conf.try_virsh_console() or self.pm.is_ping_reachable(self.vm.vm_state['Name']))
    self.pm.execute_script(script)
    parseUtil.parse_output(self.pm.stdout, self.vm)
    self.vm.attr.update({'Host': self.pm.get_hostname()})
    self.vm.attr.update({'Host_Machine': self.vm.get_host_machine(),
                         'X_server': self.vm.get_x_server(),
                         'Platform': self.vm.get_platform(),
                         })

  def close_pm_vm(self):
    if self.pm:
      self.pm.close_ssh()
      self.pm = None
    if self.vm:
      self.vm.close_ssh()
      self.vm = None

  @myLogging.log('RunCollect')
  def collect_vm_info(self):
    self.node_ids = set()
    self.vm_list = []
    sqlRunState.SQLRunState.run_state_ids = set()
    # Get last completed_pfs
    changed_site = sqlSiteConf.SQLSiteConf.get_all_conf_change(
        filter(lambda x: x != self.conf.main_conf, self.conf.conf_list))
    if changed_site:
      completed_pfs = []
      rss = run_state.objects.all()
      if rss.count():
        rss.update(Counter=0)
      sqlRunState.SQLRunState.current_counter = 1
    else:
      completed_pfs = sqlRunState.SQLRunState.get_complete_pfs()
    myLogging.logger.info("Current run state counter: %d" % sqlRunState.SQLRunState.current_counter)
    # Check vms in physical host machines.
    for host in self.conf.get_physical_host_list():
      pm = physicalMachine.HostMachine(host)
      pm.init_ssh()
      pm.update_hostname()
      self.pm_login_map[pm.get_hostname()] = host
      if pm.get_vm_ist():
        myLogging.logger.info("Vm list: %s" % pm.VmList)
        self.vm_list.extend(pm.VmList)
      pm.close_ssh()
    # Check nodes in conf
    for site in self.conf.get_site_list():
      for pf in self.conf.get_site_platform_list(site):
        current_pf = platform.objects.get(Site=site, Platform=pf)
        if current_pf in completed_pfs:
          myLogging.logger.info("Platform [%s %s] collect completed last time!" % (site, pf))
          self.node_ids.update(map(lambda x: x.id, node.objects.filter(Platform=current_pf)))
          continue
        # Update run state
        sqlRunState.SQLRunState(is_begin=True, pf=current_pf).save()
        for c_node in self.conf.get_site_platform_nodelist(site, pf):
          self.vm = None
          self.pm = None
          v_nodes = filter(lambda x: x['Name'] == c_node, self.vm_list)
          # vm is in a physical machine
          if len(v_nodes) > 1:
            myLogging.logger.error("Too many same name nodes: %s!"% v_nodes)
          if len(v_nodes):
            # only check the 1st vm
            vm_state = v_nodes[0]
            self.vm = virtMachine.VirMachine(vm_state['Name'], vm_state['Running'], vm_state['Id_in_host'])
            self.pm = physicalMachine.HostMachine(self.pm_login_map[vm_state['Host']])
            self.pm.init_ssh()
            if vm_state['Running'] != 'Y' and self.conf.open_stop_vm():
              myLogging.logger.info("Starting vm %s" % vm_state['Name'])
              self.vm.attr.update(self.pm.start_vm(self.vm))
              if self.vm.attr['Controlled'] == 'N' or not self.pm.wait_vm_start(self.vm,
                                                                                int(self.conf.get_para_float(
                                                                                  'wait_vm_start_ping_time'))):
                self.process_uncontrolled_node()
                continue
              myLogging.logger.info("Waiting for vm starting, sleep [%f] seconds!" %
                                    self.conf.get_para_float('wait_vm_start_sleep_time'))
              time.sleep(self.conf.get_para_float('wait_vm_start_sleep_time'))
            # Now vm is running, begin to check its info
            myLogging.logger.info("To check conf vm node: %s" % vm_state)
            ret = os.system('ping -c 2 -W 2 %s >/dev/null 2>&1' % vm_state['Name'])
            if not ret:
              # The node could be reached directly, use ssh.
              self.process_direct_ssh_node(self.pm.get_hostname())
            else:
              # The node could not be reached directly, use script via host machine.
              self.process_pm_only_node()
            # Now save vm info
            self.vm.save()
            self.node_ids.add(self.vm.get_id())
            if vm_state['Running'] != 'Y' and self.conf.open_stop_vm():
              self.pm.stop_vm(self.vm)
          else: # c_node is not in vm list
            myLogging.logger.info("to check non-vm conf node: %s" % c_node)
            ret = os.system('ping -c 2 -W 2 %s >/dev/null 2>&1' % c_node)
            if not ret:  # the node could be reaching
              self.vm = virtMachine.VirMachine(c_node)
              self.process_direct_ssh_node('')
            else:
              self.vm = virtMachine.VirMachine(c_node, 'N')
              self.vm.attr.update({'Ping_reachable': "N",
                                   'Platform': self.vm.get_platform(),
                                   })
            self.vm.save()
            self.node_ids.add(self.vm.get_id())
          self.close_pm_vm()
        sqlRunState.SQLRunState(is_begin=False, pf=current_pf).save()
    # Check orphan list.
    current_pf = platform.objects.get(Site=sqlOperator.SQLOperator.ORPHAN)
    sqlRunState.SQLRunState(is_begin=True, pf=current_pf).save()
    for vm_state in (x for x in filter(lambda x: x['Name'] not in self.conf.get_all_nodes(), self.vm_list)):
      myLogging.logger.info("to check orphan node: %s" % vm_state)
      self.vm = virtMachine.VirMachine(vm_state['Name'], vm_state['Running'], vm_state['Id_in_host'], True)
      self.pm = physicalMachine.HostMachine(self.pm_login_map[vm_state['Host']])
      self.pm.init_ssh()
      if vm_state['Running'] != 'Y' and self.conf.open_stop_vm():
        self.vm.attr.update(self.pm.start_vm(self.vm))
        if self.vm.attr['Controlled'] == 'N' or not self.pm.wait_vm_start(self.vm,
                                                                          int(self.conf.get_para_float(
                                                                            'wait_vm_start_ping_time'))):
          self.process_uncontrolled_node()
          continue
        myLogging.logger.info("Waiting for vm starting, sleep [%f] seconds!" %
                              self.conf.get_para_float('wait_vm_start_sleep_time'))
        time.sleep(self.conf.get_para_float('wait_vm_start_sleep_time'))
      # Now vm is running
      self.process_pm_only_node()
      self.vm.save()
      self.node_ids.add(self.vm.get_id())
      if vm_state['Running'] != 'Y' and self.conf.open_stop_vm():
        self.pm.stop_vm(self.vm)
      self.close_pm_vm()
    sqlRunState.SQLRunState(is_begin=False, pf=current_pf).save()
    myLogging.logger.info("nodes id all: [%s]" % map(lambda x: x.id, node.objects.all()))
    myLogging.logger.info("nodes id rev: [%s]" % list(self.node_ids))
    myLogging.logger.info("run_state id all: [%s]" % map(lambda x: x.id, run_state.objects.all()))
    myLogging.logger.info("run_state id rev: [%s]" % list(sqlRunState.SQLRunState.run_state_ids))
    node.objects.exclude(id__in=self.node_ids).delete()
    run_state.objects.exclude(id__in=sqlRunState.SQLRunState.run_state_ids).delete()

  @myLogging.log('RunCollect')
  def collect_display_info(self):
    xServer.XServer.xs_list = set()
    for host in self.conf.get_display_host_list():
      dm = xServer.XServer(host)
      try:
        dm.get_x_servers(self.conf.get_para_float('connect_timeout'))
      except Exception,e:
        if e.message.find('timed out') != -1:
          myLogging.logger.warning('Display machine [%s] connect timeout! Skip it!' % host)
        else:
          raise
    myLogging.logger.info("xservers id all: [%s]" % map(lambda x: x.id, X_server.objects.all()))
    myLogging.logger.info("xservers id rev: [%s]" % list(xServer.XServer.xs_list))
    X_server.objects.exclude(id__in=xServer.XServer.xs_list).delete()

  def mapping_platform_node(self):
    pass

  @myLogging.log('RunCollect')
  def run_collect(self):
    #myLogging.setup_logging()
    try:
      if not self.conf.load_conf():
        return False
      parseUtil.set_conf(self.conf)
      myLogging.logger.info(self.conf.config)
      myLogging.logger.info("Set connect timeout to [%f]" % self.conf.get_para_float('connect_timeout'))
      machine.Machine.set_class_connect_timeout(self.conf.get_para_float('connect_timeout'))
      self.init_data()
      collect_interval = self.conf.get_para_int('collect_interval')
      while True:
        start_time = time.time()
        if not self.conf.get_para_bool('skip_first_display_collect') or not self.first_run:
          self.collect_display_info()
        self.collect_vm_info()
        self.mapping_platform_node()
        connections.close_all()
        end_time = time.time()
        collect_time = int(end_time - start_time)
        sleep_time = collect_interval - collect_time
        if sleep_time < 0:
          sleep_time = 0
        myLogging.logger.info("Last collecting cost %d seconds!" % collect_time)
        myLogging.logger.info("Sleep %d seconds for next collecting!" % sleep_time)
        time.sleep(sleep_time)
        self.first_run = False
    except Exception:
      myLogging.logger.exception("Exception in run_collect!")
      return False


if __name__ == "__main__":
  os.chdir(Platform_Map.settings.BASE_DIR)
  myLogging.setup_logging()
  r = RunCollect()
  r.run_collect()
