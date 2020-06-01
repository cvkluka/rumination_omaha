#!/usr/bin/python
# coding: utf-8

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from string import Template
import sqlite3 as sqlite
import shutil
import cgi

import datetime
import time
from datetime import timedelta

from dateutil.rrule import rrule, DAILY, WEEKLY
from dateutil.relativedelta import relativedelta
import calendar 

import act_mgmt
import email_out
from config_cal import base_path, act_db, HD_db, email_from, email_to, mail_path

'''on page load, read fields from database or date if empty; on submit, edit calendar activities; 
   dups not verified because every activity edit would be read as a duplicate entry; 
   load_db() is read to load the db table activity into the edit form;
   read_form() reads sub_flds values on submit; insert_fmt formats inputs as utf-8 for foreign accents;'''

form = cgi.FieldStorage()
fields = {}

form_list = ['time_start', 'time_end', 'activity', 'location', 'other_location', 'show_loc', 'show_time', 'start_date', 'end_date']
#event_data = {'ID':('time_start':'', 'time_end':'', 'activity':'', 'location':'', 'show_loc':'', 'show_time':'')}
#form field values read into sub_flds, then stored with utf-8 in insert_fmt dict
sub_flds = {'time_start':'', 'time_end':'', 'activity':'', 'location':'', 'other_location':'', 'show_loc':'', 'show_time':'', 'start_date':'', 'end_date':''}
insert_fmt = {'time_start':'', 'time_end':'', 'activity':'', 'location':'', 'other_location':'', 'show_loc':'', 'show_time':'', 'start_date':'', 'end_date':''}
#Omit Select on Location "00_Select":"Select"
location_options = {"01_SHC":"SHC", "02_ICC":"ICC", "03_St_Raphaels":"St. Raphael's", "04_Monroe_H.S.":"Monroe H.S.", "05_Miguel":"Miguel's Restaurant", "06_Other":"Other"}
opt_match = {'On':'Yes', 'Off':'No'}

def gen_time(f1):
    
    #support events at 15' past the hour and pre-pend dtg to the time, ex: 2017-05-22 07:30:00   
    time_tuples = [] 
    f1_time_start = datetime.datetime.combine(f1, datetime.time(8, 0)) 
    f1_time_end = datetime.datetime.combine(f1_time_start, datetime.time(23, 45))   
    
    def datetime_range(start, end, delta):
        current = start
        while current <= end:
            yield current
            current += delta    
    
    for dt in datetime_range(f1_time_start, f1_time_end, timedelta(minutes=15)):
        time_str = datetime.datetime.strftime(dt, '%H:%M')
        fmt_time = datetime.datetime.strftime(dt, '%-I:%M %p')
        time_tuples.append((time_str, fmt_time))
        
    time_tuples = sorted(time_tuples)   
    time_tuples.append(('00:00', '12:00 AM'))    
    #the first is the value that is passed, the second shows up in the web page
    time_tuples.insert(0, ('', 'Select')) 
        
    return time_tuples


def gen_range(f1, f2):
    
    date_range = []
    months = {}
    for dt in rrule(WEEKLY, dtstart=f1, until=f2):
        if dt.date() <= f2:
            date_short = dt.date() 
            if dt.date() not in date_range:
                date_str = datetime.datetime.strftime(date_short, '%Y-%m-%d')
                fmt_date = date_short.strftime("%-d %b %Y")
                #date objects not iterable, use strings
                date_range.append(date_str) 
                month_name = dt.strftime("%B")
                start_month = dt.replace(day=1) 
                months[month_name] = start_month.date()                   
              
    return date_range, months

def date_menu(f1):
    
    #generate a menu of date options for the html page (2 months);  
    two_months = []
    end_range = f1 + relativedelta(months=2)  
    for dg in rrule(WEEKLY, dtstart=f1, until=end_range):
        if dg.date() <= end_range:
            date_short = dg.date()
            date_str = datetime.datetime.strftime(date_short, '%Y-%m-%d')
            fmt_date = date_short.strftime("%-d %b %Y")
            #date objects not iterable, use strings
            two_months.append((date_str, fmt_date))            
    
    return two_months

