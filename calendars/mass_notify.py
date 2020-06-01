#!/usr/bin/python

import os, sys
import sqlite3 as sqlite

import datetime
from datetime import date, timedelta

from time import gmtime, strftime
import email_out

from config_alert import base_path, sms_path, mail_path, webmail_poc, webtext_poc, email_from, db_sign

'''alert users for ministry at mass; '''

def get_contacts(): 
    
    #read db tables and store locally in dict
    ministry = {}
    cur_time = datetime.datetime.now() 
    #mass times in DTG
    try:             
        con = sqlite.connect(db_sign) 
        cursor = con.cursor()
        cursor.execute("SELECT DTG, Position, UID, First_Name, Last_Name, Notify FROM ministry")
        rows = cursor.fetchall()
        for row in rows: 
            dtg_str = str(row[0])
            dtg = datetime.datetime.strptime(dtg_str, '%Y-%m-%d_%H:%M') 
            if cur_time < dtg:            
                AID = '{0}_{1}'.format(str(row[0]), str(row[1]))
                ministry[AID] = []
                ministry[AID].append(dtg)
                data = row[1:]
                for i in data:
                    ministry[AID].append(str(i)) 
                
        con.commit()
    
    except sqlite.Error, e:
        print 'could not access the ministry table', db_sign
        sys.exit(1)
        
    #get contact info from the alerts table that matches the user in the ministry table 
    try:             
        con = sqlite.connect(db_sign) 
        cursor = con.cursor()
        cursor.execute("SELECT UID, Email, TextMsg FROM alerts")
        rows = cursor.fetchall()
        for row in rows: 
            UID = str(row[0])
            data = row[1:]
            for AID in ministry:
                if UID == ministry[AID][2]:
                    for i in data:
                        ministry[AID].append(str(i))
                    
        con.commit()

    except sqlite.Error, e:
        print 'could not access the alerts table'
        sys.exit(1)
        
    con.close() 
     
    return ministry

def compose_msg(email_to, msg_content):
    
    dtg = msg_content[0]
    svc_date = dtg.date()
    fmt_date = datetime.datetime.strftime(svc_date, '%d %B %Y')
    mass_time = datetime.datetime.strftime(dtg, '%-I:%M %p') 
    #print msg_content #[dtg, 'UID', 'Lector2', 'Rudolph', 'Valentino', 'Cell', '', '7035551212@att.net']
    email_subject = 'SHC reminder for {0} {1}'.format(msg_content[3], msg_content[4])
    msg = '{0} \n to serve as {1} on {2} at {3} \n'.format(email_subject, msg_content[1], fmt_date, mass_time)
    estore = open(mail_path, 'w')  
    estore.write('{0}\n'.format(msg))
    estore.close()   
    print('{0}\n{1}\n======='.format(email_to, msg))
    email_out.send_email(email_from, email_to, email_subject)       
        
if __name__ == "__main__":
     
    cur_time = datetime.datetime.now() 
    #read ministry db table, stored as dict; cron runs at 07:00 (Arizona 09:00)
    ministry = get_contacts()
    for AID in sorted(ministry):
        #2019-02-07_10:00_EM1: [datetime.datetime(2019, 2, 7, 10, 0), 'EM1', '1', 'James', 'Dean', 'Cell', '', '9075551212@mms.gci.net']     
        msg_content = ministry[AID]
        notify_time = ministry[AID][0] - datetime.timedelta(hours=12, minutes=30)
        if cur_time >= notify_time:
            print 'notify', msg_content
            #print dtg; priority = text msg alert
            if '@' in ministry[AID][-1]:
                if ministry[AID][-1] == webtext_poc:
                    email_to = [ministry[AID][-1]]
                    compose_msg(email_to, msg_content)
                else:
                    email_to = [webtext_poc, ministry[AID][-1]]
                    compose_msg(email_to, msg_content)
         
            elif '@' in ministry[AID][-2]:
                #email notification not used but leave this in
                if ministry[AID][-2] == webmail_poc:
                    email_to = [ministry[AID][-2]]  
                    compose_msg(email_to, msg_content)
                else:
                    email_to = [webmail_poc, ministry[AID][-2]]
                    compose_msg(email_to, msg_content)
                    
        else:
            print 'later', notify_time, msg_content        
       
                    
         
