#!/usr/bin/python

import sys
import os

from string import Template
import shutil

import datetime 
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

import sqlite3 as sqlite
import cgi
#import cgitb
#cgitb.enable()

import lit_mgmt, act_mgmt
from config_cal import base_path, web_path, mail_path, HD_db, email_from

'''give user the option of introducing Holy Days; Event_Start time in lit_schedule table is a varchar, fix later'''

form = cgi.FieldStorage()
fields = {}
#date_observed not in form fields because it is calculated
sub_flds = {'hd_name':'', 'date_actual':'', 'month_observed':'', 'day_observed':''}
form_list = ['hd_name', 'date_actual', 'month_observed', 'day_observed']
            
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
                    sub_flds[sn] = value
                    
    return sub_flds


def read_table():
    
    hd_values = {}
    
    try:
        con = sqlite.connect(HD_db)
        cursor = con.cursor()
        cursor.execute("SELECT Holy_Day, Actual, Observed FROM hd_schedule")  
        rows = cursor.fetchall()
        for row in rows:
            HD_year = str(row[0])
            Actual_date = str(row[1])
            Observed_date = str(row[2])
            hd_values[Actual_date] = [HD_year, Observed_date]
        con.commit()
        con.close()
    
    except IOError:
        print('Could not open database. Please contact {0}'.format(email_from))
        sys.exit(1)
        
    return hd_values

def form_content(hd_values):
    
    cur_day = datetime.datetime.today()
    submit_dates = []    
    
    for dt in sorted(hd_values):
        Actual_date = datetime.datetime.strptime(dt, '%Y-%m-%d')
        Observed_date = datetime.datetime.strptime(hd_values[dt][1], '%Y-%m-%d')
        if Actual_date > cur_day:
            Observed_date = Observed_date.date()
            dt = datetime.datetime.strftime(Observed_date, '%Y-%m-%d')
            submit_dates.append(dt)  
            
    return submit_dates

def change_calendar(date_observed, hd_name):
    
    #sql = 'UPDATE hd_schedule SET Observed={0} WHERE Holy_Day={1}'.format(date_observed, hd_name)
    #print sql
     
    try:
        con = sqlite.connect(HD_db)
        cursor = con.cursor()
        cursor.execute("UPDATE hd_schedule SET Observed=? WHERE Holy_Day=?", (date_observed, hd_name))  
        con.commit()
        con.close()
    
    except IOError:
        print('Could not open database. Please contact {0}'.format(email_from))
        sys.exit(1)   
        

#============================ html pages =========================================================

def page_one(hd_values, title_msg):
    
    hd_edit = os.path.join(base_path, 'calendar/control/liturgy/hd_edit.html')
    hd_header_one = os.path.join(base_path, 'calendar/control/liturgy/hd_header_one.html')    
    cur_day = datetime.datetime.today().date()
    
    target = open(hd_edit, 'w')

    try:
        shutil.copyfileobj(open(hd_header_one, 'rb'), target)

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)            
    
    for dt in sorted(hd_values):
        date_actual = datetime.datetime.strptime(dt, '%Y-%m-%d').date()
        date_observed = datetime.datetime.strptime(hd_values[dt][1], '%Y-%m-%d').date()
        f1 = cur_day.replace(day=1)
        f2 = f1 + relativedelta(months=4)    
        if f1 <= date_actual <= f2:
            hd_name = hd_values[dt][0]
            hd_short = hd_name[:-5].replace('_', ' ')
            #hd_year = '({0})'.format(hd_name[-4:])
            hd_display = '{0}'.format(hd_short)
            fmt_actual = datetime.datetime.strftime(date_actual, '%-d %B %Y')
            fmt_observed = datetime.datetime.strftime(date_observed, '%-d %B %Y')
            weekday_actual = date_actual.strftime("%A")      
            weekday_observed = date_observed.strftime("%A")            
            
            target.write('''<tr><td class="headerc">{0}</td><td class="headerc" align="center">{1} <br/> {2}</td>
            <td class="headerc" align="center">{3} <br/> {4}</td><td class="headerc" align="center">
            <input name="hd_name" type="hidden" value="{5}" />
            <input name="date_actual" type="hidden" value="{6}" />
            <input name="date_observed" type="hidden" value="{7}" />
            <input name="{8}" type="submit" value="{9}"></td></tr>\n'''.format(hd_display, weekday_actual, fmt_actual, weekday_observed, fmt_observed, hd_name, date_actual, date_observed, date_observed, date_observed))
        
    target.write('</table></form></body></html>')
    target.close()
    
    try:      
        t = Template(open(hd_edit).read())
        print(t.substitute(title_msg=title_msg))

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1) 
  
            
def day_select(target, month_actual_value, f1, f2, month_observed, day_observed): 

    target.write('''<td class="headerc" align="center">Change celebration date to: \n<br/>
    <select name="month_observed">\n''')
    for dt in rrule(MONTHLY, dtstart=f1, until=f2):
        month_value = dt.month
        month_name = dt.strftime("%B")
        if month_value == month_actual_value:
            #print '<br/>?', month_actual_value, month_value
            target.write('<option value="{0}" selected>{1}</option>\n'.format(month_value, month_name))  
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(month_value, month_name)) 

    target.write('</select>\n<select name="day_observed">\n')
    for dn in range(1,32):
        if dn == day_observed:
            target.write('<option value="{0}" selected>{1}</option>\n'.format(dn, day_observed))  
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(dn, dn))
    target.write('</select></td></tr>\n')
        
        
