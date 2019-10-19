# -*- coding: utf-8 -*-
import myLogging


class SQLOperator(object):
  ORPHAN = 'ORPHAN'

  def __init__(self):
    super(SQLOperator, self).__init__()
    self.__filter__ = None
    self.db_inst = None

  def set_filter_function(self, func):
    self.__filter__ = func

  @myLogging.log('SQLOperator')
  def insert_or_update(self, sql_object, filters):
    ns = self.__filter__(**filters)
    myLogging.logger.debug( "sql_object: [%s], filters: [%s], ns: [%d]" % (sql_object, filters, ns.count()))
    if ns.count() > 1:
      myLogging.logger.warning( "Too much records %s found in X_server table! Try to delete them!" % (filters))
      ns.delete()
    elif ns.count() == 1:
      sql_object.id = ns[0].id
      try:
        sql_object.Created = ns[0].Created
      except AttributeError:
        pass
      except Exception:
        myLogging.logger.exception("Here could not reach! If error, the next step would fail!")
      myLogging.logger.debug("id: %d" % sql_object.id)
    try:
      sql_object.save()
    except Exception, e:
      myLogging.logger.exception( "Save failed! %s error: %s" % (filters, e.message))

  def get_db_inst(self):
    return self.db_inst

  def get_id(self):
    return self.db_inst.id