#!/usr/bin/python

import cgi
import os
import sys
from string import Template
import datetime
import cgitb
cgitb.enable()

import media_archives

from config_upload import email_from, upload_default, upload_form, upload_end, upload_base

'''Bulletin uploads are treated differently (merge later); bulletin names coordinated with Parish office;
to do: throw an error if the filename has no extension.'''

form = cgi.FieldStorage()
fields = {}

def clean_filenames(fn_name):
    
    bad_chars = [":", " ", "@", "#", "'", "(", ")", "[", "]", "{", "}", "/"]
    short = []
    for c in fn_name:
        
        if c == '.':
            if fn_name[-1] == '.':
                pass
            else:
                short.append('_')
                
        elif c in bad_chars:
            pass
        
        else:
            short.append(c)
            
    clean_fn = ''.join(short)[:55]
    
    if len(clean_fn) >= 2: 
        
        return clean_fn
    
def clean_extension(ext):
    
    identifiers = []
    extension = ''
    
    if ext.lower() == 'jpeg':
        identifiers.append('.jpg')        
                
    elif ext.lower() in ['.txt', '.pdf', '.jpg', '.gif', '.png', '.mp3']:
        identifiers.append(ext.lower()) 
        
    if len(identifiers) > 0:
        #print extensions
        extension = identifiers[0]
        
        return extension
        
def find_errors(sub_flds, submit_sequence, file_name2):
    
    #form_list = ['upload_dir', 'file_properties', 'file_name1', 'file_size']
    errors = []
    
    if submit_sequence == 'Submit1':
    
        if sub_flds['upload_dir'] == 'Select':
            errors.append('Please choose a folder to store your file.') 
            
        for key in ['file_properties', 'file_name1', 'file_size']:
            if sub_flds[key] == '':
                pass
        
    elif submit_sequence == 'Submit2':  
        
        if sub_flds['upload_dir'] in ['Select', '']:
            errors.append('Please choose a folder to store your file.')
            
        else: 
                
            if sub_flds['file_name1'] == '':
                errors.append('No file selected!')
                
            elif len(sub_flds['file_name1']) < 2:
                errors.append('File name error!')  
                
            if file_name2 in ['', 'noSpaces_noExtension', 'spaces_noExtension']:
                errors.append('File name or extension missing or corrupt.')
                
            if sub_flds['file_size'] == '':
                errors.append('File content not read!')
                
            else:
                if sub_flds['file_size'] > max_size:
                    errors.append('File size exceeded!') 
                    
                elif sub_flds['file_size'] < min_size:
                    errors.append('File appears to be empty.')        
                             
    return errors

def upload_file(mfolder, mpath, file_content, file_name2):
    
    fdest = os.path.join(mpath, file_name2)   
    fout = file(fdest, 'wb')
    fout.write(file_content) 
    
    #media_folders = ['Altar', 'Apostolado', 'Bulletins', 'Education', 'Homilies', 'Youth']
    media_archives.launch_update(mfolder, mpath)
        
    title_msg = ('Your file <b>{0}</b> was successfully uploaded to the <b>{1}</b> folder.'.format(file_name2, mfolder))
    index_link = ('Return to your <a href="/shc/media/users/{0}/index.html">document index</a>'.format(mfolder))     
    
    try:
        t = Template(open(upload_end).read())
        print(t.substitute(sub_flds, title_msg=title_msg,index_link=index_link))

    except IOError:
        print('Could not open {0}! Please contact {1}'.format(file_name2, email_from)) 
        sys.exit(1) 
    
    
def read_dir(**kw):
    
    fields = kw.get('fields', {})
    #store the upload dir

    for field in form_list:

        if isinstance(form.getvalue(field), list):
            fields[field] = form.getfirst(field)
        else:
            fields[field] = form.getvalue(field)
        
        if form.getvalue(field) == None:
            fields[field] = ''
            
        for sn in sub_flds:
            if sn == field:
                sub_flds[sn] = fields[field]  
        
    return sub_flds
        
def read_upload(**kw):
     
    fields = kw.get('fields', {})
    properties = []
    
    for field in form_list:
        if isinstance(form.getvalue(field), list):
            fields[field] = form.getfirst(field)
        else:
            fields[field] = form.getvalue(field)

        if form.getvalue(field) == None:
            fields[field] = ''

        #store form values 
        for fn in form_list:
            if fn == field:
                if fn == 'file_properties':
                    try: # Windows needs stdio set for binary mode.
                        import msvcrt
                        msvcrt.setmode (0, os.O_BINARY) # stdin  = 0
                        msvcrt.setmode (1, os.O_BINARY) # stdout = 1
                    except ImportError:
                        pass 
                    
                    file_size = sys.getsizeof(fields[field])
                    properties.append(file_size)
                    sub_flds[fn] = fields[field]  
                    fileitem = form[fn]
                    #file_name1 = fileitem.filename
                    properties.append(fileitem.filename)
                    
                else:
                    sub_flds[fn] = fields[field]  
                    
    sub_flds['file_size'] = properties[0]
    sub_flds['file_name1'] = properties[1]
    
    return sub_flds
    

