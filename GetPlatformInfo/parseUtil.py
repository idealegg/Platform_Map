# -*- coding: utf-8 -*-

import re
import myLogging

UNAME_PATTERN = re.compile('^(\w+)\s+([^\s]+)\s+([^\s]+)\s+')
IFCONFIG_P1 = re.compile('^([^\s]+).*HWaddr\s+([\w:]+)')
IFCONFIG_P2 = re.compile('^\s+inet addr:([\d.]+)\s+Bcast:([\d.]+)\s+Mask:([\d.]+)')
PING = re.compile('(\d+)(\.\d+)?% packet loss')

conf = None


def set_conf(c):
  global conf
  conf = c


@myLogging.log("parseUtil")
def gen_script(cmd_list, vm_name, is_ssh=True):
  vm = vm_name
  tmp_script = []
  tmp_script.append('''#!/usr/bin/expect
spawn %s %s
set timeout %d
set done 1
set nologined 1
set timeout_case 0

while ($done) {
  expect {
    " login:" { if ($nologined) {
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
          send "\\n"
''' % (('ssh -l system' if is_ssh else 'virsh console'), vm, conf.get_para_int('remote_cmd_timeout_seconds')))
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
              if ($timeout_case < %d) {
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
  if cmd == 'uname -a':
    res = re.search(UNAME_PATTERN, cmd_out[0])
    if res:
      return {'Os': res.group(1),
               'OPS_Name': res.group(2),
               'Structure': res.group(3),
              }
    return None
  if cmd == 'cat /etc/thalix-release':
    return {'Thalix': cmd_out[0]}
  if cmd == 'ifconfig -a':
    cur_interface = ''
    interface = {}
    ret = []
    ip = []
    for line in cmd_out:
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
        interface['HWaddr'] = res.group(2)
        cur_interface = interface['Name']
      else:
        res = re.search(IFCONFIG_P2, line)
        if res:
          interface['addr'] = res.group(1)
          interface['Bcast'] = res.group(2)
          interface['Mask'] = res.group(3)
    if cur_interface:
      #ret[cur_interface] = interface
      ret.append("%s\n\tHWaddr:%s" % (cur_interface, interface['HWaddr']))
      if interface.has_key('addr'):
        ret.append("\n\taddr:%s" % (interface['addr']))
        ret.append("\n\tBcast:%s" % (interface['Bcast']))
        ret.append("\n\tMask:%s" % (interface['Mask']))
        ip.append(interface['addr'])
    return {'Interface': ret, 'IP': ' '.join(ip)}
  if cmd == 'vers':
    ret = {}
    for line in cmd_out:
      tmp = line.split('=')
      if len(tmp) > 1:
        ret[tmp[0]] = tmp[1]
    if 'RUN_CONFIG_VERS' not in ret:
      ret['RUN_CONFIG_VERS'] = ''
    return {'Config': ret['RUN_CONFIG_VERS']}
  if cmd == 'message':
    csci = []
    if vm_ops_name:
      for line in cmd_out:
        tmp = re.split('\s+', line)
        if len(tmp) > 1:
          if vm_ops_name in tmp:
            csci.append(re.sub("\d+", '', tmp[0]))  # 删除数字
    return {'CSCI': " ".join(csci)}
  if cmd.startswith('ping -c 3 -W 2'):
    for line in cmd_out:
      myLogging.logger.info( line)
      res = re.search(PING, line)
      myLogging.logger.info( res)
      if res:
        myLogging.logger.info( res.group(1))
        if int(res.group(1)) == 0:
          return {'Ping_reachable': 'Y'}
    return {'Ping_reachable': 'N'}
  if cmd.startswith('virsh s'):
    for line in cmd_out:
      if line.find("error:") != -1:
        return {'Controlled': 'N'}
    return {'Controlled': 'Y'}
  if cmd == 'ps -ef|grep Xorg':
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
    return {'x_server': x_servers}
  if cmd == 'cat /etc/xinetd.d/x11-fw':
    x11_fw = {}
    for line in cmd_out:
      fields = re.split('\s*=\s*', line.strip())
      if len(fields) > 1:
        x11_fw[fields[0].strip()] = fields[1].strip()
    return {'Display': x11_fw['redirect']} if x11_fw.has_key('redirect') else {}
  return {}