def get_location(insert_fmt):
    
    locations = []    
    
    if insert_fmt['location'] == 'Other':
        locations.append(insert_fmt['other_location'])
    else:
        locations.append(insert_fmt['location'])
        
    location = locations[0]
    
    return location
        
   
def check_errs(insert_fmt, ts, te, action):
 
    error_dt = []
  
    if ts == '':
        error_dt.append('Start time is a required field!')
                
    else:
        if ts == '':
            error_dt.append('Failure to read date or time. Please report this.')
        else:
            if isinstance(ts, basestring):
                error_dt.append('Start time {0} is in the wrong format. Please report this.'.format(ts)) 
            elif isinstance(te, basestring):
                pass
            elif ts >= te:
                error_dt.append('Ending time matches or precedes start time.') 
                
            else:      
                if action == 'new':
                    activity = insert_fmt['activity']
                    dup = detect_dup(ts, activity)   
                    if len(dup) > 0:
                        error_dt.append('Schedule conflict or duplicate entry for activity {0} on {1}'.format(activity, ts_str))                       
   
    for sub in insert_fmt:
        value = insert_fmt[sub]
                        
        if sub == 'activity':       
            if len(value) < 2:
                error_dt.append('Activity is a required field!')

        if len(value) > 128:
            error_dt.append('Character limit exceeded!')                 
                    
    return error_dt
         
       
def load_db(ID):
    
    event_data = {}
    
    try:
        con = sqlite.connect(act_db) 
        cursor = con.cursor() 
        cursor.execute("SELECT Event_Start, Activity, Event_End, Event_Location, Show_Loc, Show_Time FROM act_schedule WHERE ID=?", (ID,)) 
        row = cursor.fetchone() 
        if row:
            event_data[ID] = row[0:]
            
    except sqlite.Error, e:
        print('<br/>Could not read the database! Please contact {0}'.format(email_from))
        sys.exit(1) 
        
    return event_data 

def get_id(ts_str, activity):
    
    id_lookup = []
    
    try:
        con = sqlite.connect(act_db)
        cursor = con.cursor()     
        cursor.execute("SELECT ID from act_schedule WHERE Event_Start=? AND Activity=?", (ts_str, activity))
        rows = cursor.fetchall()
        for row in rows:
            if row:
                id_lookup.append(int(row[0]))
        con.commit()
        con.close()        
            
    except sqlite.Error, e:
        print('Could not locate event ID! Please contact {0}'.format(email_from))
        sys.exit(1) 
        
    return id_lookup
    
def read_form(**kw):
    
    fields = kw.get('fields', {})
    
    for field in form_list:
        if isinstance(form.getvalue(field), list):
            fields[field] = form.getfirst(field)
        else:
            fields[field] = form.getvalue(field)

        if form.getvalue(field) == None:
            fields[field] = ''   
    
    #store form field values in sub_flds
    for field in fields:
        for sn in sub_flds:
            if field == sn: 
                value = fields[field]
                if value != '':
                    value = value.strip()
                    sub_flds[sn] = value
                    
    return sub_flds


def delete_row(id_rcd):
    
    try:
        con = sqlite.connect(act_db)
        cursor = con.cursor()     
        cursor.execute("DELETE FROM act_schedule WHERE ID=?", (id_rcd,))    
            
    except sqlite.Error, e:   
        print('Could not locate record for deletion! Please contact {0}'.format(email_from))
        sys.exit(1)  
    
    con.commit()      
    con.close() 
        
def update_activity(ts_str, activity, te_str, location, show_loc, show_time, ID):
    
    #db table columns: ID, Event_Start, Activity, Event_End, Event_Location, POC, Phone, Email, Show_Loc, Show_Time;
    try:
        con = sqlite.connect(act_db)
        cursor = con.cursor() 
        cursor.execute("UPDATE act_schedule SET Event_Start=?, Activity=?, Event_End=?, Event_Location=?, Show_Loc=?, Show_Time=? WHERE ID=?", (ts_str, activity, te_str, location, show_loc, show_time, ID))
        
    except sqlite.Error, e:              
        print('Could not connect to database to edit this record! Please contact {0}'.format(email_from))
        sys.exit(1)   
     
    con.commit()      
    con.close()   
        
        
