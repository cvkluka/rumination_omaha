#!/usr/bin/python
# -*- coding: latin-1 -*-

import sqlite3 as sqlite
import os, sys
import shutil
from string import Template

import calendar 
import datetime 
from dateutil.rrule import rrule, MONTHLY

from ConfigParser import SafeConfigParser
from config_cal import html_head, weekday_cols, email_from, base_path, web_path, lit_db, HD_db, months_ini


def cal_page(year_num, month_name, date_start, abs_paths):
    
    '''calendar page headers'''
    
    parser = SafeConfigParser()
    parser.read(months_ini) #reads the path  
    ini_header = '{0}'.format(date_start)
    
    for cal_path in abs_paths:    
        #section = date
        
        for section in parser.sections():
            if section == ini_header:
                
                if cal_path == 'litcon_abs':
                    litcon_abs = parser.get(ini_header, 'litcon_abs')
                    litcon_prev = parser.get(ini_header, 'litcon_prev')
                    litcon_cur = parser.get(ini_header, 'litcon_cur')
                    litcon_next = parser.get(ini_header, 'litcon_next')
                    actcon_cur = parser.get(ini_header, 'actcon_cur')      
                            
                    litcon_sub = '''<table class="titre" width="1000" align="center"><tr>
                            <td class="nav" width="20"><a href="%(0)s"><img src="/shc/images/prev.png"/></a></td>\n
                            <td width="300" class="highlt"><b>%(1)s %(2)s</b></td>\n
                            <td class="highlt" width="200" align="center"><a class="page" href="%(3)s"><b>Liturgy Calendar</b></a></td>\n
                            <td class="header" width="200" align="center"><a class="page" href="%(4)s">Activity Calendar</a></td>\n
                            <td class="header" width="200" align="center"><a class="page" href="/">Home</a></td>\n               
                            <td class="nav" width="20"><a href="%(5)s"><img src="/shc/images/next.png"/></a></td></tr></table>\n ''' % {'0':litcon_prev, \
                              '1':month_name, '2':year_num, '3':litcon_cur, '4':actcon_cur, '5':litcon_next}        
                    
                    target_litcon = open(litcon_abs, 'w') 
                    target_litcon.write(html_head)
                    target_litcon.write(litcon_sub)
                    target_litcon.write(weekday_cols)
                    target_litcon.close()    
            
                    #add table cells with db content  
                    month_content(year_num, month_name, date_start, cal_path=litcon_abs)
                
                elif cal_path == 'litopen_abs':
                    litopen_abs = parser.get(ini_header, 'litopen_abs')
                    litopen_prev = parser.get(ini_header, 'litopen_prev')
                    litopen_cur = parser.get(ini_header, 'litopen_cur')
                    litopen_next = parser.get(ini_header, 'litopen_next')
                    actopen_cur = parser.get(ini_header, 'actopen_cur')  
            
                    litopen_sub = '''<table class="titre" width="1000" align="center"><tr>
                        <td class="nav" width="20"><a href="%(0)s"><img src="/shc/images/prev.png"/></a></td>\n
                        <td width="300" class="highlt"><b>%(1)s %(2)s</b></td>\n
                        <td class="highlt" width="200" align="center"><a class="page" href="%(3)s"><b>Liturgy Calendar</b></a></td>\n
                        <td class="header" width="200" align="center"><a class="page" href="%(4)s">Activity Calendar</a></td>\n
                        <td class="header" width="200" align="center"><a class="page" href="/">Home</a></td>\n               
                        <td class="nav" width="20"><a href="%(5)s"><img src="/shc/images/next.png"/></a></td></tr></table>\n''' % {'0':litopen_prev, \
                          '1':month_name, '2':year_num, '3':litopen_cur, '4':actopen_cur, '5':litopen_next}   
                    
                    target_litopen = open(litopen_abs, 'w') 
                    target_litopen.write(html_head)
                    target_litopen.write(litopen_sub)
                    target_litopen.write(weekday_cols)
                    target_litopen.close()
                      
                    month_content(year_num, month_name, date_start, cal_path=litopen_abs)
   
    
