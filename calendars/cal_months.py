#!/usr/bin/python

import os
import sys

import calendar 
import datetime
import dateutil
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

import lit_mgmt
import act_mgmt

from config_cal import base_path, web_path, months_ini

'''publish liturgy and activity calendar pages in open and control paths within the date range '''

if __name__ == "__main__":

	f0 = datetime.date.today()
	fs = f0.replace(day=1)
	f1 = fs - relativedelta(months=1)
	f2 = fs + relativedelta(months=2)    
	
	abs_paths = ['actopen_abs', 'actcon_abs', 'litopen_abs', 'litcon_abs']
	for dg in rrule(MONTHLY, dtstart=f1, until=f2): 
		date_start = datetime.datetime(dg.year, dg.month, 1).date()
		lit_mgmt.cal_page(date_start, abs_paths)
		print 'lit_mgmt', date_start
		act_mgmt.cal_page(date_start, abs_paths)
		print 'act_mgmt', date_start
