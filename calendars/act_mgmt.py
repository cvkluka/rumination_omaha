#!/usr/bin/python
# coding: utf-8

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import sqlite3 as sqlite
import shutil

from ConfigParser import SafeConfigParser
import calendar 
import datetime 
from dateutil.rrule import rrule, DAILY
from dateutil.relativedelta import relativedelta

from config_cal import email_from, base_path, web_path, act_db, HD_db, months_ini
import headers
from headers import page_header, weekday_cols

'''pnt calendar months for public and for activity managers'''

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

def read_actdb():

    '''act_schedule (Event_Start, Event_End, Activity, Event_Location, Show_Loc, Show_Time)
    limit changes to fields that are changeable (omit ID and date, 'poc', 'phone', 'email')'''

    act_date = {}

    try:
        con = sqlite.connect(act_db)
        cursor = con.cursor() 
        cursor.execute('SELECT ID, Event_Start, Event_End, Activity, Event_Location, Show_Loc, Show_Time FROM act_schedule')
        rows = cursor.fetchall()
        for row in rows:
            EID = row[0]
            act_date[str(row[1])] = [EID]
            for v in row[2:]:
                v = str(v)
                if row[0] == EID:
                    act_date[str(row[1])].append(v)
 
        con.commit()
        con.close()                                                                                                                                                     
    except IOError:
        print('Could not read the db! Please contact {0}'.format(email_from))
        sys.exit(1) 
        
    #for key in sorted(act_date):
        #print '?', key, act_date[key] #ok
        
    return act_date

def get_endTime(end_str):

    if end_str != '':
        dtg_end = datetime.datetime.strptime(end_str, '%Y-%m-%d %H:%M')
        time_endfmt = datetime.datetime.strftime(dtg_end, "%-I:%M %p") 

        return time_endfmt


def cell_content(cal_path, cal_day, cur_day):
    
    '''act_schedule db table (Event_Start, Event_End, Activity, Event_Location, Show_Loc, Show_Time)'''
    
    content_list = []
    hd_data = hd_table()
    month_object = cur_day.replace(day=1)
    act_date = read_actdb()
    
    for hd in hd_data: 
        holy_day = hd[:-5].replace('_', ' ')
        actual_date = datetime.datetime.strptime(hd_data[hd][0], '%Y-%m-%d').date()
        observed_date = datetime.datetime.strptime(hd_data[hd][1], '%Y-%m-%d').date()
        if actual_date == cal_day:
            content_list.append('<b><font color="#9e0909">{0}</font></b><br/>\n'.format(holy_day))             

        elif observed_date == cal_day:
            content_list.append('<b><font color="#9e0909">{0} (Observed)</font></b><br/>\n'.format(holy_day))  
            
    for key in sorted(act_date):
        dtg = datetime.datetime.strptime(key, '%Y-%m-%d %H:%M')
        if dtg.date() == cal_day:
            act_values = act_date[key]
            #assign names to values Event_Start:[EID, Event_End, Activity, Event_Location, Show_Loc] 
            if len(act_values) >= 5:
                EID = act_values[0]
                end_str = act_values[1]        
                activity = act_values[2]
                location = act_values[3]       
                time_startfmt = datetime.datetime.strftime(dtg, "%-I:%M %p") 
                time_endfmt = get_endTime(end_str)
                show_loc = act_values[4]
         
                if 'control' in cal_path:     
                    
                    if cal_day >= month_object:                    
                        content_list.append('{0} - {1}<br/>'.format(time_startfmt, time_endfmt))    
       
                        #link the activity  
                        if show_loc == 'On':
                            content_list.append('<a class="page" href="/shc/akc/edit_act.cgi?ID={0}&start_date={1}">{2}<br/>{3}</a><br/>\n'.format(EID, cal_day, activity, location))  
                            
                        else:
                            content_list.append('<a class="page" href="/shc/akc/edit_act.cgi?ID={0}&start_date={1}">{2}</a><br/>\n'.format(EID, cal_day, activity)) 
            
                    else:
                        #public view/open path
                        content_list.append('{0} - {1}<br/>'.format(time_startfmt, time_endfmt))    
                        
                        if show_loc == 'On':
                            content_list.append('{0}<br/>{1}</a><br/>\n'.format(activity, location))  
                            
                        else:
                            content_list.append('{0}<br/>\n'.format(activity))  
                            
                else:
                    #control events are in the past, use italic font; 
                    content_list.append('<i>{0}<br/>{1} <br/></i>\n'.format(time_startfmt, activity))                   
        
    if 'control' in cal_path:
        if cal_day >= month_object:                        
            
            if len(content_list) >= 3:
                content_list.append('<br/><a class="page" href="/shc/akc/edit_act.cgi?start_date={0}">Add Activity</a>\n'.format(cal_day)) 
            else:
                #Add empty lines if the day is empty
                content_list.append('<br/><br/><a class="page" href="/shc/akc/edit_act.cgi?start_date={0}">Add Activity</a>\n'.format(cal_day)) 

    return content_list
    