def page_two(dt, hd_display, title_msg):
    
    hd_editshort = os.path.join(base_path, 'calendar/control/liturgy/hd_editshort.html')
    hd_header_two = os.path.join(base_path, 'calendar/control/liturgy/hd_header_two.html')    
    
    if dt != '':
        #dt is a string whose value is set to the observed date (actual doesn't change)
        date_actual = datetime.datetime.strptime(sub_flds['date_actual'], '%Y-%m-%d')
        date_observed = datetime.datetime.strptime(dt, '%Y-%m-%d')
        month_actual = date_actual.strftime("%B")
        month_actual_value = date_actual.month
        month_observed = date_observed.strftime("%B")
        f1 = date_observed - relativedelta(months=1)
        f2 = date_observed + relativedelta(months=1)        
        day_observed = date_observed.day
        weekday_actual = date_actual.strftime("%A")            
        weekday_observed = date_observed.strftime("%A")
        
        target = open(hd_editshort, 'w')
    
        try:
            shutil.copyfileobj(open(hd_header_two, 'rb'), target)
    
        except IOError:
            print('Could not read the form! Please contact {0}'.format(email_from))
            sys.exit(1)         
        
        target.write('''\n<tr><td class="headerc" align="center">{0}</td>
        <td class="headerc" align="center">{1} {2} {3}, {4}</td>'''.format(hd_display, weekday_actual, month_actual, date_actual.day, date_actual.year))
        target.write('<td class="headerc" align="center">{0} {1} {2}, {3}</td>'.format(weekday_observed, month_actual, date_observed.day, date_observed.year))
        
        day_select(target, month_actual_value, f1, f2, month_observed, day_observed)
        
        target.write('''<tr><td colspan="4" class="fillero" align="right">
            <input name="hd_name" type="hidden" value="{0}" />
            <input name="date_actual" type="hidden" value="{1}" />
            <input name="month_observed" type="hidden" value="{2}" />
            <input name="day_observed" type="hidden" value="{3}" />    
            <input name="Submit_Day" type="submit" value="Submit"></td></tr></form>\n'''.format(hd_name, date_actual, month_observed, day_observed))       
        
        target.write('''<form action="/shc/calendar/control/holy_days.cgi" method="post">\n<tr><td colspan="4">   
        <input name="Cancel" type="submit" value="Cancel" /></td></tr></form></table>\n</body></html>''')  
        target.close()  
            
        try:      
            t = Template(open(hd_editshort).read())
            print(t.substitute(title_msg=title_msg))
    
        except IOError:
            print('Could not read the form! Please contact {0}'.format(email_from))
            sys.exit(1) 
            
    
