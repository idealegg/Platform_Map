# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
import models
#from views import datetime2str, str2datetime


admin.site.site_header = 'Platform Admin'
admin.site.site_title = 'Platform Mapping Admin'


# Register your models here.
@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'password', 'email', 'mobile', 'is_staff', 'is_active', 'date_joined', 'last_login',
                    'is_superuser')
    list_per_page = 50
    ordering = ('date_joined',)
    list_editable = list(list_display[1:])
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'groups')  # 过滤器
    search_fields = ('username', 'email')  # 搜索字段
    date_hierarchy = 'last_login'


@admin.register(models.platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('id', 'Site', 'Platform', 'Description', 'Owner', 'Validity')
    ordering = ('Site', 'Platform')
    list_editable = list(list_display[1:])


@admin.register(models.host_machine)
class HostMachineAdmin(admin.ModelAdmin):
    list_display = ('id', 'Node', 'Host_name')
    ordering = ('Node', 'Host_name')
    list_editable = list(list_display[1:])


@admin.register(models.display_machine)
class DisplayMachineAdmin(admin.ModelAdmin):
    list_display = ('id', 'Node', 'Host_name', 'IP', 'Thalix', 'Owner')
    ordering = ('Node', 'Host_name')
    list_editable = list(list_display[1:])


@admin.register(models.X_server)
class XServerAdmin(admin.ModelAdmin):
    list_display = ('id', 'Host', 'Port', 'Tty', 'Active', 'Display_machine_id')
    ordering = ('Host', 'Port')
    fk_fields = ('Display_machine_id',)
    list_editable = list(list_display[1:])


@admin.register(models.node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'Name', 'Os', 'OPS_Name', 'Structure', 'Host', 'Host_Machine_id', 'Ping_reachable',
                    'Reachable', 'Controlled', 'Orphan', 'Id_in_host', 'Running', 'IP', 'Interface', 'Thalix',
                    'Display', 'X_server_id', 'Config', 'CSCI',
                    'Restarting', 'Platform_id')
    ordering = ('Name', 'OPS_Name')
    fk_fields = ('Host_Machine_id', 'X_server_id', 'Platform_id')
    list_editable = list(list_display[1:])


@admin.register(models.run_state)
class RunStateAdmin(admin.ModelAdmin):
    list_display = ('id', 'Begin', 'End', 'State', 'Counter', 'used', 'Current_platform_id')
    ordering = ('Begin', 'End')
    fk_fields = ('Current_platform_id',)
    list_editable = ('Begin', 'End', 'State', 'Counter', 'Current_platform_id')

