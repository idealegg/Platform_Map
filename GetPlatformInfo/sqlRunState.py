# -*- coding: utf-8 -*-

from GetPlatformInfo.sqlOperator import SQLOperator
from Display_Platform_Info.models import run_state
import myLogging
import time


class SQLRunState(SQLOperator):
  run_state_ids = set()
  current_counter = 0

  def __init__(self, begin, pf):
    super(SQLRunState, self).__init__()
    now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    self.platform = pf
    self.attr = {'Current_platform': pf,
                 }
    self.set_filter_function(run_state.objects.filter)
    if not begin:
      self.attr['Begin'] = now
      self.attr['End'] = None
      self.attr['State'] = "Collecting"
    else:
      self.attr['Begin'] = begin
      self.attr['End'] = now
      self.attr['State'] = "Completed"

  def save(self):
    self.attr['Counter'] = SQLRunState.current_counter
    self.db_inst = run_state(**self.attr)
    self.insert_or_update(self.db_inst, filters={'Current_platform': self.attr['Current_platform']})
    SQLRunState.run_state_ids.add(self.get_id())

  @classmethod
  @myLogging.log('SQLRunState')
  def get_complete_pfs(cls):
    complete_pfs = []
    rss = run_state.objects.all()
    counters = map(lambda x: x.Counter, rss)
    if not counters:
      # There is no data in table
      SQLRunState.current_counter = 1
    else:
      max_c = max(counters)
      min_c = min(counters)
      if max_c == min_c:
        rss2 = rss.filter(State='Collecting')
        if rss2.count():
          SQLRunState.current_counter = max_c
          rss3 = rss.filter(State='Completed')
          complete_pfs = map(lambda x: x.Current_platform, rss3)
          SQLRunState.run_state_ids.update(map(lambda x: x.id, rss3))
        else:
          SQLRunState.current_counter = max_c + 1
      else:
        if max_c - min_c > 1:
          myLogging.logger.error("run_state counters minus is bigger than 1!")
          raise RuntimeError()
        else:
          SQLRunState.current_counter = max_c
          rss3 = rss.filter(State='Completed', Counter=max_c)
          complete_pfs = map(lambda x: x.Current_platform, rss3)
          SQLRunState.run_state_ids.update(map(lambda x: x.id, rss3))
    return complete_pfs

