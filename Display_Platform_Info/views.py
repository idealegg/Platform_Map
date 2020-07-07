# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db import transaction
from django.db.utils import IntegrityError
import GetPlatformInfo.runCollect as runCollect
import GetPlatformInfo.myLogging as myLogging
import GetPlatformInfo.virtMachine as virtMachine
import GetPlatformInfo.xServer as xServer

from django.views.decorators.csrf import csrf_exempt
from Display_Platform_Info.models import node, host_machine, display_machine, X_server, run_state, User
import Display_Platform_Info.models
import Platform_Map.settings
import os
import re
import socket
from dwebsocket.decorators import accept_websocket
import threading
import datetime
import json
import time
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


MAX_WEB_CONNECTION = 5
ORPHAN_NAME = 'ORPHAN'
if 'PLAT_FORM_SITE' not in os.environ or os.environ['PLAT_FORM_SITE'] == 'JV':
  ROOM_MAPPING = [
    {'name': '15层', 'rooms':
     [
      #{'short': 'EQP', 'name': '开放办公室1'}
      {'short': 'IHP', 'name': '内部平台'}
      ,{'short': 'HDS', 'name': '横断山脉'}
      #,{'short': 'MER', 'name': '1号会议室'}
      #,{'short': 'SGN', 'name': '2号会议室'}
     ]
     }, # floor 15
    {'name': '16层', 'rooms':
     [
      #{'short': 'PMO', 'name': '项目部'},
      #{'short': 'GMO', 'name': '总经理'},
      {'short': 'HIM', 'name': '喜马拉雅山脉'}
      #{'short': 'NAM', 'name': '验收室'},
      #{'short': 'SHI', 'name': '培训教室'},
      #{'short': 'KAN', 'name': '会议室'},
      #{'short': 'YAM', 'name': '电话室1'},
      #{'short': 'MAN', 'name': '电话室2'},
      #{'short': 'MKT', 'name': '市场部'},
      #{'short': 'TDO', 'name': '技术总监'},
      #{'short': 'DGM', 'name': '副总经理'},
      #{'short': 'FIN', 'name': '财务办公室'}
     ]
     }, # floor 16
  ]
else:
  ROOM_MAPPING = [
    {'name': '内厅', 'rooms':
      [{'short': 'CDT', 'name': '办公区'}]
    },
    {'name': '外厅', 'rooms':
      [{'short': 'BEC', 'name': '平台区'}]
    },
  ]
rooms = []
for room_map in ROOM_MAPPING:
  rooms.extend(map(lambda x: x['short'], room_map['rooms']))
DESC_PATTERN = re.compile('^\s*Description\s*[:=]')
OWNER_PATTERN = re.compile('^\s*Owner\s*[:=]')
VAILID_PATTERN = re.compile('^\s*Validity\s*[:=]')
rand_list = []
sockets = {}
lock = threading.Lock()
lock2 = threading.Lock()
lock3 = threading.Lock()
lock4 = threading.Lock()
lock5 = threading.Lock()


def datetime2str(dt):
  if not dt:
    return ''
  return "%s.%06d" % (dt.strftime('%Y-%m-%d %H:%M:%S'), dt.microsecond)


def str2datetime(s):
  if not s:
    return datetime.datetime.min
  return datetime.datetime(
    int(s[:4]),
    int(s[5:7]),
    int(s[8:10]),
    int(s[11:13]),
    int(s[14:16]),
    int(s[17:19]),
    int(s[20:])
  )


def get_ip(request):
  if 'HTTP_X_FORWARDED_FOR' in request.META:
    ip = request.META['HTTP_X_FORWARDED_FOR']
  else:
    ip = request.META['REMOTE_ADDR']
  #print "client ip: %s"  % ip
  return ip


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
        if type(line) is not unicode:
          line = line.decode('utf8')
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
      fd2.write(''.join(lines).encode('utf8'))
  myLogging.logger.info("To delete conf file!")
  os.unlink(conf)
  myLogging.logger.info("To rename new conf file!")
  os.rename(conf_new, conf)
  #sc = site_conf.objects.get(Site=pf.Site)
  #sc.Md5 = sqlSiteConf.SQLSiteConf.get_conf_md5(conf)
  #myLogging.logger.info("To update site_conf table!")
  #sc.save()


