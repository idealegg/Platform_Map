# -*- coding: utf-8 -*-

import re
import myLogging
import os
import platform


UNAME_PATTERN = re.compile('^(\w+)\s+([^\s]+)\s+([^\s]+)\s+')
IFCONFIG_P1 = re.compile('^([^\s:]+).*?(HWaddr\s+([\w:]+))?$')
IFCONFIG_P2 = re.compile('^\s+inet addr:([\d.]+)\s+Bcast:([\d.]+)\s+Mask:([\d.]+)')
IFCONFIG_P3 = re.compile('^\s+ether\s+([\w:]+)')
IFCONFIG_P4 = re.compile('^\s+inet\s+([\d.]+)\s+netmask\s+([\d.]+)\s+broadcast\s+([\d.]+)')
PING = re.compile('\s+(\d+)(\.\d+)?% packet loss')

conf = None


def set_conf(c):
  global conf
  conf = c


@myLogging.log("parseUtil")
def gen_script(cmd_list, vm_name, is_ssh=True):
  vm = vm_name
  tmp_script = []
  ssh_cmd = 'ssh -o ConnectTimeout=%d -l system' % int(conf.get_para_float('connect_timeout'))
  tmp_script.append('''#!/usr/bin/expect
set timeout %d
set done 1
set nologined 1
set timeout_case 0
spawn %s %s
while (${done}) {
  expect {
    " login:" { if (${nologined}) {
                   send "system\\n"
                   }
    }
    "Password:" { send "abc123\\n"
                  set nologined 0
                  }
    "password:" { send "abc123\\n"
                  set nologined 0
                  }
    "system@" {
          set done 0
''' % (conf.get_para_int('remote_cmd_timeout_seconds'), (ssh_cmd if is_ssh else 'virsh console'), vm))
  for cmd in cmd_list:
    tmp_script.append('expect "system@"\nsend "%s\\n"\n' % (cmd))
  tmp_script.append('''          expect "system@"
          send "exit\\n"
          expect " login:"
          send_user "\\n\\nFinished...\\n\\n"
          %s
          exit
        }
        timeout {
              if (${timeout_case} < %d) {
                send "\\n" }
              else{
                  puts stderr "Login time out...\\n"
                  exit 1
              }
           incr timeout_case
         }
   }
}


%s

exit 0''' % ('' if is_ssh else 'close', conf.get_para_int('remote_cmd_timeout_times'), '' if is_ssh else 'close'))
  myLogging.logger.info( tmp_script)
  return ''.join(tmp_script)


@myLogging.log("parseUtil")
def parse_output(output, vm_class, prompt='system@'):
  cur_cmd = ''
  cmd_out = []
  for line in output:
    myLogging.logger.info( line)
    if line[line.find('|')+1:].startswith(prompt):
      cmd = line[line.find('$')+1:-1].strip()
      if cmd:
        myLogging.logger.info( "cmd1: %s" % cmd)
        if cur_cmd:
          myLogging.logger.info( "cur_cmd: %s" % cur_cmd)
          tmp_result = parse_cmd(cur_cmd, cmd_out, vm_class.get_ops_name())
          myLogging.logger.info( tmp_result)
          vm_class.attr.update(tmp_result)
        cur_cmd = cmd
        cmd_out = []
    else:
      cmd_out.append(line[:-1])
  if cur_cmd:
    tmp_result = parse_cmd(cur_cmd, cmd_out)
    vm_class.attr.update(tmp_result)
    vm_class.attr.update({'Reachable': 'Y'})
  else:
    vm_class.attr.update({'Reachable': 'N'})