def get_times(dt, time_start, time_end):
    
    #time_start, time_end are form inputs; time_vars = [ts, ts_str, ts_fmt, te, te_str, te_fmt]
    time_vars = []
    if time_start in ['Select', '']:
        time_vars = ['', '', '', '', '', '']
    
    else:
        hour_start = datetime.datetime.strptime(time_start, '%H:%M').time()
        ts = datetime.datetime.combine(dt, hour_start) 
        ts_string = datetime.datetime.strftime(ts, '%Y-%m-%d %H:%M')  
        #converts with :00 for seconds, remove trailing zeros
        ts_str = ts_string[:16]  
        ts_fmt = datetime.datetime.strftime(ts, '%-I:%M %p')   
        
        if time_end != '':
            hour_end = datetime.datetime.strptime(time_end, '%H:%M').time()
            if time_end == '00:00':
                add_day = dt + timedelta(days=1)
                te = datetime.datetime.combine(add_day, hour_end) 
                te_string = datetime.datetime.strftime(te, '%Y-%m-%d %H:%M')
                #date object shows :00 for seconds, remove
                te_str = te_string[:16]
                te_fmt = datetime.datetime.strftime(te, '%-I:%M %p')
                te_midnight = '{0} (midnight)'.format(te_fmt)
                time_vars = [ts, ts_str, ts_fmt, te, te_str, te_midnight]  
                
            else:
                te = datetime.datetime.combine(dt, hour_end)
                te_string = datetime.datetime.strftime(te, '%Y-%m-%d %H:%M')    
                #date object shows :00 for seconds, remove
                te_str = te_string[:16]  
                te_fmt = datetime.datetime.strftime(te, '%-I:%M %p')                                
                time_vars = [ts, ts_str, ts_fmt, te, te_str, te_fmt]  
                
        else:
            #no end time 
            time_vars = [ts, ts_str, ts_fmt, '', '', '']

            
                
    return time_vars   
                     

def detect_dup(ts, activity): 
    
    '''db table columns: ID, Event_Start, Activity, Event_End, Event_Location,POC, Phone, Email, Show_Loc, Show_Time;
    insert_fmt keys: start time, end time, activity, location, poc, phone, email '''   
    dup = []
    statement = 'SELECT Event_Start, activity FROM act_schedule WHERE Event_Start="{0}" AND Activity=\"{1}\"'.format(ts, activity)                                                                           
        
    try:
        con = sqlite.connect(act_db)
        cursor = con.cursor() 
        cursor.execute(statement)
        row = cursor.fetchone()
        if row:
            dup.append('Duplicate entry for {0} starting at {1}'.format(row[1], row[0]))  
        con.commit()
        con.close()             
                                       
    except sqlite.Error, e:
        sys.exit(1) 
    
    return dup

        
def insert_activity(ts_str, activity, te_str, location, show_loc, show_time):
    
    try:
        con = sqlite.connect(act_db)
        cursor = con.cursor() 
        cursor.execute('''INSERT INTO act_schedule (Event_Start, Activity, Event_End, Event_Location, Show_Loc, Show_Time) 
                       VALUES(?, ?, ?, ?, ?, ?)''', (ts_str, activity, te_str, location, show_loc, show_time))
        con.commit()
        con.close()        
        
    except sqlite.Error, e:  
        print 'Could not connect to database to insert this record! Please contact {0}'.format(email_from)
        sys.exit(1) 
        
def get_vars(sub_flds, dt):
    
    '''omit ID and date, 'poc', 'phone', 'email'; utf = val.decode('utf-8') = string to unicode;'''
    
    for k in form_list:
        for sn in sub_flds:
            if sn == k:
                value = sub_flds[sn]
                
                if sn == 'start_date':
                    insert_fmt[sn] = value

                elif sn == 'time_start':
                    insert_fmt[sn] = value

                elif sn == 'time_end':
                    if value == 'Select':
                        insert_fmt[sn] = ''
                    else:
                        insert_fmt[sn] = value

                elif sn == 'activity':
                    if "'" in value:
                        val = value.replace("'", "\'")
                        utf = val.decode('utf-8')
                        insert_fmt[sn] = utf
                        
                    else:
                        utf = value.decode('utf-8')
                        insert_fmt[sn] = utf

                elif sn == 'location':
                    for key in location_options:
                        if key[3:] == value:
                            insert_fmt[sn] = key[3:]
                            
                elif sn == 'other_location':
                    if "'" in value:
                        val = value.replace("'", "\'")
                        utf = val.decode('utf-8')
                        insert_fmt[sn] = utf
                    else:
                        utf = value.decode('utf-8')
                        insert_fmt[sn] = utf

                elif sn == 'show_loc':
                    insert_fmt[sn] = value

                elif sn == 'show_time':
                    insert_fmt[sn] = value

                elif sn == 'end_date':
                    insert_fmt[sn] = value
                    
    #end date initially empty (on new activity or edit activity)

    return insert_fmt
    

