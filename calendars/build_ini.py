#!/usr/bin/python

import os
import sys
import shutil

import calendar 
import datetime
import dateutil
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

from config_cal import base_path, base_web, litopen_base, litopen_web, litopen_head, litcon_base, litcon_web, litcon_head, \
     actopen_base, actopen_web, actopen_head, actcon_base, actcon_web, actcon_head, months_ini

'''generate the ini file to update calendar months'''

def build_paths(dtg, date_list, calendar_type):
    
    litcon_list = []
    litopen_list = []
    actcon_list = []
    actopen_list = []
    
    #set up relative links; note: prev_year, next_year are years belonging to prev, next_month...
    litcon_str = '/shc/calendar/control/liturgy'
    litopen_str = '/shc/calendar/liturgy'
    actcon_str = '/shc/calendar/control/activity'
    actopen_str = '/shc/calendar/activity'
    #date_list imported as arg, [prev_month_name, prev_month, month_name, this_month, next_month_name, next_month]
    this_year = str(date_list[3].year)
    this_month = str(date_list[2])
        
    if litcon_str in calendar_type:
        
        abs_path = os.path.join(base_path, 'calendar/control/liturgy/{0}/{1}.html').format(this_year, this_month)
        act_path = '/shc/calendar/control/activity/{0}/{1}.html'.format(this_year, this_month)             
        
        litcon_prev_year = os.path.join(litcon_str, str(date_list[1].year))
        litcon_this_year = os.path.join(litcon_str, str(date_list[3].year))
        litcon_next_year = os.path.join(litcon_str, str(date_list[5].year))   
        litcon_prev_month = os.path.join(litcon_prev_year, '{0}.html'.format(date_list[0]))
        litcon_this_month = os.path.join(litcon_this_year, '{0}.html'.format(date_list[2]))
        litcon_next_month = os.path.join(litcon_next_year, '{0}.html'.format(date_list[4]))                               
        litcon_list = [abs_path, litcon_prev_month, litcon_this_month, litcon_next_month, act_path]    
        
    elif litopen_str in calendar_type:
    
        abs_path = os.path.join(base_path, 'calendar/liturgy/{0}/{1}.html').format(this_year, this_month)
        act_path = '/shc/calendar/activity/{0}/{1}.html'.format(this_year, this_month)     
        
        litopen_prev_year = os.path.join(litopen_str, str(date_list[1].year))
        litopen_this_year = os.path.join(litopen_str, str(date_list[3].year))
        litopen_next_year = os.path.join(litopen_str, str(date_list[5].year))
        litopen_prev_month = os.path.join(litopen_prev_year, '{0}.html'.format(date_list[0]))
        litopen_this_month = os.path.join(litopen_this_year, '{0}.html'.format(date_list[2]))
        litopen_next_month = os.path.join(litopen_next_year, '{0}.html'.format(date_list[4]))
        litopen_list = [abs_path, litopen_prev_month, litopen_this_month, litopen_next_month, act_path]
        
    elif actcon_str in calendar_type:
        
        abs_path = os.path.join(base_path, 'calendar/control/activity/{0}/{1}.html').format(this_year, this_month)
        lit_path = '/shc/calendar/control/liturgy/{0}/{1}.html'.format(this_year, this_month)     
        
        actcon_prev_year = os.path.join(actcon_str, str(date_list[1].year))
        actcon_this_year = os.path.join(actcon_str, str(date_list[3].year))
        actcon_next_year = os.path.join(actcon_str, str(date_list[5].year))
        actcon_prev_month = os.path.join(actcon_prev_year, '{0}.html'.format(date_list[0]))
        actcon_this_month = os.path.join(actcon_this_year, '{0}.html'.format(date_list[2]))
        actcon_next_month = os.path.join(actcon_next_year, '{0}.html'.format(date_list[4]))
                                         
        actcon_list = [abs_path, actcon_prev_month, actcon_this_month, actcon_next_month, lit_path]  
        
    elif actopen_str in calendar_type:
    
        abs_path = os.path.join(base_path, 'calendar/activity/{0}/{1}.html').format(this_year, this_month)
        lit_path = '/shc/calendar/liturgy/{0}/{1}.html'.format(this_year, this_month)   
        
        actopen_prev_year = os.path.join(actopen_str, str(date_list[1].year))
        actopen_this_year = os.path.join(actopen_str, str(date_list[3].year))
        actopen_next_year = os.path.join(actopen_str, str(date_list[5].year))
        actopen_prev_month = os.path.join(actopen_prev_year, '{0}.html'.format(date_list[0]))
        actopen_this_month = os.path.join(actopen_this_year, '{0}.html'.format(date_list[2]))
        actopen_next_month = os.path.join(actopen_next_year, '{0}.html'.format(date_list[4]))                               
        actopen_list = [abs_path, actopen_prev_month, actopen_this_month, actopen_next_month, lit_path]    
        
    return litcon_list, litopen_list, actcon_list, actopen_list
    