@csrf_exempt
def generate(request):
    r = runCollect.RunCollect()
    r.run_collect()
    return render(request, 'login.html', {'result': u"生成成功"})


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
@login_required()
def platform(request):
  ip = get_ip(request)
  myLogging.logger.info("IP: %s, user: %s" % (ip, request.user.username))
  request.session['IP'] = ip
  request.session['username'] = request.user.username
  #a=request.session.get('IP', None)
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
              'last_mod': datetime2str(pf.Last_modified),
              'nodes': nodes}
      a_site['pfs'].append(a_pf)
    if site != ORPHAN_NAME:
      ret_info.append(a_site)
    else:
      orphan_site.update(a_site)
  if 'pfs' in orphan_site:
    if len(orphan_site['pfs']):
      orphan_site['pfs'][0]['nodes'].union(node.objects.filter(Platform__isnull=True))
  ret_info.append(orphan_site)
  myLogging.logger.info("ret: %s" % ret_info)
  return render(request, 'Platform.html', {'sites': ret_info,
                                           })


@myLogging.log('views')
@csrf_exempt
def submit_platform(request):
  ret = {'ret': 'Failed',
         'last_mod': '',
         }
  locked = False
  myLogging.logger.info("IP: %s, user: %s" % (get_ip(request), request.user.username))
  if request.method == 'POST':
    try:
      site = request.POST.get('site').strip()
      pf = request.POST.get('pf').strip()
      desc = request.POST.get('desc').strip()
      owner = request.POST.get('owner').strip()
      valid = request.POST.get('valid').strip()
      last_mod = request.POST.get('last_mod').strip()
      myLogging.logger.info('POST:\nsite: %s\n pf: %s\n desc: %s\n owner: %s\n valid: %s\nlast_mod: %s'
                            % (site, pf, desc, owner, valid, last_mod))
      pf_info = Display_Platform_Info.models.platform.objects.get(Site=site, Platform=pf)
      if str2datetime(last_mod) < pf_info.Last_modified:
        ret['ret'] = 'Platform modified by others, please refresh page!'
      elif pf_info.Description == desc and pf_info.Owner == owner and pf_info.Validity == valid:
        ret['ret'] = 'No change!'
      else:
        #print "user: %s" % request.user
        #print "type: %s" % type(request.user)
        own_right = (request.user.username.lower() == pf_info.Owner.lower()
                      and datetime.datetime.now().date() <= pf_info.Validity)
        get_right = (request.user.username.lower() == owner.lower()
                      and str(datetime.datetime.now().date()) <= valid)
        other_right = (pf_info.Owner.lower() != owner.lower()
                      and datetime.datetime.now().date() <= pf_info.Validity)
        if (not other_right and get_right) or (own_right and not get_right):
          pf_info.Description = desc
          pf_info.Owner = owner
          pf_info.Validity = valid if valid else None
          lock2.acquire()
          locked = True
          with transaction.atomic():
            pf_info.save()
            pf_info.Validity = valid if valid else ''
            write_back_to_conf(pf_info)
          ret['last_mod'] = datetime2str(pf_info.Last_modified)
          lock2.release()
          locked = False
          ret['ret'] = 'Successful'
        else:
          ret['ret'] = 'You have no rights, please refresh page!'
    except Exception, e:
      if locked:
        lock2.release()
      myLogging.logger.exception('Exception in submit_platform!')
      ret = "%s: %s" % (e.__class__.__name__, e.message)
  myLogging.logger.info('ret: %s' % ret)
  return JsonResponse(ret)


