#!/usr/bin/python
#coding: utf-8

import os, sys
import sqlite3 as sqlite

import datetime as dt
import calendar 

from string import Template
import cgi
import shutil

import cgitb
cgitb.enable()

from config_cal import db_sign, psn_form, hsp_form, psn_header
from config_alert import email_from, correlate, sign_remove, relaciones

'''Loads initial page to sign up for ministry, should match form inputs to db inputs for date and hd and mass
new version adds Spanish mass; high masses to be added via hd_list for Christmas and its Vigil mass,
Palm Sunday, Holy Thursday, Good Friday, Holy Saturday, Easter and its Vigil mass, Corpus Christi, 
Sacred Heart of Jesus, Pentecost, Trinity, All Saints Day; hd_list = [ datetime.date(year, month, day), et al. ]
sub_form reads DTG, HD from form passed as args; sub_db reads from db; '''

#import names from database
form = cgi.FieldStorage()
fields = {}
full_list = []
#Position read from the db to match keys to page
form_list = ['ID', 'UID', 'DTG', 'HD', 'First_Name', 'Last_Name', 'Avisos', 'EM1', 'EM2', 'EM3', 'EM4', 'EM5', 'EM6', 'Lector1', 'Lector2', 'Lector3', 'Lector4', 'Lector5', 'Lector6', \
              'Oraciones', 'Altar1', 'Altar2', 'Altar3', 'Altar4', 'Altar5', 'Altar6', 'Altar7', 'Altar8', 'Altar9', 'Coro', 'Sacristan', 'Deacon', 'Choir']  
hd_list = [dt.datetime(2018, 12, 25, 11, 0), dt.datetime(2018, 12, 24, 16, 30), dt.datetime(2018, 12, 24, 18, 30), dt.datetime(2018, 12, 24, 23, 30)]
#Two values are read from the form (as passed from the calendar page): DTG and HD; ID for the day/svc read from ministry table
sub_form = {'DTG':'', 'HD':'', 'ID':''}

#Store values from db to assign names to each position (one per row of the database, ID for the day/svc, UID for the user)
sub_db = {'ID':'', 'UID':'', 'DTG':'', 'HD':'', 'EM1':'', 'EM2':'', 'EM3':'', 'EM3':'', 'EM4':'', 'EM5':'', 'EM6':'', 'Choir':'', 'Lector1':'', 'Lector2':'', 'Lector3':'', 'Lector4':'', \
          'Lector5':'', 'Lector6':'', 'Altar1':'', 'Altar2':'', 'Altar3':'', 'Altar4':'', 'Altar5':'', 'Altar6':'', 'Altar7':'', 'Altar8':'', 'Altar9':'', \
          'Concelebrant':'', 'Sacristan':'', 'Deacon':'', 'Oraciones':'', 'Avisos':'', 'Coro':''} 

def pnt_cell(target, psn, psn_title, DTG_form, mass, HD, username, ID):

    if mass == '13:00':    
    
        target.write('<td class="main" width="33%" align="center">') 
        if ID != '':
            target.write('{0}<br/><a href="/shc/akc/delete_svc.cgi?ID={1}&DTG={2}&HD={3}">{4}</a></td>\n'.format(psn_title, ID, DTG_form, HD_form, username))
        else:
            target.write('<a href="/shc/akc/sign_up.cgi?Position={0}&DTG={1}&HD={2}">{3}</a></td>\n'.format(psn, DTG_form, HD_form, psn_title))
            
    else:
        
        target.write('<td class="main" width="33%" align="center">') 
        if ID != '':
            target.write('{0}<br/><a href="/shc/akc/delete_svc.cgi?ID={1}&DTG={2}&HD={3}">{4}</a></td>\n'.format(psn_title, ID, DTG_form, HD_form, username))        
        else:
            #link position to sign-up 
            target.write('<a href="/shc/akc/sign_up.cgi?Position={0}&DTG={1}&HD={2}">{3}</a></td>\n'.format(psn, DTG_form, HD_form, psn_title))
  
    
