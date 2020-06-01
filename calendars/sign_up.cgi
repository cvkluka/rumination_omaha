#!/usr/bin/python
# coding: utf-8

import os
import sys
from string import Template
import sqlite3 as sqlite
import shutil
import datetime
from datetime import timedelta
import cgi

from config_cal import web_path, db_sign, mail_path, email_from, email_to
from config_alert import sign_header, sign_up, sign_re, sign_switch, sign_form, sign_confirm, correlate, relaciones, positions

form = cgi.FieldStorage()
fields = {}  

'''build (sign_field?) dict with position data passed from lem.cgi; correlate dict matches for the selected position 
(imported); the initial sign_up.html has 2 Submits: New and User, and
a Contact field used for the User email or sms; the follow-up sign_form.html has 1 Submit: New_Reg; '''

#form values read by read_form(**kw); #some values are obtained from the db (example: uid)
form_list = ['status', 'Contact', 'DTG', 'HD', 'Position', 'First_Name', 'Last_Name', 'Notify', 'User_First', 'User_Last', 'Email', 'Cell', 'Provider', 'TextMsg'] 
providers = ['ATT', 'GCI-ACS', 'GCI','Sprint','T-Mobile', 'Verizon']
map_pv = {'Select a Provider':'Select','ATT':'ATT','GCI':'GCI','Sprint':'Sprint','T-Mobile':'T-Mobile','Verizon':'Verizon'}
sub_flds = {'status':'', 'Contact':'', 'DTG':'', 'HD':'', 'Position':'', 'First_Name':'', 'Last_Name':'', 'Notify':'', 'User_First':'', 'User_Last':'', 'Email':'', 'Cell':'', 'Provider':'', 'TextMsg':''}
    
def gen_time(f1):
    
    #support events at 15' past the hour and pre-pend dtg to the time, ex: 2017-05-22 07:30:00   
    time_tuples = [] 
    f1_time_start = datetime.datetime.combine(f1, datetime.time(8, 0)) 
    f1_time_end = datetime.datetime.combine(f1, datetime.time(22, 45))   
    
    def datetime_range(start, end, delta):
        current = start
        while current < end:
            yield current
            current += delta    
    
    for dt in datetime_range(f1_time_start, f1_time_end, timedelta(minutes=15)):
        #time_str = datetime.datetime.strftime(dt, '%Y-%m-%d %H:%M')
        hour_str = datetime.datetime.strftime(dt, '%H:%M')
        fmt_time = datetime.datetime.strftime(dt, '%-I:%M %p')
        time_tuples.append((hour_str, fmt_time))
        
    time_tuples = sorted(time_tuples)   
        
    return time_tuples
          

def build_sms(sub_flds):
       
    sms = ''
    
    if sub_flds['Provider'] == 'GCI':
        #tested 1/06/2015 w/ built-in reply capability; default '@mobile.gci.net' fails on script-generated source
        sms = ('{0}@mms.gci.net'.format(sub_flds['Cell'] )) 
           
    elif sub_flds['Provider'] == 'ATT':
        sms = ('{0}@txt.att.net'.format(sub_flds['Cell'] ))
        
    elif sub_flds['Provider'] == 'Sprint':
        sms = ('{0}@messaging.sprintpcs.com'.format(sub_flds['Cell'] ))
                
    elif sub_flds['Provider'] == 'T-Mobile':
        sms = ('{0}@tmomail.net'.format(sub_flds['Cell'] )) 
        
    elif sub_flds['Provider'] == 'Verizon':
        sms = ('{0}@vtext.com'.format(sub_flds['Cell'] ))     
          
    return sms


def min_list(sub_flds, db_contact, max_UID, status):
    
    db_min = []   
    
    if status == 'User':
        db_min = []     
        db_min.append(db_contact['UID'])
        for sub in ['DTG', 'HD', 'Position', 'User_First', 'User_Last']:  
            db_min.append(sub_flds[sub])
        #Add Notify (cell or email) from alerts table
        db_min.append(db_contact['Alerts'])     
    
    else:
        db_min.append(max_UID)
        for sub in ['DTG', 'HD', 'Position', 'First_Name', 'Last_Name', 'Notify']:
            db_min.append(sub_flds[sub])
       
    return db_min 

