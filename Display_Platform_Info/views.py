# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import GetPlatformInfo.runCollect as runCollect
import GetPlatformInfo.sqlSiteConf as sqlSiteConf
import GetPlatformInfo.myLogging as myLogging
import GetPlatformInfo.virtMachine as virtMachine

from django.views.decorators.csrf import csrf_exempt
from Display_Platform_Info.models import node, host_machine, display_machine, X_server, site_conf
import Display_Platform_Info.models
import Platform_Map.settings
import os
import re
import socket


ORPHAN_NAME = 'ORPHAN'
ROOM_MAPPING = [
  [{'short': 'EQP', 'name': '开放办公室1'},
  {'short': 'IHP', 'name': '开放办公室2'},
  {'short': 'HDS', 'name': '开放办公室3'},
  {'short': 'MER', 'name': '1号会议室'},
  {'short': 'SGN', 'name': '2号会议室'}], # floor 15
  [{'short': 'PMO', 'name': '项目部'},
  {'short': 'GMO', 'name': '总经理'},
  {'short': 'HIM', 'name': '开放办公室'},
  {'short': 'NAM', 'name': '验收室'},
  {'short': 'SHI', 'name': '培训教室'},
  {'short': 'KAN', 'name': '会议室'},
  {'short': 'YAM', 'name': '电话室1'},
  {'short': 'MAN', 'name': '电话室2'},
  {'short': 'MKT', 'name': '市场部'},
  {'short': 'TDO', 'name': '技术总监'},
  {'short': 'DGM', 'name': '副总经理'},
  {'short': 'FIN', 'name': '财务办公室'}], # floor 16
]
rooms = []
for room_map in ROOM_MAPPING:
  rooms.extend(map(lambda x: x['short'], room_map))
DESC_PATTERN = re.compile('^\s*Description\s*[:=]')
OWNER_PATTERN = re.compile('^\s*Owner\s*[:=]')
VAILID_PATTERN = re.compile('^\s*Validity\s*[:=]')


@myLogging.log('views')
def write_back_to_conf(pf):
  conf = os.path.join(Platform_Map.settings.BASE_DIR, 'conf', pf.Site, '%s.conf' % pf.Site)
  conf_new = "%s.new" % conf
  SITE_PATTERN = re.compile('^\s*\[\s*%s\s+%s\s*\]' % (pf.Site, pf.Platform))
  written = {'Description': False, 'Owner': False, 'Validity': False}
  site_found = False
  desc_found = False
  completed = False
  with open(conf) as fd:
    with open(conf_new, 'w') as fd2:
      lines = []
      for line in fd:
        if not completed:
          ret = re.search(SITE_PATTERN, line)
          if ret:
            site_found = True
          elif site_found:
            ret = re.search(DESC_PATTERN, line)
            if ret:
              desc_found = True
              line = 'Description: %s\n' % pf.Description
              written['Description'] = True
            else:
              if desc_found:
                if not line.startswith('#') and not line.startswith(';') and not line.startswith(' '):
                  desc_found = False
                else:
                  myLogging.logger.info("Skip the second line for Description!")
                  continue
              ret = re.search(OWNER_PATTERN, line)
              if ret:
                line = 'Owner: %s\n' % pf.Owner
                written['Owner'] = True
              else:
                ret = re.search(VAILID_PATTERN, line)
                if ret:
                  line = 'Validity: %s\n' % pf.Validity
                  written['Validity'] = True
                elif line.replace(" ", '').startswith('['):
                  completed = True
                  if not written['Description']:
                    line = "".join([line, 'Description: %s\n' % pf.Description])
                  if not written['Owner']:
                    line = "".join([line, 'Owner: %s\n' % pf.Owner])
                  if not written['Validity']:
                    line = "".join([line, 'Validity: %s\n' % pf.Validity])
        lines.append(line)
      fd2.write(''.join(lines))
  myLogging.logger.info("To delete conf file!")
  os.unlink(conf)
  myLogging.logger.info("To rename new conf file!")
  os.rename(conf_new, conf)
  sc = site_conf.objects.get(Site=pf.Site)
  sc.Md5 = sqlSiteConf.SQLSiteConf.get_conf_md5(conf)
  myLogging.logger.info("To update site_conf table!")
  sc.save()


