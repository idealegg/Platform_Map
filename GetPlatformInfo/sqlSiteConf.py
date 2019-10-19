# -*- coding: utf-8 -*-

from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import site_conf
import myLogging
import hashlib
import os


class SQLSiteConf(SQLOperator):
  site_conf_ids = set()

  def __init__(self, site, md5):
    super(SQLSiteConf, self).__init__()
    self.attr = {'Site': site,
                 'Md5': md5
                 }
    self.set_filter_function(site_conf.objects.filter)

  def save(self):
    self.db_inst = site_conf(**self.attr)
    self.insert_or_update(self.db_inst, filters={'Site': self.attr['Site']})
    SQLSiteConf.site_conf_ids.add(self.get_id())

  @classmethod
  @myLogging.log('SQLSiteConf')
  def get_conf_md5(cls, conf_path):
    h = ''
    with open(conf_path) as fd:
      h = hashlib.md5(fd.read()).hexdigest()
    return h

  @classmethod
  @myLogging.log('SQLSiteConf')
  def get_all_conf_change(cls, conf_list):
    SQLSiteConf.site_conf_ids = set()
    scs = site_conf.objects.all()
    new_added = []
    modified = []
    for conf in conf_list:
      site = os.path.basename(conf).replace(".conf", '')
      try:
        sc = scs.get(Site=site)
      except Exception:
        myLogging.logger.debug('Ignore this exception!')
        new_added.append(site)
        sc = site_conf(Site=site, Md5=SQLSiteConf.get_conf_md5(conf))
        sc.save()
        SQLSiteConf.site_conf_ids.add(sc.id)
        continue
      new_md5 = SQLSiteConf.get_conf_md5(conf)
      if sc.Md5 != new_md5:
        modified.append(site)
        sc.Md5 = new_md5
        sc.save()
      SQLSiteConf.site_conf_ids.add(sc.id)
    new_added.extend(modified)
    myLogging.logger.info("site_conf ids all: [%s]" % map(lambda x: x.id, scs))
    myLogging.logger.info("site_conf ids rev: [%s]" % SQLSiteConf.site_conf_ids)
    site_conf.objects.exclude(id__in=SQLSiteConf.site_conf_ids).delete()
    return new_added



