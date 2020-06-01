#!/usr/bin/python

import os
import sys
import datetime
import calendar
import shutil
from PIL import Image
from PIL.ExifTags import TAGS

'''use bash (space_files.sh) to build inventory (text file) of downloaded files with origination dates; 
   1) read the inventory text file into image_store dict
   2) create new (no-space) filenames in lower case, add origination date from inventory file;
   3) rotate, resize and save jpg/jpeg images to ~/Pictures path, filed by year and month (will lose exif data);
   4) shutil.copy2 the rest (mov, aae) with new names to ~/Pictures by year and date
   5) check stdout against len(inventory), run copy_check.py to id any missing files'''

def build_record(inventory):
    
    #read inventory.txt files w/ ts; #first (ts) and last (fn) lines are truncated: (this only fixes a single error)
    image_store = {}
    hold_time = []
    with open(inventory) as f:
        content = f.readlines()
    content = content = [x.strip() for x in content] 
    for line in content:
        if line[0].isdigit():
            hold_time.append(line)
        else:
            ll = line.split('\t')
            if ll:
                if ll[0].startswith('/'):
                    fpath = ll[0]
                    flist = fpath.split('/')
                    fname = flist[-1]  
                    if len(ll) == 2:
                        image_store[fname] = ll[1]                    
                    elif len(ll) == 1:
                        image_store[fname] = hold_time[0]  
            
    for fn in image_store:
        #convert m-d-Year to Year-m-d format 
        if image_store[fn] == '':
            print 'timestamp error:', fn
        else:
            dtg_obj = datetime.datetime.strptime(image_store[fn], '%m-%d-%Y %H:%M:%S')
            dtg_str = datetime.datetime.strftime(dtg_obj, '%Y-%m-%d_%H-%M-%S')
            image_store[fn] = dtg_str
            #print fn, image_store[fn]    
                    
    return image_store
       

def add_date(fn_base, fn_ext, date_origin):
    
    ext = fn_ext.lower()
    fn_hold = []
    no_space = fn_base.replace(' ', '')
    
    if ext in ['.jpg', '.mov', '.aae']:
        fn_replace = '{0}_{1}{2}'.format(no_space, date_origin, ext)
        fn_hold.append(fn_replace.lower())   
        
    elif ext == '.jpeg':
        fn_replace = '{0}e_{1}.jpg'.format(no_space, date_origin)
        fn_hold.append(fn_replace.lower())  
    
    if len(fn_hold) == 1:    
        fn_new = fn_hold[0]
        
        return fn_new

def get_dstPath(date_merge, dst_path, fn_new):    
    
    dtg = datetime.datetime.strptime(date_merge, '%Y-%m-%d_%H-%M-%S')
    month_name = dtg.strftime("%B")
    month_path = os.path.join(dst_path, '{0}/{1}'.format(dtg.year, month_name))
    img_dst = os.path.join(month_path, '{0}'.format(fn_new))

    return img_dst

def border(new_img, img_dst, border_width=5, color="White"):
    
    x,y = new_img.size
    bordered = Image.new("RGB", (x+(2*border_width), y+(2*border_width)), color)
    bordered.paste(new_img, (border_width, border_width)) 
    bordered.save(img_dst) 
    
    return bordered

def img_resize(width, height, img_dst, image):
    
    def multiply_factor(width, height, factor, img_dst, image):    
        
        new_width = int(width*factor)
        new_height = int(height*factor) 
        new_img = image.resize((new_width, new_height))
        new_img.save(img_dst)   
        resize_list = [new_img, img_dst, new_width, new_height]
    
        return resize_list        
        
    if width in range(4000, 5000) or height in range(4000, 5000):
        factor = 0.25
        multiply_factor(width, height, factor, img_dst, image)
                    
    elif width in range(3000, 4000) or height in range(3000, 4000):
        factor = 0.30    
        multiply_factor(width, height, factor, img_dst, image)
            
    elif width in range(2000, 3000) or height in range(2000, 3000):  
        factor = 0.35   
        multiply_factor(width, height, factor, img_dst, image)
            
    elif width in range(1000, 2000) or height in range(1000, 2000):
        if (width * 0.5) < 600 or (height * 0.5) < 600:
            factor = 0.75
            multiply_factor(width, height, factor, img_dst, image)
            
    elif width in range(200, 1000) or height in range(200, 1000):
        factor = 1.0    
        multiply_factor(width, height, factor, img_dst, image)
        
    image.close()  
    