def alert_list(max_UID, sub_flds, sms, status):
    
    db_alert = []        
    #alerts table schema = UID, FN, LN, Notify, Email, Cell, TextMsg; add row for new users    
    
    if status == 'User':
        pass
    
    else: 
    
        for value in [max_UID, sub_flds['First_Name'], sub_flds['Last_Name'], sub_flds['Notify'], sub_flds['Email'], sub_flds['Cell'], sms]: 
            db_alert.append(value)  
        
    return db_alert
    
    

def check_rows(sub_flds):
    
    #check for duplication; then build lists to insert db rows    
    ministry_check = []
    alert_check = []
    fn = sub_flds['User_First']
    ln = sub_flds['User_Last']
    
    try:
        con = sqlite.connect(db_sign)
        cursor = con.cursor() 
        cursor.execute("SELECT ID, DTG, Position FROM ministry")
        rows = cursor.fetchall()
        for row in rows:
            if row[1] == sub_flds['DTG'] and row[2] == sub_flds['Position']:
                ministry_check.append('Duplicate entry!')                   
        con.commit()
        con.close() 
    
    except sqlite.Error, e:
        print "<br/>Failed to connect to the ministry table (to identify possible duplication)."
        sys.exit(1)  
        
    try:
        con = sqlite.connect(db_sign)
        cursor = con.cursor()
        cursor.execute("SELECT First_Name, Last_Name FROM alerts WHERE First_Name=? AND Last_Name=?", (fn, ln))
        row = cursor.fetchone()
        if row:
            alert_check.append('Duplicate entry!')
        con.commit()
        con.close()
        
    except sqlite.Error, e:
        print "<br/>Failed to connect to the alerts table (to identify possible duplication)."
        sys.exit(1) 
        
    return ministry_check, alert_check
    

def read_form(**kw):
    
    fields = kw.get('fields', {})
    
    #read values into the form fields dict
    for field in form_list:
        if isinstance(form.getvalue(field), list):
            fields[field] = form.getfirst(field)
        else:
            fields[field] = form.getvalue(field)

        if form.getvalue(field) == None:
            fields[field] = '' 
            
        #store form values in sub_flds  
        for sub in sub_flds:
            if sub == field:
                sub_flds[sub] = fields[field]
                if sub_flds[sub] != '':
                    sub_flds[sub] = sub_flds[sub].strip()
                
                    if sub in ['First_Name', 'Last_Name', 'User_First', 'User_Last']:
                        sub_flds[sub] = sub_flds[sub].title()
                    
                    elif sub == 'Cell':
                        value = sub_flds['Cell']
                        sub_flds['Cell'] = ''.join(char for char in value if char.isdigit())
                    
                    elif sub == 'Contact':
                        value = sub_flds['Contact']
                        if value[-1].isdigit():
                            sub_flds['Contact'] = ''.join(char for char in value if char.isdigit())                    
                           
    '''html form has four keys to pass; 3 here, last one in form_args()
    <input type="hidden" name="DTG" value="${DTG}">
    <input type="hidden" name="HD" value="${HD}">
    <input type="hidden" name="Position" value="${Position}">
    <input type="hidden" name="mass_lem" value="${mass_lem}">'''    
    
    return sub_flds
                                                                

def form_args(dtg, sub_flds):
    
    full_list = []
    day_only = dtg.date()
    format_date = day_only.strftime("%-d %B %Y")  
    mass = dtg.strftime("%H:%M")            
    
    full_list.append('on {0}'.format(format_date))
        
    if sub_flds['HD'] not in ['not', '']:
        rep_val = sub_flds['HD'].replace('_', ' ')   
        full_list.append(' {0}'.format(rep_val))
    
    #24-hour format; format the mass time in am/pm; using time_tuples (hour_str, fmt_time)
    time_tuples = gen_time(f1=dtg)
    for hour_str, fmt_time in time_tuples:
        if hour_str == mass:        
            full_list.append(' at {0}'.format(fmt_time))   
            
    #positions dict provides pnt-friendly names for position values
    for key in positions:
        if key == sub_flds['Position']:
            full_list.append(' as {0}'.format(positions[key]))    
    
    return full_list

def get_values(sub_flds):
    
    keys = ['Notify', 'Email', 'Cell', 'Provider']
    sub_values = []
    
    for key in keys:
        for sub in sub_flds:
            if sub == key:
                sub_values.append(sub_flds[sub])
            
    return sub_values
        
                                            