if __name__ == "__main__":
    
    cur_day = datetime.date.today() 
    f1 = cur_day - relativedelta(months=3)
    f2 = cur_day + relativedelta(months=7)  
    #writes to base_path + /shc/akc/month_heads.ini
    target = open(months_ini, 'w')
    
    for dtg in rrule(MONTHLY, dtstart=f1, until=f2): 
        str_year = str(dtg.year)
        month_name = dtg.strftime("%B")
        prev_month = dtg - relativedelta(months=1)
        next_month = dtg + relativedelta(months=1)
        prev_month_name = prev_month.strftime("%B")
        next_month_name = next_month.strftime("%B")        
        #set keys to first day of month
        this_month = datetime.datetime(dtg.year, dtg.month, 1).date()
        date_str = datetime.datetime.strftime(this_month, '%Y-%m-%d')
        date_list = [prev_month_name, prev_month, month_name, this_month, next_month_name, next_month]
        for calendar_type in [litcon_web, litopen_web, actcon_web, actopen_web]:
            
            if calendar_type == litcon_web:
                litcon_tuple = build_paths(dtg, date_list, calendar_type)
                target.write('[litcon_{0}]\n'.format(date_str))
                for litcon_list in litcon_tuple:
                    if len(litcon_list) > 0:
                        for index, path in enumerate(litcon_list):
                            if index == 0:
                                target.write("litcon_abs = {0}\n".format(path))
                            elif index == 1:
                                target.write("litcon_prev = {0}\n".format(path))
                            elif index == 2:
                                target.write("litcon_cur = {0}\n".format(path))
                            elif index == 3:
                                target.write("litcon_next = {0}\n".format(path))
                            elif index == 4:
                                target.write("actcon_cur = {0}\n".format(path))
                        target.write('\n')     
                        
            elif calendar_type == litopen_web:
                litopen_tuple = build_paths(dtg, date_list, calendar_type)
                target.write('[litopen_{0}]\n'.format(date_str))
                for litopen_list in litopen_tuple:
                    if len(litopen_list) > 0:
                        for index, path in enumerate(litopen_list):
                            if index == 0:
                                target.write("litopen_abs = {0}\n".format(path))
                            elif index == 1:
                                target.write("litopen_prev = {0}\n".format(path))
                            elif index == 2:
                                target.write("litopen_cur = {0}\n".format(path))
                            elif index == 3:
                                target.write("litopen_next = {0}\n".format(path))
                            elif index == 4:
                                target.write("actopen_cur = {0}\n".format(path))
                        target.write('\n')  
                        
            elif calendar_type == actcon_web:
                actcon_tuple = build_paths(dtg, date_list, calendar_type)
                target.write('[actcon_{0}]\n'.format(date_str))
                for actcon_list in actcon_tuple:
                    if len(actcon_list) > 0:
                        for index, path in enumerate(actcon_list):
                            if index == 0:
                                target.write("actcon_abs = {0}\n".format(path))
                            elif index == 1:
                                target.write("actcon_prev = {0}\n".format(path))
                            elif index == 2:
                                target.write("actcon_cur = {0}\n".format(path))
                            elif index == 3:
                                target.write("actcon_next = {0}\n".format(path))
                            elif index == 4:
                                target.write("litcon_cur = {0}\n".format(path))
                        target.write('\n') 
                        
            elif calendar_type == actopen_web:
                actopen_tuple = build_paths(dtg, date_list, calendar_type)
                target.write('[actopen_{0}]\n'.format(date_str))
                for actopen_list in actopen_tuple:
                    if len(actopen_list) > 0:
                        for index, path in enumerate(actopen_list):
                            if index == 0:
                                target.write("actopen_abs = {0}\n".format(path))
                            elif index == 1:
                                target.write("actopen_prev = {0}\n".format(path))
                            elif index == 2:
                                target.write("actopen_cur = {0}\n".format(path))
                            elif index == 3:
                                target.write("actopen_next = {0}\n".format(path))
                            elif index == 4:
                                target.write("litopen_cur = {0}\n".format(path))
                        target.write('\n')       
    target.close()
        
    