def get_properties(img_src, fn_new, img_dst):
    
    image=Image.open(img_src)
    width, height = image.size    
    find_key = []
    
    try: 
        info = image._getexif()
        if info:
            for key, value in info.items():
                key = TAGS.get(key)
                find_key.append(key) #LensSpecification, WhiteBalance, ResolutionUnit, ...
                if key == 'Orientation':  
                    image_list = [img_src, width, height, value, img_dst]
                    
                    if value == 1:
                        #1 = default, no rotation required; 
                        img_resize(fn_new, width, height, img_dst, image=image)
            
                    elif value == 2:
                        new_img = image.transpose(Image.FLIP_LEFT_RIGHT)
                        img_resize(fn_new, width, height, img_dst, image=new_img)
                
                    elif value == 3:
                        new_img = image.rotate(180, expand=True) 
                        img_resize(fn_new, width, height, img_dst, image=new_img)
                
                    elif value == 4:
                        new_img = image.rotate(180).transpose(Image.FLIP_LEFT_RIGHT) 
                        img_resize(fn_new, width, height, img_dst, image=new_img)
                
                    elif value == 5:
                        new_img = image.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT) 
                        img_resize(fn_new, width, height, img_dst, image=new_img)
                
                    elif value == 6:
                        #image = image.rotate(270, expand=True) #upside down, fails for top-right
                        #image = image.rotate(180, expand=True) #flipped on its side, fails for top-right
                        new_img = image.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT) 
                        img_resize(fn_new, width, height, img_dst, image=new_img)
                
                    elif value == 7:
                        new_img = image.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT) 
                        img_resize(fn_new, width, height, img_dst, image=new_img)
                
                    elif value == 8:
                        new_img = image.rotate(90, expand=True)
                        img_resize(fn_new, width, height, img_dst, image=new_img)
                
                    else:
                        print 'Orientation key exists but orientation is not populated for', fn_origin
                        #img_resize(fn_new, width, height, img_dst, image=image)
                        
    except (AttributeError, KeyError, IndexError):
        print 'missing exif data for image', img_src
                    
    if 'Orientation' in find_key:
        #img_list previously defined
        pass
    
    else:
        #catch the remaining files (no orientation in exif), resize; record orig w,h to debug scaling
        image_list = [img_src, width, height, 0, img_dst]
        resize_list = img_resize(fn_new, width, height, img_dst, image=image)
        
    return resize_list
        

if __name__ == "__main__":
    
    inventory = '/absolute/path/to/inventory.txt' 
    src_path = '/absolute/path/to/downloaded/images'
    dst_path = '/absolute/path/to/destination/dirs' 
    
    image_store = build_record(inventory)
    #print 'inventory:', len(image_store) #2229, 1607, 2396
    
    for fn_origin in image_store:
        img_src = os.path.join(src_path, fn_origin)
        date_origin = image_store[fn_origin]
        fn_base, fn_ext = os.path.splitext(fn_origin)
        
        #save to path by date; compare stdout with len(image_store)
        if fn_ext.lower() in ['.jpg', '.jpeg']:
            fn_new = add_date(fn_base, fn_ext, date_origin) 
            img_dst = get_dstPath(date_origin, dst_path, fn_new) 
            #reorient, resize & save 
            resize_list = get_properties(img_src, img_dst) 
            print 'resized jpg', resize_list[1:]
            #for html albums, add optional image border
            new_img = resize_list[0]
            bordered = border(new_img, img_dst, border_width=5, color="White")              
            
        else:
            #.mov, .aae (xml)
            fn_new = add_date(fn_base, fn_ext, date_origin) 
            img_dst = get_dstPath(date_origin, dst_path, fn_new) 
            shutil.copy2(img_src, img_dst)   
            print 'copying movie/other', fn_origin, img_dst 
            
