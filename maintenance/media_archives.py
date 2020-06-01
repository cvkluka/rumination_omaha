#!/usr/bin/python

import os
import sys
import time
import datetime
from dateutil.relativedelta import relativedelta
import operator
import re
import shutil

from config_upload import upload_base

'''this is launched by file_upload to update the index page of the media folder; consolidate bulletins later'''

allowed_ext = ['.pdf', '.txt', '.jpg', '.png', '.gif']

def parse_files(mpath):
    
    media_files = {}
    file_dates = {}
    
    for filename in os.listdir(mpath):
        fpath = os.path.join(mpath, filename)
        t = os.path.getmtime(fpath)
        tdate = datetime.datetime.fromtimestamp(t) 
        fdate = tdate.replace(microsecond=0)
        fn, ext = os.path.splitext(filename)
        if ext.lower() in allowed_ext:
            fn_list = fn.split(' ')
            if len(fn_list) > 1:
                new_name = '_'.join(fn_list)
                new_name_ext = '{0}{1}'.format(new_name, ext.lower())
                file_dates[new_name_ext] = fdate
            else:
                new_name_ext = '{0}{1}'.format(fn, ext.lower())
                file_dates[new_name_ext] = fdate
                
    return file_dates

def get_trailing_numbers(dts):
    
    result = re.search(r'\d+$', dts)
    
    return int(result.group()) if result else None

def parse_bulletins(mpath):
    
    bulletin_dates = {}
    
    for fn in os.listdir(mpath):
        if fn.startswith('Bulletin') and fn[-4:] == '.pdf':
            #catch bulletins that are already renamed (which should always be true)
            if '_' in fn:
                fn_list = fn.split('_')
                dt_ext = fn_list[1]
                dts = dt_ext[:-4]
                result = get_trailing_numbers(dts)
                if result:
                    dtg = datetime.datetime.strptime(dts, '%b-%d-%Y')
                    dt = datetime.datetime.strftime(dtg.date(), '%Y-%m-%d')
                    bulletin_dates[dt] = fn
                
    return bulletin_dates
    

def update_index(mpath, mfolder, file_dates):
    
    #page headers = header_index.html in same folder with uploaded files (clean this up later)
    header = os.path.join(mpath, 'header_index.html')
    mpath_index = os.path.join(mpath, 'index.html')   
    sorted_file_dates = sorted(file_dates.items(), key=operator.itemgetter(1), reverse=True) 
    cur_day = datetime.date.today() 
    earliest = cur_day - relativedelta(months=12)  
    earliest_dt = datetime.datetime.combine(earliest, datetime.time.min)
    
    target = open(mpath_index, 'w')
        
    try:
        shutil.copyfileobj(open(header, 'rb'), target)
    except IOError:
        print('Could not copy form header! Please contact webmaster@sacredheartak.org')
        sys.exit(1)
        
    if mfolder == 'Bulletins':
        bulletin_dates = parse_bulletins(mpath)
        most_recent = sorted(bulletin_dates.keys())[-1]
        bulletin_current = os.path.join(mpath, 'bulletin_current.pdf')   
        for fdate in bulletin_dates:
            fn = bulletin_dates[fdate]
            if fdate == most_recent:
                copy_bulletin = os.path.join(mpath, fn)
                shutil.copy2(copy_bulletin, bulletin_current)
                        
        #Bulletin index page updates      
        target.write('<tr><td colspan="3" align="center"><table width="400">')                
        for fdate in sorted(bulletin_dates.keys(), reverse=True):
            fn = bulletin_dates[fdate]
            dt = datetime.datetime.strptime(fdate, '%Y-%m-%d')
            #include one year of files; print "recent:", fn, dt
            if dt > earliest_dt:
                display_date = datetime.datetime.strftime(dt.date(), '%Y-%m-%d')
                target.write('<tr><td><a href="/shc/media/users/Bulletins/{0}" target="_blank">{1}</a></td><td>&nbsp;</td><td>{2}</td></tr>\n'.format(fn, fn, display_date))      
                
        target.write('</table></td></tr></table>\n</body></html>\n')    
        target.close()             
    
    elif mfolder == 'Education':
        target.write('<tr><td colspan="3" align="center"><table width="400">')     
        
        if len(sorted_file_dates) > 1:
            target.write('''<tr><td colspan="2" align="center"><hr color="#9e0909" width="400">
            Documents are listed in the order they were uploaded.
            <hr color="#9e0909" width="400"></td></tr>''')
        for fn, ts in sorted_file_dates:
            if fn == 'Registration_Form.pdf':
                pass
            elif file_dates[fn] > earliest_dt:
                #file is more recent than one year ago; print "recent:", fn, ts
                display_date = datetime.datetime.strftime(ts.date(), '%Y-%m-%d')
                target.write('<tr><td><a href="/shc/media/users/{0}/{1}" target="_blank">{2}</a></td><td>&nbsp;</td><td>{3}</td></tr>\n'.format(mfolder, fn, fn, display_date))
                         
        target.write('</table></td></tr></table>\n</body></html>\n')    
        target.close()                     
         
    else:
        #Altar, Apostolate, Education, Youth index page updates; listed by timestamp of upload            
        target.write('<tr><td colspan="3" align="center"><table width="400">')                
        for fn, ts in sorted_file_dates:
            if file_dates[fn] > earliest_dt:
                #file is more recent than one year ago; print "recent:", fn, ts
                display_date = datetime.datetime.strftime(ts.date(), '%Y-%m-%d')
                target.write('<tr><td><a href="/shc/media/users/{0}/{1}" target="_blank">{2}</a></td><td>&nbsp;</td><td>{3}</td></tr>\n'.format(mfolder, fn, fn, display_date))
    
        target.write('</table></td></tr></table>\n</body></html>\n')    
        target.close()           
                             
                    
if __name__ == "__main__":
    
    #passed from file_upload; parsing bulletin dates by name, all others by timestamp of file upload 
    media_folders = ['Altar', 'Apostolate', 'Bulletins', 'Education', 'Youth']
    for mfolder in media_folders:
        mpath = os.path.join(upload_base, mfolder)
        if mfolder == 'Bulletins':
            bulletin_dates = parse_bulletins(mpath)
            update_index(mpath, mfolder, file_dates=bulletin_dates)
        else:
            file_dates = parse_files(mpath)
            update_index(mpath, mfolder, file_dates)