#Build the html pages #############################################################

def sub_events(start_date, end_date, ID):
    
    target = open(act_edit, 'a')  
    target.write('<tr><td class="main" align="center"><input type="text" size="35" maxlength="50" name="activity" value="{0}" /></td>\n'.format(insert_fmt['activity']))
    target.write('<td class="main" align="center"><select class="select_menu" name="location">')
    for key in sorted(location_options):
        #use sub_flds 
        if sub_flds['location'] == location_options[key]:   
            target.write('<option selected value="{0}">{1}</option>\n'.format(key[3:], location_options[key]))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(key[3:], location_options[key]))                      
    target.write('</select></td>\n') 

    target.write('<td class="main" align="center"><b>Start time:</b>&nbsp;<select class="select_times" name="time_start">')
    for date_option, fmt_time in time_tuples:  
        
        if date_option == insert_fmt['time_start']:
            target.write('<option selected value="{0}">{1}</option>\n'.format(date_option, fmt_time))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(date_option, fmt_time))
    target.write('</select><br/>')
       
    target.write('<b>End time:</b><br/>(Optional)&nbsp;<select class="select_times" name="time_end">\n')
    for date_option, fmt_time in time_tuples:  
        if date_option == insert_fmt['time_end']:
            target.write('<option selected value="{0}">{1}</option>\n'.format(date_option, fmt_time))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(date_option, fmt_time))
    target.write('</select></td>')
        
    #Adding end dates, use a 90-day window
    target.write('''<td class="main" align="center"><b>Start date: </b><br/>{0}<br/>
    <br/><b>End date: </b>\n<select class="select_dates" name="end_date">'''.format(fmt_start))
    for date_option, fmt_date in two_months:
        if date_option == end_date:                       
            target.write('<option selected value="{0}">{1}</option>\n'.format(date_option, fmt_date))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(date_option, fmt_date))
                            
    target.write('''</select></td></tr>
    <tr><td class="main" colspan="4">If Location is "Other" specify here: <input type="text" size="30" maxlength="50" name="other_location" value="{0}"></td></tr>
    <tr><td class="main" colspan="4" align="center">The location and time of the event (required fields) are shown in the calendar by default.<br/>
            To remove one or more of these entries from the calendar page, select "No" from the corresponding menu. <br/>'''.format(insert_fmt['other_location']))    
    
    target.write('<b>Show Location: </b>\n<select class="select_options" name="show_loc">')
   
    for key in opt_match:
        #start with sub_flds, on submit read insert_fmt; default to SHC with no-show on location
        if sub_flds['show_loc'] == '' and key == 'Off':
            target.write('<option selected value="Off">No</option>\n')        
        elif key == insert_fmt['show_loc']:
            target.write('<option selected value="{0}">{1}</option>\n'.format(key, opt_match[key]))
        
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(key, opt_match[key]))
    target.write('</select>')
    
    target.write('<b>Show Time: </b>\n<select class="select_options" name="show_time">')
    for key in opt_match:
        if key == sub_flds['show_time']:
            target.write('<option selected value="{0}">{1}</option>\n'.format(key, opt_match[key]))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(key, opt_match[key]))        
    target.write('</select></td></tr>\n')
    
    target.write('''<tr><td class="main" colspan="4" align="center"><input type="hidden" name="start_date" value="{0}">
    <input type="hidden" name="end_date" value="{1}">
    <input type="hidden" name="ID" value="{2}">
    <input type="submit" name="Submit_New" value="Submit"/>
    </td></tr></form>
    <form action="{3}" method="post">
    <tr><td colspan="4"><input type="submit" name="Cancel" value="Cancel"/></td></tr></table>
    </form></body></html>\n'''.format(start_date, end_date, ID, actcon_this_month))    
      
    target.close()    
    
