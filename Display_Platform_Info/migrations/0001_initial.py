# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-07-03 16:50
from __future__ import unicode_literals

import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='display_machine',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('Node', models.CharField(max_length=20, unique=True)),
                ('IP', models.CharField(default='', max_length=100)),
                ('Host_name', models.CharField(default='', max_length=20)),
                ('Thalix', models.CharField(default='11.0', max_length=10)),
                ('Last_modified', models.DateTimeField(auto_now=True)),
                ('Created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'display_machine',
            },
        ),
        migrations.CreateModel(
            name='host_machine',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('Node', models.CharField(max_length=20, unique=True)),
                ('Host_name', models.CharField(default='', max_length=20)),
            ],
            options={
                'db_table': 'host_machine',
            },
        ),
        migrations.CreateModel(
            name='node',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('Name', models.CharField(max_length=20, unique=True)),
                ('Os', models.CharField(default='', max_length=10)),
                ('OPS_Name', models.CharField(default='', max_length=20)),
                ('Structure', models.CharField(default='', max_length=40)),
                ('Host', models.CharField(default='', max_length=20)),
                ('Ping_reachable', models.CharField(choices=[('Y', 'Yes'), ('N', 'No')], default='N', max_length=1)),
                ('Reachable', models.CharField(choices=[('Y', 'Yes'), ('N', 'No')], default='N', max_length=1)),
                ('Controlled', models.CharField(choices=[('Y', 'Yes'), ('N', 'No')], default='N', max_length=1)),
                ('Orphan', models.CharField(choices=[('Y', 'Yes'), ('N', 'No')], default='N', max_length=1)),
                ('Id_in_host', models.IntegerField(default=0)),
                ('Running', models.CharField(choices=[('Y', 'Yes'), ('N', 'No')], default='N', max_length=1)),
                ('IP', models.CharField(default='', max_length=100)),
                ('Interface', models.TextField(default='', max_length=1000)),
                ('Thalix', models.CharField(default='', max_length=10)),
                ('Display', models.CharField(default='', max_length=30)),
                ('Config', models.CharField(default='', max_length=100)),
                ('CSCI', models.CharField(default='', max_length=100)),
                ('Restarting', models.BooleanField(default=False)),
                ('Last_modified', models.DateTimeField(auto_now=True)),
                ('Created', models.DateTimeField(auto_now_add=True)),
                ('Host_Machine', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Display_Platform_Info.host_machine')),
            ],
            options={
                'db_table': 'node',
            },
        ),
        migrations.CreateModel(
            name='platform',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('Site', models.CharField(max_length=6)),
                ('Platform', models.CharField(max_length=10)),
                ('Description', models.CharField(default='', max_length=100, null=True)),
                ('Owner', models.CharField(default='', max_length=30, null=True)),
                ('Validity', models.DateField(default='', null=True)),
                ('Last_modified', models.DateTimeField(auto_now=True)),
                ('Created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'platform',
            },
        ),
        migrations.CreateModel(
            name='platform_node_list',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('Node', models.CharField(max_length=20, unique=True)),
                ('Platform', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Display_Platform_Info.platform')),
            ],
            options={
                'db_table': 'platform_node_list',
            },
        ),
        migrations.CreateModel(
            name='run_state',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('Begin', models.DateTimeField(default=None, null=True)),
                ('End', models.DateTimeField(default=None, null=True)),
                ('State', models.CharField(max_length=10)),
                ('Counter', models.BigIntegerField()),
                ('Current_platform', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Display_Platform_Info.platform')),
            ],
            options={
                'db_table': 'run_state',
            },
        ),
        migrations.CreateModel(
            name='site_conf',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('Site', models.CharField(max_length=6)),
                ('Md5', models.CharField(max_length=40)),
            ],
            options={
                'db_table': 'site_conf',
            },
        ),
        migrations.CreateModel(
            name='X_server',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('Host', models.CharField(max_length=20)),
                ('Port', models.IntegerField()),
                ('Tty', models.IntegerField()),
                ('Active', models.BooleanField(default=False)),
                ('Display_machine', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Display_Platform_Info.display_machine')),
            ],
            options={
                'db_table': 'X_server',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.ASCIIUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('mobile', models.CharField(max_length=11)),
                ('Last_modified', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'User',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='node',
            name='Platform',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Display_Platform_Info.platform'),
        ),
        migrations.AddField(
            model_name='node',
            name='X_server',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Display_Platform_Info.X_server'),
        ),
    ]
