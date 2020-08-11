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
    list_per_page = 5
    ordering = ('date_joined',)
    list_editable = list(list_display[1:])
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'groups')  # 过滤器
    search_fields = ('username', 'email')  # 搜索字段
    date_hierarchy = 'last_login'


@admin.register(models.platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('id', 'Site', 'Platform', 'Description', 'Owner', 'Validity', 'used')
    list_per_page = 10
    ordering = ('Site', 'Platform')
    list_editable = list(list_display[1:-1])
    list_filter = ('Site', 'Owner')
    search_fields = ('=Site', '^Platform', 'Description', '=Owner', '^Validity')
    date_hierarchy = 'Validity'


@admin.register(models.host_machine)
class HostMachineAdmin(admin.ModelAdmin):
    list_display = ('id', 'Node', 'Host_name')
    list_per_page = 15
    ordering = ('Node', 'Host_name')
    search_fields = ('Node', 'Host_name')
    list_editable = list(list_display[1:])


@admin.register(models.display_machine)
class DisplayMachineAdmin(admin.ModelAdmin):
    list_display = ('id', 'Node', 'Host_name', 'IP', 'Thalix', 'Owner')
    list_per_page = 15
    ordering = ('Node', 'Host_name')
    list_editable = list(list_display[1:])
    search_fields = ('Node', 'Host_name', 'IP', '^Thalix', 'Owner')
    list_filter = ('Thalix', 'Owner')


@admin.register(models.X_server)
class XServerAdmin(admin.ModelAdmin):
    list_display = ('id', 'Host', 'Port', 'Tty', 'Active')
    list_per_page = 15
    ordering = ('Host', 'Port')
    fk_fields = ('Display_machine_id',)
    list_editable = list(list_display[1:])
    search_fields = ('Host', )
    list_filter = ('Active',)


@admin.register(models.node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'Name', 'Os', 'OPS_Name', 'Structure', 'Host', 'Host_Machine_id', 'Ping_reachable',
                    'Reachable', 'Controlled', 'Orphan', 'Id_in_host', 'Running', 'IP',
                    #'Interface',
                    'Thalix',
                    'Display', 'X_server_id', 'Config', 'CSCI',
                    'Restarting')
    list_per_page = 15
    ordering = ('Name', 'OPS_Name')
    fk_field = ('Host_Machine_id', 'X_server_id', 'Platform_id')
    list_editable = ['Name', 'Os', 'OPS_Name', 'Structure', 'Host', 'Ping_reachable',
                    'Reachable', 'Controlled', 'Orphan', 'Id_in_host', 'Running', 'IP',
                     #'Interface',
                    'Thalix',
                    'Display', 'Config', 'CSCI',
                    'Restarting']
    search_fields = ('Name', 'OPS_Name', 'IP', '^Thalix', '^Display', 'Config', 'CSCI')
    list_filter = ('Host', 'Ping_reachable', 'Reachable', 'Controlled', 'Orphan', 'Running', 'Thalix', 'Restarting')


@admin.register(models.run_state)
class RunStateAdmin(admin.ModelAdmin):
    list_display = ('id', 'Begin', 'End', 'State', 'Counter', 'used', 'Current_platform_id')
    list_per_page = 7
    ordering = ('Begin', 'End')
    fk_fields = ('Current_platform_id',)
    list_editable = ('Begin', 'End', 'State', 'Counter')

