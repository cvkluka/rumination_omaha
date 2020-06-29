#!/usr/bin/python
# coding: utf-8

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import datetime
import time
from datetime import timedelta

from dateutil.rrule import rrule, DAILY, WEEKLY
from dateutil.relativedelta import relativedelta
import calendar 

from string import Template
import sqlite3 as sqlite
import shutil
import cgi

import act_mgmt
import email_out
from config_cal import base_path, act_db, HD_db, email_from, email_to, mail_path

'''on page load, read fields from database or date if empty; on submit, change calendar activities; 
   dups not verified because every activity edit would be read as a duplicate entry; 
   read_form() reads sub_flds values on submit; insert_fmt formats inputs as utf-8 for foreign accents;
   events_all = {'ID':('time_start':'', 'time_end':'', 'activity':'', 'location':'', 'show_loc':'')}; show_time omitted.'''

form = cgi.FieldStorage()
fields = {}

form_list = ['time_start', 'time_end', 'activity', 'menu_location', 'text_location', 'show_loc', 'start_date', 'end_date']
#form field values read into sub_flds; #menu_location is pull-down, text_location is a text input entry
sub_flds = {'time_start':'', 'time_end':'', 'activity':'', 'menu_location':'', 'text_location':'', 'show_loc':'', 'start_date':'', 'end_date':''}
#store text inputs as utf-8; how to tie to sub_flds?
insert_fmt = {'activity':'', 'text_location':''}
#Omit Select from location inputs to db table
location_options = {"Select":"Select", "SHC_Cathedral":"SHC (Cathedral)", "SHC_Outdoors":"SHC (Outdoors)", "Online":"Online", "Other":"Other" }
location_list = ["Select", "SHC_Cathedral", "SHC_Outdoors", "Online", "Other"]
#menu options to select whether location is shown on calendar page
opt_match = {'On':'Yes', 'Off':'No'}

'''to do: the location variable passed to db_events(start_date, end_date, events_all, location, ID) and 
sub_events(start_date, end_date, location, ID) isn't doing anything, clean this up...'''

def gen_time(f1):

    #support events at 15' past the hour; pre-pend dtg to the time, ex: 2017-05-22 07:30:00   
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
    time_tuples.insert(0, ('Select', 'Select')) 

    return time_tuples


def gen_range(f1, f2):

    '''adjusted date range based on end date selection'''
    date_range = []
    for dtg in rrule(WEEKLY, dtstart=f1, until=f2):
        dt = dtg.date()
        dt_str = datetime.datetime.strftime(dt, '%Y-%m-%d')
        date_range.append(dt_str)

    return date_range    

def html_options(f1):

    '''predetermined date range on load; combine this with gen_range()'''
    html_range = []
    last_option = f1 + relativedelta(months=2)  
    for dt in rrule(WEEKLY, dtstart=f1, until=last_option):
        date_short = dt.date()
        date_str = date_short.strftime('%Y-%m-%d')
        fmt_date = date_short.strftime("%-d %b %Y")
        html_range.append((date_str, fmt_date))

    return html_range


def get_location(sub_flds, insert_fmt):

    locations = [] 

    #loading html page with selected option
    for k in location_options:
        if sub_flds['menu_location'] in ['Select', 'Other']:
            if insert_fmt['text_location'] != '':
                locations.append(insert_fmt['text_location'])
        elif k == sub_flds['menu_location']:
            locations.append(location_options[k])   

    if len(locations) > 0:
        location = locations[0]    

        return location

def get_form_location(location_options, event_location):

    text_field = []

    for key in location_options:
        if location_options[key] == event_location:
            text_field.append('')

    if len(text_field) == 0:
        #account for records w/o location inputs
        if event_location == None:
            text_field.append('')
        else:
            text_field.append(event_location)

    text_location = text_field[0]

    return text_location