def check_errs(sub_flds, db_contact, db_alert, ministry_check, alert_check, status):
    
    #status options: 'Start_New', 'New_Reg', 'User', 'Fin_Reg'
    errors = []
               
    if status == 'Start_New':
            
        if sub_flds['First_Name'] in ['First Name', '']:
            errors.append('First name is invalid.')        
                        
        if sub_flds['Last_Name'] in ['Last Name', '']:
            errors.append('Last name is invalid.')   
        
        if sub_flds['Notify'] in ['Select', 'Select a notification method']:
            errors.append('Please select a notification method')
            
        if sub_flds['First_Name'] == db_contact['First_Name'] and sub_flds['Last_Name'] == db_contact['Last_Name']:
            errors.append('{0} {1} is already registered!'.format(sub_flds['First_Name'], sub_flds['Last_Name']))           
            
            
    elif status == 'New_Reg':          
        
        if sub_flds['First_Name'] in ['First Name', '']:
            errors.append('First name is invalid.')        
                        
        if sub_flds['Last_Name'] in ['Last Name', '']:
            errors.append('Last name is invalid.')   
    
        if sub_flds['Notify'] in ['Select', 'Select a notification method']:
            errors.append('Please select a notification method')        
        
            
    elif status == 'Fin_Reg':
    
        sub_values = get_values(sub_flds)
        #keys = ['Notify', 'Email', 'Cell', 'Provider']; Provider_value = sub_values[3]
        if sub_values[0] == 'Email':
            if sub_values[1] == '':
                errors.append('Please provide an email address for notification.')
        
        elif sub_values[0] == 'Cell':
            if len(sub_values[2]) < 10: 
                errors.append('Please check the cellphone number - it must include an area code.') 
            
            if sub_values[3] not in providers:
                errors.append('Please select a provider for notification.') 
            
        if len(ministry_check) > 0 and len(alert_check) > 0:
            errors.append('Duplicate entry!') 
                    
            
    elif status == 'User':
        
        if db_contact['UID'] in ['', 0]:
            errors.append('User not registered.')
            
        if len(ministry_check) > 0 and len(alert_check) > 0:
            errors.append('Duplicate row in ministry table.') 
                                           
        if sub_flds['User_First'] in ['First Name', '']:
            errors.append('First name is invalid.')     
                        
        if sub_flds['User_Last'] in ['Last Name', '']:
            errors.append('Last name is invalid.')  
            
        if sub_flds['User_First'] != db_contact['First_Name'] and sub_flds['User_Last'] != db_contact['Last_Name']:
            errors.append('User name not found.') 
            
        if sub_flds['Contact'] in ['', '(limit to one entry)']:
            errors.append('Please complete your contact information')
               
    return errors
                           
def alerts_table(fn, ln):
    
    #the names lookup varies based on whether the user is new or registered; use status to check 
    alert_table = ['UID', 'First_Name', 'Last_Name', 'Alerts', 'Email', 'Cell', 'SMS']
    db_lookup = []
    db_contact = {'UID':'', 'First_Name':'', 'Last_Name':'', 'Alerts':'', 'Email':'', 'Cell':'', 'SMS':''}

    try:
        con = sqlite.connect(db_sign)
        cursor = con.cursor()   
        cursor.execute("SELECT UID, First_Name, Last_Name, Alerts, Email, Cell, TextMsg FROM alerts WHERE First_Name=? AND Last_Name=?", (fn, ln))
        row = cursor.fetchone()
        if row:
            for column_value in row:
                db_lookup.append(str(column_value))
        con.commit()
        con.close()

    except sqlite.Error, e:
        sys.exit(1) 
      
    for index, column_name in enumerate(alert_table):
        for i, column_value in enumerate(db_lookup):
            if i == index:
                db_contact[column_name] = column_value
                
    return db_contact


def calc_uid():
    
    max_UID = 0
    
    try:
        con = sqlite.connect(db_sign)
        cursor = con.cursor() 
        cursor.execute("SELECT max(UID) from alerts")
        row = cursor.fetchone()
        if row:
            UID = int(row[0]) 
        con.commit()
        con.close()
                
    except sqlite.Error, e:
        sys.exit(1)
    
    if UID != int(UID):
        pass
    else:
        max_UID = UID + 1
    
    return max_UID   
        
  
