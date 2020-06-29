#!/usr/bin/python

import os
import sys
import time
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import operator
import re
import shutil
import headers
from config_upload import upload_base, homily_archive

'''launch_update(mfolder, mpath) from file_upload.cgi to update the index page of the media folder; bulletins, homilies parsed by name, all others by timestamp of upload '''

allowed_ext = ['.pdf', '.txt', '.jpg', '.png', '.gif', '.mp3']

def read_date(fdate, fname):

	ts = ''

	if fname == 'Bulletin':
		ts = datetime.datetime.strptime(fdate, '%b-%d-%Y')	

	elif fname == 'CVBulletin':
		ts = datetime.datetime.strptime(fdate, '%m-%d-%Y')

	return ts


def parse_files(mfolder, mpath):

	file_dates = {}
	same_date = {'2020-03-22 10:10:10': '2020-03-22_Laetere_Sunday_Introduction.pdf', '2020-03-22 11:11:11': '2020-03-22_Laetere_Sunday_Homily.pdf'}
	omit = ['bulletin_current.pdf', 'homily_current.pdf']
	#omit Bulletins, Homilies from mfolders (indexing is different)
	mfolders = ['Altar', 'Apostolado', 'Education', 'Letters', 'Youth']

	for fn in os.listdir(mpath):
		if fn in omit:
			pass		
		elif fn[-4:] == '.pdf':
			if '_' in fn:
				#files w/o underscore, images will not be indexed @ Bulletins, Homilies
				fn_list = fn.split('_')
				
				if 'Bulletins' in mpath:
					#filename ends with date, sort by filename
					if 'Bulletin' in fn_list[0]:
						fname = fn_list[0]
						fdate = fn_list[1][:-4] 
						ts = read_date(fdate, fname)
						if ts != '':
							display_date = datetime.datetime.strftime(ts, '%b-%d-%Y')	
							fnew = 'Bulletin_{0}.pdf'.format(fdate)
							file_dates[ts] = fnew
							old_path = os.path.join(mpath, fn)
							new_path = os.path.join(mpath, fnew)
							os.rename(old_path, new_path)
							file_dates[ts] = fnew
						
				elif 'Homilies' in mpath:
					#filename starts with date, sort by filename
					if fn_list[0].startswith('2020'):
						fdate = fn_list[0] 		
						fname = fn_list[1:]
						if fdate == '2020-03-22':
							for dt in same_date:
								if same_date[dt] == fn:
									ts = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
									file_dates[ts] = fn
						else:
							ts = datetime.datetime.strptime(fdate, '%Y-%m-%d')
							file_dates[ts] = fn
								
			if mfolder in mfolders:
				#use timestamp on upload
				fpath = os.path.join(mpath, fn)
				t = os.path.getmtime(fpath)
				#print t #1586728372.59
				tdate = datetime.datetime.fromtimestamp(t) 
				fdate = tdate.replace(microsecond=0) 			
				if fdate:
					#use fpath (not fn) to organize by mfolder
					file_dates[fdate] = fpath
					
	return file_dates


def copy_bulletin(mpath, file_dates):

	#pdf copy omits metadata on upload; not readable in older browsers
	compare = list(file_dates.iteritems())
	sorted_values = sorted(compare, key=lambda x: x[0])
	if sorted_values:
		last_tuple = sorted_values[-1]
		fn = last_tuple[1]
		src_bulletin = os.path.join(mpath, fn)
		dst_bulletin = os.path.join(mpath, 'bulletin_current.pdf')
		if os.path.exists(src_bulletin):
			if os.path.islink(dst_bulletin):
				os.remove(dst_bulletin)
				os.symlink(src_bulletin, dst_bulletin)
			else:
				os.symlink(src_bulletin, dst_bulletin)
		else:
			print('Source path for {0} does not exist, exiting'.format(fn))

def copy_homily(mpath, file_dates):

	#pdf copies omit metadata on upload; use symbolic links 
	compare = list(file_dates.iteritems())
	sorted_values = sorted(compare, key=lambda x: x[0])
	if sorted_values:
		last_tuple = sorted_values[-1]
		dst_fn_path = os.path.join(mpath, last_tuple[1])
		dst_date = last_tuple[0].strftime('%Y-%m-%d')
		dst_homily_path = os.path.join(mpath, 'homily_current.pdf')

		if os.path.islink(dst_homily_path):
			os.remove(dst_homily_path)
			os.symlink(dst_fn_path, dst_homily_path)
			
		else:
			#no link exists but if file exists there's an error!
			if not os.path.isfile(dst_homily_path):
				os.symlink(dst_fn_path, dst_homily_path)