def check_errs(events_all, sub_flds, insert_fmt, action):

    errors = []

    if sub_flds['time_start'] in ['', 'Select']:
        errors.append('Start time is a required field. Please try again!')

    if sub_flds['time_end'] in ['', 'Select']:
        errors.append('End time is a required field. Please try again!')

    if sub_flds['activity'] == '':
        errors.append('Activity is a required field. Please try again!') 

    if len(errors) == 0:
        #f1 = f2! only evaluates the first day of date range
        start_date = sub_flds['start_date']       
        ts_str = '{0} {1}'.format(start_date, sub_flds['time_start'])
        ts_obj = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M')   
        te_str = '{0} {1}'.format(start_date, sub_flds['time_end'])
        te_obj = datetime.datetime.strptime(te_str, '%Y-%m-%d %H:%M')   

        if ts_obj >= te_obj:
            errors.append('Ending time matches or precedes start time. Please try again!'.format(start_date))                  

    if len(insert_fmt['activity']) <= 2:
        errors.append('Activity is ambiguous!')

    elif sub_flds['menu_location'] in ['Select', 'Other'] and insert_fmt['text_location'] == '':
        errors.append('Location input is required. Please try again!')

    elif len(insert_fmt['activity']) > 128 or len(insert_fmt['text_location']) > 128:
        errors.append('Character limit exceeded!')                 

    return errors


def load_db():

    events_all = {}

    try:
        con = sqlite.connect(act_db) 
        cursor = con.cursor() 
        cursor.execute("SELECT ID, Event_Start, Activity, Event_End, Event_Location, Show_Loc FROM act_schedule")
        rows = cursor.fetchall()
        for row in rows:
            eid = str(row[0])
            events_all[eid] = [str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5])]   

    except sqlite.Error, e:
        print('<br/>Could not read the database! Please contact {0}'.format(email_from))
        sys.exit(1) 

    return events_all


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

                if sn in ['activity', 'text_location']:
                    if value != '':
                        value = value.strip()
                        sub_flds[sn] = value

                else:
                    sub_flds[sn] = value

    return sub_flds


def delete_row(eid):

    try:
        con = sqlite.connect(act_db)
        cursor = con.cursor()     
        cursor.execute("DELETE FROM act_schedule WHERE ID=?", (eid,))    

    except sqlite.Error, e:   
        print('Could not locate record for deletion! Please contact {0}'.format(email_from))
        sys.exit(1)  

    con.commit()      
    con.close() 


def update_activity(ts_str, activity, te_str, location, show_loc, ID):

    #db table columns: ID, Event_Start, Activity, Event_End, Event_Location, POC, Phone, Email, Show_Loc;
    try:
        con = sqlite.connect(act_db)
        cursor = con.cursor() 
        cursor.execute("UPDATE act_schedule SET Event_Start=?, Activity=?, Event_End=?, Event_Location=?, Show_Loc=? WHERE ID=?", (ts_str, activity, te_str, location, show_loc, ID))

    except sqlite.Error, e:              
        print('Could not connect to database to edit this record! Please contact {0}'.format(email_from))
        sys.exit(1)   

    con.commit()      
    con.close()   


def detect_dups(events_all, activity, dts): 

    '''db table columns: ID, Event_Start, Activity, Event_End, Event_Location,POC, Phone, Email, Show_Loc, Show_Time; 
       insert_fmt keys: activity, location'''   
    dup = []
    for eid in events_all:
        ts_start = events_all[eid][0]      
        db_date = datetime.datetime.strptime(ts_start, '%Y-%m-%d %H:%M').date()
        dt = datetime.datetime.strptime(dts, '%Y-%m-%d').date()
        db_activity = events_all[eid][1]  
        if db_date == dt and db_activity == activity:
            dup.append(eid)

    return dup

def insert_activity(ts_str, activity, te_str, location, show_loc):

    try:
        con = sqlite.connect(act_db)
        cursor = con.cursor() 
        cursor.execute('''INSERT INTO act_schedule (Event_Start, Activity, Event_End, Event_Location, Show_Time, Show_Loc) VALUES(?, ?, ?, ?, 'On', ?)''', (ts_str, activity, te_str, location, show_loc))
        con.commit()
        con.close()        

    except sqlite.Error, e:  
        print 'Could not connect to database to insert this record! Please contact {0}'.format(email_from)
        sys.exit(1) 