def db_events(start_date, end_date, event_data, ID):
    
    target = open(act_edit, 'a')  
        
    '''event_data[ID] = Event_Start, Activity, Event_End, Event_Location, Show_Loc, Show_Time]
    on load, use db entries except for end_date (a range); on submit, use insert_fmt entries '''
    
    for id_rcd in event_data:
        if id_rcd == ID:
            time_start = event_data[id_rcd][0]
            event_activity = event_data[id_rcd][1]
            time_end = event_data[id_rcd][2]
            event_location = event_data[id_rcd][3]
            event_showloc = event_data[id_rcd][4]
            event_showtime = event_data[id_rcd][5]
            #event_data = {'ID':('time_start':'', 'time_end':'', 'activity':'', 'location':'', 'show_loc':'', 'show_time':'')}
            hour_start = time_start[-5:]
            hour_end = time_end[-5:]  
           
            #format undefined if foreign accent is present #activity = event_data['activity'].encode('utf-8') #insert_fmt fix?
            target.write('<tr><td class="main" align="center"><input type="text" size="35" maxlength="50" name="activity" value="{0}" /></td>\n'.format(event_activity))
                 
            target.write('<td class="main" align="center"><select class="select_menu" name="location">')
            for key in sorted(location_options):
                if key[3:] == event_location:   
                    target.write('<option selected value="{0}">{1}</option>\n'.format(key[3:], location_options[key]))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(key[3:], location_options[key]))                      
            target.write('</select></td>\n') 
                
            target.write('<td class="main" align="center"><b>Start time:</b>&nbsp;<select class="select_times" name="time_start">')
            for time_24, fmt_time in time_tuples: 
                if time_24 == hour_start:
                    target.write('<option selected value="{0}">{1}</option>\n'.format(time_24, fmt_time))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(time_24, fmt_time))
            target.write('</select><br/>')
                      
            target.write('<b>End time:</b><br/>(Optional)&nbsp;<select class="select_times" name="time_end">\n')
            for time_24, fmt_time in time_tuples:  
                #returned values are hour_end, fmt_end #08:00, 8:00 AM 
                if time_24 == hour_end:
                    target.write('<option selected value="{0}">{1}</option>\n'.format(time_24, fmt_time))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(time_24, fmt_time))
            target.write('</select></td>')
                    
            #Adding end dates, use a 90-day window
            target.write('<td class="main" align="center"><b>Start date: </b><br/>{0}<br/>'.format(fmt_start))
            target.write('<br/><b>End date: </b>\n<select class="select_dates" name="end_date">')
            for date_option, fmt_date in two_months:
                #loading an ID, the end date == the start date; use defaults
                if date_option == end_date:                     
                    target.write('<option selected value="{0}">{1}</option>\n'.format(date_option, fmt_date))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(date_option, fmt_date))
                            
            target.write('''</select></td><tr><td class="main" colspan="4" align="center">
                    The location and time of the event (required fields) are shown in the calendar by default.<br/>
                    To remove one or more of these entries from the calendar page, select "No" from the corresponding menu. <br/>''')    
            
            target.write('<b>Show Location: </b>\n<select class="select_options" name="show_loc">')
           
            for key in opt_match:
                if key == event_showloc:
                    target.write('<option selected value="{0}">{1}</option>\n'.format(key, opt_match[key]))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(key, opt_match[key]))
            target.write('</select>')
            
            target.write('<b>Show Time: </b>\n<select class="select_options" name="show_time">')
            for key in opt_match:
                if key == event_showtime:
                    target.write('<option selected value="{0}">{1}</option>\n'.format(key, opt_match[key]))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(key, opt_match[key]))        
            target.write('</select></td></tr>\n')  
            
    target.write('''<tr><td class="main" colspan="4" align="center"><input type="hidden" name="start_date" value="{0}">
    <input type="hidden" name="end_date" value="{1}">
    <input type="hidden" name="ID" value="{2}">
    <input type="submit" name="Submit_Edit" value="Submit"/>
    <input type="submit" name="Delete" value="Delete"/></td></tr></form>
    <form action="{3}" method="post">
    <tr><td colspan="4"><input type="submit" name="Cancel" value="Cancel"/></td></tr></table>
    </form></body></html>\n'''.format(start_date, end_date, ID, actcon_this_month))
            
    target.close()  
    

