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
import sqlDisplayMachine, sqlPlatform, sqlPlatformNodeList, sqlRunState, sqlOperator, machine
from Display_Platform_Info.models import platform, platform_node_list, host_machine, display_machine, X_server, node, run_state
import Platform_Map.settings
import os
import time
import shutil
from django.db import connections
from django.db.models import F
import requests
import ConfigParser


class RunCollect:
  def __init__(self):
    self.conf = None
    self.db_path = Platform_Map.settings.DATABASES['default']['NAME']
    self.vm_list = []
    self.vm = None
    self.pm = None
    self.node_ids = set()
    self.pm_login_map = {}
    self.first_run = True
    self.unmodified_pfs = []
    self.current_rs = None
    self.last_all_begin_time = None
    self.last_all_end_time = None

  @myLogging.log('RunCollect')
  def init_data(self):
    # Back up db
    if os.path.isfile(self.db_path):
      #with open('.'.join([self.db_path, time.strftime('%y%m%d%H%M', time.localtime())]), 'wb') as fw:
      #  with open(self.db_path, 'rb') as fr:
      #    fw.write(fr.read())
      if not self.first_run:
        shutil.copyfile(self.db_path, '.'.join([self.db_path, time.strftime('%y%m%d%H%M%S', time.localtime())]))
      else:
        shutil.copyfile(self.db_path, '.'.join([self.db_path, 'last_ver']))

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
      sql_dm.save(is_init=True)
      display_machine_ids.add(sql_dm.get_id())
    # Delete the odd data
    myLogging.logger.info("display_machines id all: [%s]" % map(lambda x: x.id, display_machine.objects.all()))
    myLogging.logger.info("display_machines id rev: [%s]" % list(display_machine_ids))
    display_machine.objects.exclude(id__in=display_machine_ids).delete()

  @myLogging.log('RunCollect')
  def process_uncontrolled_node(self):
    myLogging.logger.info('To process a uncontrolled node:')
    myLogging.logger.error("Start vm [%s] failed!" % self.vm.vm_state)
    self.vm.attr.update({'Host': self.pm.get_hostname()})
    self.vm.attr.update({'Host_Machine': self.vm.get_host_machine(),
                         'Platform': self.vm.get_platform(),
                         })
    self.vm.save()
    self.node_ids.add(self.vm.get_id())

  @myLogging.log('RunCollect')
  def process_direct_ssh_node(self, host, name):
    myLogging.logger.info('To process a direct ssh node:')
    self.vm.set_user('system')
    self.vm.set_host(name)
    try:
      self.vm.init_ssh()
    except Exception, e:
      myLogging.logger.exception("Exception in init ssh to node %s" % self.vm.attr['Name'])
      # if e.message.find('timed out') != -1:
      #   myLogging.logger.warning('Node [%s] ssh connect timeout!' % self.vm.attr['Name'])
      self.vm.attr.update({'Host': host})
      self.vm.attr.update({'Ping_reachable': "Y",
                             'Reachable': 'N',
                             'Host_Machine': self.vm.get_host_machine(),
                             'Platform': self.vm.get_platform(),
                             })
      return
      # else:
    #    raise
    # for cmd in self.conf.get_cmd_list():
    #   self.vm.execute_cmd(cmd)
    #   self.vm.attr.update(parseUtil.parse_cmd(cmd, self.vm.stdout.read().split("\n"), self.vm.get_ops_name()))
    self.vm.execute_cmd('ksh -lc "%s"' % ';'.join(map(lambda x: "echo 'system@$ " + x + "';" + x, self.conf.get_cmd_list())))
    parseUtil.parse_output(self.vm.stdout, self.vm)
    self.vm.attr.update({'Host': host})
    self.vm.attr.update({'Ping_reachable': "Y",
                         'Reachable': 'Y',
                         'Host_Machine': self.vm.get_host_machine(),
                         'X_server': self.vm.get_x_server(),
                         'Platform': self.vm.get_platform(),
                         })

  def process_pm_only_node(self, name):
    myLogging.logger.info('To process a pm only node:')
    #self.vm.attr.update({'Ping_reachable': "N"}) # default value.
    use_ssh = not self.conf.try_virsh_console() or self.pm.is_ping_reachable(name)
    script = parseUtil.gen_script(map(lambda x: x.strip(), self.conf.get_cmd_list()),
                                  name if use_ssh else self.vm.vm_state['Name'],
                                  use_ssh)
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
  def send_req2web(self, is_completed=False):
    try:
      inst = self.current_rs.get_db_inst()
      req = requests.post(self.conf.get_para('backend_push_link'),
                          data={
                                                                    'site': inst.Current_platform.Site,
                                                                    'pf': inst.Current_platform.Platform,
                                                                    'begin': inst.Begin,
                                                                    'end': inst.End,
                                                                    'state': 'Completed' if is_completed else 'Collecting',
                                                                    'counter': inst.Counter,
                                                                  },
                          timeout=self.conf.get_para_float('backend_push_timeout'))
      myLogging.logger.info("req: %s" % req)
    except:
      myLogging.logger.info("Exception in send_req2web!")

  @myLogging.log('RunCollect')
  def collect_vm_info(self):
    self.node_ids = set()
    self.vm_list = []
    sqlRunState.SQLRunState.run_state_ids = set()
    if self.unmodified_pfs:
      myLogging.logger.info('Conf changed.')
      myLogging.logger.info('Un-modified pf: %s.' % self.unmodified_pfs)
      completed_pfs = map(lambda x: platform.objects.get(Site=x[0], Platform=x[1]), self.unmodified_pfs)
      self.unmodified_pfs = []
      rss = run_state.objects.filter(id__in=map(lambda x: x.id, completed_pfs))
      rss.update(Counter=F('Counter')+1)
      sqlRunState.SQLRunState.run_state_ids.update(map(lambda x: x.id, rss))
      myLogging.logger.info('Update their counter to %d' % rss[0].Counter)
      sqlRunState.SQLRunState.current_counter = rss[0].Counter
    else:
      completed_pfs = sqlRunState.SQLRunState.get_complete_pfs()
      myLogging.logger.info('completed_pfs: %s' % map(lambda x: ' '.join([x.Site, x.Platform]), completed_pfs))
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
        myLogging.logger.info("Begin collect site [%s], pf [%s]" % (site, pf))
        current_pf = platform.objects.get(Site=site, Platform=pf)
        if current_pf in completed_pfs:
          myLogging.logger.info("Platform [%s %s] collect completed last time!" % (site, pf))
          self.node_ids.update(map(lambda x: x.id, node.objects.filter(Platform=current_pf)))
          continue
        # Update run state
        self.current_rs = sqlRunState.SQLRunState(begin=None, pf=current_pf)
        self.current_rs.save()
        self.send_req2web()
        for c_node in self.conf.get_site_platform_nodelist(site, pf):
          self.vm = None
          self.pm = None
          v_nodes = filter(lambda x: parseUtil.node_equal(x['Name'], c_node), self.vm_list)
          # vm is in a physical machine
          if len(v_nodes) > 1:
            myLogging.logger.error("Too many same name nodes: %s!"% v_nodes)
          if len(v_nodes):
            # only check the 1st vm
            vm_state = v_nodes[0]
            self.pm = physicalMachine.HostMachine(self.pm_login_map[vm_state['Host']])
            self.pm.init_ssh()
            vm_state['Running'] = self.pm.update_vm_status(vm_state)
            self.vm = virtMachine.VirMachine(vm_state['Name'], vm_state['Running'], vm_state['Id_in_host'])
            self.vm.set_conf_name(c_node)
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
            ret = parseUtil.ping_a_node(c_node)
            myLogging.logger.info('Ping result: %d' % ret)
            if not ret:
              # The node could be reached directly, use ssh.
              # if c_node not equal vm_state['Name'], like 'umerod002lit' vs 'umerod002li'
              self.process_direct_ssh_node(self.pm.get_hostname(), c_node)
            else:
              # The node could not be reached directly, use script via host machine.
              self.process_pm_only_node(c_node)
            # Now save vm info
            self.vm.save()
            self.node_ids.add(self.vm.get_id())
            if vm_state['Running'] != 'Y' and self.conf.open_stop_vm():
              myLogging.logger.info("Stopping vm %s" % vm_state['Name'])
              self.pm.stop_vm(self.vm)
          else: # c_node is not in vm list
            myLogging.logger.info("To check non-vm conf node: %s" % c_node)
            ret = parseUtil.ping_a_node(c_node)
            myLogging.logger.info('Ping result: %d' % ret)
            if not ret:  # the node could be reaching
              self.vm = virtMachine.VirMachine(c_node)
              self.vm.set_conf_name(c_node)
              self.process_direct_ssh_node('', c_node)
            else:
              self.vm = virtMachine.VirMachine(c_node, 'N')
              self.vm.set_conf_name(c_node)
              self.vm.attr.update({'Ping_reachable': "N",
                                   'Platform': self.vm.get_platform(),
                                   })
            self.vm.save()
            self.node_ids.add(self.vm.get_id())
          self.close_pm_vm()
        sqlRunState.SQLRunState(begin=self.current_rs.attr['Begin'], pf=current_pf).save()
        self.send_req2web(True)
    # Check orphan list.
    myLogging.logger.info('Try to get orphan list')
    current_pf = platform.objects.get(Site=sqlOperator.SQLOperator.ORPHAN)
    self.current_rs = sqlRunState.SQLRunState(begin=None, pf=current_pf)
    self.current_rs.save()
    self.send_req2web()
    for vm_state in (x for x in filter(lambda x: parseUtil.node_not_in_list(x['Name'], self.conf.get_all_nodes()),
                                       self.vm_list)):
      myLogging.logger.info("To check orphan node: %s" % vm_state)
      self.pm = physicalMachine.HostMachine(self.pm_login_map[vm_state['Host']])
      self.pm.init_ssh()
      vm_state['Running'] = self.pm.update_vm_status(vm_state)
      self.vm = virtMachine.VirMachine(vm_state['Name'], vm_state['Running'], vm_state['Id_in_host'], True)

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
      # Now vm is running
      self.process_pm_only_node(vm_state['Name'])
      self.vm.save()
      self.node_ids.add(self.vm.get_id())
      if vm_state['Running'] != 'Y' and self.conf.open_stop_vm():
        myLogging.logger.info("Stopping vm %s" % vm_state['Name'])
        self.pm.stop_vm(self.vm)
      self.close_pm_vm()
    sqlRunState.SQLRunState(begin=self.current_rs.attr['Begin'], pf=current_pf).save()
    self.send_req2web(True)
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
      xs = xServer.XServer(host)
      xs.get_x_servers(self.conf.get_para_float('connect_timeout'))
    myLogging.logger.info("xservers id all: [%s]" % map(lambda x: x.id, X_server.objects.all()))
    myLogging.logger.info("xservers id rev: [%s]" % list(xServer.XServer.xs_list))
    X_server.objects.exclude(id__in=xServer.XServer.xs_list).delete()

  def mapping_platform_node(self):
    pass

  @myLogging.log('RunCollect')
  def check_conf_change_timeout(self):
    while time.time() - self.last_all_begin_time < float(self.conf.get_para_int('collect_interval')):
      new_conf = confUtil.Conf()
      if new_conf.read_conf():
        com_ret = confUtil.Conf.compare_conf(self.conf, new_conf)
        if com_ret['ret']:
          if com_ret['para_mod'] or com_ret['host_mod'] or com_ret['display_mod']:
            self.unmodified_pfs = []
            return False
          if com_ret['site_mod']:
            self.unmodified_pfs = com_ret['site_same']
            myLogging.logger.info("Found Conf change, run next collect at once.")
            return False
      myLogging.logger.info("Sleep %.02f seconds!" % self.conf.get_para_float('check_conf_interval'))
      myLogging.logger.info("Next collecting is after %.02f seconds!" %
                          (float(self.conf.get_para_int('collect_interval') - time.time() + self.last_all_begin_time)))
      time.sleep(self.conf.get_para_float('check_conf_interval'))
    myLogging.logger.info("Interval time reached, run next collect at once.")
    return True

  @myLogging.log('RunCollect')
  def run_collect(self):
    #myLogging.setup_logging()
    while True:
      try:
        re_load_conf = False
        if not self.first_run:
          re_load_conf = not self.check_conf_change_timeout()
        if self.first_run or re_load_conf:
          self.conf = confUtil.Conf()
          if not self.conf.load_conf():
            return False
          parseUtil.set_conf(self.conf)
          myLogging.logger.info(self.conf.config)
          myLogging.logger.info("Set connect timeout to [%f]" % self.conf.get_para_float('connect_timeout'))
          machine.Machine.set_class_connect_timeout(self.conf.get_para_float('connect_timeout'))
        begin_time = time.time()
        if not re_load_conf:
          self.last_all_begin_time = begin_time
        myLogging.logger.info("Starting collecting!")
        # Get last completed_pfs
        #self.changed_site = sqlSiteConf.SQLSiteConf.get_all_conf_change(
        #  filter(lambda x: x != self.conf.main_conf, self.conf.conf_list))
        if self.first_run or re_load_conf:
          myLogging.logger.info("Starting init db data after loading conf!")
          self.init_data()
        if not self.conf.get_para_bool('skip_first_display_collect') or not self.first_run:
          myLogging.logger.info("Starting collect display info!")
          self.collect_display_info()
        myLogging.logger.info("Starting collect vm info!")
        self.collect_vm_info()
        self.mapping_platform_node()
        connections.close_all()
        end_time = time.time()
        if not re_load_conf:
          self.last_all_end_time = end_time
        collect_time = int(end_time - begin_time)
        myLogging.logger.info("Last collecting cost %d seconds!" % collect_time)
        self.first_run = False
      except ConfigParser.ParsingError:
        myLogging.logger.exception("Exception in config parser!Exit!")
        raise
      except Exception:
        myLogging.logger.exception("Exception in run_collect!")
        self.first_run = False
    return False


if __name__ == "__main__":
  os.chdir(Platform_Map.settings.BASE_DIR)
  myLogging.setup_logging()
  r = RunCollect()
  r.run_collect()
