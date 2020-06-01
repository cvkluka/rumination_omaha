#!/usr/bin/python

import shutil
import os
import sys

import datetime

#src_path = '/home/cvkluka/public_html/shc/bce'
#dst_path = '/home/cvkluka/public_html/site_support/db_local'
#src_path = '/Users/cvkluka/Sites/shc/bce'
#dst_path = '/Users/cvkluka/Sites/site_support/db_local'
src_path = '/home/sacredak/public_html/shc/bce'
dst_path = '/home/sacredak/site_support/db_backups'

cur_day = datetime.date.today()     
date_str = datetime.datetime.strftime(cur_day, '%Y-%m-%d')  
db_names = ['activities.db', 'cal_lit.db', 'sign_up.db', 'pilgrims.db']

for db in db_names:

    db_name, ext = os.path.splitext(db)
    dst_name = ('{0}_{1}.db'.format(db_name, date_str))
    #print dst_name
    src = os.path.join(src_path, db)
    dst = os.path.join(dst_path, dst_name)
    print 'backing up {0} to {1}'.format(src, dst)
    shutil.copy(src, dst)
    
    