def insert_mins(db_min):
    
    #insert new row in the ministry table to hold information on when users will serve and how to notify them (cell/email)
    try:
        con = sqlite.connect(db_sign)
        cursor = con.cursor() 
        cursor.execute("INSERT INTO ministry (UID, DTG, Holy_Day, Position, First_Name, Last_Name, Notify) VALUES (?,?,?,?,?,?,?)", db_min) 
        con.commit()
        con.close()                   

    except sqlite.Error, e:
        print "<br/>Error failed to insert record!" #print db_min, len(db_min)#insertion succeeds at the command line
        sys.exit(1)

def insert_alerts(db_alert):
    
    #insert new row in the alerts table to hold contact information for each new volunteer  
    try:
        con = sqlite.connect(db_sign)
        cursor = con.cursor()  
        cursor.execute("INSERT INTO alerts (UID, First_Name, Last_Name, Alerts, Email, Cell, TextMsg) VALUES (?,?,?,?,?,?,?)", db_alert)
        con.commit()
        con.close() 
        
    except sqlite.Error, e:
        print "<br/>Error failed to create new alerts table row", db_alert
        sys.exit(1)
        
    
#Next functions to pnt the html page #############################################################

def gen_cell(sub_flds):

    target = open(sign_form, 'w')    
                     
    try:
        shutil.copyfileobj(open(sign_header, 'rb'), target)
    
    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from, True)) 
        sys.exit(1) 
    
    target.write('<tr>')
    for k in ['First_Name', 'Last_Name', 'Cell', 'Provider']:
        pname = k.replace('_', ' ')     
        if k == 'First_Name':
            target.write('<td class="main" align="center">{0}<br/><input type="text" name="{1}" value="{2}"></td>\n'.format(pname, k, sub_flds[k])) 
        elif k == 'Last_Name':
            target.write('<td class="main" align="center">{0}<br/><input type="text" name="{1}" value="{2}"></td></tr>\n'.format(pname, k, sub_flds[k]))                 
        elif k == 'Cell':
            target.write('<tr><td class="main" align="center">Cell Phone Number <br/>(example: 9071114444) <br/> \
             <input type="text" name="Cell" value="{0}" maxlength="15"></td>\n'.format(sub_flds[k]))             
            
        elif k == 'Provider':
            target.write('<td class="main" align="center">Provider <br/> <select name="Provider" style="font-family:Helvetica Neue, Helvetica, Arial, sans-serif; font-size:12px">)\n')      
            for option in ['Select a Provider','ATT','GCI','Sprint','T-Mobile','Verizon']:
                option_value = map_pv[option]
                if sub_flds['Provider'] == option_value:
                    target.write('<option selected value="{0}">{1}</option>\n'.format(option_value, option))
                else:
                    target.write('<option value="{0}">{1}</option>\n'.format(option_value, option))
            target.write('</select></td></tr>\n')
                              
    target.write('''<tr><td class="main" colspan="3" align="center">
        <input type="submit" name="Fin_Reg" value="Submit"/></td></tr></table></form>
        <form action="{0}" method="post">
        <table width="600" align="center"><tr><td align="center">
        <input type="submit" value="Cancel" name="Cancel" /></td></tr></table></form></body></html>'''.format(month_path))           
    target.close()
    
def gen_mail(sub_flds):
    
    target = open(sign_form, 'w')

    try:
        shutil.copyfileobj(open(sign_header, 'rb'), target)
    
    except IOError:
        print 'Could not read the form! Please contact {0}'.format(email_from)
        sys.exit(1) 
        
    target.write('<tr>')
    for k in ['First_Name', 'Last_Name', 'Email', 'Notify']:
        #for key in sub_flds: #if key == k:
        pname = k.replace('_', ' ')     
        if k == 'First_Name':
            target.write('<td class="main" align="center">{0}<br/><input type="text" name="{1}" value="{2}"></td>\n'.format(pname, k, sub_flds[k])) 
        elif k == 'Last_Name':
            target.write('<td class="main" align="center">{0}<br/><input type="text" name="{1}" value="{2}"></td></tr>\n'.format(pname, k, sub_flds[k]))                
        elif k == 'Email':
            target.write('<tr><td class="main" align="center">Email Address<br/><input type="text" size="30" maxlength="40" name="Email" value="{0}"></td>\n'.format(sub_flds[k]))
        elif k == 'Notify': 
            target.write('<td class="main" align="center">Notify by:<br/> Email</td></tr>\n')    

    target.write('''<tr><td class="main" colspan="3" align="center">
        <input type="submit" name="Fin_Reg" value="Submit"/></td></tr></table></form>
        <form action="{0}" method="post">
        <table width="600" align="center"><tr><td align="center">
        <input type="submit" value="Cancel" name="Cancel" /></td></tr></table></form></body></html>'''.format(month_path))           
    target.close()          
    target.close()
    
    