@myLogging.log('views')
@csrf_exempt
@login_required()
def physical(request):
  ip = get_ip(request)
  myLogging.logger.info("IP: %s, user: %s" % (ip, request.user.username))
  request.session['IP'] = ip
  request.session['username'] = request.user.username
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
@login_required()
def display(request):
  ip = get_ip(request)
  myLogging.logger.info("IP: %s, user: %s" % (ip, request.user.username))
  request.session['IP'] = ip
  request.session['username'] = request.user.username
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
          a_dm.append({'n_name': '', 'x': x_server, 'conflict': 'N', 'n_time': []})
        else:
          a_dm.append({'n_name': ' '.join(map(lambda x: x.Name, ns)),
                       'x': x_server,
                       'conflict': 'N' if ns.count() == 1 else 'Y',
                       'n_time': map(lambda x: {'n': x.Name, 't': datetime2str(x.Last_modified), 'r': x.Running}, ns),
                       })
      a_room.append({'n': {
                            'Node': d.Node,
                            'Host_name': d.Host_name,
                            'n_t': datetime2str(d.Last_modified),
                            'os': d.Thalix,
                            'usr': d.Owner,
                           }, 'xs': a_dm})
    room_infos.append({'room': room, 'ds': a_room})
  #print "ds: %s" % ds
  myLogging.logger.info("room_infos: %s" % room_infos)
  return render(request, 'Display.html', {'room_infos': room_infos,
                                           'rooms': ROOM_MAPPING,
                                          })


@myLogging.log('views')
def update_dm_user(host, user):
  try:
    dm = display_machine.objects.get(Node=host, Owner="")
  except:
    myLogging.logger.info("Owner exists! Skip update.")
    return
  dm.Owner = user
  dm.save()
  

@myLogging.log('views')
@csrf_exempt
def submit_display(request):
  myLogging.logger.info("IP: %s, user: %s" % (get_ip(request), request.user.username))
  ret = 'Failed'
  ret2 = ''
  ret_cx =  []
  changed_xs = set([])
  host = ""
  locked = False
  if request.method == 'POST':
    try:
      host = request.POST.get('host').strip()
      nodes = request.POST.get('ns').strip().split()
      n_time = request.POST.get('n_time').strip()
      tty = int(request.POST.get('tty').strip().replace('TTY', ''))
      myLogging.logger.info("POST:\nhost: %s\nnodes: %s\ntty: %s" % (host, nodes, tty))
      myLogging.logger.info("POST:n_time: %s" % n_time)
      lock3.acquire()
      locked = True
      if n_time:
        j = json.loads(n_time)
        try:
          for n in j:
            node.objects.get(Name=n['n'], Last_modified=str2datetime(n['t']))
        except node.DoesNotExist:
          if locked:
            lock3.release()
            locked = False
          ret = 'Node modified by others, pls refresh!'
          myLogging.logger.info('ret: %s' % ret)
          return JsonResponse({'ret': ret, 'cx': ret_cx})
      nodes.sort()
      nodes =filter(lambda y: y, nodes)
      x = X_server.objects.get(Host=host, Tty=tty)
      ns = node.objects.filter(X_server=x)
      nodes2 = map(lambda y: y.Name, ns)
      nodes2.sort()
      if cmp(nodes, nodes2) != 0:
        for n in [y for y in nodes if y not in nodes2] + [y for y in nodes2 if y not in nodes]:
          vm = virtMachine.VirMachine(n)
          with transaction.atomic():
            vm_db = vm.get_vm_db_inst()
            vm.set_x_server(x if n in nodes else None)
          old_x =None if not vm_db else vm_db.X_server
          ret2 = vm.change_x11_fw(x if n in nodes else None)
          ret = ret2
          if ret2 != "Successful":
            changed_xs = set([])
            break
          changed_xs.add(x)
          if old_x:
            changed_xs.add(old_x)
        for cx in changed_xs:
          cx_ns = node.objects.filter(X_server=cx)
          s_ns = ' '.join(map(lambda y: y.Name, cx_ns))
          ret_cx.append({'host': cx.Host,
                         'tty': cx.Tty,
                         'ns': s_ns,
                         'c': 'Y' if s_ns.count(' ') else 'N',
                         'n_time': map(lambda y: {'n': y.Name, 't': datetime2str(y.Last_modified), 'r': y.Running}, cx_ns)
                         })
        if not ret2 and not changed_xs:
          ret = 'Not allowed to remove!'
      else:
        ret = 'No change!'
      if locked:
        lock3.release()
        locked = False
    except socket.gaierror:
      myLogging.logger.exception('getaddrinfo failed in submit display!')
      ret = 'Getaddrinfo failed'
    except Exception, e:
      myLogging.logger.exception('Exception in submit display!')
      ret = "%s: %s" % (e.__class__.__name__, e.message)
    finally:
      if locked:
        lock3.release()
        #locked = False
      if ret == "Successful":
        update_dm_user(host, request.user.username)
  myLogging.logger.info('ret: %s' % ret)
  myLogging.logger.info('cx: %s' % ret_cx)
  return JsonResponse({'ret': ret, 'cx': ret_cx})