def pnt_row(target, psn, psn_title, DTG_form, mass, username, ID): 
    
    dtg = dt.datetime.strptime(DTG_form, '%Y-%m-%d_%H:%M')
    
    if mass == '13:00':   
    
        if psn == 'Avisos':
            target.write('<tr>')
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)
        elif psn in ['Altar1', 'Lector1', 'Coro']:
            target.write('</tr><tr>') 
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)
        elif psn == 'Deacon':
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)
            target.write('</tr>') 
        else:
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)
            
    elif dtg in hd_list:
        
        #['EM1', 'EM2', 'EM3', 'EM4', 'EM5', 'EM6', 'Lector1', 'Lector2', 'Lector3', 'Lector4', 'Lector5', 'Lector6', 'Altar1', 'Altar2', 
        #'Altar3', 'Altar4', 'Altar5', 'Altar6', 'Altar7', 'Altar8', 'Altar9', 'Sacristan', 'Deacon', 'Choir']
        
        if psn == 'EM1':
            target.write('<tr>')
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)
        
        elif psn in ['EM4', 'Lector1', 'Lector4', 'Altar1', 'Altar4', 'Altar7']:
            target.write('</tr><tr>')
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)
                
        elif psn == 'Sacristan':
            target.write('</tr><tr>')
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)

        else:
            #pnt table cell 
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)  
            if psn == 'Choir':
                target.write('</tr>')    
            
    else:
        #regular mass
        if psn == 'EM1':
            target.write('<tr>')
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)
        
        elif psn in ['Lector1', 'Altar2']:
            target.write('</tr><tr>')
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)
                
        elif psn == 'Sacristan':
            target.write('</tr><tr>')
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)
                  
        elif psn in ['EM2', 'EM3', 'Lector1', 'Lector2', 'Altar1', 'Altar3', 'Altar4', 'Deacon', 'Choir']:
            #just a td
            pnt_cell(target, psn, psn_title, DTG_form, mass, HD_form, username, ID)
            if psn == 'Choir':
                target.write('</tr>')
        

def page_sp(display_sp, month_path, month_name, DTG_form, mass):
    
    #Spanish mass
    target = open(hsp_form, 'w')

    try:
        shutil.copyfileobj(open(psn_header, 'rb'), target)

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)  
        
    #needed to order table cells
    target.write('<table class="main" width="550" align="center">\n')
    for psn_name in form_list[6:]:
        for psn in display_sp:
            if psn == psn_name:
                psn_title = display_sp[psn][0]
                if len(display_sp[psn]) > 1:
                    username = display_sp[psn][1]
                    ID = display_sp[psn][2]
                    pnt_row(target, psn, psn_title, DTG_form, mass, username, ID)
                else:
                    username = ''
                    ID = ''
                    pnt_row(target, psn, psn_title, DTG_form, mass, username, ID)
                                                     
    #end nested table, footer       
    target.write('</table>\n')                  
    target.write('<table align="center"><tr><td>\n<form action="{0}" method="post">\n'.format(month_path))
    target.write('''<div class="g-recaptcha" data-sitekey="6Lfs4h4TAAAAABnAo-cyzd4N8BoM4WpvJ-CtI-8z"></div>\n
    <input type="Submit" name="Submit1" value="Volver"></td></tr></table></form>\n
    <script src='https://www.google.com/recaptcha/api.js'></script></body></html>\n''')               
    target.close()                                                
                                    
  
def page_en(display_en, month_path, month_name, DTG_form, mass): 
    
    #Sunday Mass (English)
    try:
        target = open(psn_form, 'w')
        shutil.copyfileobj(open(psn_header, 'rb'), target)

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)  
    
    #needed to order table cells
    target.write('<table class="main" width="550" align="center">\n')
    for psn_name in form_list[6:]:
        for psn in display_en:
            if psn == psn_name:
                psn_title = display_en[psn][0]
                if len(display_en[psn]) > 1:
                    username = display_en[psn][1]
                    ID = display_en[psn][2]
                    pnt_row(target, psn, psn_title, DTG_form, mass, username, ID)
                else:
                    username = ''
                    ID = ''
                    pnt_row(target, psn, psn_title, DTG_form, mass, username, ID)                 
                        
    #end nested table, footer       
    target.write('</table>\n')                  
    target.write('<table align="center"><tr><td>\n<form action="{0}" method="post">\n'.format(month_path))
    target.write('''<input type="Submit" name="Submit1" value="Return to {0}"></td></table></form>\n
    </body></html>\n'''.format(month_name))               
    target.close()
    

def title_list(DTG_form, dtg, HD_form):

    dtg_full = dt.datetime.strptime(DTG_form, '%Y-%m-%d_%H:%M')
    dtg_date = dtg_full.date()
    dtg_12 = dtg_full.strftime("%-I:%M %p")
    format_date = dtg_date.strftime("%-d %B %Y")
   
    if DTG_form.endswith('13:00'):
        full_list.append(format_date)
        full_list.append('a la {0}'.format(dtg_12)) 
    
    else:
        full_list.append(format_date)
        full_list.append('at {0}'.format(dtg_12))  
        
    HD_form = form.getvalue('HD')
    Holy_Day = HD_form.replace('_', ' ')
    full_list.insert(1, Holy_Day)
                                     
    return full_list

