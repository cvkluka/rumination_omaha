#!/usr/bin/python

import os
import sys
import datetime

#user_path = '/home/cvkluka/Public/site_support/db_backups'
#user_path = '/Users/cvkluka/Sites/site_support/db_backups'
user_path = '/home/sacredak/site_support/db_backups'
cur_day = datetime.datetime.today() 
#one_month = cur_day - datetime.timedelta(365/12)
one_month = cur_day - datetime.timedelta(days=31)   
#activities, pilgrims, sign_up, cal_lit
check_files = []

for db_name in os.listdir(user_path):
    db, ext = os.path.splitext(db_name)
    name_list = db.split('_')
    if name_list[0] in ['activities', 'pilgrims']:
        db_date = datetime.datetime.strptime(name_list[1], '%Y-%m-%d')
        if one_month > db_date:
            check_files.append(db_name)
            
    else:
        db_date = datetime.datetime.strptime(name_list[2], '%Y-%m-%d')
        if one_month > db_date:
            check_files.append(db_name)
                  
print 'start', len(check_files)           
for db_name in sorted(check_files):
    #print 'removing', i
    db_purge = os.path.join(user_path, db_name)
    if os.path.isfile(db_purge):
        print 'isfile', db_name
        os.remove(db_purge) 
        check_files.remove(db_name)

print 'finish', len(check_files)
    
    
    
    