@myLogging.log('views')
@csrf_exempt
def submit_restart_mmi(request):
  myLogging.logger.info("IP: %s, user: %s" % (get_ip(request), request.user.username))
  ret = 'Failed'
  vm = None

  def return2(ret1, rollback_restarting=True):
    myLogging.logger.info('ret: %s' % ret1)
    if rollback_restarting:
      vm.save_restarting(False)
    return JsonResponse({'ret': ret1, 'n_t': datetime2str(vm.db_inst.Last_modified) if vm else ''})

  if request.method == 'POST':
    try:
      host = request.POST.get('host').strip()
      nd = request.POST.get('node').strip()
      n_time = request.POST.get('n_time').strip()
      timeout = int(request.POST.get('timeout').strip())
      myLogging.logger.info("POST:\nhost: %s\nnode: %s\nn_time: %s\ntimeout: %d" % (host, nd, n_time, timeout))
      start_time = time.time()
      with transaction.atomic():
        try:
          node.objects.get(Name=nd, Last_modified=str2datetime(n_time))
        except node.DoesNotExist:
            return return2 ( 'Node modified by others, pls refresh!', False)
        try:
          node.objects.get(Name=nd, Last_modified=str2datetime(n_time), Restarting=False)
        except node.DoesNotExist:
          return return2('Node restarted by others, pls wait!', False)
        vm = virtMachine.VirMachine(nd)
        vm.set_user('system')
        vm.save_restarting(True)
      dm = display_machine.objects.get(Node=host)
      if not vm.db_inst.CSCI.count('MMI'):
        if not vm.stop_node(timeout - (time.time()-start_time)):
          return return2('Stop node failed or timeout!')
        if not vm.start_node(timeout - (time.time()-start_time)):
          return return2('Start node failed or timeout!')
      else:
        #if not vm.stop_mmi(timeout - (time.time()-start_time)):
        if not vm.stop_node(timeout - (time.time() - start_time)):
          return return2('Stop mmi failed or timeout!')
        if not vm.copy_key_mapping_files(dm.Thalix):
          return return2('Copy key mapping files failed!')
        #if not vm.start_mmi(timeout - (time.time()-start_time)):
        if not vm.start_node(timeout - (time.time() - start_time)):
          return return2('Start mmi failed or timeout!')
      vm.save_restarting(False)
      ret = 'Successful'
    except socket.gaierror:
      myLogging.logger.exception('getaddrinfo failed in submit display!')
      ret = 'Getaddrinfo failed'
    except Exception, e:
      myLogging.logger.exception('Exception in submit display!')
      ret = "%s: %s" % (e.__class__.__name__, e.message)
    finally:
      if vm and vm.db_inst.Restarting:
        vm.save_restarting(False)
      if ret == "Successful":
        update_dm_user(host, request.user.username)
  n_t = datetime2str(vm.db_inst.Last_modified) if vm else ''
  myLogging.logger.info('ret: %s, n_t: %s' % (ret, n_t))
  return JsonResponse({'ret': ret, 'n_t': n_t})