def confirmation_page(title_msg, title_end, mass_lem, month_path, mail_list, email_to):
    
    title_all = title_msg + title_end
    
    try:
        t = Template(open(sign_confirm).read())
        print(t.substitute(title_msg=title_all,mass_lem=mass_lem,month_path=month_path))
    
    except IOError:
        print 'Could not open form! Please contact {0}'.format(email_from)
        sys.exit(1)  
    
    fn_ln = ' '.join(mail_list) 
    email_envoi = open(mail_path, 'w')
    email_subject = 'Lay Ministry Sign-Up for {0}'.format(fn_ln)
    email_msg = title_msg.replace('<br/>', '\n')     
    email_envoi.write(email_msg)
    email_envoi.write('\n')
    email_envoi.close()
    email_out.send_email(email_from, email_to, email_subject)   
    
        
def start_sign(sub_flds, title_msg, month_path):
    
    #the sequence: this loads the page with default values but on submit, defaults are lost :-)
    defaults = {'status':'Start', 'First_Name':'First Name', 'Last_Name':'Last Name', 'User_First':'First Name', 'User_Last':'Last Name'}
    
    for key in defaults:
        for sub in sub_flds:
            if sub == key:
                sub_flds[sub] = defaults[key]
            
    #populate html hidden keys to load /shc/calendar/forms/sign_up.html
    DTG = sub_flds['DTG']
    Position = sub_flds['Position']
    HD = sub_flds['HD']
    
    try:
        t = Template(open(sign_up).read())
        print(t.substitute(sub_flds, month_path=month_path,title_msg=title_msg))

    except IOError:
        print 'Could not open form! Please contact {0}'.format(email_from)
        sys.exit(1)   
        
def load_options(error_str):
    
    load_switch = []
    match_errors = ['not found', 'already registered']
      
    for e in match_errors:
        if e in error_str:
            load_switch.append('1')
            
        else:
            load_switch.append('0')
            
    return load_switch
            
        
        
def restart_page(sub_flds, month_path, title_msg, error_str):
    
    #form hidden values: DTG and Position in the html form; used for input errors?
    DTG = sub_flds['DTG']
    Position = sub_flds['Position']
    HD = sub_flds['HD']  
    load_switch = load_options(error_str)
    
    if '1' in load_switch:
        try:
            t = Template(open(sign_switch).read())
            print(t.substitute(sub_flds,month_path=month_path,title_msg=title_msg))
    
        except IOError:
            print 'Could not open form! Please contact {0}'.format(email_from)
            sys.exit(1)    
            
    else:
        try:
            t = Template(open(sign_re).read())
            print(t.substitute(sub_flds,month_path=month_path,title_msg=title_msg))
    
        except IOError:
            print 'Could not open form! Please contact {0}'.format(email_from)
            sys.exit(1)      
    
        
def signing_form(sub_flds, month_path, title_msg):
    
    try:
        t = Template(open(sign_form).read())
        print(t.substitute(sub_flds,month_path=month_path,title_msg=title_msg))

    except IOError:
        print 'Could not open form! Please contact {0}'.format(email_from)
        sys.exit(1)    
        
#the end ################################################################################