def edit_day(start_date, title_msg, end_date, event_data, ID):
    
    edit_acthead = os.path.join(base_path, 'calendar/forms/edit_acthead.html')
    target = open(act_edit, 'w')  
    try:
        shutil.copyfileobj(open(edit_acthead, 'rb'), target)
        
    except IOError:
        print('Could not read the management form! Please contact {0}'.format(email_from))
        sys.exit(1)      
        
    target.close()
    
    if ID != '':   
        db_events(start_date, end_date, event_data, ID)
        
    else:
        sub_events(start_date, end_date, ID)
    
    try:      
        t = Template(open(act_edit).read())
        print(t.substitute(start_date=start_date,month_path=actcon_this_month,title_msg=title_msg))

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)          
     
    
def confirm_page(title_msg, months):
    
    mail_list = []
    mail_msg = title_msg.replace('<br/>', '\n')
    mail_list.append(mail_msg)
    #print mail_list  #utf-8 works in mail_path?  
    act_confirm = os.path.join(base_path, 'calendar/control/activity/act_confirm.html')
    confirm_actheader = os.path.join(base_path, 'calendar/forms/confirm_actheader.html')
    
    target = open(act_confirm, 'w')
    
    try:
        shutil.copyfileobj(open(confirm_actheader, 'rb'), target)

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1) 
        
    #end nested table, footer 
    target.write('<tr><td class="main" colspan="4" align="center">Reload the calendar month page(s) as needed to view your changes.</td></tr></table>\n')             
    target.write('<table align="center"><tr><td>\n<form action="{0}" method="post">\n'.format(actcon_this_month))
    target.write('<input type="Submit" name="Submit1" value="Return"></form></td></tr></table></body></html>\n')               
    target.close()              

    try:      
        t = Template(open(act_confirm).read())
        print(t.substitute(title_msg=title_msg,month_path=actcon_this_month))
        
    except IOError:
        print 'Could not read the form! Please contact {0}'.format(email_from)
        sys.exit(1)  
        
    if len(months) > 0:
        for month_name in months:
            #month_start is a datetime, year is an int
            date_start = months[month_name]
            year_num = date_start.year
            act_mgmt.cal_page(year_num, month_name, date_start, abs_paths)            
              
    email_envoi = open(mail_path, 'w')
    email_subject = 'SHC Calendar Activity Changed'
    email_message = '\n'.join(mail_list) 
    email_envoi.write(email_message)
    email_envoi.write('\n')
    email_envoi.close()
    email_out.send_email(email_from, email_to, email_subject)                    
             
