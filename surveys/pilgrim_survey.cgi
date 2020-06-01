#!/usr/bin/python
# coding: utf-8

import os
import sys
import cgi
from types import ListType
from string import Template
import sqlite3 as sqlite
import shutil
import datetime
import email_out

from config_pilgrim import email_from, email_to, mail_path, db_pilgrim, sign_up, survey_form, survey_head, confirmation_page, survey_head_short

'''figure out why the timestamp on localhost is 8 hours ahead on the spreadsheet / sqlite3...'''

form = cgi.FieldStorage()
fields = {}  

form_list = ['First_Name', 'Last_Name', 'Cell', 'Email', 'Age', 'Gender', 'Parish', 'Bicycle', \
             'Proficiency', 'Adult_Sponsor', 'Volunteer', 'Rehearsal', 'Pilgrimage']
sub_flds = {'First_Name':'', 'Last_Name':'', 'Cell':'', 'Email':'', 'Age':'', 'Gender':'', 'Parish':'', 'Bicycle':'', \
            'Proficiency':'', 'Adult_Sponsor':'', 'Volunteer':'', 'Rehearsal':'', 'Pilgrimage':''}
required = ['First_Name', 'Last_Name', 'Age', 'Gender', 'Parish', 'Bicycle', 'Proficiency']


def read_form(**kw):
    
    fields = kw.get('fields', {})
    
    #read values into the form fields dict
    for field in form_list:
        value = form.getvalue(field)
        if isinstance(value, ListType):
            fields[field] = ', '.join(value)
        else:
            fields[field] = form.getvalue(field)

        if form.getvalue(field) == None:
            fields[field] = '' 
            
        #store form values in sub_flds  
        for sub in sub_flds:
            if sub == field:
                sub_flds[sub] = fields[field]
                if sub_flds[sub] != '':
                    list_vals = []
                    if isinstance(sub_flds[sub], (list,)): 
                        for val in sub_flds[sub]:
                            list_vals.append(sub_flds[sub]) 
                        sub_flds[sub] = ', '.join(list_vals) 
                
                    elif sub in ['First_Name', 'Last_Name', 'Adult_Sponsor']:
                        sub_flds[sub] = sub_flds[sub].title()
                    
                    elif sub == 'Cell':
                        value = sub_flds['Cell']
                        sub_flds['Cell'] = ''.join(char for char in value if char.isdigit())
    
    if sub_flds['Age'] != '':                    
        age = int(sub_flds['Age'])
        if age > 18:
            sub_flds['Adult_Sponsor'] = 'N/A'
                      
    return sub_flds

def db_lookup(sub_flds):
    
    uid_list = []
    fn = sub_flds['First_Name']
    ln = sub_flds['Last_Name']
    cell = sub_flds['Cell']
    email = sub_flds['Email']
    
    try:
        con = sqlite.connect(db_pilgrim)
        cursor = con.cursor() 
        cursor.execute("SELECT UID, First_Name, Last_Name FROM cycle WHERE First_Name=? AND Last_Name=?", (fn, ln))
        row = cursor.fetchone()
        if row:
            #None is appended by default on localhost but not on remote host; manually inserted the first record            
            if row[0] == None:
                uid_list.append(0)
            else:
                uid_list.append(row[0])
                #print 'db lookup row', row
        
        con.commit()
        con.close()        
                
    except sqlite.Error, e:
        print("<br/>Failed to connect to the user table to obtain the UID")
        sys.exit(1)
         
    #establish duplication 
    if len(uid_list) > 0:
        #manually inserted the first record on remote host
        if uid_list[0] > 1:
            db_uid = int(uid_list[0])
                    
            return db_uid
        
    
def max_id():
    
    max_ids = []
    
    try:
        con = sqlite.connect(db_pilgrim)
        cursor = con.cursor() 
        cursor.execute("SELECT max(UID) FROM cycle")
        row = cursor.fetchone()
        if row:
            #None is appended by default on localhost but not on remote host; manually inserted the first record
            if row[0] == None:
                max_ids.append(0)
            else:
                max_ids.append(row[0])
       
        con.commit()
        con.close()

    except sqlite.Error, e:
        print('</br>Could not read user table to get max id')
        sys.exit(1)  
        
    #mirror db_uid behavior
    if len(max_ids) > 0:
        #manually inserted the first record on remote host
        if max_ids[0] > 1:
            new_uid = int(max_ids[0]) + 1       
    
            return new_uid


