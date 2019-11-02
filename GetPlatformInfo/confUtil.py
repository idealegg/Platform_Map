# -*- coding: utf-8 -*-

import Platform_Map.settings
import os
import ConfigParser
import re
import myLogging


class Conf:
  def __init__(self):
    self.HOST_NODE_DOMAIN = re.compile('bestsrv\d{2}li[dp]?')
    self.DISPLAY_NODE_DOMAIN = re.compile('(\w{3})(r\d{2})(c\d{2})')
    self.DATA_NODE_DOMAIN = re.compile('(\w{2})(sev|dev|min|fat|trn)(\d{2})([pv])(\d{3})')
    self.negative = ['N', 'NO', 'F', 'FALSE']
    self.positive = ['Y', 'YES', 'T', 'TRUE']
    self.conf_dir = os.path.join(Platform_Map.settings.BASE_DIR, 'conf')
    self.main_conf = os.path.join(self.conf_dir, 'main.conf')
    self.parser = ConfigParser.ConfigParser()
    self.conf_list = []
    self.nodes = []
    self.config = {}
    self.default_config ={ 'site': {},
                   'host': {},
                   'display': {},
                   'parameter': {
                    'open_stop_vm': 'F',
                    'try_virsh_console': 'F',
                    'check_domain_format': 'F',
                    'check_site_platform_format': 'F',
                    'remote_cmd_timeout_seconds': 3,
                    'remote_cmd_timeout_times': 2,
                    'collect_interval': 3600,
                    'connect_timeout': 10.0,
                    'skip_first_display_collect': 'F',
                    'wait_vm_start_ping_time': 30.0,
                    'wait_vm_start_sleep_time': 10.0,
                    'check_conf_interval': 5.0,
                    'cmd_list': ['uname -a',
                                 'cat /etc/thalix-release',
                                 'ifconfig -a',
                                 'vers',
                                 'message',
                                 'cat /etc/xinetd.d/x11-fw'
                                ],
                    }
                  }

  @myLogging.log('Conf')
  def read_conf(self):
    self.config = self.default_config
    # -- check path
    if not os.path.isdir(self.conf_dir):
      myLogging.logger.error("Conf dir %s does not exist!" % self.conf_dir)
      return False
    if not os.path.isfile(self.main_conf):
      myLogging.logger.error("Main conf file %s does not exist!" % self.main_conf)
      return False
    self.conf_list.append(self.main_conf)
    # -- check conf count
    for site_dir in [x for x in os.listdir(self.conf_dir) if x != 'common_config']:
      abs_dir = os.path.join(self.conf_dir, site_dir)
      if os.path.isdir(abs_dir):
        site_f = os.path.join(abs_dir, "%s.conf" % site_dir)
        if not os.path.isfile(site_f):
          myLogging.logger.error("Conf [%s.conf] should be defined in %s!" % (site_dir, abs_dir))
          return False
        self.conf_list.append(site_f)
    if len(self.conf_list) < 2:
      myLogging.logger.error("At least a site conf should be defined in %s!" % self.conf_dir)
      return False
    # -- check host
    self.parser.read(map(lambda x: os.path.join(self.conf_dir, x), self.conf_list))
    return True

  @myLogging.log('Conf')
  def load_conf(self):
    if not self.read_conf():
      return False
    if not self.parser.has_section('host'):
      myLogging.logger.error( "Physical host machines should be defined in %s!" % self.main_conf)
      return False
    self.config['host'] = dict(self.parser.items('host'))
    myLogging.logger.debug(self.config['host'])
    self.config['host']['list'] = re.split('\s+', self.config['host']['nodelist'])
    if self.check_domain_format() and not self.check_domain('host'):
      return False
    # -- check display
    if not self.parser.has_section('display'):
      myLogging.logger.error( "Display host nodes should be defined in %s!" % self.main_conf)
      return False
    self.config['display'] = dict(self.parser.items('display'))
    self.config['display']['list'] = re.split('\s+', self.config['display']['nodelist'])
    if self.check_domain_format() and not self.check_domain('display'):
      return False
    # -- check parameter
    if self.parser.has_section('parameter'):
      self.config['parameter'].update(dict(self.parser.items('parameter')))
      if self.config['parameter'].has_key('cmds'):
        self.config['parameter']['cmd_list'] = re.split('\s+', self.config['parameter']['cmds'])
    # -- check site
    for section in self.parser.sections():
      if section not in ['host', 'display', 'parameter']:
        site, platform = re.split('\s+', section)
        if not self.config['site'].has_key(site):
          self.config['site'][site] = {}
        self.config['site'][site][platform] =dict(self.parser.items(section))
        self.config['site'][site][platform]['site'] = site
        self.config['site'][site][platform]['list'] = re.split('\s+', self.config['site'][site][platform]['nodelist'])
    if self.check_domain_format() and not self.check_domain('site'):
      return False
    return True

  def get_physical_host_list(self):
    return self.config['host']['list']

  def get_display_host_list(self):
    return self.config['display']['list']

  def get_site_list(self):
    return self.config['site'].keys()

  def get_site(self, site):
    return self.config['site'][site]

  def get_site_platform_list(self, site):
    return self.config['site'][site].keys()

  def get_site_platform(self, site, platform):
    return self.config['site'][site][platform]

  def get_site_platform_nodelist(self, site, platform):
    return self.config['site'][site][platform]['list']

  def get_all_nodes(self):
    if not self.nodes:
      for site in self.config['site'].keys():
        for platform in self.config['site'][site].keys():
          self.nodes.extend(self.config['site'][site][platform]['list'])
    return self.nodes

  def try_virsh_console(self):
    return self.config['parameter']['try_virsh_console'].upper() in self.positive

  def open_stop_vm(self):
    return self.config['parameter']['open_stop_vm'].upper() in self.positive

  def check_domain_format(self):
    return self.config['parameter']['check_domain_format'].upper() in self.positive

  def check_site_platform_format(self):
    return self.config['parameter']['check_site_platform_format'].upper() in self.positive

  def get_para_bool(self, parameter):
    return self.config['parameter'][parameter].upper() in self.positive

  def get_para_int(self, parameter):
    return int(self.config['parameter'][parameter])

  def get_para_float(self, parameter):
    return float(self.config['parameter'][parameter])

  def get_cmd_list(self):
    return self.config['parameter']['cmd_list']

  def check_domain(self, t):
    if t == 'host':
      for n in self.config['host']['list']:
        if not re.match(self.HOST_NODE_DOMAIN, n):
          myLogging.logger.error( "Domain '%s' format is not correct in [host]!" % n)
          return False
    elif t == 'display':
      for n in self.config['display']['list']:
        if not re.match(self.DISPLAY_NODE_DOMAIN, n):
          myLogging.logger.error( "Domain '%s' format is not correct in [display]!" % n)
          return False
    elif t == 'site':
      for site in self.config['site'].keys():
        for platform in self.config['site'][site].keys():
          for n in self.config['site'][site][platform]['list']:
            res = re.match(self.DATA_NODE_DOMAIN, n)
            if not res:
              myLogging.logger.error( "Domain '%s' format is not correct in [%s %s]!" % (n, site, platform))
              return False
            elif self.check_site_platform_format():
              if site.lower() != res.group(1) or platform.lower() != ''.join([res.group(2), res.group(3)]):
                myLogging.logger.error( "Domain '%s' format is not correct in [%s %s]!" % (n, site, platform))
                return False
    return True

  @classmethod
  @myLogging.log('Conf')
  def compare_conf(cls, old_conf, new_conf):
    ret = {'ret': True,
           'same': [],
           'mod': False,
           }
    s1 = set(old_conf.parser.sections())
    s2 = set(new_conf.parser.sections())
    s_same = s1 & s2
    s_del = filter(lambda x: x not in ['host', 'display', 'parameter'], s1 ^ s_same)
    s_add = filter(lambda x: x not in ['host', 'display', 'parameter'], s2 ^ s_same)
    if s_del or s_add:
      ret['mod'] = True
    if 'parameter' not in s_same or 'host' not in s_same or 'display' not in s_same:
      myLogging.logger.warning('"parameter" or "host" or "display" is not in new main.conf!')
      ret['ret'] = False
      return ret
    for s in s_same:
      if s in ['host', 'display', 'parameter']:
        continue
      i1 = set(re.split('\s+', dict(old_conf.parser.items(s))['nodelist']))
      i2 = set(re.split('\s+', dict(new_conf.parser.items(s))['nodelist']))
      if not i1^i2:
        ret['same'].append(re.split('\s+', s))
      else:
        ret['mod'] = True
    myLogging.logger.debug('ret: %s' % ret)
    return ret


if __name__ =="__main__":
  import pprint
  os.chdir(Platform_Map.settings.BASE_DIR)
  myLogging.setup_logging()
  c = Conf()
  c.load_conf()
  myLogging.logger.debug(pprint.pformat(c.config))