def rename_bulletin(file_name1):
    
    bulletin_name = '' 
    fn_list = file_name1.split('.')
    if ' ' in fn_list[0]:
        fn_nameList = fn_list[0].split(' ')
        #remove empty list item(s) if extra spaces are found
        for x in fn_nameList:
            if x == '':
                fn_nameList.remove(x)            
        dt = datetime.datetime.strptime(fn_nameList[1].strip(), '%m-%d-%Y').date()
        fmt_date = datetime.datetime.strftime(dt, '%b-%d-%Y')
        bulletin_name = 'Bulletin_{0}.pdf'.format(fmt_date)
    else:
        #Bulletin_Dec-23-2018.pdf
        bulletin_name = file_name1
    
    return bulletin_name
    
    
def rename_file(file_name1):
    
    file_name2 = ''
    fn_values = []
    
    if ' ' in file_name1:
        fn_list = file_name1.split(' ')
        fn_nospace_all = '_'.join(fn_list)
        fn_nospace = fn_nospace_all[:-4]
        ext = fn_nospace_all[-4:]
        
        clean_fn = clean_filenames(fn_name=fn_nospace)  
        extension = clean_extension(ext)
        
        if not extension:
            fn_values.append('spaces_noExtension')
            
        else:
            file_name2 = '{0}{1}'.format(clean_fn, extension) 
            fn_values.append(file_name2)
        
    else: 
        #no spaces in file name
        fn_nospace = file_name1[:-4]
        ext = file_name1[-4:]
        
        clean_fn = clean_filenames(fn_name=fn_nospace)  
        extension = clean_extension(ext)
        
        if not extension: 
            fn_values.append('noSpaces_noExtension')
           
        else:
            file_name2 = '{0}{1}'.format(clean_fn, extension) 
            fn_values.append(file_name2)           
        
    if len(fn_values) > 0:
        file_name2 = fn_values[0]
        
        return file_name2
                
          

if __name__ == "__main__":
                    
    print "Content-type: text/html\n\n"
    
    max_size = (20 * 1024 * 1024)   #20 MB
    min_size = 10
    form_list = ['upload_dir', 'file_properties', 'file_name1', 'file_size']
    sub_flds = {'upload_dir':'', 'file_properties':'', 'file_name1':'', 'file_size':''}       
    media_folders = ['Altar', 'Apostolado', 'Bulletins', 'Education', 'Homilies', 'Letters', 'Youth']
    
    if 'Submit1' in form:
        
        sub_flds = read_dir(fields=fields)
        #upload_dir is a hidden value in the upload_form 
        upload_dir = sub_flds['upload_dir']
        submit_sequence = 'Submit1'
        errors = find_errors(sub_flds, submit_sequence, file_name2='')
  
        if len(errors) > 0:
            title_msg = ' '.join(errors)
            try:
                t = Template(open(upload_default).read())
                print(t.substitute(title_msg=title_msg))
                        
            except IOError:
                print('Could not open form! Please contact {0}'.format(email_from))
                sys.exit(1)                  
            
        else: 
            title_msg = ('Your file will be placed in the "{0}" folder'.format(upload_dir))
            try:
                t = Template(open(upload_form).read())
                print(t.substitute(title_msg=title_msg,upload_dir=upload_dir))
                        
            except IOError:
                print('Could not open form! Please contact {0}'.format(email_from)) 
                #print '{0}'.format(upload_form)
                sys.exit(1) 
           
    elif 'Submit2' in form:
        
        submit_sequence = 'Submit2'
        sub_flds = read_upload(fields=fields)
        file_name1 = sub_flds['file_name1']
        file_content = sub_flds['file_properties']
        upload_dir = sub_flds['upload_dir']
        
        for mfolder in media_folders: 
            if mfolder == upload_dir:
                mpath = os.path.join(upload_base, mfolder)  
  
                if 'Bulletin' in file_name1:
                    bulletin_name = rename_bulletin(file_name1)
                    errors = find_errors(sub_flds, submit_sequence, file_name2=bulletin_name)
                
                    if len(errors) > 0:
                        title_msg = ' '.join(errors) 
                        try:
                            t = Template(open(upload_end).read())
                            print(t.substitute(sub_flds, title_msg=title_msg, index_link=''))
                    
                        except IOError:
                            print('Could not open {0}! Please contact {1}'.format(file_name1, email_from)) 
                            sys.exit(1)  
                        
                    else:
                        upload_file(mfolder, mpath, file_content, file_name2=bulletin_name)    
                        
                else:
                    file_name2 = rename_file(file_name1)
                    errors = find_errors(sub_flds, submit_sequence, file_name2)
                    if len(errors) > 0:
                        title_msg = ' '.join(errors) 
                        try:
                            t = Template(open(upload_end).read())
                            print(t.substitute(sub_flds, title_msg=title_msg, index_link=''))
                    
                        except IOError:
                            print('Could not open {0}! Please contact {1}'.format(file_name1, email_from)) 
                            sys.exit(1)  
                            
                    else:
                        upload_file(mfolder, mpath, file_content, file_name2)
                       
    else:
        #load the default page
        title_msg = 'Please select a directory to store your file.'
        try:
            t = Template(open(upload_default).read())
            print(t.substitute(sub_flds, title_msg=title_msg))
                    
        except IOError:
            print('Could not open form! Please contact {0}'.format(email_from))
            sys.exit(1)   
            