def display_table(display1, mass):
    
    display_sp = {}
    display_en = {}
    
    if mass == '13:00':
    
        #Build a table that includes the sign_up info  
        for psn_name in form_list[6:]:
            for psn in relaciones:
                if psn == psn_name:
                    psn_title = relaciones[psn]
                    display_sp[psn] = []
                    display_sp[psn].append(psn_title)
                    for key in display1:
                        if key == psn:
                            username = display1[key][0]
                            ID = display1[key][1]
                            display_sp[psn].append(username)
                            display_sp[psn].append(ID)
                            
    else:
        
        #Build a table that includes the sign_up info  
        for psn_name in form_list[6:]:
            for psn in correlate:
                if psn == psn_name:
                    psn_title = correlate[psn]
                    display_en[psn] = []
                    display_en[psn].append(psn_title)
                    for key in display1:
                        if key == psn:
                            username = display1[key][0]
                            ID = display1[key][1]
                            display_en[psn].append(username)
                            display_en[psn].append(ID) 
    
    return display_sp, display_en    

def read_form(**kw):

    fields = kw.get('fields', {}) 

    for field in form_list:
        if isinstance(form.getvalue(field), list):
            fields[field] = form.getfirst(field)
        else:
            fields[field] = form.getvalue(field)

        if form.getvalue(field) == None:
            fields[field] = ''     

        #store form values in sub_form 
        for sub in sub_form:
            if sub == field:
                sub_form[sub] = fields[field]
                                            
    return sub_form

def read_db(DTG_form):
    
    sign_up = {}
    display1 = {}
    
    try:
        con = sqlite.connect(db_sign)
        cursor = con.cursor() 
        cursor.execute("SELECT ID, DTG, Holy_Day, Position, First_Name, Last_Name, UID FROM ministry WHERE DTG=?", (DTG_form,))  
        rows = cursor.fetchall() 
        for row in rows:
            ID = row[0]
            sign_up[ID] = row[1:]

        con.commit()
        con.close()

    except IOError:
        print('Could not open database. Please contact {0}'.format(email_from))
        sys.exit(1) 
     
    for ID in sign_up:
        psn = str(sign_up[ID][2])
        ln_abbrev = '{0}.'.format(str(sign_up[ID][4][0]))
        username = '{0} {1}'.format(str(sign_up[ID][3]), ln_abbrev)
        display1[psn] = []
        display1[psn].append(username)
        display1[psn].append(ID)
        
    return display1            
        

if __name__ == "__main__":

    print "Content-type: text/html; charset=utf-8\n"

    #DTG = '2017-07-09_13:00 #HD = 'not'
    DTG_form = form.getvalue('DTG')
    HD_form = form.getvalue('HD')   
    sub_form = read_form(fields=fields)
    if DTG_form != '':
    
        dtg = dt.datetime.strptime(DTG_form, '%Y-%m-%d_%H:%M')
        #2017-09-05 09:00:00
        year_str = dtg.strftime("%Y")
        month_int = dtg.month
        month_name = dtg.strftime("%B")
        day = dtg.strftime("%d")
        mass = dtg.strftime("%H:%M")
        
        full_list = title_list(DTG_form, dtg, HD_form)
        month_path = '/shc/calendar/liturgy/{0}/{1}.html'.format(year_str, month_name)
        
        title_str = ' '.join(full_list) 
        display1 = read_db(DTG_form)
        display_sp = display_table(display1, mass)[0]
        display_en = display_table(display1, mass)[1]
        
        if mass == '13:00':
            page_sp(display_sp, month_path, month_name, DTG_form, mass) 
            title_msg = ('Seleccione un enlace para servir a misa el <br/>{0} <br/>'.format(title_str))
            try: 
                t = Template(open(hsp_form).read()) 
                print(t.substitute(title_msg=title_msg))
        
            except IOError:
                print('Could not read the form! Please contact {0}'.format(email_from))
                sys.exit(1)
                
        else:
            
            page_en(display_en, month_path, month_name, DTG_form, mass)
            title_msg = ('Please select a link to sign up for mass on <br/>{0} <br/>'.format(title_str))  
            try: 
                t = Template(open(psn_form).read()) 
                print(t.substitute(title_msg=title_msg))
        
            except IOError:
                print('Could not read the form! Please contact {0}'.format(email_from))
                sys.exit(1)  
                
    else:
        pass
        
        
