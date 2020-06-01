#!/usr/bin/python

import os
import sys

import calendar 
import datetime
import dateutil
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

import lit_mgmt
import act_mgmt

from config_cal import base_path, web_path, months_ini

'''build ini; publish liturgy and activity calendar pages in open and control paths within the date range '''

def build_ini(f1, f2):
    
    target = open(months_ini, 'w')
    for dg in rrule(MONTHLY, dtstart=f1, until=f2):
        if dg.date() <= f2:
            date_start = dg.replace(day=1)
            month_num = date_start.month
            month_name = date_start.strftime("%B")
            year_num = date_start.year   
            prev_month = date_start - relativedelta(months=1)
            next_month = date_start + relativedelta(months=1)
            prev_month_name = prev_month.strftime("%B")
            next_month_name = next_month.strftime("%B")
            prev_year_num = prev_month.year
            next_year_num = next_month.year     
            
            litopen_abs = os.path.join(base_path, 'calendar/liturgy/{0}/{1}.html'.format(year_num, month_name)) 
            litopen_cur ='/shc/calendar/liturgy/{0}/{1}.html'.format(year_num, month_name)
            litopen_prev ='/shc/calendar/liturgy/{0}/{1}.html'.format(prev_year_num, prev_month_name)
            litopen_next ='/shc/calendar/liturgy/{0}/{1}.html'.format(next_year_num, next_month_name)
            litcon_abs = os.path.join(base_path, 'calendar/control/liturgy/{0}/{1}.html'.format(year_num, month_name))
            litcon_cur ='/shc/calendar/control/liturgy/{0}/{1}.html'.format(year_num, month_name)
            litcon_prev ='/shc/calendar/control/liturgy/{0}/{1}.html'.format(prev_year_num, prev_month_name)
            litcon_next ='/shc/calendar/control/liturgy/{0}/{1}.html'.format(next_year_num, next_month_name)
            
            actopen_abs = os.path.join(base_path, 'calendar/activity/{0}/{1}.html'.format(year_num, month_name)) 
            actopen_cur ='/shc/calendar/activity/{0}/{1}.html'.format(year_num, month_name)
            actopen_prev ='/shc/calendar/activity/{0}/{1}.html'.format(prev_year_num, prev_month_name)
            actopen_next ='/shc/calendar/activity/{0}/{1}.html'.format(next_year_num, next_month_name)
            actcon_abs = os.path.join(base_path, 'calendar/control/activity/{0}/{1}.html'.format(year_num, month_name))
            actcon_cur ='/shc/calendar/control/activity/{0}/{1}.html'.format(year_num, month_name)
            actcon_prev ='/shc/calendar/control/activity/{0}/{1}.html'.format(prev_year_num, prev_month_name)
            actcon_next ='/shc/calendar/control/activity/{0}/{1}.html'.format(next_year_num, next_month_name)         
            
            target.write('[{0}]\n'.format(date_start.date()))
            target.write('litopen_abs = {0}\n'.format(litopen_abs))
            target.write('litopen_cur = {0}\n'.format(litopen_cur))
            target.write('litopen_prev = {0}\n'.format(litopen_prev))
            target.write('litopen_next = {0}\n'.format(litopen_next))
            
            target.write('litcon_abs = {0}\n'.format(litcon_abs))
            target.write('litcon_cur = {0}\n'.format(litcon_cur))
            target.write('litcon_prev = {0}\n'.format(litcon_prev))
            target.write('litcon_next = {0}\n'.format(litcon_next))
            
            target.write('actopen_abs = {0}\n'.format(actopen_abs))
            target.write('actopen_cur = {0}\n'.format(actopen_cur))
            target.write('actopen_prev = {0}\n'.format(actopen_prev))
            target.write('actopen_next = {0}\n'.format(actopen_next))
            
            target.write('actcon_abs = {0}\n'.format(actcon_abs))
            target.write('actcon_cur = {0}\n'.format(actcon_cur))
            target.write('actcon_prev = {0}\n'.format(actcon_prev))
            target.write('actcon_next = {0}\n'.format(actcon_next))

    target.close()
    
    
if __name__ == "__main__":
      
    f0 = datetime.date.today()
    fs = f0.replace(day=1)
    f1 = fs - relativedelta(months=1)
    f2 = fs + relativedelta(months=3)    
    build_ini(f1, f2)
    abs_paths = ['actopen_abs', 'actcon_abs', 'litopen_abs', 'litcon_abs']
    
    for dg in rrule(MONTHLY, dtstart=f1, until=f2): 
        year_str = str(dg.year)
        month_name = dg.strftime("%B")
        #set keys to first day of month
        date_start = datetime.datetime(dg.year, dg.month, 1).date()
        year_num = date_start.year
        lit_mgmt.cal_page(year_num, month_name, date_start, abs_paths)
        act_mgmt.cal_page(year_num, month_name, date_start, abs_paths)
                    