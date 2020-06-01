#!/usr/bin/python
# -*- coding: latin-1 -*-

import sqlite3 as sqlite
import os, sys
import shutil

import calendar 
import datetime 
from dateutil.rrule import rrule, MONTHLY

from ConfigParser import SafeConfigParser
from config_cal import email_from, base_path, web_path, lit_db, HD_db, months_ini
import headers
from headers import page_header, weekday_cols

'''date_start is passed from cal_months.py or from edit_lit.cgi; calendar page headers are read from months.ini'''

def run_copy(current_month, current_default):

    target = open(current_default, 'w')       
    try:
        shutil.copy(current_month, current_default)

    except IOError:
        print('Could not read the management form! Please contact {0}'.format(email_from))
        sys.exit(1)   

    target.close() 
    

def hd_table():

    hd_data = {}

    try:
        con = sqlite.connect(HD_db)
        cursor = con.cursor()
        cursor.execute("SELECT Holy_Day, Actual, Observed FROM hd_schedule")  
        rows = cursor.fetchall()
        for row in rows:
            Holy_Day = str(row[0])
            Actual_date = str(row[1])
            Observed_date = str(row[2])
            hd_data[Holy_Day] = [Actual_date, Observed_date]
        con.commit()
        con.close()

    except IOError:
        print('Could not open database. Please contact {0}'.format(email_from))
        sys.exit(1)

    return hd_data

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
    if end_value in ['Select', '']:
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

def cal_edit(event_tuple, cal_day):
    
    events_day = []
    
    for event_group in sorted(event_tuple):
        event_start = event_group[0]
        dtg = datetime.datetime.strptime(event_start, "%Y-%m-%d %H:%M")       
        if dtg.date() == cal_day: 
            events_day.append(cal_day)
            
    return events_day


def cell_content(cal_path, date_start, cal_day, cur_day):

    content_list = []
    hd_data = hd_table()
    event_tuple = read_litdb() 

    for hd in hd_data: 
        holy_day = hd[:-5].replace('_', ' ')
        actual_date = datetime.datetime.strptime(hd_data[hd][0], '%Y-%m-%d').date()
        observed_date = datetime.datetime.strptime(hd_data[hd][1], '%Y-%m-%d').date()
        if actual_date == cal_day:
            content_list.append('<b><font color="#9e0909">{0}</font></b><br/><br/>\n'.format(holy_day))             

        elif observed_date == cal_day:
            content_list.append('<b><font color="#9e0909">{0} (Observed)</font></b><br/><br/>\n'.format(holy_day))          

    for event_group in sorted(event_tuple):
        #(u'2018-10-07 13:00', u'Mass_(Hispanic)', u'', u'SHC') 
        event_start = event_group[0]
        dtg = datetime.datetime.strptime(event_start, "%Y-%m-%d %H:%M") 
        if dtg.date() == cal_day:    
            dtg_arg = event_start.replace(' ', '_')
            time_starts = event_start[-5:]
            time_startfmt = datetime.datetime.strftime(dtg, "%-I:%M %p") 
            value_list = event_group[1:]
            if value_list and len(value_list) == 3:
                dt = dtg.date()
                event = value_list[0]
                end_value = value_list[1] 
                location = value_list[2] 
                time_endfmt = get_eventEnd(dt, end_value)
                event_name = event.replace('_', ' ')

                if cal_day >= cur_day:
                    if time_endfmt:
                        content_list.append('{0} - {1} <br/>{2}<br/>\n'.format(time_startfmt, time_endfmt, event_name)) 
                    else:
                        content_list.append('{0} - {1} <br/>\n'.format(time_startfmt, event_name))                                                   
                else:
                    #event is in the past; italicize
                    content_list.append('<i>{0} - {1}</i><br/>'.format(time_startfmt, event_name))                     

    if len(hd_data) == 0 and len(content_list) == 0:
        #there's nothing in the event db for that day; print empty cell
        content_list.append('')     

    if 'control' in cal_path:   
        events_day = cal_edit(event_tuple, cal_day)
        #if cal_day >= cur_day: #if cal_day >= datetime.datetime(2019, 12, 1).date(): #for retroactive posts
        if cal_day >= date_start:
            if len(events_day) > 0:
                content_list.append('<a class="page" href="/shc/akc/edit_lit.cgi?start_date={0}">Edit</a> or \n'.format(cal_day)) 
                content_list.append('<a class="page" href="/shc/akc/del_lit.cgi?start_date={0}">Delete</a><br/>\n'.format(cal_day)) 
            else:
                if len(content_list) == 0:
                    #print '<br/>content_list = 0 for {0}'.format(cal_day) #but this is always true, hmmm...
                    content_list.append('<br/><a class="page" href="/shc/akc/edit_lit.cgi?start_date={0}">Add</a><br/>\n'.format(cal_day)) 
                elif hd_data and len(content_list) == 1:
                    content_list.append('<br/><a class="page" href="/shc/akc/edit_lit.cgi?start_date={0}">Add</a><br/>\n'.format(cal_day)) 
                else:
                    content_list.append('<a class="page" href="/shc/akc/edit_lit.cgi?start_date={0}">Edit</a> or \n'.format(cal_day)) 
                    content_list.append('<a class="page" href="/shc/akc/del_lit.cgi?start_date={0}">Delete</a><br/>\n'.format(cal_day)) 
            
    return content_list


