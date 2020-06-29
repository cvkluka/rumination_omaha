#!/usr/bin/python

import os
import sys
from ConfigParser import SafeConfigParser
import calendar 
import datetime
import dateutil
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

import lit_mgmt
import act_mgmt
import headers
from headers import weekday_cols

from config_cal import base_path, web_path, months_ini

'''copy liturgy (and activity) calendar page heads in open and control paths within the date range; launch lit_mgmt to publish the content for each calendar day; run in cron each night '''

def cal_headers(dtg, month_start):

	#dtg is a date object, month_start is a string, both for first day of month
	month_name = dtg.strftime("%B")    
	parser = SafeConfigParser()
	parser.read(months_ini) #reads the path  
	
	ini_header = '{0}'.format(dtg)
	html_header = headers.page_header(label='Liturgy')  

	for abs_path in abs_paths: 
		for section_date in parser.sections():
			if section_date == month_start:
				parser_values = dict(parser.items(section_date))
				for key in parser_values:
					if key == 'litcon_head':
						litcon_head = parser_values['litcon_head']
						litcon_sub = '''<table class="titre" width="1000" align="center"><tr>
							    <td class="nav" width="20"><a href="%(0)s"><img src="/shc/images/prev.png"/></a></td>\n
							    <td width="300" class="highlt"><b>%(1)s %(2)s</b></td>\n
							    <td class="highlt" width="200" align="center"><a class="page" href="%(3)s"><b>Liturgy Calendar</b></a></td>\n
							    <td class="header" width="200" align="center"><a class="page" href="%(4)s">Activity Calendar</a></td>\n
							    <td class="header" width="200" align="center"><a class="page" href="/">Home</a></td>\n               
							    <td class="nav" width="20"><a href="%(5)s"><img src="/shc/images/next.png"/></a></td></tr></table>\n ''' % {'0':parser_values['litcon_prev'], '1':month_name, '2':dtg.year, '3':parser_values['litcon_cur'], '4':parser_values['actcon_cur'], '5':parser_values['litcon_next']}     
					
						target_litcon = open(litcon_head, 'w') 
						target_litcon.write(html_header)
						target_litcon.write(litcon_sub)
						target_litcon.write(weekday_cols)
						target_litcon.close()    

					elif key == 'litopen_head':
						litopen_head = parser_values['litopen_head']
						litopen_sub = '''<table class="titre" width="1000" align="center"><tr>
						<td class="nav" width="20"><a href="%(0)s"><img src="/shc/images/prev.png"/></a></td>\n
						<td width="300" class="highlt"><b>%(1)s %(2)s</b></td>\n
						<td class="highlt" width="200" align="center"><a class="page" href="%(3)s"><b>Liturgy Calendar</b></a></td>\n
						<td class="header" width="200" align="center"><a class="page" href="%(4)s">Activity Calendar</a></td>\n
						<td class="header" width="200" align="center"><a class="page" href="/">Home</a></td>\n               
						<td class="nav" width="20"><a href="%(5)s"><img src="/shc/images/next.png"/></a></td></tr></table>\n''' % {'0':parser_values['litopen_prev'], '1': month_name, '2':dtg.year, '3':parser_values['litopen_cur'], '4':parser_values['actopen_cur'], '5':parser_values['litopen_next']}
						
						target_litopen = open(litopen_head, 'w') 
						target_litopen.write(html_header)
						target_litopen.write(litopen_sub)
						target_litopen.write(weekday_cols)
						target_litopen.close()
						
					elif key == 'actcon_head':
						actcon_head = parser_values['actcon_head']
						actcon_sub = '''<table class="titre" width="1000" align="center"><tr>
						<td class="nav" width="20"><a href="%(0)s"><img src="/shc/images/prev.png"/></a></td>\n
						<td width="300" class="highlt"><b>%(1)s %(2)s</b></td>\n
						<td class="header" width="200" align="center"><a class="page" href="%(3)s"><b>Liturgy Calendar</b></a></td>\n
						<td class="highlt" width="200" align="center"><a class="page" href="%(4)s">Activity Calendar</a></td>\n
						<td class="header" width="200" align="center"><a class="page" href="/">Home</a></td>\n               
						<td class="nav" width="20"><a href="%(5)s"><img src="/shc/images/next.png"/></a></td></tr></table>\n ''' % {'0':parser_values['actcon_prev'], '1':month_name, '2':dtg.year, '3':parser_values['litcon_cur'], '4':parser_values['actcon_cur'], '5':parser_values['actcon_next']}        
					
						target_actcon = open(actcon_head, 'w') 
						target_actcon.write(html_header)
						target_actcon.write(actcon_sub)
						target_actcon.write(weekday_cols)
						target_actcon.close()    
					
					elif key == 'actopen_head':    
						actopen_head = parser_values['actopen_head']
						actopen_sub = '''<table class="titre" width="1000" align="center"><tr>
						<td class="nav" width="20"><a href="%(0)s"><img src="/shc/images/prev.png"/></a></td>\n
						<td width="300" class="highlt"><b>%(1)s %(2)s</b></td>\n
						<td class="header" width="200" align="center"><a class="page" href="%(3)s"><b>Liturgy Calendar</b></a></td>\n
						<td class="highlt" width="200" align="center"><a class="page" href="%(4)s">Activity Calendar</a></td>\n
						<td class="header" width="200" align="center"><a class="page" href="/">Home</a></td>\n               
						<td class="nav" width="20"><a href="%(5)s"><img src="/shc/images/next.png"/></a></td></tr></table>\n''' % {'0':parser_values['actopen_prev'], '1':month_name, '2':dtg.year, '3':parser_values['litopen_cur'], '4':parser_values['actopen_cur'], '5':parser_values['actopen_next']}   
					
						target_actopen = open(actopen_head, 'w') 
						target_actopen.write(html_header)
						target_actopen.write(actopen_sub)
						target_actopen.write(weekday_cols)
						target_actopen.close()					
		
				
if __name__ == "__main__":

	f0 = datetime.date.today()
	fs = f0.replace(day=1)
	f1 = fs - relativedelta(months=1)
	f2 = fs + relativedelta(months=2)    
	
	abs_paths = ['actopen_abs', 'actcon_abs', 'litopen_abs', 'litcon_abs']
		
	for dg in rrule(MONTHLY, dtstart=f1, until=f2): 
		dtg = datetime.datetime(dg.year, dg.month, 1).date()
		month_start = datetime.datetime.strftime(dtg, '%Y-%m-%d')
		cal_headers(dtg, month_start)
		lit_mgmt.copy_header(dtg, month_start)
		print('lit', dtg)
		act_mgmt.copy_header(dtg, month_start) 
		print('act', dtg)