def seq_methods(fn, ln, sub_flds, dtg, mass_lem, title_str, status):
    
    time_tuples = gen_time(f1=dtg)       
    db_contact = alerts_table(fn, ln)
    sms = build_sms(sub_flds)   
    max_UID = calc_uid()
    db_min = min_list(sub_flds, db_contact, max_UID, status)
    db_alert = alert_list(max_UID, sub_flds, sms, status)
    ministry_check = check_rows(sub_flds)[0]
    alert_check = check_rows(sub_flds)[1]    
    errors = check_errs(sub_flds, db_contact, db_alert, ministry_check, alert_check, status)  
    mail_list = [fn, ln]      
    
    if status == 'User':
        
        if len(errors) > 0:
            
            error_str = '\n'.join(errors)
            
            if 'not found' in error_str:
                title_msg = ("{0} <br/>Please try again under the 'New User' part of this form.<br/>{1}".format(error_str, title_str))
                restart_page(sub_flds, mass_lem, title_msg, error_str)
                
            elif 'Duplicate entry' in error_str:
                title_msg = '{0} {1} is already signed up at mass <br/>{2}'.format(fn, ln, title_str)
                title_end = ''
                confirmation_page(title_msg, title_end, title_str, mass_lem, month_path, mail_list)            
                    
            else:
                title_msg = ' {0} </br>to serve at mass <br/>{1}'.format(error_str, title_str)
                restart_page(sub_flds, mass_lem, title_msg, error_str)
            
        else:
            #no errors, add registered user to ministry table service; do not change the alerts table
            insert_mins(db_min)     
                
            if sub_flds['Contact'] == db_contact['Cell']:
                title_msg = 'Thanks {0} {1} for signing up for mass <br/>{2}'.format(fn, ln, title_str)
                title_end = '<br/>We are sending a confirmation message to {0}.'.format(db_contact['SMS'])                      
                email_to.append(db_contact['SMS'])
                confirmation_page(title_msg, title_end, mass_lem, month_path, mail_list, email_to)   
                
            elif sub_flds['Contact'] == db_contact['Email']:
                title_msg = 'Thanks {0} {1} for signing up for mass <br/>{2}'.format(fn, ln, title_str)
                title_end = '<br/>We are sending a confirmation message to {0}.'.format(db_contact['Email'])                      
                email_to.append(db_contact['Email'])
                confirmation_page(title_msg, title_end, mass_lem, month_path, mail_list, email_to)      
               
            else: 
                title_msg = 'Thanks {0} {1} for signing up for mass <br/>{2}!'.format(fn, ln, title_str)
                title_end =  '<br/>Please contact the webmaster regarding your notification address {0}'.format(sub_flds['Contact'])
                confirmation_page(title_msg, title_end, mass_lem, month_path, mail_list, email_to) 
                    
    elif status == 'Start_New':
        
        if len(errors) > 0:
            error_str = '\n'.join(errors)
            
            if 'already registered' in error_str:
                title_msg = ("{0} Please try again under the 'Already signed up' part of this form.".format(error_str))
                restart_page(sub_flds, mass_lem, title_msg, error_str)
                
            elif 'Duplicate entry' in error_str:
                title_msg = '{0} {1} is already signed up at mass <br/>{2}'.format(fn, ln, title_str) 
                title_end = ''
                confirmation_page(title_msg, title_end, mass_lem, month_path, mail_list, email_to)       
                
            else:
                title_msg = ' {0} </br>to serve at mass <br/>{1}'.format(error_str, title_str)
                restart_page(sub_flds, mass_lem, title_msg, error_str)
            
        else:
            #proceed to get information from new user
            if sub_flds['Notify'] == 'Email':
                gen_mail(sub_flds)
                title_msg = ('Please complete this form to receive a confirmation email for service at mass <br/>{0}'.format(title_str))
                signing_form(sub_flds, month_path, title_msg)
                
            elif sub_flds['Notify'] == 'Cell':
                gen_cell(sub_flds)
                title_msg = ('Please complete this form to receive a confirmation text message for service at mass <br/>{0}'.format(title_str))
                signing_form(sub_flds, month_path, title_msg)            
                
    elif status == 'New_Reg':
        
        if len(errors) > 0:
            error_str = '\n'.join(errors)
                
            if 'Duplicate entry' in error_str:
                title_msg = '{0} {1} is already signed up at mass <br/>{2}'.format(fn, ln, title_str)
                title_end = ''
                confirmation_page(title_msg, title_end, mass_lem, month_path, mail_list, email_to)       
                    
            else:
                title_msg = ' {0} </br>to serve at mass <br/>{1}'.format(error_str, title_str)
                restart_page(sub_flds, mass_lem, title_msg, error_str)
               
        else:
            
            if sub_flds['Notify'] == 'Email':
                gen_mail(sub_flds)
                title_msg = ('Please complete this form to receive a confirmation email for service at mass <br/>{0}'.format(title_str))
                signing_form(sub_flds, month_path, title_msg)
                
            elif sub_flds['Notify'] == 'Cell':
                gen_cell(sub_flds)
                title_msg = ('Please complete this form to receive a confirmation text message for service at mass <br/>{0}'.format(title_str))
                signing_form(sub_flds, month_path, title_msg)   
                
    elif status == 'Fin_Reg':
                
        if len(errors) > 0:
            
            error_str = '\n'.join(errors)   
            #continue to get information from new user
            if sub_flds['Notify'] == 'Email':
                gen_mail(sub_flds)
                title_msg = ('{0}<br/>Please complete this form to receive a confirmation email for service at mass <br/>{1}'.format(error_str, title_str))
                signing_form(sub_flds, month_path, title_msg)
                
            elif sub_flds['Notify'] == 'Cell':
                gen_cell(sub_flds)
                title_msg = ('{0}<br/>Please complete this form to receive a confirmation text message for service at mass <br/>{1}'.format(error_str, title_str))
                signing_form(sub_flds, month_path, title_msg)                
                    
        else:
            #finalizing a new registration; 
            insert_mins(db_min) 
            insert_alerts(db_alert)
             
            if sub_flds['Notify'] == 'Cell' and sms != '':   
                title_msg = 'Thanks {0} {1} for signing up for mass <br/>{2}'.format(fn, ln, title_str)
                title_end = '<br/>We are sending a confirmation message to {0}.'.format(sms)                      
                email_to.append(sms)
                confirmation_page(title_msg, title_end, mass_lem, month_path, mail_list, email_to)   
                
            elif sub_flds['Notify']== 'Email' and sub_flds['Email'] != '':
                title_msg = 'Thanks {0} {1} for signing up for mass <br/>{2}'.format(fn, ln, title_str)
                title_end = '<br/>We are sending a confirmation message to {0}.'.format(sub_flds['Email'])                      
                email_to.append(db_contact['Email'])
                confirmation_page(title_msg, title_end, mass_lem, month_path, mail_list, email_to)      
               
            else: 
                title_msg = 'Thanks {0} {1} for signing up for mass <br/>{2}!'.format(fn, ln, title_str)
                title_end =  '<br/>Please contact the webmaster regarding your notification address {0} {1}'.format(sub_flds['Email'], sub_flds['Cell'])
                confirmation_page(title_msg, title_end, mass_lem, month_path, mail_list, email_to)     

                                      