@myLogging.log('views')
@csrf_exempt
def submit_tty(request):
  myLogging.logger.info("IP: %s, user: %s" % (get_ip(request), request.user.username))
  ret = 'Failed'
  locked = False
  n_t = ''
  if request.method == 'POST':
    try:
      host = request.POST.get('host').strip()
      n_time = request.POST.get('n_time').strip()
      tty = int(request.POST.get('tty').strip().replace('TTY', ''))
      myLogging.logger.info("POST:\nhost: %s\ntty: %s\nn_time: %s" % (host, tty, n_time))
      lock4.acquire()
      locked = True
      try:
        dm = display_machine.objects.get(Node=host, Last_modified=str2datetime(n_time))
      except display_machine.DoesNotExist:
        if locked:
          lock4.release()
          locked = False
        ret = 'Node modified by others, pls refresh!'
        myLogging.logger.info('ret: %s' % ret)
        return JsonResponse({'ret': ret, 'n_t': n_t})
      n_t = datetime2str(dm.Last_modified)
      xs = xServer.XServer(host)
      try:
        xs.init_ssh()
      except Exception, e:
        ret = 'Init ssh failed!'
        myLogging.logger.info('ret: %s' % ret)
        if locked:
          lock4.release()
          locked = False
        return JsonResponse({'ret': ret, 'n_t': n_t})
      xs.execute_cmd('chvt %d' % tty)
      xs.close_ssh()
      x_new = X_server.objects.get(Host=host, Tty=tty)
      with transaction.atomic():
        x_olds = X_server.objects.filter(Display_machine=dm, Active=True).exclude(Tty=tty)
        for x_old in x_olds:
          x_old.Active = False
          x_old.save()
        x_new.Active = True
        x_new.save()
        dm.save()
        ret = 'Successful'
        n_t = datetime2str(dm.Last_modified)
    except socket.gaierror:
      myLogging.logger.exception('getaddrinfo failed in submit display!')
      ret = 'Getaddrinfo failed'
    except Exception, e:
      myLogging.logger.exception('Exception in submit tty!')
      ret = "%s: %s" % (e.__class__.__name__, e.message)
    finally:
      if locked:
        lock4.release()
      if ret == "Successful":
        update_dm_user(host, request.user.username)
        #locked = False
  myLogging.logger.info('ret: %s, n_t: %s' % (ret, n_t))
  return JsonResponse({'ret': ret, 'n_t': n_t})


@myLogging.log('views')
@csrf_exempt
def backend(request):
  rss = run_state.objects.all().order_by('-Counter', 'Begin')
  myLogging.logger.info("rss: %s" % rss)
  return render(request, 'Backend.html', {'rss': rss,
                                          })


@myLogging.log('views')
@csrf_exempt
@login_required()
def backend2(request):
  ip = get_ip(request)
  myLogging.logger.info("IP: %s, user: %s" % (ip, request.user.username))
  request.session['IP'] = ip
  request.session['username'] = request.user.username
  now = datetime.datetime.now()
  rss = run_state.objects.all().order_by('-Counter', 'Begin')
  max_begin = max(map(lambda x: x.Begin, rss)) if rss.count() else now
  myLogging.logger.info("rss: %s" % rss)
  myLogging.logger.info("max_begin: %s" % max_begin)
  return render(request, 'Backend2.html', {'rss': rss,
                                            'req_time': datetime2str(max_begin),
                                           })


@myLogging.log('views')
@csrf_exempt
@accept_websocket
def client_connect(request):
  if request.is_websocket():
    lock.acquire()
    if len(sockets) >= MAX_WEB_CONNECTION:
      request.websocket.close()
      lock.release()
      return
    sockets[request.websocket] = {}
    lock.release()
    myLogging.logger.info("socket number: %d" % len(sockets))
    myLogging.logger.info('enter message process')
    for message in request.websocket:
      myLogging.logger.info("Received a message: %s" % message)
      if message:
        if len(message) == 26:
          sockets[request.websocket]['begin'] = str2datetime(message)
      #request.websocket.send('abc')
    myLogging.logger.info('exit message process')
    lock.acquire()
    del sockets[request.websocket]
    lock.release()
  else:
    return HttpResponse('Are you kiding me?')