def read_litdb():
    
    event_tuple = []
    try:
        con = sqlite.connect(lit_db)
        cursor = con.cursor() 
        cursor.execute('SELECT Event_Start, Liturgy_Event, Event_End, Event_Location from lit_schedule')
        rows = cursor.fetchall()
        for row in rows:
            event_tuple.append(row[0:])
                                                                                                                                 
    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1) 

    con.commit()
    con.close()   
                
    return event_tuple

def get_eventEnd(dt, end_value):
    
    end_options = []
    if end_value == 'Select':
        end_options.append('')
    
    elif end_value == '':
        end_options.append('')
    
    else:  
        strip_time = end_value[-5:]
        time_end = datetime.datetime.strptime(strip_time, '%H:%M').time()
        if isinstance(dt, datetime.date):
            dt_end = datetime.datetime.combine(dt, time_end)
            time_endfmt = datetime.datetime.strftime(dt_end, '%-I:%M %p') 
            end_options.append(time_endfmt)
              
    time_endfmt = end_options[0]    
      
    return time_endfmt


def hd_table(cal_str):
    
    hd_values = {}
    hd_data = ['not', '', '']
    
    try:
        con = sqlite.connect(HD_db)
        cursor = con.cursor()
        cursor.execute("SELECT Holy_Day, Actual, Observed FROM hd_schedule")  
        rows = cursor.fetchall()
        for row in rows:
            Holy_Day = str(row[0])
            Actual_date = str(row[1])
            Observed_date = str(row[2])
            hd_values[Holy_Day] = [Actual_date, Observed_date]
            if cal_str in hd_values[Holy_Day]:
                hd_data = [Holy_Day, Actual_date, Observed_date]
        con.commit()
        con.close()
    
    except IOError:
        print('Could not open database. Please contact {0}'.format(email_from))
        sys.exit(1)
             
    #print hd_data
     
    return hd_data


def cell_content(cal_path, date_start, cal_day, cur_day, hd_data):
    
    content_list = []
    #matching holy day to calendar day
    hd = hd_data[0]
    event_tuple = read_litdb() 
    
    for event_group in sorted(event_tuple):
        #(u'2018-10-07 13:00', u'Mass_(Hispanic)', u'', u'SHC') 
        event_start = event_group[0]
        dtg = datetime.datetime.strptime(event_start, "%Y-%m-%d %H:%M") 
        dtg_arg = event_start.replace(' ', '_')
        dt = dtg.date()
        time_starts = event_start[-5:]
        time_startfmt = datetime.datetime.strftime(dtg, "%-I:%M %p") 
            
        if dt == cal_day:
            value_list = event_group[1:]
            if value_list and len(value_list) == 3:
                event = value_list[0]
                end_value = value_list[1] 
                location = value_list[2] 
                time_endfmt = get_eventEnd(dt, end_value)
                event_name = event.replace('_', ' ')
                
                if cal_day >= cur_day:
                
                    #was linking masses that need servers (never at 7:30 or 17:30) but there are html5 validation errors
                    if 'Mass' in event:
                        if time_starts in ['08:00', '11:00', '12:10', '13:00', '16:30', '19:00']:
                            mass_link = '<a class="page" href="/shc/akc/lem.cgi?DTG={0}&HD={1}"> {2} - {3} </a><br/>\n'.format(dtg_arg, hd, time_startfmt, event_name)
                            #mass_nolink = '<font color="#9e0909">{0} - {1}</font><br/>\n'.format(time_startfmt, event_name) 
                            content_list.append(mass_link)
                        
                        elif time_starts in ['07:30', '17:30']: 
                            content_list.append('{0} - {1}<br/>\n'.format(time_startfmt, event_name)) 
                            
                        else: 
                            content_list.append('{0} - {1}<br/>\n'.format(time_startfmt, event_name))                         
                        
                    else:
                        content_list.append('{0} - {1} {2}<br/>\n'.format(time_startfmt, time_endfmt, event_name))                     
                            
                                      
                else:
                    #event is in the past; italicize
                    content_list.append('<i>{0} - {1}</i><br/>'.format(time_startfmt, event_name))   
                    
                    
    if 'control' in cal_path:
        if cal_day >= date_start:
        #if cal_day >= cur_day: #if cal_day >= datetime.datetime(2019, 12, 1).date(): #for retroactive posts   
            content_list.append('<a class="page" href="/shc/akc/edit_lit.cgi?start_date={0}">Edit</a><br/>\n'.format(cal_day)) 
          
     
    return content_list


