#!/usr/bin/python
# coding: utf-8

import os
import sys

from string import Template
import sqlite3 as sqlite
import shutil
import datetime
import cgi

from config_pilgrim import email_from, base_path, parish_survey, parish_survey_head, parish_form, confirm_parish, confirm_parish_head, parishes_survey, submit_options

form = cgi.FieldStorage()
fields = {}  
errors = []
db_pilgrim = os.path.join(base_path, 'bce/pilgrims.db')
#UID is read from db (not from form) but stored and used...
form_list = ['Parish', 'Flyer', 'Bulletin', 'Emails', 'Youth_Number']
sub_flds = {'Parish':'', 'Flyer':'', 'Bulletin':'', 'Emails':'', 'Youth_Number':''}
parishes_list = ['ICC', 'SHC', 'St_Raphael', 'St_Mark', 'FWA', 'St_Nick', 'Eielson', 'Delta_Junction']
        
def read_form(**kw):
    
    fields = kw.get('fields', {})
   
    #read values into the form fields dict
    for field in form_list:
        if isinstance(form.getvalue(field), list):
            fields[field] = form.getfirst(field)
        else:
            fields[field] = form.getvalue(field)
            print '<br/>', field, fields[field]

        if form.getvalue(field) == None:
            fields[field] = '' 
            
        #store form values in sub_flds  
        for sub in sub_flds:
            if sub == field:
                sub_flds[sub] = fields[field]
                if sub_flds[sub] != '':
                    sub_flds[sub] = sub_flds[sub].strip()
                                
    return sub_flds

def get_values(sub_flds):
    
    track_list = []
    
    for key in sub_flds:
        track_list.append(sub_flds[key])
        
    return track_list
         
        
def update_chart(key, value, parish):
    
    statement = "UPDATE tracking SET {0}='{1}' WHERE Parish='{2}'".format(key, value, parish)
    
    try:
        con = sqlite.connect(db_pilgrim)
        cursor = con.cursor() 
        cursor.execute(statement)
        con.commit()
        con.close()                   

    except sqlite.Error, e:
        print "<br/>Error failed to update tracking data!"
        sys.exit(1)
        

def read_db(parish_name):
    
    #column names match form fields: Parish, Flyer, Bulletin, Emails, Youth_Number
    statement = "SELECT Flyer, Bulletin, Emails, Youth_Number FROM tracking WHERE Parish='{0}'".format(parish_name)
    
    try:
        con = sqlite.connect(db_pilgrim)
        cursor = con.cursor() 
        cursor.execute(statement)
        row = cursor.fetchone()
        con.commit()
        con.close() 
            
    except sqlite.Error, e:
        print "<br/>Failed to connect to the tracking table!"   
        sys.exit(1)  
    
    db_post = {'Parish':parish_name, 'Flyer':'', 'Bulletin':'', 'Emails':'', 'Youth_Number':''}          
    kv = {0:'Parish', 1:'Flyer', 2:'Bulletin', 3:'Emails', 4:'Youth_Number'}  
    row_index = 0
    if row:
        #if len(row) == 4:
        for val in row:
            row_index = row_index + 1
            for integer in kv:
                key_name = kv[integer]
                if integer == row_index:
                    if val == None:
                        db_post[key_name]  = ''
                    else:
                        db_post[key_name]  = str(val)
                
    return db_post
            

#======================================HTML pages===========================================================#


def confirm_inputs(sub_flds, title_msg):
    
    #print confirm_parish
    target = open(confirm_parish, 'w')    
    
    try:
        shutil.copyfileobj(open(confirm_parish_head, 'rb'), target)
   
    except IOError:
        print('Could not read the survey form! Please contact {0}'.format(email_from)) 
        sys.exit(1)     
    
    target.write('''</td></tr><tr><td class="pilgrim">
    <p align="right">To view or edit results, <a class="yellow" href="/shc/akc/parish_survey.cgi">return to form</a></td></tr>
    </table>\n</body></html>\n''')
    target.close()
    
    try:
        t = Template(open(confirm_parish).read())
        print(t.substitute(title_msg=title_msg))
    
    except IOError:
        print('Could not open the confirmation page! Please contact {0}'.format(email_from)) 
        sys.exit(1)    
        

        
def show_results(db_post):
    
    #print table rows as read from pilgrims.db
    target.write('<tr>')
    for k in form_list:
        for key in db_post:
            
            if key == k:
                if key == 'Parish':
                    parish = parishes_survey[parish_name]
                    target.write('<td class="board">{0}</td>'.format(parish))
                    
                elif key == 'Youth_Number':
                    target.write('<td class="board" align="center"><input type="text" size="5" name="Youth_Number" maxlength="5" value="{0}"></td>'.format(db_post[key]))
                
                elif key in ['Flyer', 'Bulletin', 'Emails']:
                    if db_post[key] != '':
                        target.write('<td class="board" align="center"><input type="checkbox" name="{0}" value="{1}" checked /></td>'.format(key, key))
                    else:
                        target.write('<td class="board" align="center"><input type="checkbox" name="{0}" value="{1}" /></td>'.format(key, key))

    submit_start = db_post['Parish'] 
    submit_name = parishes_survey[submit_start]
    for k in submit_options:
        if k == submit_start:
            target.write('<td class="board" align="center"><input type="submit" name="{0}" Value="Update" /></td>\n'.format(submit_options[k]))
    target.write('</tr>\n')    

if __name__ == "__main__":
    
    print "Content-type: text/html; charset=utf-8\n" 
      
    for parish in submit_options:
        if submit_options[parish] in form:
            print 'Submit found for {0}'.format(parish)
        
            sub_flds = read_form(fields=fields)
            print 'Submit in form', sub_flds
            #write only one parish
            for key in sub_flds:
                if key != 'Parish':
                    value = sub_flds[key]
                    #print key, value
                    update_chart(key, value, parish)
            
            #read db tracking table and post results here
            title_msg = 'Thanks for your input to this parish survey!'
            #add error-checking to see if sub_flds is empty 
            
            target = open(parish_form, 'w')    
        
            try:
                shutil.copyfileobj(open(parish_survey_head, 'rb'), target)
        
            except IOError:
                print('Could not read the survey form! Please contact {0}'.format(email_from))  
                sys.exit(1)  
            
            #read all parishes   
            for parish_name in parishes_list:
                db_post = read_db(parish_name)
                show_results(db_post)
                
            target.write('</table>\n</body></html>')
            target.close()
            confirm_inputs(sub_flds, title_msg)
                        
        else:
            pass
        
    #set some sort of argument here because this is always true...
    if 'Submit' not in form:
              
        title_msg = 'Please complete this form for your parish only.'  #built into default page        
        target = open(parish_form, 'w')    
                
        try:
            shutil.copyfileobj(open(parish_survey_head, 'rb'), target)
    
        except IOError:
            print('Could not read the survey form! Please contact {0}'.format(email_from))  
            sys.exit(1)  
                    
        #read all parishes   
        for parish_name in parishes_list:
            db_post = read_db(parish_name)
            show_results(db_post)
            
        target.write('</table></form>\n</body></html>')
        target.close()  
        
        try:
            t = Template(open(parish_form).read())
            print(t.substitute(title_msg=title_msg))
        
        except IOError:
            print('Could not open the confirmation page! Please contact {0}'.format(email_from)) 
            sys.exit(1)         
                
                
        
                
                    

        
        
        

        

       
                    
    