def fmt_utf8(sub_flds):

    '''omit ID and date, 'poc', 'phone', 'email'; utf = val.decode('utf-8') = string to unicode;'''
    insert_fmt = {}

    for k in ['activity', 'text_location']:
        for sn in sub_flds:
            if sn == k:
                value = sub_flds[sn]
                if "'" in value:
                    val = value.replace("'", "\'")
                    utf = val.decode('utf-8')
                    insert_fmt[sn] = utf

                else:
                    utf = value.decode('utf-8')
                    insert_fmt[sn] = utf

    return insert_fmt


#Build the html pages #############################################################

def sub_events(start_date, end_date, ID):
    #no ID, set your defaults to add an activity
    target = open(act_edit, 'a')  
    target.write('<tr><td class="main" align="center"><input type="text" size="35" maxlength="50" name="activity" value="{0}" /></td>\n'.format(insert_fmt['activity']))
    target.write('<td class="main" align="center"><select class="select_menu" name="menu_location">')
    for k in location_list:
        for key in location_options:
            if key == k:
                if sub_flds['menu_location'] == key:  
                    target.write('<option selected value="{0}">{1}</option>\n'.format(key, location_options[key]))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(key, location_options[key]))               
    target.write('</select></td>\n') 

    target.write('<td class="main" align="center"><b>Start time:</b>&nbsp;<select class="select_times" name="time_start">')
    for time_str, fmt_time in time_tuples: 
        if time_str == sub_flds['time_start']:
            target.write('<option selected value="{0}">{1}</option>\n'.format(time_str, fmt_time))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(time_str, fmt_time))
    target.write('</select><br/>')

    target.write('<b>End time:</b><br/><select class="select_times" name="time_end">\n')
    for time_str, fmt_time in time_tuples:
        if time_str == sub_flds['time_end']:
            target.write('<option selected value="{0}">{1}</option>\n'.format(time_str, fmt_time))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(time_str, fmt_time))
    target.write('</select></td>')

    #Adding end dates, use a 90-day window
    target.write('''<td class="main" align="center"><b>Start date: </b><br/>{0}<br/>
    <br/><b>End date: </b>\n<select class="select_dates" name="end_date">'''.format(fmt_start))
    for date_str, fmt_date in html_range:
        if date_str == end_date:                       
            target.write('<option selected value="{0}">{1}</option>\n'.format(date_str, fmt_date))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(date_str, fmt_date))

    target.write('''</select></td></tr>
    <tr><td class="main" colspan="4">If Location is "Other" specify here: <input type="text" size="30" maxlength="50" name="text_location" value="{0}"></td></tr>
    <tr><td class="main" colspan="4" align="center">To show the location in the calendar page, select "Yes" from the menu below. <br/>'''.format(insert_fmt['text_location']))    

    target.write('<b>Show Location: </b>\n<select class="select_options" name="show_loc">')

    for key in opt_match:
        #default to no-show on location
        if key == 'Off':
            target.write('<option selected value="Off">No</option>\n')        
        elif key == 'On':
            target.write('<option value="On">Yes</option>\n')
    target.write('</select></td></tr>')

    target.write('''<tr><td class="main" colspan="4" align="center"><input type="hidden" name="start_date" value="{0}">
    <input type="hidden" name="end_date" value="{1}">
    <input type="hidden" name="ID" value="{2}">
    <input type="submit" name="Submit_New" value="Submit"/>
    </td></tr></form>
    <form action="{3}" method="post">
    <tr><td colspan="4"><input type="submit" name="Cancel" value="Cancel"/></td></tr></table>
    </form></body></html>\n'''.format(start_date, end_date, ID, actcon_this_month))    

    target.close()    