def index(request):
    if request.method == 'GET':
        return render(request, 'index.html')


@csrf_exempt
def generate(request):
    r = runCollect.RunCollect()
    r.run_collect()
    return render(request, 'index.html', {'result': u"生成成功"})


def clear_unuse_fields(n):
  n1={}
  n1['Name'] = n.Name
  n1['OPS_Name'] = n.OPS_Name
  n1['Host'] = n.Host
  n1['Reachable'] = n.Reachable
  n1['Running'] = n.Running
  n1['Thalix'] = n.Thalix
  n1['Display'] = "%s %s" % (n.X_server.Host, n.X_server.Tty) if n.X_server else None
  n1['Config'] = n.Config
  n1['CSCI'] = n.CSCI
  return n1


@myLogging.log('views')
@csrf_exempt
def platform(request):
  platforms = Display_Platform_Info.models.platform.objects.all()
  sites = list(set(map(lambda x: x.Site, platforms)))
  sites.sort()
  ret_info = []
  orphan_site = {}
  for site in sites:
    a_site = {'site_name': site,
              'pfs': []}
    pfs = platforms.filter(Site=site).order_by('Platform')
    for pf in pfs:
      nodes = node.objects.filter(Platform=pf).order_by('Name')
      a_pf = {'pf_name': pf.Platform,
              'desc': pf.Description,
              'owner': pf.Owner,
              'valid': pf.Validity,
              'nodes': nodes}
      a_site['pfs'].append(a_pf)
    if site != ORPHAN_NAME:
      ret_info.append(a_site)
    else:
      orphan_site.update(a_site)
  ret_info.append(orphan_site)
  myLogging.logger.info("ret: %s" % ret_info)
  return render(request, 'Platform.html', {'sites': ret_info,
                                           })


@myLogging.log('views')
@csrf_exempt
def submit_platform(request):
  ret = 'Failed'
  if request.method == 'POST':
    try:
      site = request.POST.get('site').strip()
      pf = request.POST.get('pf').strip()
      desc = request.POST.get('desc').strip()
      owner = request.POST.get('owner').strip()
      valid = request.POST.get('valid').strip()
      myLogging.logger.info('POST:\nsite: %s\n pf: %s\n desc: %s\n owner: %s\n valid: %s' % (site, pf, desc, owner, valid))
      pf_info = Display_Platform_Info.models.platform.objects.get(Site=site, Platform=pf)
      if pf_info.Description != desc or pf_info.Owner != owner or pf_info.Validity != valid:
        pf_info.Description = desc
        pf_info.Owner = owner
        pf_info.Validity = valid
        pf_info.save()
        write_back_to_conf(pf_info)
        ret = 'Successful'
      else:
        ret = 'No change!'
    except Exception, e:
      myLogging.logger.exception('Exception in submit_platform!')
      ret = e.message
  myLogging.logger.info('ret: %s' %ret)
  return HttpResponse(ret)


@myLogging.log('views')
@csrf_exempt
def physical(request):
  hms = host_machine.objects.all().order_by('Host_name')
  ret_info = []
  for hm in hms:
    ns = node.objects.filter(Host_Machine=hm).order_by('Name')
    ret_info.append({'hm_name': hm.Host_name,
                     'nodes': ns,
                     'total': ns.count(),
                     'running': ns.filter(Running='Y').count(),
                     })
  myLogging.logger.info("ret_info: %s" % ret_info)
  return render(request, 'Physical.html', {'hms': ret_info,
                                           })


