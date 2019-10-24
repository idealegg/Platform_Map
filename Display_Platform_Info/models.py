# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.db import models


class platform(models.Model):
  id = models.BigAutoField(primary_key=True)
  Site = models.CharField(max_length=6)
  Platform = models.CharField(max_length=10)
  Description = models.CharField(max_length=100, null=True, default='')
  Owner = models.CharField(max_length=30, null=True, default='')
  Validity = models.DateField(null=True, default='')
  Last_modified = models.DateTimeField(auto_now=True)
  Created = models.DateTimeField(auto_now_add=True)
  class Meta:
    db_table = 'platform'


class platform_node_list(models.Model):
  id = models.BigAutoField(primary_key=True)
  Platform = models.ForeignKey(platform, on_delete=models.SET_NULL, null=True, default=None)
  Node = models.CharField(max_length=20, unique=True)

  class Meta:
    db_table = 'platform_node_list'


class host_machine(models.Model):
  id = models.BigAutoField(primary_key=True)
  Node = models.CharField(max_length=20, unique=True)
  Host_name = models.CharField(max_length=20, default='')

  class Meta:
    db_table = 'host_machine'


class display_machine(models.Model):
  id = models.BigAutoField(primary_key=True)
  Node = models.CharField(max_length=20, unique=True)
  IP = models.CharField(max_length=100, default='')
  Host_name = models.CharField(max_length=20, default='')

  class Meta:
    db_table = 'display_machine'


class X_server(models.Model):
  id = models.BigAutoField(primary_key=True)
  Host = models.CharField(max_length=20, null=False)
  Display_machine = models.ForeignKey(display_machine, on_delete=models.SET_NULL, null=True, default=None)
  Port = models.IntegerField()
  Tty = models.IntegerField()
  Active = models.BooleanField(default=False)

  class Meta:
    db_table = 'X_server'


class node(models.Model):
  Y_N = (('Y', 'Yes'),
         ('N', 'No'))
  id = models.BigAutoField(primary_key=True)
  Name = models.CharField(max_length=20, unique=True)
  Os = models.CharField(max_length=10, default='')
  OPS_Name = models.CharField(max_length=20, default='')
  Structure = models.CharField(max_length=40, default='')
  Host = models.CharField(max_length=20, default='')
  Host_Machine = models.ForeignKey(host_machine, on_delete=models.SET_NULL, null=True, default=None)
  Ping_reachable = models.CharField(max_length=1, choices=Y_N, default='N')
  Reachable = models.CharField(max_length=1, choices=Y_N, default='N')
  Controlled = models.CharField(max_length=1, choices=Y_N, default='N')
  Orphan = models.CharField(max_length=1, choices=Y_N, default='N')
  Id_in_host = models.IntegerField(default=0)
  Running = models.CharField(max_length=1, choices=Y_N, default='N')
  IP = models.CharField(max_length=100, default='')
  Interface = models.TextField(max_length=1000, default='')
  Thalix = models.CharField(max_length=10, default='')
  Display = models.CharField(max_length=30, default='')
  X_server = models.ForeignKey(X_server, on_delete=models.SET_NULL, null=True, default=None)
  Config = models.CharField(max_length=100, default='')
  CSCI = models.CharField(max_length=100, default='')
  Platform = models.ForeignKey(platform, on_delete=models.SET_NULL, null=True, default=None)
  Last_modified = models.DateTimeField(auto_now=True)
  Created = models.DateTimeField(auto_now_add=True)

  class Meta:
    db_table = 'node'


class run_state(models.Model):
  id = models.BigAutoField(primary_key=True)
  Begin = models.DateTimeField(default=None, null=True)
  End = models.DateTimeField(default=None, null=True)
  State = models.CharField(max_length=10)
  Counter = models.BigIntegerField()
  Current_platform = models.ForeignKey(platform, on_delete=models.SET_NULL, null=True, default=None)

  class Meta:
    db_table = 'run_state'


class site_conf(models.Model):
  id = models.BigAutoField(primary_key=True)
  Site = models.CharField(max_length=6)
  Md5 = models.CharField(max_length=40)

  class Meta:
    db_table = 'site_conf'

  #创建模型在login应用下的models.py文件里，然后迁移文件和创建数据库
  # （python manage.py makemigrations）
  # (python manage.py migrate)