def db_events(start_date, end_date, events_all, ID):

    target = open(act_edit, 'a')  
    '''events_all[ID] = Event_Start, Activity, Event_End, Event_Location, Show_Loc]
    on load, use db entries except for end_date (a range); on submit, use insert_fmt entries 
    activity = events_all['activity'].encode('utf-8') fails; use insert_fmt.'''

    for eid in events_all:
        if eid == ID:
            time_start = events_all[eid][0]
            event_activity = events_all[eid][1]
            time_end = events_all[eid][2]
            event_location = events_all[eid][3]
            event_showloc = events_all[eid][4]
            hour_start = time_start[-5:]
            hour_end = time_end[-5:] 
            text_location = get_form_location(location_options, event_location)
            target.write('<tr><td class="main" align="center"><input type="text" size="35" maxlength="50" name="activity" value="{0}" /></td>\n'.format(event_activity))

            target.write('<td class="main" align="center"><select class="select_menu" name="menu_location">')
            for k in location_list:
                for key in location_options:
                    if key == k:
                        if event_location == location_options[key]:
                            target.write('<option selected value="{0}">{1}</option>\n'.format(key, location_options[key]))
                        elif sub_flds['menu_location'] == key:  
                            target.write('<option selected value="{0}">{1}</option>\n'.format(key, location_options[key]))
                        elif sub_flds['menu_location'] == location_options[key]:
                            target.write('<option selected value="{0}">{1}</option>\n'.format(key, location_options[key]))
                        else:
                            target.write('<option value="{0}">{1}</option>\n'.format(key, location_options[key]))
            target.write('</select>')
            target.write('</td>\n')             

            target.write('<td class="main" align="center"><b>Start time:</b>&nbsp;<select class="select_times" name="time_start">')
            for time_24, fmt_time in time_tuples: 
                if time_24 == hour_start:
                    target.write('<option selected value="{0}">{1}</option>\n'.format(time_24, fmt_time))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(time_24, fmt_time))
            target.write('</select><br/>')

            target.write('<b>End time:</b><br/><select class="select_times" name="time_end">\n')
            for time_24, fmt_time in time_tuples:  
                if time_24 == hour_end:
                    target.write('<option selected value="{0}">{1}</option>\n'.format(time_24, fmt_time))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(time_24, fmt_time))
            target.write('</select></td>')

            #Adding end dates, use a 90-day window
            target.write('<td class="main" align="center"><b>Start date: </b><br/>{0}<br/>'.format(fmt_start))
            target.write('<br/><b>End date: </b>\n<select class="select_dates" name="end_date">')
            for date_option, fmt_date in html_range:
                #loading an ID, the end date == the start date; use defaults
                if date_option == end_date:                     
                    target.write('<option selected value="{0}">{1}</option>\n'.format(date_option, fmt_date))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(date_option, fmt_date))

            target.write('''</select></td><tr><td class="main" colspan="4" align="center">To show the location in the calendar page, select "Yes" from the menu below. <br/>''')    

            target.write('<b>Show Location: </b>\n<select class="select_options" name="show_loc">')

            for key in opt_match:
                if key == event_showloc:
                    target.write('<option selected value="{0}">{1}</option>\n'.format(key, opt_match[key]))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(key, opt_match[key]))
            target.write('</select></td></tr>')

            target.write('''
            <tr><td class="main" colspan="4">If Location is "Other" specify here: <input type="text" size="30" maxlength="50" name="text_location" value="{0}"></td></tr>
            <tr><td class="main" colspan="4" align="center"><input type="hidden" name="start_date" value="{1}">
            <input type="hidden" name="end_date" value="{2}">
            <input type="hidden" name="ID" value="{3}">
            <input type="submit" name="Submit_Edit" value="Submit"/>
            <input type="submit" name="Delete" value="Delete"/></td></tr></form>
            <form action="{4}" method="post">
            <tr><td colspan="4"><input type="submit" name="Cancel" value="Cancel"/></td></tr></table>
            </form></body></html>\n'''.format(text_location, start_date, end_date, ID, actcon_this_month))     
            target.close()  