def month_content(dtg, month_name, cal_path):
              
    cur_day = datetime.date.today() 
    act_date = read_actdb()
    calendar.setfirstweekday(6) 
    calobject = calendar.monthcalendar(dtg.year, dtg.month)
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
                cal_day = datetime.date(dtg.year, dtg.month, day)
                content_list = cell_content(cal_path, cal_day, cur_day)
                if content_list and len(content_list) > 0:
                    content_str = ''.join(content_list)       
                    if cal_day == cur_day: 
                        #set day number in red;
                        target.write('<td align="center"><table width="140"><tr><td class="number">{0}</td></tr>\n'.format(day)) 
                        target.write('<tr><td class="weekday">{0}</td></tr></table></td>\n'.format(content_str))    
                    else:
                        target.write('<td align="center"><table width="140"><tr><td class="num">{0}</td></tr>\n'.format(day))
                        target.write('<tr><td class="weekday">{0}</td></tr></table></td>\n'.format(content_str))  
                                                                                                   
                else:
                    #no events
                    target.write('<td align="center"><table width="140"><tr><td class="num">{0}</td></tr>\n'.format(day))
                    target.write('<tr><td class="weekday"></td></tr></table></td>\n') 		                                                                                         
    target.write('</table><br/></body></html>')  
    target.close() 
    
    if dtg.year == cur_day.year and dtg.month == cur_day.month:
        current_control = os.path.join(base_path, 'calendar/control/activity/{0}/{1}.html'.format(dtg.year, month_name))  
        default_control = os.path.join(base_path, 'calendar/control/activity/current_month.html')
        run_copy(current_month=current_control, current_default=default_control) 

        current_open = os.path.join(base_path, 'calendar/activity/{0}/{1}.html'.format(dtg.year, month_name))
        default_open = os.path.join(base_path, 'calendar/activity/current_month.html')
        run_copy(current_month=current_open, current_default=default_open)  
        
def copy_header(dtg, month_start):

    #dtg is a month object for first day of month; month_start is a string
    month_name = dtg.strftime("%B")    
    parser = SafeConfigParser()
    parser.read(months_ini) 

    html_header = headers.page_header(label='Liturgy')  
    assoc_paths = {'actopen_abs':'actopen_head', 'actcon_abs':'actcon_head'}

    for cal_path in assoc_paths: 
        for section_date in parser.sections():
            if section_date == month_start:
                abs_path = parser.get(section_date, cal_path)  
                header_path = parser.get(section_date, assoc_paths[cal_path])

                target = open(abs_path, 'w')

                try:
                    shutil.copyfileobj(open(header_path, 'rb'), target)

                except IOError:
                    print('Could not read the form! Please contact {0}'.format(email_from))
                    sys.exit(1)  

                target.close()
                month_content(dtg, month_name, cal_path=abs_path)