def run_copy(current_month, current_default):

    target = open(current_default, 'w')       
    try:
        shutil.copyfileobj(open(current_month, 'rb'), target)

    except IOError:
        print('Could not read the management form! Please contact {0}'.format(email_from))
        sys.exit(1)   

    target.close()    

    
def month_content(year_num, month_name, date_start, cal_path):
    
    #read all holy day information from sql table
    cur_day = datetime.date.today()
    calendar.setfirstweekday(6) 
    calobject = calendar.monthcalendar(year_num, date_start.month)
    nweeks = len(calobject) 
    target = open(cal_path, 'a')
    
    for w in range(0,nweeks): 
        week = calobject[w]
        target.write('</tr><tr>')
        
        for x in xrange(0,7): 
            day = week[x] 
            if day == 0:
                target.write('<td align="center"><table width="140"><tr><td class="num"></td></tr>\n')
                target.write('<tr><td class="weekday">&nbsp;</td></tr></table></td>\n') 
                
            else:
                cal_day = datetime.date(year_num, date_start.month, day)
                cal_str = datetime.datetime.strftime(cal_day, '%Y-%m-%d')
                #match holy day in sql table to calendar day
                hd_data = hd_table(cal_str)
                content_list = cell_content(cal_path, date_start, cal_day, cur_day, hd_data) 
                holy_day = hd_data[0][:-5].replace('_', ' ')
                #hd_data[1]=actual, hd_data[2]=observed
                if hd_data[1] == cal_str:
                    content_list.insert(0, '<b><font color="#9e0909">{0}</font></b><br/>\n'.format(holy_day))  
                elif hd_data[2] == cal_str:
                    content_list.insert(0, '<b><font color="#9e0909">{0} (Observed)</font></b><br/>\n'.format(holy_day))
                
                content = ''.join(content_list)       
                if cal_day == cur_day: 
                    #set font color of date to red;     
                    target.write('<td align="center"><table width="140"><tr><td class="number">{0}</td></tr>\n'.format(day)) 
                    target.write('<tr><td class="weekday">{0}</td></tr></table></td>\n'.format(content))    
                else:
                    target.write('<td align="center"><table width="140"><tr><td class="num">{0}</td></tr>\n'.format(day))                         
                    target.write('<tr><td class="weekday">{0}</td></tr></table></td>\n'.format(content))  
   
    #end the month table - 
    target.write('</table><br/></body></html>')  
    target.close()
    
    #if the month == current month, copy to ../current_month.html
    if 'control' in cal_path:          
        current_month = os.path.join(base_path, 'calendar/control/liturgy/{0}/{1}.html'.format(year_num, month_name))            
        if year_num == cur_day.year and date_start.month == cur_day.month:
            current_default = os.path.join(base_path, 'calendar/control/liturgy/current_month.html')
            run_copy(current_month, current_default) 
            
    else:
        current_month = os.path.join(base_path, 'calendar/liturgy/{0}/{1}.html'.format(year_num, month_name))          
        if date_start.year == cur_day.year and date_start.month == cur_day.month:
            current_default = os.path.join(base_path, 'calendar/liturgy/current_month.html')
            run_copy(current_month, current_default)    
   