if __name__ == "__main__":
    
    print "Content-type: text/html; charset=utf-8\n" 
    
    start_date = form.getvalue('start_date')
    ID = form.getvalue('ID')
    #print 'start_date, ID', start_date, ID
    end_date = form.getvalue('start_date')
    f1 = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()  
    year = f1.year
    month_name = f1.strftime("%B")
    abs_paths = ['actopen_abs', 'actcon_abs']
    act_edit = os.path.join(base_path, 'calendar/control/activity/act_edit.html')
    actcon_this_month = '/shc/calendar/control/activity/{0}/{1}.html'.format(year, month_name)         
    #insert_fmt modifies sub_fld values with utf-8 formatting
    event_data = load_db(ID)
    sub_flds = read_form(fields=fields)
    insert_fmt = get_vars(sub_flds, dt=start_date)  
    #{'time_start':'', 'time_end':'', 'activity':'', 'location':'', 'show_loc':'', 'show_time':'', 'start_date':'', 'end_date':''}
    f2 = datetime.datetime.strptime(end_date, '%Y-%m-%d').date() 
    time_tuples = gen_time(f1)
    two_months = date_menu(f1)
    f1_weekday = calendar.day_name[f1.weekday()]
    fmt_start = f1.strftime("%-d %B %Y")    
    fmt_end = f2.strftime("%-d %B %Y") 
    date_range = gen_range(f1, f2)[0]
    errors = []
    
    if 'Submit_New' in form:
        end_date = insert_fmt['end_date']
        f2 = datetime.datetime.strptime(end_date, '%Y-%m-%d').date() 
        fmt_end = f2.strftime("%-d %B %Y") 
        date_range = gen_range(f1, f2)[0]
        months = gen_range(f1, f2)[1]   
        titles = []
        
        #get dates for db table; 
        for dt_str in sorted(date_range):  
            dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d')
            time_start = insert_fmt['time_start']
            time_end = insert_fmt['time_end']  
            time_vars = get_times(dt, time_start, time_end) 
            #time_vars = [ts, ts_str, ts_fmt, te, te_str, te_fmt]
            if len(time_vars) == 6:
                ts = time_vars[0]
                te = time_vars[3]
                error_dt = check_errs(insert_fmt, ts, te, action='new')
                for err in error_dt:
                    errors.append(err)
                    
                if len(errors) > 0:
                    title_msg = ' '.join(errors)  
                    titles.append(title_msg)
                    
                else:     
                    #time_vars = [ts, ts_str, ts_fmt, te, te_str, te_fmt]; ts, te passed to check_errs
                    ts_str = time_vars[1] 
                    ts_fmt = time_vars[2] 
                    te_str = time_vars[4]
                    te_fmt = time_vars[5]
                    activity = insert_fmt['activity']
                    location = get_location(insert_fmt)
                    show_loc = insert_fmt['show_loc']
                    show_time = insert_fmt['show_time']    
                    insert_activity(ts_str, activity, te_str, location, show_loc, show_time)
                    
                    if fmt_start == fmt_end:
                        #the start date and the end date are the same
                        title_msg = ('You have added the following activity:<br/>{0} - {1} <br/>{2}<br/>on {3} {4}'.format(ts_fmt, te_fmt, activity, f1_weekday, fmt_start))
                        titles.append(title_msg)  
                        
                    else:
                        title_msg = ('You have added the following activity:<br/>{0} - {1}<br/>{2}<br/>from {3} {4} - {5} {6}'.format(ts_fmt, te_fmt, activity, f1_weekday, fmt_start, f1_weekday, fmt_end))
                        titles.append(title_msg)                  
        
        if len(titles) > 0:      
            title_msg = titles[0]
            if len(errors) > 0:
                edit_day(start_date, title_msg, end_date, event_data='', ID='')
                                   
            else:   
                confirm_page(title_msg, months)
                
        else:
            title_msg = 'No action was taken. Please report this error.'
            confirm_page(title_msg, months)
                      

    elif 'Submit_Edit' in form:  
        
        #default to form inputs
        end_date = insert_fmt['end_date']
        f2 = datetime.datetime.strptime(end_date, '%Y-%m-%d').date() 
        fmt_end = f2.strftime("%-d %B %Y")   
        date_range = gen_range(f1, f2)[0]
        months = gen_range(f1, f2)[1] 
        titles = []
        id_rcds = []

        for dt_str in sorted(date_range):
            dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d') 
            for id_rcd in event_data:
                time_start = event_data[id_rcd][0][-5:]         
                db_activity = event_data[id_rcd][1]  
                time_end = event_data[id_rcd][2][-5:]                  
                time_vars = get_times(dt, time_start, time_end) 
                if len(time_vars) == 6:
                    ts_str = time_vars[1]          
                    id_lookup = get_id(ts_str, activity=db_activity)
                    #one activity per start time w/ same name; id_lookup is a list;
                    if len(id_lookup) > 0:
                        for id_rcd in id_lookup:
                            #submit form values
                            time_start = insert_fmt['time_start']
                            time_end = insert_fmt['time_end']  
                            time_vars = get_times(dt, time_start, time_end) 
                            ts = time_vars[0]
                            ts_str = time_vars[1] 
                            ts_fmt = time_vars[2]  
                            te = time_vars[3]
                            te_str = time_vars[4]
                            te_fmt = time_vars[5]
                            activity = insert_fmt['activity']
                            location = get_location(insert_fmt)
                            show_loc = insert_fmt['show_loc']
                            show_time = insert_fmt['show_time']                               
                            error_dt = check_errs(insert_fmt, ts, te, action='edit')            
                            for err in error_dt:
                                errors.append(err)                   
       
                            if len(errors) > 0:
                                title_msg = '<br/>'.join(errors)
                                titles.append(title_msg)                
                                   
                            else:   
                                #assumes that for each day, there is only one activity per start time;
                                update_activity(ts_str, activity, te_str, location, show_loc, show_time, ID=id_rcd) 
                            
        if fmt_start == fmt_end:
            #the start date = the end date
            title_msg = ('You have updated the following activity:<br/>{0} - {1} <br/>{2}<br/>on {3} {4}'.format(ts_fmt, te_fmt, activity, f1_weekday, fmt_start))
            titles.append(title_msg)   
            
        else:
            title_msg = ('You have updated the following activity:<br/>{0} - {1}<br/>{2}<br/>from {3} {4} - {5} {6}'.format(ts_fmt, te_fmt, activity, f1_weekday, fmt_start, f1_weekday, fmt_end))
            titles.append(title_msg)
    
        if len(titles) > 0:
            title_msg = titles[0]
            if len(errors) > 0:
                edit_day(start_date, title_msg, end_date, event_data, ID=ID)       
            else:
                confirm_page(title_msg, months)
                
        else:
            title_msg = 'No records were changed. Please report this error.'
            confirm_page(title_msg, months)
        
    elif 'Delete' in form:
        
        end_date = insert_fmt['end_date']
        f2 = datetime.datetime.strptime(end_date, '%Y-%m-%d').date() 
        fmt_end = f2.strftime("%-d %B %Y") 
        months = gen_range(f1, f2)[1]   
        date_range = gen_range(f1, f2)[0]
        months = gen_range(f1, f2)[1]  
        titles = []
        id_rcds = []
        activities = []
        
        for dt_str in sorted(date_range):
            dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d') 
            for id_rcd in event_data:
                time_start = event_data[id_rcd][0][-5:]         
                db_activity = event_data[id_rcd][1]  
                time_end = event_data[id_rcd][2][-5:]                  
                time_vars = get_times(dt, time_start, time_end) 
                if len(time_vars) == 6:
                    ts = time_vars[0]
                    ts_str = time_vars[1] 
                    ts_fmt = time_vars[2] 
                    te = time_vars[3]
                    te_str = time_vars[4]
                    te_fmt = time_vars[5]        
                    id_lookup = get_id(ts_str, activity=db_activity)
                    #one activity per start time with the same name (mass, confession etc.); id_lookup is a list;
                    for id_rcd in id_lookup:
                        delete_row(id_rcd)
                
        if fmt_start == fmt_end:
            #the start date = the end date
            title_msg = ('You have deleted the following activity:<br/>{0} - {1} <br/>{2}<br/>on {3} {4}'.format(ts_fmt, te_fmt, db_activity, f1_weekday, fmt_start))
            titles.append(title_msg)   
            
        else:
            title_msg = ('You have deleted the following activity:<br/>{0} - {1}<br/>{2}<br/>from {3} {4} - {5} {6}'.format(ts_fmt, te_fmt, db_activity, f1_weekday, fmt_start, f1_weekday, fmt_end))
            titles.append(title_msg)
        
        if len(titles) > 0: 
            title_msg = titles[0]        
            confirm_page(title_msg, months)
        else:
            title_msg = 'Nothing was deleted. Please report this error.'
            confirm_page(title_msg, months)
        
    else:
        
        if ID:   
            title_msg = ('''You may edit the activity below on {0} {1}.<br/>If the activity spans multiple weeks,
            select an ending date (the date range is applied weekly but not daily).'''.format(f1_weekday, fmt_start)) 
            edit_day(start_date, title_msg, end_date, event_data, ID)        
                
        else:
            title_msg = ('''You may add an activity to the schedule starting on {0} {1}. <br/> 
                            Please complete all fields that apply.'''.format(f1_weekday, fmt_start)) 
            edit_day(start_date, title_msg, end_date, event_data='', ID='')
        