def confirm_page(hd_display, year_num, date_actual, date_observed, weekday_observed, month_name):
    
    fmt_actual = datetime.datetime.strftime(date_actual, '%-d %B %Y')
    fmt_observed = datetime.datetime.strftime(date_observed, '%-d %B %Y')    
    litcon_month = os.path.join(web_path, 'calendar/control/liturgy/{0}/{1}.html'.format(year_num, month_name))
    hd_confirm = os.path.join(base_path, 'calendar/control/liturgy/hd_confirm.html')
    hd_header_confirm = os.path.join(base_path, 'calendar/control/liturgy/hd_header_confirm.html')  
    full_list = ['Holy Day: ', hd_display, 'Date: ', fmt_actual, 'To be observed on: ', weekday_observed, fmt_observed]
    
    target = open(hd_confirm, 'w')

    try:
        shutil.copyfileobj(open(hd_header_confirm, 'rb'), target)

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1) 
        
   
    target.write('''<tr><td colspan="4" class="filler" align="center">{0} ({1}) will be observed this year on {2} {3}</td></tr></form>\n
                 <tr><td class="mainnb" colspan="4">
                 <table width="700"><tr><td colspan="2">
                 <form action="/shc/calendar/control/holy_days.cgi" method="post"><input type="submit" value="List of Holy Days"></form></td>\n
                 <td colspan="2" align="right"><form action="{4}" method="post"><input type="submit" value="Go to calendar page"></form></td></tr>\n
                 </table></td></tr></table></body></html>\n'''.format(hd_display, fmt_actual, weekday_observed, fmt_observed, litcon_month))        
            
    target.close()  
        
    try:      
        t = Template(open(hd_confirm).read())
        print(t.substitute(title_msg=''))   
        
    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)  
        
    email_envoi = open(mail_path, 'w')
    email_subject = 'Holy Day observance'
    email_string = '\n'.join(full_list)
    email_message = '{0}\n'.format(email_string)
    email_envoi.write(email_message)
    email_envoi.close()
    email_out.send_email(email_from, email_to, email_subject)          
         
        
if __name__ == "__main__":
        
    print "Content-type: text/html; charset=utf-8\n"
    
    cur_day = datetime.date.today()
    hd_values = read_table()
    sub_flds = read_form(fields=fields)
          
    if 'Submit_Day' in form:
         
        hd_name = sub_flds['hd_name']
        hd_short = hd_name[:-5].replace('_', ' ')
        hd_display = '{0}'.format(hd_short)        
        date_actual = datetime.datetime.strptime(sub_flds['date_actual'], '%Y-%m-%d %H:%M:%S')
        year_num = date_actual.year
        month_observed = int(sub_flds['month_observed'])
        day_observed = int(sub_flds['day_observed'])
        date_observed = datetime.datetime(date_actual.year, month_observed, day_observed).date()
        weekday_observed = date_observed.strftime("%A")
        month_name = date_observed.strftime("%B")
        change_calendar(date_observed, hd_name)
        #add vars to launch lit_mgmt
        date_start = date_observed.replace(day=1)
        abs_paths = ['litopen_abs', 'litcon_abs', 'actopen_abs', 'actcon_abs']     
        lit_mgmt.cal_page(year_num, month_name, date_start, abs_paths) 
        act_mgmt.cal_page(year_num, month_name, date_start, abs_paths) 
        confirm_page(hd_display, year_num, date_actual, date_observed, weekday_observed, month_name)
        
        
    elif sub_flds['hd_name'] != '':
        #print sub_flds #{'hd_name': 'Assumption_of_Mary_2019' etc. (always the first);
        submit_dates = form_content(hd_values)
        for dt in submit_dates:
            if dt in form:
                sub_flds['date_observed'] = dt
                for date_actual in hd_values:
                    hd_name = hd_values[date_actual][0]
                    date_observed = hd_values[date_actual][1] 
                    if date_observed == dt:
                        sub_flds['hd_name'] = hd_name
                        sub_flds['date_actual'] = date_actual
                        #print '<br/>new:', sub_flds
                        hd_display = hd_name[:-5].replace('_', ' ')
                        page_two(dt, hd_display, title_msg='') 
                        
    else:
        page_one(hd_values, title_msg='')         
                    
    
        
            
    
        
       
        
    
       

