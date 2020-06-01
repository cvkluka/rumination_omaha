#!/usr/bin/python
# coding: utf-8

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import sqlite3 as sqlite
import shutil
from string import Template
from ConfigParser import SafeConfigParser
import calendar 
import datetime 
from dateutil.rrule import rrule, DAILY
from dateutil.relativedelta import relativedelta

from config_cal import html_head, weekday_cols, email_from, base_path, web_path, act_db, HD_db, months_ini
                       
location_options = {"01_SHC":"SHC", "02_ICC":"ICC", "03_St_Raphaels":"St. Raphael's", "04_Monroe_H.S.":"Monroe H.S.", "05_Miguel":"Miguel's Restaurant", "06_Other":"Other"}

'''pnt calendar months for public and for activity managers'''

def cal_page(year_num, month_name, date_start, abs_paths):
    
    '''calendar page headers'''
    
    parser = SafeConfigParser()
    parser.read(months_ini) #reads the path  
    ini_header = '{0}'.format(date_start)
    
    for cal_path in abs_paths:    
        for section in parser.sections():
            if section == ini_header:
                      
                if cal_path == 'actcon_abs':
                    actcon_abs = parser.get(ini_header, 'actcon_abs')
                    actcon_prev = parser.get(ini_header, 'actcon_prev')
                    actcon_cur = parser.get(ini_header, 'actcon_cur')
                    actcon_next = parser.get(ini_header, 'actcon_next')
                    litcon_cur = parser.get(ini_header, 'litcon_cur')                              
                    
                    actcon_sub = '''<table class="titre" width="1000" align="center"><tr>
                            <td class="nav" width="20"><a href="%(0)s"><img src="/shc/images/prev.png"/></a></td>\n
                            <td width="300" class="highlt"><b>%(1)s %(2)s</b></td>\n
                            <td class="header" width="200" align="center"><a class="page" href="%(3)s"><b>Liturgy Calendar</b></a></td>\n
                            <td class="highlt" width="200" align="center"><a class="page" href="%(4)s">Activity Calendar</a></td>\n
                            <td class="header" width="200" align="center"><a class="page" href="/">Home</a></td>\n               
                            <td class="nav" width="20"><a href="%(5)s"><img src="/shc/images/next.png"/></a></td></tr></table>\n ''' % {'0':actcon_prev, \
                              '1':month_name, '2':year_num, '3':litcon_cur, '4':actcon_cur, '5':actcon_next}        
                
                    target_actcon = open(actcon_abs, 'w') 
                    target_actcon.write(html_head)
                    target_actcon.write(actcon_sub)
                    target_actcon.write(weekday_cols)
                    target_actcon.close()    
            
                    #add table cells with db content 
                    month_content(year_num, month_name, date_start, cal_path=actcon_abs)
                
                elif cal_path == 'actopen_abs':      
                    actopen_abs = parser.get(ini_header, 'actopen_abs')
                    actopen_prev = parser.get(ini_header, 'actopen_prev')
                    actopen_cur = parser.get(ini_header, 'actopen_cur')
                    actopen_next = parser.get(ini_header, 'actopen_next')
                    litopen_cur = parser.get(ini_header, 'litopen_cur')                      
            
                    actopen_sub = '''<table class="titre" width="1000" align="center"><tr>
                        <td class="nav" width="20"><a href="%(0)s"><img src="/shc/images/prev.png"/></a></td>\n
                        <td width="300" class="highlt"><b>%(1)s %(2)s</b></td>\n
                        <td class="header" width="200" align="center"><a class="page" href="%(3)s"><b>Liturgy Calendar</b></a></td>\n
                        <td class="highlt" width="200" align="center"><a class="page" href="%(4)s">Activity Calendar</a></td>\n
                        <td class="header" width="200" align="center"><a class="page" href="/">Home</a></td>\n               
                        <td class="nav" width="20"><a href="%(5)s"><img src="/shc/images/next.png"/></a></td></tr></table>\n''' % {'0':actopen_prev, \
                          '1':month_name, '2':year_num, '3':litopen_cur, '4':actopen_cur, '5':actopen_next}   
                
                    target_actopen = open(actopen_abs, 'w') 
                    target_actopen.write(html_head)
                    target_actopen.write(actopen_sub)
                    target_actopen.write(weekday_cols)
                    target_actopen.close()
                
                    month_content(year_num, month_name, date_start, cal_path=actopen_abs)
                    
