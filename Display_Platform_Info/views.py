# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from django.shortcuts import render,render_to_response
from django import forms
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib.auth.hashers import make_password,check_password
import json
import pprint
import GetPlatformInfo.runCollect as runCollect

from django.views.decorators.csrf import csrf_exempt
from Display_Platform_Info.models import node, platform_node_list, host_machine, display_machine, X_server
import Display_Platform_Info.models


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


def index(request):
    if request.method == 'GET':
        return render(request, 'index.html')


@csrf_exempt
def generate(request):
    r = runCollect.RunCollect()
    r.run_collect()
    return render(request, 'index.html', {'result': u"生成成功"})


@csrf_exempt
def platform(request):
  selected_pf_inst = None
  selected_pf = None
  selected_site = ''
  all_clear = ''
  is_update = False
  error = 'ok'
  modified = {'description': '', 'owner': '', 'validity': '', 'info': ''}
  if request.method == 'POST':
    selected_site = request.POST.get('site')
    selected_pf = request.POST.get('platform')
    for key in modified.keys():
      modified[key] = request.POST.get(key)
  if modified['info']:
    selected_site, selected_pf, all_clear = modified['info'].split()
  if all_clear:
    is_update = all_clear == 'Y' or modified['description'] or modified['owner'] or modified['validity']
  print 'modified: %s' % modified
  platforms = Display_Platform_Info.models.platform.objects.all()
  sites = list(set(map(lambda x: x.Site, platforms)))
  sites.sort()
  if not selected_site:
    selected_site = sites[0]
  pfs = []
  if selected_site.upper() != ORPHAN_NAME:
    pfs = list(set(map(lambda x: x.Platform, platforms.filter(Site=selected_site))))
    pfs.sort()
    if not selected_pf:
      selected_pf = pfs[0]
    print "select site: %s, pf: %s " % (selected_site, selected_pf)
    selected_pf_inst = platforms.get(Site=selected_site, Platform=selected_pf)
    if is_update:
      selected_pf_inst.Description = modified['description']
      selected_pf_inst.Owner = modified['owner']
      selected_pf_inst.Validity = modified['validity'] if modified['validity'] else None
      selected_pf_inst.save()
    pnls = platform_node_list.objects.filter(Platform=selected_pf_inst)
    nodes = node.objects.filter(Platform=selected_pf_inst)
    print "sites: %s" % sites
    print "pfs: %s" % pfs
    print "pnls: %s" % pnls
    print "nodes: %s" % nodes
    print "selected_site: %s" % selected_site
    print "selected_pf: %s" % selected_pf
    print "selected_pf_inst: %s" % selected_pf_inst
  else:
    nodes = node.objects.filter(Orphan='Y')
  if selected_pf_inst and not selected_pf_inst.Validity:
    selected_pf_inst.Validity = ''
  return render(request, 'Platform.html', {'nodes': nodes,
                                           'platforms': pfs,
                                           'sites': sites,
                                           'selected': selected_pf_inst,
                                           'error': error
                                           })


@csrf_exempt
def physical(request):
  selected_p = ''
  p_inst = None
  if request.method == 'POST':
    selected_p = request.POST.get('physical')
  physicals = host_machine.objects.all()
  ps = map(lambda x: x.Host_name, physicals)
  ps.sort()
  if not selected_p:
    selected_p = ps[0]
  for p in physicals:
    if p.Host_name == selected_p:
      p_inst = p
  print "p_inst: %s" % p_inst
  print "selected_p: %s" % selected_p
  ns = node.objects.filter(Host_Machine=p_inst).order_by('Name')
  nodes = map(lambda x: x.Name, ns)
  print "ps: %s" % ps
  print "nodes: %s" % nodes
  return render(request, 'Physical.html', {'nodes': ns,
                                           'physicals': ps,
                                           'selected': p_inst,
                                           'attr': {'total': ns.count(), 'running': ns.filter(Running='Y').count()}})


@csrf_exempt
def display(request):
  selected_room = ''
  if request.method == 'POST':
    selected_room = request.POST.get('room')
  if not selected_room:
    selected_room = 'EQP'
  items = []
  items2 = []
  ds = display_machine.objects.filter(Host_name__startswith=selected_room.lower())
  for d in ds:
    x_servers = X_server.objects.filter(Display_machine=d)
    ds_list = {'n': d, 'x': []}
    for x_server in x_servers:
      ns = node.objects.filter(X_server=x_server)
      for n in ns:
        conflicts = map(lambda x: x.Name if x!=n else '', ns)
        print 'conflicts: %s' % conflicts
        items.append({'n': n, 'x': x_server, 'conflict': ' '.join(conflicts)})
      if not ns.count():
        items.append({'n': None, 'x': x_server})
      ds_list['x'].append({'x': x_server, 'ns': ns})
    items2.append(ds_list)
  print "selected_room: %s" % selected_room
  print "ds: %s" % ds
  print "items: %s" % items
  return render(request, 'Display.html', {'selected': selected_room,
                                          'items': items,
                                          'rooms': ROOM_MAPPING,
                                          'items2': items2,
                                          })