def month_content(date_start, month_name, cal_path):

    #read all holy day information from sql table
    cur_day = datetime.date.today()
    calendar.setfirstweekday(6) 
    calobject = calendar.monthcalendar(date_start.year, date_start.month)
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
                cal_day = datetime.date(date_start.year, date_start.month, day)
                content_list = cell_content(cal_path, date_start, cal_day, cur_day) 
                content_str = ''.join(content_list)       
                if cal_day == cur_day: 
                    #set day number in red;
                    target.write('<td align="center"><table width="140"><tr><td class="number">{0}</td></tr>\n'.format(day)) 
                    target.write('<tr><td class="weekday">{0}</td></tr></table></td>\n'.format(content_str))    
                else:
                    target.write('<td align="center"><table width="140"><tr><td class="num">{0}</td></tr>\n'.format(day))
                    target.write('<tr><td class="weekday">{0}</td></tr></table></td>\n'.format(content_str))  
    
    target.write('</table><br/></body></html>')                      
    target.close()

    #if the month == current month, copy to ../current_month.html
    if date_start.year == cur_day.year and date_start.month == cur_day.month:
        current_control = os.path.join(base_path, 'calendar/control/liturgy/{0}/{1}.html'.format(date_start.year, month_name))  
        default_control = os.path.join(base_path, 'calendar/control/liturgy/current_month.html')
        run_copy(current_month=current_control, current_default=default_control) 

        current_open = os.path.join(base_path, 'calendar/liturgy/{0}/{1}.html'.format(date_start.year, month_name))
        default_open = os.path.join(base_path, 'calendar/liturgy/current_month.html')
        run_copy(current_month=current_open, current_default=default_open)  
                
def cal_page(date_start, abs_paths):

    #date_start is the first day of each month that is edited
    month_name = date_start.strftime("%B")    
    parser = SafeConfigParser()
    parser.read(months_ini) #reads the path  
    
    ini_header = '{0}'.format(date_start)
    html_header = headers.page_header(label='Liturgy')  

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
                            <td class="nav" width="20"><a href="%(5)s"><img src="/shc/images/next.png"/></a></td></tr></table>\n ''' % {'0':litcon_prev, '1':month_name, '2':date_start.year, '3':litcon_cur, '4':actcon_cur, '5':litcon_next}        

                    target_litcon = open(litcon_abs, 'w') 
                    target_litcon.write(html_header)
                    target_litcon.write(litcon_sub)
                    target_litcon.write(weekday_cols)
                    target_litcon.close()    

                    #add table cells with db content  
                    month_content(date_start, month_name, cal_path=litcon_abs)

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
                    <td class="nav" width="20"><a href="%(5)s"><img src="/shc/images/next.png"/></a></td></tr></table>\n''' % {'0':litopen_prev, '1': month_name, '2':date_start.year, '3':litopen_cur, '4':actopen_cur, '5':litopen_next}
                    target_litopen = open(litopen_abs, 'w') 
                    target_litopen.write(html_header)
                    target_litopen.write(litopen_sub)
                    target_litopen.write(weekday_cols)
                    target_litopen.close()

                    month_content(date_start, month_name, cal_path=litopen_abs)