def check_errs(sub_flds):
    
    errors = []
    #required = ['First_Name', 'Last_Name', 'Age', 'Gender', 'Parish', 'Bicycle', 'Proficiency']
        
    for k in required:
        for key in sub_flds:
            if key == k:
                if sub_flds[key] in ['', 'Select', 'First Name', 'Last Name', 'Age']:
                    if '_' in key:
                        key = key.replace('_', ' ')
                        errors.append('{0} is a required field.'.format(key))
                    else:
                        errors.append('{0} is a required field.'.format(key))
     
    if sub_flds['Age'] != '':                        
        age = int(sub_flds['Age'])
        if age < 18 and sub_flds['Adult_Sponsor'] == '':
            errors.append('Please type in the name of an adult sponsor')
                                        
    if sub_flds['Cell'] in ['9071112222', ''] and len(sub_flds['Email']) < 7:
        errors.append('Contact information is required (email or cell phone).')
        
    #if sub_flds['Rehearsal'] == '' and sub_flds['Pilgrimage'] == '':
        #errors.append('Please select the test ride, the pilgrimage or both.')
        
    return errors   


def insert_new(clist, vlist):
    
    col_str = ", ".join(clist)
    value_str = "', '".join(vlist)
    #cursor.execute("INSERT INTO cycle(column_names) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (colum_values))
    insert_str = "INSERT INTO cycle({0}) VALUES('{1}')".format(col_str, value_str)
    
    try:
        con = sqlite.connect(db_pilgrim)
        cursor = con.cursor() 
        
        cursor.execute(insert_str)
        con.commit()
        con.close()                   

    except sqlite.Error, e:
        print "<br/>Error failed to insert new user record!"
        sys.exit(1)
        
    
def record_user(sub_flds, new_uid):
    
    clist = ['UID']
    vlist = [str(new_uid)]
    for k in form_list:
        clist.append(k)
        if k == 'Volunteer':
            pass
        else:
            for sub in sub_flds:
                if sub == k:
                    vlist.append(sub_flds[sub])
    
    if isinstance(sub_flds['Volunteer'], (list,)):  
        vol = ', '.join(sub_flds['Volunteer'])
        vlist.insert(-2, vol)
        insert_new(clist, vlist)
    else:
        vol = sub_flds['Volunteer']
        vlist.insert(-2, vol)
        insert_new(clist, vlist)
            
#======================================HTML pages===========================================================#
def load_start(sub_flds, title_msg):
    
    cabin_fee = "$30"
    person_fee = "$15"
    
    #sign_up page contains instructions
    try:      
        t = Template(open(sign_up).read())
        print(t.substitute(sub_flds,title_msg=title_msg,cabin_fee=cabin_fee,person_fee=person_fee))

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)        

def restart_page(sub_flds, title_msg):
    
    #survey_form is limited to form inputs  
    target = open(survey_form, 'w')    
    
    try:
        shutil.copyfileobj(open(survey_head, 'rb'), target)

    except IOError:
        print('Could not read the survey form! Please contact {0}'.format(email_from)) 
        sys.exit(1) 

    target.write('<tr><td class="pilgrim1" align="right">Parish</td><td class="pilgrim"><select name="Parish">')
    for k in ['Select', 'ICC', 'SHC', 'FWA', 'St_Mark', 'St_Nicholas', 'St_Raphael', 'Monroe', 'Eielson', 'Delta_Junction']:
        display_value = k.replace('_', ' ')
        if sub_flds['Parish'] == k:
            target.write('<option selected value="{0}">{1}</option>\n'.format(k, display_value))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(k, display_value))
    target.write('</select></td></tr>')
    
    target.write('<tr><td class="pilgrim1" align="right">Bicycle</td><td class="pilgrim"><select name="Bicycle">')
    for k in ['Select', 'Commuter', 'Mountain_Bike', 'Hybrid_Bike', 'Touring_Bike', 'Racing_Bike']:
        display_value = k.replace('_', ' ')
        if sub_flds['Bicycle'] == k:
            target.write('<option selected value="{0}">{1}</option>\n'.format(k, display_value))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(k, display_value))
    target.write('</select></td></tr>')
                    
    target.write('<tr><td class="pilgrim1" align="right">Proficiency</td><td class="pilgrim"><select name="Proficiency">')
    for k in ['Select', 'Basic', 'Intermediate', 'Advanced']:
        if sub_flds['Proficiency'] == k:
            target.write('<option selected value="{0}">{1}</option>\n'.format(k, k))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(k, k))    
                    
    target.write('''</select></td></tr></table></td><td><table class="pilgrim" width="70%">   
    <tr><td class="pilgrim1">If minor, provide adult sponsor name:</td></tr> ''')
    target.write('<tr><td class="pilgrim1"><input type="text" name="Adult_Sponsor" maxlength="80" value="{0}"></td></tr>'.format(sub_flds['Adult_Sponsor']))
    target.write('<tr><td class="yellow">Volunteer:</td></tr>\n<tr><td class="pilgrim1">\n')
    
    for k in ['Safety_Checks', 'Logistics', 'Group_Leaders', 'Communications']:
        display_value = k.replace('_', ' ')
        if k in sub_flds['Volunteer']:
            target.write('<input type="checkbox" name="Volunteer" value="{0}" checked /> {1}<br/>\n'.format(k, display_value))
        else:
            target.write('<input type="checkbox" name="Volunteer" value="{0}" /> {1}<br/>\n'.format(k, display_value))
    target.write('</td></tr>')
            
    target.write('''</td></tr></table>\n<tr><td colspan="2" align="center"><input type="submit" name="Submit1" value="Submit"/></form>
    </td></tr></table>\n</body></html>''')
    
    target.close()
    
    try:
        t = Template(open(survey_form).read())
        print(t.substitute(sub_flds,title_msg=title_msg))
    
    except IOError:
        print('Could not read the survey form! Please contact {0}'.format(email_from)) 
        sys.exit(1)    
        
        