def edit_day(start_date, title_msg, end_date, events_all, ID):

    edit_acthead = os.path.join(base_path, 'calendar/forms/edit_acthead.html')
    target = open(act_edit, 'w')  
    try:
        shutil.copyfileobj(open(edit_acthead, 'rb'), target)

    except IOError:
        print('Could not read the management form! Please contact {0}'.format(email_from))
        sys.exit(1)      

    target.close()

    if ID != '':   
        db_events(start_date, end_date, events_all, ID)

    else:
        sub_events(start_date, end_date, ID)

    try:      
        t = Template(open(act_edit).read())
        print(t.substitute(start_date=start_date,month_path=actcon_this_month,title_msg=title_msg))

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)          


def confirm_page(f1, f2, title_msg):   
    
    act_confirm = os.path.join(base_path, 'calendar/control/activity/act_confirm.html')
    confirm_actheader = os.path.join(base_path, 'calendar/forms/confirm_actheader.html')

    target = open(act_confirm, 'w')

    try:
        shutil.copyfileobj(open(confirm_actheader, 'rb'), target)

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)         

    #end nested table, add footer 
    target.write('<tr><td class="main" colspan="4" align="center">Reload the calendar month page(s) as needed to view your changes.</td></tr></table>\n')             
    target.write('<table align="center"><tr><td>\n<form action="{0}" method="post">\n'.format(actcon_this_month))
    target.write('<input type="Submit" name="Submit1" value="Return"></form></td></tr></table></body></html>\n')               
    target.close()              

    try:      
        t = Template(open(act_confirm).read())
        print(t.substitute(title_msg=title_msg,month_path=actcon_this_month))

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)  
        
    for m in [f1, f2]:
        #limited to 2 months, enough for now
        dtg = m.replace(day=1)
        month_start = datetime.datetime.strftime(dtg, '%Y-%m-%d')
        #act_mgmt will copy the headers and retrieve sqlite data
        act_mgmt.copy_header(dtg, month_start)    
    
    mail_list = []
    mail_msg = title_msg.replace('<br/>', '\n')
    mail_list.append(mail_msg)
    #print mail_list  #utf-8 works in mail_path              
    email_envoi = open(mail_path, 'w')
    email_subject = 'Change in SHC Calendar Activity'
    email_message = '\n'.join(mail_list) 
    email_envoi.write(email_message)
    email_envoi.write('\n')
    email_envoi.close()
    #email_out.send_email(email_from, email_to, email_subject)         