@myLogging.log('views')
@csrf_exempt
def display(request):
  room_infos = []
  ds = display_machine.objects.all()
  for room in rooms:
    ds_a_room = ds.filter(Host_name__startswith=room.lower()).order_by('Host_name')
    a_room = []
    for d in ds_a_room:
      x_servers = X_server.objects.filter(Display_machine=d).order_by('Tty')
      a_dm = []
      for x_server in x_servers:
        ns = node.objects.filter(X_server=x_server).order_by('Name')
        #print "x:[%s %d], n:[%s]" % (x_server.Host, x_server.Tty, map(lambda x: x.Name, ns))
        if not ns.count():
          a_dm.append({'ns': '', 'x': x_server, 'conflict': 'N'})
        elif ns.count() == 1:
          a_dm.append({'ns': ns[0].Name, 'x': x_server, 'conflict': 'N'})
        else:
          a_dm.append({'ns': ' '.join(map(lambda x: x.Name, ns)), 'x': x_server, 'conflict': 'Y'})
      a_room.append({'n': d, 'xs': a_dm})
    room_infos.append({'room': room, 'ds': a_room})
  #print "ds: %s" % ds
  myLogging.logger.info("room_infos: %s" % room_infos)
  return render(request, 'Display.html', {'room_infos': room_infos,
                                          'rooms': ROOM_MAPPING,
                                          })


@myLogging.log('views')
def change_x11_fw(vm, n, x):
  err = 'Successful'
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
  ''' % (x.Host, x.Port)
  vm.init_ssh()
  vm.execute_cmd(cmd, redirect_stderr=False)
  stderr = vm.stdout.read()
  if stderr:
    vm.close_ssh()
    err = "Write x11-fw error!"
    myLogging.logger.error(err)
    return err
  vm.execute_cmd('service xinetd reload', redirect_stderr=False)
  myLogging.logger.info(vm.stdout.read())
  stderr = vm.stderr.read()
  if stderr:
    vm.close_ssh()
    err = "Reload x11-fw error!"
    myLogging.logger.error(err)
    return err
  vm.close_ssh()
  ret = vm.set_x_server(x)
  if not ret:
    err = "Set x server error!"
    myLogging.logger.error(err)
  return err


@myLogging.log('views')
@csrf_exempt
def submit_display(request):
  ret = 'Failed'
  ret_cx =  []
  changed_xs = []
  if request.method == 'POST':
    try:
      host = request.POST.get('host').strip()
      nodes = request.POST.get('ns').strip().split()
      nodes.sort()
      nodes =filter(lambda y: y, nodes)
      tty = int(request.POST.get('tty').strip().replace('TTY', ''))
      myLogging.logger.info("POST:\nhost: %s\nnodes: %s\ntty: %s" % (host, nodes, tty))
      x = X_server.objects.get(Host=host, Tty=tty)
      ns = node.objects.filter(X_server=x)
      nodes2 = map(lambda y: y.Name, ns)
      nodes2.sort()
      if cmp(nodes, nodes2) != 0:
        for n in [y for y in nodes if y not in nodes2]:
          vm = virtMachine.VirMachine(n)
          vm_db = vm.get_vm_db_inst()
          old_x =None if not vm_db else vm_db.X_server
          ret = change_x11_fw(vm, n, x)
          if ret != "Successful":
            break
          if not changed_xs:
            changed_xs.append(x)
          if old_x:
            changed_xs.append(old_x)
        for cx in changed_xs:
          cx_ns = ' '.join(map(lambda y: y.Name, node.objects.filter(X_server=cx)))
          ret_cx.append({'host': cx.Host,
                         'tty': cx.Tty,
                         'ns': cx_ns,
                         'c': 'Y' if cx_ns.count(' ') else 'N',
                         })
        if not changed_xs:
          ret = 'Not allowed to remove!'
      else:
        ret = 'No change!'
    except socket.gaierror:
      myLogging.logger.exception('getaddrinfo failed in submit display!')
      ret = 'Getaddrinfo failed'
    except Exception, e:
      myLogging.logger.exception('Exception in submit display!')
      if e.message:
        ret = e.message
      else:
        ret = e.__class__.__name__
  myLogging.logger.info('ret: %s' % ret)
  myLogging.logger.info('cx: %s' % ret_cx)
  return JsonResponse({'ret': ret, 'cx': ret_cx})