def confirm_inputs(sub_flds, title_msg):
    
    mail_list = []
    
    target = open(confirmation_page, 'w')    
    
    try:
        shutil.copyfileobj(open(survey_head_short, 'rb'), target)
    
    except IOError:
        print('Could not read the survey form! Please contact {0}'.format(email_from)) 
        sys.exit(1)    
        
    omit_values = ['Select', 'Select round trip', '', ' ', '9071112222']
    
    target.write('<tr><td class="pilgrim1">')
    
    for k in form_list:
        for key in sub_flds:
            if key == k:
                if sub_flds[key] not in omit_values:
                    
                    if '_' in key or '_' in sub_flds[key]:
                        display_key = key.replace('_', ' ')
                        display_val = sub_flds[key].replace('_', ' ')
                        target.write('<br/>{0}: {1}'.format(display_key, display_val))
                        mail_list.append('{0}: {1}'.format(display_key, display_val))
                    
                    else:
                        #no underscores
                        target.write('<br/>{0}: {1}'.format(key, sub_flds[key]))  
                        mail_list.append('{0}: {1}'.format(key, sub_flds[key]))  
                            
    target.write('''</td></tr>\n<tr><td class="pnote" align="center">Please copy this data / save this page for your records. 
    </td></tr>\n<tr><td align="right"><a class="yellow" href="/shc/pilgrim/pilgrim_survey.cgi">Return to form</a></td></tr>
    </table>\n</body></html>\n''')
    target.close()
    
    try:
        t = Template(open(confirmation_page).read())
        print(t.substitute(title_msg=title_msg))
    
    except IOError:
        print('Could not read the survey form! Please contact {0}'.format(email_from)) 
        sys.exit(1)  
        
    email_envoi = open(mail_path, 'w')
    email_subject = 'Bicycle Pilgrimage Sign-Up'
    email_msg = '\n'.join(mail_list) 
    email_envoi.write(email_msg)
    email_envoi.write('\n')
    email_envoi.close()
    email_out.send_email(email_from, email_to, email_subject)       
                        

if __name__ == "__main__":
    
    print "Content-type: text/html; charset=utf-8\n" 
    
    sub_flds = read_form(fields=fields)
    errors = check_errs(sub_flds)
    #db_uid = db_lookup(sub_flds) #used in 2018 to avoid duplicate posts 
        
    if 'Submit1' in form:
    
        if len(errors) == 0:
            #create a new record 
            new_uid = max_id()
            record_user(sub_flds, new_uid)
            title_msg = 'Thank you for signing up!'
            confirm_inputs(sub_flds, title_msg)            
            
        else:
            #errors to appear in restart page
            title_msg = '<br/>'.join(errors)
            restart_page(sub_flds, title_msg)
            
    else:
        #add a method to load the start page
        title_msg = 'Complete this survey to join us!'
        load_start(sub_flds, title_msg)
        