@myLogging.log("parseUtil")
def parse_cmd(cmd, cmd_out, vm_ops_name=''):
  myLogging.logger.info( "cmd2: %s" % cmd)
  myLogging.logger.info("cmd_out: %s" % cmd_out)
  myLogging.logger.debug("vm_ops_name: %s" % vm_ops_name)
  ret1 = {}
  if cmd == 'uname -a':
    res = re.search(UNAME_PATTERN, cmd_out[0])
    if res:
      ret1 =  {'Os': res.group(1),
               'OPS_Name': res.group(2),
               'Structure': res.group(3),
              }
  elif cmd == 'cat /etc/thalix-release':
    ret1 = {'Thalix': cmd_out[0].strip()}
  elif cmd.find('ifconfig') != -1:
    cur_interface = ''
    interface = {}
    ret = []
    ip = []
    for line in cmd_out:
      line = line.rstrip()
      res = re.search(IFCONFIG_P1, line)
      if res:
        if cur_interface:
          #ret[cur_interface] = interface
          ret.append("%s\r\n\tHWaddr:%s" % (cur_interface, interface['HWaddr']))
          if interface.has_key('addr'):
            ret.append("\r\n\taddr:%s" % (interface['addr']))
            ret.append("\r\n\tBcast:%s" % (interface['Bcast']))
            ret.append("\r\n\tMask:%s" % (interface['Mask']))
            ip.append(interface['addr'])
        interface = {}
        interface['Name'] = res.group(1)
        interface['HWaddr'] = res.group(3)
        cur_interface = interface['Name']
      else:
        res = re.search(IFCONFIG_P2, line)
        if res:
          interface['addr'] = res.group(1)
          interface['Bcast'] = res.group(2)
          interface['Mask'] = res.group(3)
        else:
          res = re.search(IFCONFIG_P3, line)
          if res:
            interface['HWaddr'] = res.group(1)
          else:
            res = re.search(IFCONFIG_P4, line)
            if res:
              interface['addr'] = res.group(1)
              interface['Bcast'] = res.group(3)
              interface['Mask'] = res.group(2)
    if cur_interface:
      #ret[cur_interface] = interface
      ret.append("%s\n\tHWaddr:%s" % (cur_interface, interface['HWaddr']))
      if interface.has_key('addr'):
        ret.append("\n\taddr:%s" % (interface['addr']))
        ret.append("\n\tBcast:%s" % (interface['Bcast']))
        ret.append("\n\tMask:%s" % (interface['Mask']))
        ip.append(interface['addr'])
    ret1 = {'Interface': ret, 'IP': ' '.join(ip)}
  elif cmd == 'vers':
    ret = {}
    avoid_color = ''
    for line in cmd_out:
      line = line.strip()
      tmp = line.split('=')
      if len(tmp) > 1:
        ret[tmp[0]] = tmp[1]
        if tmp[0].find('RUN_CONFIG_') != -1:
          avoid_color = tmp[1]
    if 'RUN_CONFIG_VERS' not in ret:
      ret['RUN_CONFIG_VERS'] = avoid_color
    ret1 = {'Config': ret['RUN_CONFIG_VERS']}
  elif cmd == 'message':
    csci = []
    if vm_ops_name:
      for line in cmd_out:
        tmp = re.split('\s+', line)
        if len(tmp) > 1:
          if vm_ops_name in tmp:
            csci.append(re.sub("\d+", '', tmp[0]))  # 删除数字
    ret1 = {'CSCI': " ".join(csci)}
  elif cmd.startswith('ping -c'):
    ret1 = {'Ping_reachable': 'N'}
    for line in cmd_out:
      myLogging.logger.debug( line)
      res = re.search(PING, line)
      myLogging.logger.debug( res)
      if res:
        myLogging.logger.info( res.group(1))
        if int(res.group(1)) == 0:
          ret1 = {'Ping_reachable': 'Y'}
  elif cmd.startswith('virsh s'):
    ret1 = {'Controlled': 'Y'}
    for line in cmd_out:
      if line.find("error:") != -1:
        ret1 = {'Controlled': 'N'}
  elif cmd == 'ps -ef|grep Xorg':
    x_servers = []
    for line in cmd_out:
      fields = re.split('\s+', line)
      if fields[7] == '/usr/bin/Xorg':
        x_server = {
          'Host': '',
          'Tty': int(fields[5].replace('tty', '')),
          'Port': 6000 + int(fields[8].replace(':', ''))
        }
        x_servers.append(x_server)
    ret1 = {'x_server': x_servers}
  elif cmd == 'cat /etc/xinetd.d/x11-fw':
    x11_fw = {}
    for line in cmd_out:
      fields = re.split('\s*=\s*', line.strip())
      if len(fields) > 1:
        x11_fw[fields[0].strip()] = fields[1].strip()
    ret1 = {'Display': x11_fw['redirect']} if 'redirect' in x11_fw else {}
  myLogging.logger.debug('ret1: %s' % ret1)
  return ret1


def ping_a_node(n):
  pa = platform.architecture()
  if pa[1].find('Win') != -1:
    #ret = os.system('ping -n 2 -w 2 %s >NUL 2>&1' % n)
    ret = os.system('ping -n 2 -w 2 %s' % n)
  else:
    #ret = os.system('ping -c 2 -W 2 %s >/dev/null 2>&1' % n)
    ret = os.system('ping -c 2 -W 2 %s' % n)
  return ret


def node_equal(n1, n2):
  if os.environ['PLAT_FORM_SITE'] == 'JV':
    return n1 == n2
  else:
    if n1.endswith('t') or n1.endswith('s') or n1.endswith('x'):
      n1 = n1[:-1]
    if n2.endswith('t') or n2.endswith('s') or n2.endswith('x'):
      n2 = n2[:-1]
    return n1 == n2


def node_not_in_list(n, l):
  if os.environ['PLAT_FORM_SITE'] == 'JV':
    return n not in l
  else:
    if n.endswith('t') or n.endswith('s') or n.endswith('x'):
      n = n[:-1]
    l2 = filter(lambda x: node_equal(x, n), l)
    return not len(l2)