def update_index(mfolder, mpath, target, file_dates):
	
	cur_day = datetime.date.today() 
	months_ago = cur_day - relativedelta(months=3)  
	months_dt = datetime.datetime.combine(months_ago, datetime.time.min)
	days_ago = cur_day - relativedelta(days=12)
	days_dt = datetime.datetime.combine(days_ago, datetime.time.min)
	days_limit = cur_day - relativedelta(days=30)
	#hours_limit = cur_day - relativedelta(hours=12)
	
	if 'Bulletins' in mpath: 
		
		if len(file_dates) > 0:        
			target.write('<tr><td colspan="3" align="center"><table align="center" width="600">')            
			for ts in sorted(file_dates, reverse=True):
				fn = file_dates[ts]
				if ts > months_dt:
					display_date = datetime.datetime.strftime(ts.date(), '%Y-%m-%d')
					target.write('<tr><td align="center"><a href="/shc/media/users/Bulletins/{0}" target="_blank">{1}</a></td><td>&nbsp;</td><td align="center">{2}</td></tr>\n'.format(fn, fn, display_date))                      
			target.write('</table></td></tr></table>\n</body></html>\n')          

	elif 'Homilies' in mpath:            

		if len(file_dates) > 0:        
			target.write('<tr><td colspan="3" align="center"><table align="center" width="600">') 
			for ts in sorted(file_dates, reverse=True):
				fn = file_dates[ts]
				display_date = ts.date()
				fname = fn[:-4]
				pdf_file = os.path.join(mpath, fn)
				audio_file = '{0}.mp3'.format(fname)
				audio_path = os.path.join(mpath, audio_file)
				if os.path.exists(pdf_file):
					#accommodate requests
					if fn == '2020-04-19_Divine_Mercy_Sunday.pdf':
						target.write('<tr><td align="center"><a href="/shc/media/users/Homilies/{0}" target="_blank">{1}</a></td><td align="center">{2}</td>\n'.format(fn, fn, display_date))
						target.write('<td><a target="_blank" rel="noopener noreferrer" href="{3}">Audio file</a></td></tr>\n'.format(fn, fn, display_date, audio_file))			
					elif display_date >= days_limit:
						#display 30 days of homilies
						target.write('<tr><td align="center"><a href="/shc/media/users/Homilies/{0}" target="_blank">{1}</a></td><td align="center">{2}</td>\n'.format(fn, fn, display_date))
						if ts > days_dt:
							target.write('<td><a target="_blank" rel="noopener noreferrer" href="{3}">Audio file</a></td></tr>\n'.format(fn, fn, display_date, audio_file))
						else:
							#file is older than 12 days, move outside web path/advise user to request audio file
							if os.path.exists(audio_path): 
								audio_dest = os.path.join(homily_archive, fn)
								shutil.move(audio_path, audio_dest)
								target.write('<td><a href="/shc/akc/request_audio.cgi?audio_file={0}">Request audio</td></tr>\n'.format(audio_file))
							else:
								target.write('<td><a href="/shc/akc/request_audio.cgi?audio_file={0}">Request audio</td></tr>\n'.format(audio_file))
					else:
						pdf_dest = os.path.join(homily_archive, fn)
						shutil.move(pdf_file, pdf_dest)

			target.write('</table></body></html>')


	elif 'Education' in mpath:
		sorted_file_dates = sorted(file_dates.items(), key=operator.itemgetter(1), reverse=True) 
		target.write('<tr><td colspan="3" align="center"><table align="center" width="600">')     

		if len(file_dates) > 1:
			target.write('''<tr><td colspan="2" align="center"><hr color="#9e0909" width="400">
            Documents are listed in the order they were uploaded.
            <hr color="#9e0909" width="400"></td></tr>''')
		for fdate in file_dates:
			fn = file_dates[fdate]
			if fn == 'Registration_Form.pdf':
				pass
			else:
				#evaluate file date later (not enough files)
				target.write('<tr><td><a href="/shc/media/users/{0}/{1}" target="_blank">{2}</a></td><td>&nbsp;</td><td>{3}</td></tr>\n'.format(mfolder, fn, fn, fdate))
		target.write('</table></td></tr></table>\n</body></html>\n')    


	else:
		#Altar, Apostolado, Education, Letters, Youth index; files listed by date of upload 
		target.write('<tr><td colspan="3" align="center"><table align="center" width="500">') 
		if len(file_dates) > 0:
			for ts in sorted(file_dates, reverse=True):
				fpath = file_dates[ts]
				display_date = ts.date()
				flist = fpath.split('/')
				fn = flist[-1]
				target.write('<tr><td colspan="2"><a href="/shc/media/users/{0}/{1}" target="_blank">{2}</a></td><td>{3}</td></tr>\n'.format(mfolder, fn, fn, display_date))
				
		target.write('</table></td></tr></table>\n</body></html>\n')    

def launch_update(mfolder, mpath):

	mpath_index = os.path.join(mpath, 'index.html')  
	target = open(mpath_index, 'w')
	labels = {'Altar':'Altar Server Archives', 'Apostolado':'Archivos', 'Bulletins':'Bulletin Archives', 'Education':'Education Archives', 'Homilies':'Homily Archives', 'Letters':'Letters to the Parish', 'Youth':'Youth Archives'}
	
	if mfolder in mpath:
		for key in labels:
			if key == mfolder: 
				label = labels[key]
				media_head = headers.media_header(label, mfolder)
				target.write(media_head)
				file_dates = parse_files(mfolder, mpath) 
				
				if file_dates:
					update_index(mfolder, mpath, target, file_dates)		
				
					if 'Bulletins' in mpath:
						copy_bulletin(mpath, file_dates) 
				
					elif 'Homilies' in mpath:
						copy_homily(mpath, file_dates)

	target.close()


if __name__ == "__main__":

	media_folders = ['Altar', 'Apostolado', 'Bulletins', 'Education', 'Homilies', 'Letters', 'Youth']

	for mfolder in media_folders:
		mpath = os.path.join(upload_base, mfolder)   
		launch_update(mfolder, mpath)

