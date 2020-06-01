#!/usr/bin/python
# coding: utf-8

import os
import sys
import cgi
from types import ListType
from string import Template
import sqlite3 as sqlite
import datetime
from dateutil import tz
import shutil

from config_pilgrim import db_pilgrim, admin_head, pilgrim_admin

column_labels = ['Registration<br/>Date', 'First Name', 'Last Name', 'Cell Phone', 'Email', 'Age', 'Gender', 'Parish', 'Bicycle', \
             'Proficiency', 'Adult Sponsor', 'Volunteer']

def convert_sqldate(gmt):
    
    #nb: gmt is a unicode object
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Anchorage')
    
    # utc = datetime.utcnow()
    utc = datetime.datetime.strptime(gmt, '%Y-%m-%d %H:%M:%S')
    
    # Tell the datetime object that it's in UTC time zone since datetime objects are 'naive' by default
    utc = utc.replace(tzinfo=from_zone)
    
    # Convert time zone
    dtg = utc.astimezone(to_zone)
    
    # Convert to text to iterate print statements for table values #2019-03-20 15:53:01-08:00
    date_entered = datetime.datetime.strftime(dtg, '%Y-%m-%d %H:%M:%S')
    
    return date_entered
    
    
    

def db_lookup():

    row_values = {}
    try:
        con = sqlite.connect(db_pilgrim)
        cursor = con.cursor() 
        cursor.execute("SELECT UID, Dtg, First_Name, Last_Name, Cell, Email, Age, Gender, Parish, Bicycle, Proficiency, Adult_Sponsor, Volunteer FROM cycle;")      
        rows = cursor.fetchall()
        for row in rows:
            uid = row[0]
            gmt = row[1]
            row_values[uid] = [] 
            date_entered = convert_sqldate(gmt)
            row_values[uid].append(date_entered)
            for col in row[2:]:
                #omit text message (unpopulated); 
                if col == None:
                    row_values[uid].append('')
                else:
                    row_values[uid].append(str(col))
            
        con.commit()
        con.close()        

    except sqlite.Error, e:
        print("<br/>Failed to connect to the user table to obtain column values")
        sys.exit(1)

    return row_values

#========================== html table methods ==============================#

def pnt_cell(target, index, vol_index, column_value): 
    
    '''vol_index = 13; range covers 0-11; 12th iteration = 13;'''
    
    if index in range(vol_index - 1):
        target.write('<td class="pilgrimb">{0}</td>'.format(column_value))
     
    else:
        target.write('<td class="pilgrimb">')
        if len(column_value) > 1:
            if ',' in column_value:
                short_list = column_value.split(',')
                for val in short_list:
                    target.write('{0}<br/>'.format(val))  
            else: 
                target.write('{0}'.format(column_value))
        target.write('</td>')    

def build_table(row_values):
    
    '''omitting text message, not populated'''
    
    target = open(pilgrim_admin, 'w')
    
    try:
        shutil.copyfileobj(open(admin_head, 'rb'), target)

    except IOError:
        print('Could not read the survey form! Please contact webmaster@sacredheartak.org') 
        sys.exit(1)     
    
    target.write('<table class="pilgrimb" align="center"><tr>')
    for col in column_labels:
        target.write('<th class="pilgrimb">{0}</th>'.format(col))
    target.write('</tr>\n')
    
    for uid in row_values:
        #target.write('<tr><td class="pilgrimb">{0}</td>'.format(uid))
        target.write('<tr>')
        for index, column_value in enumerate(row_values[uid]):
            vol_index = len(column_labels) 
            if '_' in column_value:
                column_value = column_value.replace('_', ' ')
                pnt_cell(target, index, vol_index, column_value)
            else:
                pnt_cell(target, index, vol_index, column_value)
    
        target.write('</tr>\n')
        
    target.write('</table><p></p></body></html>')
    target.close()      
        

if __name__ == "__main__":

    print "Content-type: text/html; charset=utf-8\n" 

    row_values = db_lookup()
    build_table(row_values)
    title_msg = 'Registered Cyclists'
    
    try:
        t = Template(open(pilgrim_admin).read())
        print(t.substitute(title_msg=title_msg))
    
    except IOError:
        print('Could not read the admin page! Please contact webmaster@sacredheartak.org') 
        sys.exit(1)      
        