if __name__ == "__main__":

    print "Content-type: text/html; charset=utf-8\n" 

    start_date = form.getvalue('start_date')
    end_date = form.getvalue('start_date')
    ID = form.getvalue('ID')
    events_all = load_db()    

    f1 = datetime.datetime.strptime(start_date, '%Y-%m-%d').date() 
    f1_weekday = f1.strftime('%A')
    fmt_start = f1.strftime("%-d %B %Y")
    time_tuples = gen_time(f1)
    html_range = html_options(f1) 
    month_name = f1.strftime("%B")  
    abs_paths = ['actopen_abs', 'actcon_abs']
    act_edit = os.path.join(base_path, 'calendar/control/activity/act_edit.html')
    actcon_this_month = '/shc/calendar/control/activity/{0}/{1}.html'.format(f1.year, month_name)           

    if 'Submit_New' in form:

        sub_flds = read_form(fields=fields)
        insert_fmt = fmt_utf8(sub_flds)   
        start_date = sub_flds['start_date']
        end_date = sub_flds['end_date']
        f1 = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        f2 = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        fmt_start = f1.strftime("%-d %B %Y") 
        fmt_end = f2.strftime("%-d %B %Y") 
        date_range = gen_range(f1, f2)
        #f2 > f1 to build date range; does not evaluate start and end times w/in same date !      
        activity = insert_fmt['activity']
        location = get_location(sub_flds, insert_fmt) 
        show_loc = sub_flds['show_loc']
        errors = check_errs(events_all, sub_flds, insert_fmt, action='new')
        title_messages = []

        if len(errors) > 0:
            title_msg = '<br/>'.join(errors)     
            edit_day(start_date, title_msg, end_date, events_all='', ID='')  

        else:
            if len(date_range) == 1:
                #one date to insert; use these time vars 
                ts_str = '{0} {1}'.format(start_date, sub_flds['time_start'])
                ts_obj = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M')   
                ts_fmt = datetime.datetime.strftime(ts_obj, '%-I:%M %p') 
                te_str = '{0} {1}'.format(end_date, sub_flds['time_end'])
                te_obj = datetime.datetime.strptime(te_str, '%Y-%m-%d %H:%M')
                te_fmt = datetime.datetime.strftime(te_obj, '%-I:%M %p')                     
                dup = detect_dups(events_all, activity, dts)
                if len(dup) == 0:
                    insert_activity(ts_str, activity, te_str, location, show_loc)

                    title_msg = ('You have inserted the following activity:<br/>{0} - {1}<br/>{2}<br/>Location: {3} <br/>on {4} {5}'.format(ts_fmt, te_fmt, activity, location, f1_weekday, fmt_start))  

                    confirm_page(f1, f2, title_msg)               

            elif len(date_range) > 1:
                for dts in date_range:
                    #keep start, end times tied to the same date!
                    ts_str = '{0} {1}'.format(dts, sub_flds['time_start'])
                    ts_obj = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M')   
                    ts_fmt = datetime.datetime.strftime(ts_obj, '%-I:%M %p') 
                    te_str = '{0} {1}'.format(dts, sub_flds['time_end'])
                    te_obj = datetime.datetime.strptime(te_str, '%Y-%m-%d %H:%M')            
                    te_fmt = datetime.datetime.strftime(te_obj, '%-I:%M %p') 
                    dup = detect_dups(events_all, activity, dts)
                    if len(dup) > 0:
                        eid = dup[0]
                        #update the records by eid; matches date and activity name... 
                        update_activity(ts_str, activity, te_str, location, show_loc, ID=eid)

                        title_messages.append('You have edited the following activity:<br/>{0} - {1}<br/>{2}<br/>Location: {3} <br/>from {4} {5} - {6} {7}'.format(ts_fmt, te_fmt, activity, location, f1_weekday, fmt_start, f1_weekday, fmt_end))         

                    else:
                        #insert the records by dts
                        insert_activity(ts_str, activity, te_str, location, show_loc)

                        title_messages.append('You have edited the following activity:<br/>{0} - {1}<br/>{2}<br/>Location: {3} <br/>from {4} {5} - {6} {7}'.format(ts_fmt, te_fmt, activity, location, f1_weekday, fmt_start, f1_weekday, fmt_end))       

        title_msg = title_messages[0]
        confirm_page(f1, f2, title_msg)                                                            

    elif 'Submit_Edit' in form:  

        sub_flds = read_form(fields=fields)
        insert_fmt = fmt_utf8(sub_flds)
        #on load, the end date = the start date
        start_date = sub_flds['start_date']
        end_date = sub_flds['end_date']
        f1 = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        f2 = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        fmt_start = f1.strftime("%-d %B %Y")   
        fmt_end = f2.strftime("%-d %B %Y")   
        date_range = gen_range(f1, f2)
        ts_str = '{0} {1}'.format(start_date, sub_flds['time_start'])
        ts_obj = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M')   
        ts_fmt = datetime.datetime.strftime(ts_obj, '%-I:%M %p') 
        te_str = '{0} {1}'.format(end_date, sub_flds['time_end'])
        te_obj = datetime.datetime.strptime(te_str, '%Y-%m-%d %H:%M')
        te_fmt = datetime.datetime.strftime(te_obj, '%-I:%M %p')     
        activity = insert_fmt['activity']
        location = get_location(sub_flds, insert_fmt) 
        show_loc = sub_flds['show_loc']
        errors = check_errs(events_all, sub_flds, insert_fmt, action='edit')
        title_messages = []

        if len(errors) > 0:
            title_msg = '<br/>'.join(errors)     
            edit_day(start_date, title_msg, end_date, events_all, ID)  

        else:
            if len(date_range) == 1:   

                update_activity(ts_str, activity, te_str, location, show_loc, ID) 
                title_msg = ('You have edited the following activity:<br/>{0} - {1}<br/>{2}<br/>Location: {3} <br/>on {4} {5}'.format(ts_fmt, te_fmt, activity, location, f1_weekday, fmt_start))  

                confirm_page(f1, f2, title_msg)                

            elif len(date_range) > 1:

                for dts in date_range:
                    ts_str = '{0} {1}'.format(dts, sub_flds['time_start'])
                    ts_obj = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M')   
                    ts_fmt = datetime.datetime.strftime(ts_obj, '%-I:%M %p') 
                    te_str = '{0} {1}'.format(dts, sub_flds['time_end'])
                    te_obj = datetime.datetime.strptime(te_str, '%Y-%m-%d %H:%M')
                    te_fmt = datetime.datetime.strftime(te_obj, '%-I:%M %p')                  

                    dup = detect_dups(events_all, activity, dts) 
                    if len(dup) > 0:
                        eid = dup[0]
                        update_activity(ts_str, activity, te_str, location, show_loc, ID=eid)

                        title_messages.append('You have edited the following activity:<br/>{0} - {1}<br/>{2}<br/>Location: {3} <br/>from {4} {5} - {6} {7}'.format(ts_fmt, te_fmt, activity, location, f1_weekday, fmt_start, f1_weekday, fmt_end))         

                    elif len(dup) == 0:
                        #insert the records for date range (f2 > f1); 
                        insert_activity(ts_str, activity, te_str, location, show_loc)

                        title_messages.append('You have edited the following activity:<br/>{0} - {1}<br/>{2}<br/>Location: {3} <br/>from {4} {5} - {6} {7}'.format(ts_fmt, te_fmt, activity, location, f1_weekday, fmt_start, f1_weekday, fmt_end))  

        title_msg = title_messages[0]
        confirm_page(f1, f2, title_msg)                    


    elif 'Delete' in form:

        sub_flds = read_form(fields=fields)
        start_date = sub_flds['start_date']
        end_date = sub_flds['end_date']
        f1 = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        f2 = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        fmt_start = f1.strftime("%-d %B %Y")   
        fmt_end = f2.strftime("%-d %B %Y")   
        date_range = gen_range(f1, f2)
        #these vars are used for the confirmation message
        ts_str = '{0} {1}'.format(start_date, sub_flds['time_start'])
        ts_obj = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M')   
        ts_fmt = datetime.datetime.strftime(ts_obj, '%-I:%M %p') 
        te_str = '{0} {1}'.format(end_date, sub_flds['time_end'])
        te_obj = datetime.datetime.strptime(te_str, '%Y-%m-%d %H:%M')
        te_fmt = datetime.datetime.strftime(te_obj, '%-I:%M %p')   
        title_messages = []

        for dts in date_range:
            ts_str = '{0} {1}'.format(dts, sub_flds['time_start'])  
            ts_obj = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M')   
            for eid in events_all:
                db_start = events_all[eid][0]
                db_activity = events_all[eid][1]
                if db_start == ts_str and db_activity == sub_flds['activity']:
                    #one activity of the same name per start date
                    delete_row(eid)

                    if f1 == f2:
                        title_messages.append('You have deleted the following activity:<br/>{0} - {1} <br/>{2}<br/>on {3} {4}'.format(ts_fmt, te_fmt, db_activity, f1_weekday, fmt_start))

                    else:
                        title_messages.append('You have deleted the following activity:<br/>{0} - {1}<br/>{2}<br/>from {3} {4} - {5} {6}'.format(ts_fmt, te_fmt, db_activity, f1_weekday, fmt_start, f1_weekday, fmt_end))

        title_msg = title_messages[0]               
        confirm_page(f1, f2, title_msg)

    else:
        if ID:   
            title_msg = ('''You may edit the activity below on {0} {1}.<br/>If the activity spans multiple weeks, select an ending date (the date range is applied weekly but not daily).'''.format(f1_weekday, fmt_start)) 
            edit_day(start_date, title_msg, end_date, events_all, ID)        

        else:
            title_msg = ('''You may add an activity to the schedule starting on {0} {1}. <br/> 
                            Please complete all fields that apply.'''.format(f1_weekday, fmt_start)) 
            edit_day(start_date, title_msg, end_date, events_all='', ID='')