@myLogging.log('views')
@csrf_exempt
def backend_push(request):
  if request.method == 'POST':
    rs_site = request.POST.get('site').strip()
    rs_pf = request.POST.get('pf').strip()
    rs_b = request.POST.get('begin').strip()
    rs_s = request.POST.get('state').strip()
    rs_c = request.POST.get('counter').strip()
    myLogging.logger.info('site: %s, pf: %s' % (rs_site, rs_pf))
    myLogging.logger.info('rs_b: %s, rs_s: %s, rs_c: %s' % (rs_b, rs_s, rs_c))
    dt = str2datetime(rs_b)
    lock.acquire()
    for sock in sockets:
      # rss = run_state.objects.filter(Begin__range=[sockets[sock]['begin'], dt],
      #                                Counter=int(rs_c)).order_by('-Counter', 'Begin')
      rss = run_state.objects.filter(Begin__range=[sockets[sock]['begin'], dt],
                                     Counter=int(rs_c)).order_by('Begin')
      ret = map(lambda x: {'Site': x.Current_platform.Site,
                            'Platform': x.Current_platform.Platform,
                            'Begin': datetime2str(x.Begin) if x.Begin else '',
                            'End': datetime2str(x.End) if x.End else '',
                            'State': rs_s if x.Begin == dt else 'Completed',
                            'Counter': x.Counter,
                           },
                rss)
      myLogging.logger.info('ret: %s' % ret)
      sock.send(json.dumps(ret))
      sockets[sock]['begin'] = dt
    lock.release()
  return HttpResponse('ok')


valid_users ={'time': datetime.datetime.min, 'list':[]}
blacklist = ['tools', 'ben', 'dengzp', 'lixinwei', 'eleroux', 'liudan', 'ss', 'alex', 'lir', 'liuh', 'wangj']
whitelist = []


@myLogging.log('views')
def update_valid_user():
  try:
    vm = virtMachine.VirMachine('tai2')
    vm.set_user('system')
    vm.init_ssh()
    vm.execute_cmd("/usr/bin/awk -F':' '/home/{print $1}' /etc/passwd")
    global valid_users
    valid_users['list'] = [x.strip() for x in vm.stdout]
    vm.close_ssh()
    valid_users['time'] = datetime.datetime.now()
    myLogging.logger.info(valid_users)
  except:
    myLogging.logger.exception("update_valid_user failed!")


def is_valid_user(usr):
  # update every 7 days
  if valid_users['time'] == datetime.datetime.min or datetime.datetime.now() - valid_users['time'] > datetime.timedelta(7):
    update_valid_user()
  return usr in whitelist or (usr in valid_users['list'] and usr not in blacklist)


@myLogging.log('views')
def reg(request):
    myLogging.logger.info("IP: %s, user: %s" % (get_ip(request), request.user.username))
    if request.method == 'GET':
        return render(request, 'reg.html')
    elif request.method == 'POST':
        username = request.POST.get('username').lower()
        if not is_valid_user(username):
          return HttpResponse('Usenname should be a tai2 user account!')
        pwd = request.POST.get('password')
        if len(pwd) < 6:
          return HttpResponse('Password should not less than 6 chars!')
        mobile = request.POST.get('mobile')
        if (len(mobile)!=11) or mobile[0]!='1' or not mobile.isdigit():
          return HttpResponse('Invalid mobile!')
        email = request.POST.get('email')
        if not email.endswith('@easysky.com.cn') or len(email) < 17:
          return HttpResponse('Invalid email!')
        myLogging.logger.info("usr: %s, mobile: %s, email: %s" % (username, mobile, email))
        # 插入信息
        try:
          User.objects.create_user(username=username, password=pwd, email=email, mobile=mobile)
        except IntegrityError:
          return HttpResponse('User existed!')
        return HttpResponseRedirect('/login/')
    return HttpResponseRedirect('/reg/')


@myLogging.log('views')
def log_in(request):
  myLogging.logger.info("IP: %s, user: %s" % (get_ip(request), request.user.username))
  #is_authenticated = False
  #if request.user.is_authenticated:
  #  pass
  if request.method == 'GET':
      return render(request, 'login.html')
  elif request.method == 'POST':
    username = request.POST.get('username').lower()
    pwd = request.POST.get('password')
    #print "ip: %s" % get_ip(request)
    #print "user: %s, passwd: %s" % (username, pwd)
    myLogging.logger.info("usr: %s" % (username,))
    usern = authenticate(username=username, password=pwd)
    print "usern: %s" % usern
    if usern:
      login(request, usern)  # 登陆
      next_url = request.GET.get('next', None)
      if not next_url:
        next_url = '/platform/'
      return HttpResponseRedirect(next_url)
  return HttpResponseRedirect('/login/')


@myLogging.log('views')
def log_out(request):
  myLogging.logger.info("IP: %s, user: %s" % (get_ip(request), request.user.username))
  logout(request)
  return HttpResponseRedirect('/login/')