def hd_table():
    
    hd_values = {}
    
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
        con.commit()
        con.close()
    
    except IOError:
        print('Could not open database. Please contact {0}'.format(email_from))
        sys.exit(1)
        
    return hd_values

def read_rows():
    
    '''act_schedule (Event_Start, Event_End, Activity, Event_Location, Show_Loc, Show_Time)
    limit changes to fields that are changeable (omit ID and date, 'poc', 'phone', 'email')'''
    
    track_days = {}
        
    try:
        con = sqlite.connect(act_db)
        cursor = con.cursor() 
        cursor.execute('SELECT ID, Event_Start, Event_End, Activity, Event_Location, Show_Loc, Show_Time FROM act_schedule')
        rows = cursor.fetchall()
        for row in rows:
            if row: 
                key = str(row[0])
                values = []
                for val in row[1:]:
                    values.append(val)
                track_days[key] = values
           
        con.commit()
        con.close()         
                                                                                                                                                    
    except IOError:
        print('Could not read the db! Please contact {0}'.format(email_from))
        sys.exit(1) 
        
    #for EID in track_days:
        #track_days[EID] = [ts, te, activity, location, show_loc, show_time]

    return track_days

def get_vars(track_days):
    
    export_fmt = {}
    
    '''utf = val.decode('utf-8') = string to unicode; use the ID for activity updates in the db; 
       track_days[ID] = [Event_Start, Event_End, Activity, Event_Location, Show_Loc, Show_Time]'''
    
    for EID in track_days:
        #track_days[ID] = [Event_Start, Event_End, Activity, Event_Location, Show_Loc, Show_Time]
        #print 'track_days', track_days[EID], len(track_days[EID])
        export_fmt[EID] = []
        if len(track_days[EID]) == 6:
            start_time = str(track_days[EID][0])
            ts = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M')
            dt = ts.date()
            end_time = str(track_days[EID][1])
            te = get_eventEnd(dt, end_time)
            activity_utf = str(track_days[EID][2]).encode('utf-8')
            location = track_days[EID][3]
            show_location = track_days[EID][4]
            show_time = track_days[EID][5]
            if show_time == 'On':
                start = datetime.datetime.strftime(ts, '%-I:%M %p')
                if te != '':
                    finish = datetime.datetime.strftime(te, '%-I:%M %p')   
                    export_fmt[EID].append('{0} - {1}'.format(start, finish))
                else:
                    export_fmt[EID].append('{0}'.format(start))      
            #show_time is off
            elif show_time == 'Off':
                export_fmt[EID].append('') 
                
            #append activity
            if "'" in activity_utf:
                render_act = activity_utf.replace("'", "\'")  
                export_fmt[EID].append(render_act)
            elif "'" not in activity_utf:
                export_fmt[EID].append(activity_utf)

            if show_location == 'On':  
                export_fmt[EID].append(location)
                
            elif show_location == 'Off':
                export_fmt[EID].append('')
       
    return export_fmt

def count_events(year, month_start, track_days, cur_day):
    
    #use for "Add Activity" links
    d2 = cur_day + relativedelta(months=3)  
    map_link = {}
    for dg in rrule(DAILY, dtstart=month_start, until=d2):
        dg = dg.date()
        map_link[dg] = []
        for EID in track_days:
            dtg_start = str(track_days[EID][0])
            dtgs = datetime.datetime.strptime(dtg_start, '%Y-%m-%d %H:%M')
            if dg == dtgs.date():
                map_link[dg].append(EID)
                 
    return map_link

def get_eventEnd(dt, end_time):
    
    end_options = []
    if end_time in ['Select', '']:
        end_options.append('')
    
    else:  
        #print end_value, type(end_value) #2018-10-27 16:00, unicode
        strip_time = end_time[-5:]
        time_end = datetime.datetime.strptime(strip_time, '%H:%M').time()
        if isinstance(dt, datetime.date):
            dt_end = datetime.datetime.combine(dt, time_end)
            end_options.append(dt_end)
              
    te = end_options[0]
      
    return te