if __name__ == "__main__":
    
    print "Content-type: text/html; charset=utf-8\n" 
    
    #'2017-06-25_11:00', using underscore to pass as arg;
    DTG = form.getvalue('DTG')
    dtg = datetime.datetime.strptime(DTG, '%Y-%m-%d_%H:%M')    
    sub_flds = read_form(fields=fields) 
    full_list = form_args(dtg, sub_flds)
    title_str = ' '.join(full_list)   
    mass_lem = ('/shc/akc/lem.cgi?DTG={0}&HD={1}&status=?'.format(DTG, sub_flds['HD'])) 
    month_path = '/shc/calendar/liturgy/{0}/{1}.html'.format(dtg.year, dtg.strftime("%B"))      
    
    if "User" in form:
        status = 'User'
        fn = sub_flds['User_First']
        ln = sub_flds['User_Last']    
        seq_methods(fn, ln, sub_flds, dtg, mass_lem, title_str, status)
        
    elif 'Start_New' in form:
        status = 'Start_New'
        fn = sub_flds['First_Name']
        ln = sub_flds['Last_Name']
        seq_methods(fn, ln, sub_flds, dtg, mass_lem, title_str, status)
        
    elif 'New_Reg' in form:
        #sign_switch.html, sign_re.html
        status = 'New_Reg'
        fn = sub_flds['First_Name']
        ln = sub_flds['Last_Name']
        seq_methods(fn, ln, sub_flds, dtg, mass_lem, title_str, status)
       
    elif 'Fin_Reg' in form:
        #sign_form.html; differs from New_Reg html pages
        status = 'Fin_Reg'
        fn = sub_flds['First_Name']
        ln = sub_flds['Last_Name']
        seq_methods(fn, ln, sub_flds, dtg, mass_lem, title_str, status)
        
    else:
        #default page should load at /shc/calendar/forms/control/sign_up.html
        title_msg = ('Please sign up for mass <br/>{0}'.format(title_str))
        start_sign(sub_flds, title_msg, month_path)
        