def cell_content(cal_path, cal_day, cur_day, track_days, map_link, export_fmt):
    '''lit_mgmt: 
    def cell_content(cal_path, cal_day, cur_day):'''
    
    content_list = ['']
    hd_values = hd_table()
    
    '''act_schedule (Event_Start, Event_End, Activity, Event_Location, Show_Loc, Show_Time)
    track_days[EID] = [ts, te, activity, location, show_loc, show_time];'''
    
    for hd in hd_values: 
        holy_day = hd[:-5].replace('_', ' ')
        actual_date = datetime.datetime.strptime(hd_values[hd][0], '%Y-%m-%d').date()
        observed_date = datetime.datetime.strptime(hd_values[hd][1], '%Y-%m-%d').date()
        if actual_date == cal_day:
            content_list.append('<b><font color="#9e0909">{0}</font></b><br/>\n'.format(holy_day))             
        
        elif observed_date == cal_day:
            content_list.append('<b><font color="#9e0909">{0} (Observed)</font></b><br/>\n'.format(holy_day))     
        
    for EID, value in sorted(track_days.items(), key=lambda (EID, value): value[0]):
        #assess by timestamp to list events in sequence
        start_str = track_days[EID][0]
        dt = datetime.datetime.strptime(start_str, '%Y-%m-%d %H:%M')
        for ID in export_fmt:
            if ID == EID:  
                if len(export_fmt[ID]) == 3:
                    if dt.date() == cal_day:
                        times = export_fmt[ID][0]
                        activity = export_fmt[ID][1]
                        location = export_fmt[ID][2]
                        #time is in black, event and location in red
                        if dt.date() >= cur_day:
                            content_list.append('<br/>{0}\n'.format(times))
                            
                            if 'control' in cal_path:
                                content_list.append('<br/><a class="page" href="/shc/akc/edit_act.cgi?ID={0}&start_date={1}">{2} {3}</a>\n'.format(ID, cal_day, activity, location))
                            else:
                                content_list.append('<br/><font color="#9e0909">{0} {1}</font>\n'.format(activity, location))
    
                        else:
                            #control events are in the past, use italic font
                            content_list.append('<i>{0}<br/>{1} {2}<br/></i>\n'.format(times, activity, location)) 
    
    if 'control' in cal_path: 
        for dtg in sorted(map_link):
            if dtg >= cur_day:
                if dtg == cal_day:
                    if len(map_link[dtg]) < 3:
                        content_list.append('<br/><a class="page" href="/shc/akc/edit_act.cgi?start_date={0}">Add Activity</a>\n'.format(cal_day))
            
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
    
    cur_day = datetime.date.today() 
    track_days = read_rows()
    map_link = count_events(year_num, date_start, track_days, cur_day)
    export_fmt = get_vars(track_days)
    calendar.setfirstweekday(6) 
    calobject = calendar.monthcalendar(year_num, date_start.month)
    nweeks = len(calobject) 
    target = open(cal_path, 'a')
                
    for w in range(0,nweeks): 
        cnt = 0
        week = calobject[w]
        #control table rows
        target.write('</tr><tr>')
        
        for x in xrange(0,7): 
            day = week[x] 
            if day == 0:
                target.write('<td align="center"><table width="140"><tr><td class="num"></td></tr>\n')
                target.write('<tr><td class="weekday">&nbsp;</td></tr></table></td>\n') 
            else:
                cal_day = datetime.date(year_num, date_start.month, day)
                content_list = cell_content(cal_path, cal_day, cur_day, track_days, map_link, export_fmt)
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
    
    if 'control' in cal_path:
        current_month = os.path.join(base_path, 'calendar/control/activity/{0}/{1}.html'.format(year_num, month_name))           
        if year_num == cur_day.year and date_start.month == cur_day.month:
            current_default = os.path.join(base_path, 'calendar/control/activity/current_month.html')
            run_copy(current_month, current_default)
    else:
        current_month = os.path.join(base_path, 'calendar/activity/{0}/{1}.html'.format(year_num, month_name))    
        if year_num == cur_day.year and date_start.month == cur_day.month:
            current_default = os.path.join(base_path, 'calendar/activity/current_month.html')
            run_copy(current_month, current_default)          

 