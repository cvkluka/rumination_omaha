#!/usr/bin/python

import sys
import os
import datetime
from PIL import Image
from config_album import album_head, img_head, img_page

''' resize images as needed; generate 1 html page per img, and an index page table to link to them;
original date lost in transmission #date_origin = "2019-07-27" '''
    
def get_properties(img_dir, fp):
    
    image=Image.open(img_dir)
    width, height = image.size    
    image.close()
    prop_list = [fp, width, height]
        
    return prop_list


def image_page(html_page, fp, width, height, seq, prev_link, next_link):
    
    target = open(html_page, 'w')
    target.write(img_head) 
    sub_values = {'0':prev_link, '1':fp, '2':width, '3':height, '4':next_link}
    
    target.write('''<table class="album_img" align="center">
    <tr><td class="album_img"><a class="album_img" href="/shc/pilgrim/album/img_pages/index.html#thumbnails">Return to index</a></td>
    <td><br/></td><td class="album_img" align="right">Page %(0)s of %(1)s</tr>
    <tr><td class="album_img" align="right"><a href="%(2)s"><img src="/shc/images/prev.png"/></a></td>
        <td class="album_img"><img class="img" src="/shc/pilgrim/album/img_dst/%(3)s" width="%(4)s" height="%(5)s" /></td>
        <td class="album_img"><a href="%(6)s"><img src="/shc/images/next.png" /></a></td></tr>
        <tr><td class="album_img" colspan="3" align="center">27 - 28 July 2019</td></tr>
        </table></body></html>''' % {'0':seq, '1':len_large, '2':prev_link, '3':fp, '4':width, '5':height, '6':next_link})
    target.close() 
    
    
def navigate_page(html_page, fp, width, height, seq):
    
    if seq == 1:
        prev_link = 'index.html'
        next_link = 'img_2.html'
        image_page(html_page, fp, width, height, seq, prev_link, next_link)   

    elif seq == len(large_images):
        prev_page = seq - 1
        prev_link = 'img_{0}.html'.format(prev_page)
        next_link = 'index.html'
        image_page(html_page, fp, width, height, seq, prev_link, next_link)  

    else:
        prev_page = (seq - 1)
        prev_link = 'img_{0}.html'.format(prev_page)
        next_page = (seq + 1)
        next_link = 'img_{0}.html'.format(next_page)     
        image_page(html_page, fp, width, height, seq, prev_link, next_link)
            
def row_breaks(len_large):
    
    new_row = []
    z_index = len_large + 1
    for seq in range(1, z_index):
        if (seq % 5 == 0):
            new_row.append((seq + 1))
            
    #new_row = [6, 11, 16, 21, 26, 31 of 30]
    return new_row

            
def small_cells(reg_index, fp, img_dir, width, height, seq):
    
    if fp == 'image1_00.jpg':
        #video link and new row
        reg_index.write('<tr><td class="index_page"><a href="https://www.youtube.com/embed/name"><img src="{0}" width="{1}" height="{2}" /></a></td>\n'.format(img_dir, width, height))
    
    elif fp == 'image2_00.jpg':
        #video link and new row
        reg_index.write('<tr><td class="index_page"><a href="https://www.youtube.com/embed/name"><img src="{0}" width="{1}" height="{2}" /></a></td>\n'.format(img_dir, width, height))
    
    elif seq == 7:
        #new row
        reg_index.write('</tr><tr><td class="index_page" align="center"><img src="{0}" width="{1}" height="{2}" /></td>\n'.format(img_dir, width, height)) 
    
    elif seq == len(small_images):
        reg_index.write('<td class="index_page" align="center"><img src="{0}" width="{1}" height="{2}" /></td></tr></table>'.format(img_dir, width, height))    
    
    else:
        reg_index.write('<td class="index_page" align="center"><img src="{0}" width="{1}" height="{2}" /></td>\n'.format(img_dir, width, height))
        
def thumb_nails(new_row, reg_index, img_dir, thumb_width, thumb_height, seq):
    
    if thumb_width == 100:
    
        if seq == 1:
            reg_index.write('<tr><td class="index_page" align="center"><a href="img_{0}.html"><img src="{1}" width="{2}" height="{3}" /></a></td>\n'.format(seq, img_dir, thumb_width, thumb_height)) 
        
        elif seq in new_row:
            reg_index.write('</tr><tr><td class="index_page" align="center"><a href="img_{0}.html"><img src="{1}" width="{2}" height="{3}" /></a></td>\n'.format(seq, img_dir, thumb_width, thumb_height))
            
        elif seq == len(large_images):
            reg_index.write('<td class="index_page" align="center"><a href="img_{0}.html"><img src="{1}" width="{2}" height="{3}" /></a></td></tr></table>\n</body></html>\n'.format(seq, img_dir, thumb_width, thumb_height))        
            
        else:
            reg_index.write('<td class="index_page" align="center"><a href="img_{0}.html"><img src="{1}" width="{2}" height="{3}" /></a></td>\n'.format(seq, img_dir, thumb_width, thumb_height))
    
            
if __name__ == "__main__":
    
    dir_path = '/absolute/path/to/album/img_dst'    
    href_path = '/relative/path/to/album/img_dst'
    index_page = '/absolute/path/to/album/index.html'    
    
    #image properties (width, height, orientation) corrupted; use gimp and this dict
    small_list = ['image1_00.jpg', 'image01.jpg', 'image02.jpg', 'image2_00.jpg', 'image1.jpg', 'image2.jpg', 'image3.jpg', \
                  'image5.jpg', 'image6.jpg']
    small_images = {1:['image1_00.jpg', 240, 320], 2:['image01.jpg', 320, 240], 3:['image02.jpg', 320, 240], 4:['image2_00.jpg', 240, 320],\
                    5:['image1.jpg', 240, 320], 6:['image2.jpg', 240, 320], 7:['image3.jpg', 320, 240], 8:['image5.jpg', 240, 320], 9:['image6.jpg', 240, 320]}   
    
    reg_index = open(index_page, 'w')
    reg_index.write(album_head)  
    reg_index.write('<tr><td colspan="3" align="center">No links except to videos</td></tr>\n')    
    
    for seq in sorted(small_images):
        fp = small_images[seq][0]
        new_name = '{0}_2019-07-27.jpg'.format(fp[:-4])
        img_dir = os.path.join(dir_path, new_name)
        width = small_images[seq][1]
        height = small_images[seq][2]
        #9 images; change full img_dir path to relative img_href path
        small_cells(reg_index, fp, img_dir, width, height, seq)                            
    
    reg_index.close()
    
    #build dict of large pics
    large_images = {}
    count = 0
    for fp in os.listdir(dir_path):
        if fp.startswith('image'):
            pass
        else:
            img_dir = os.path.join(dir_path, fp)  
            fn_base, fn_ext = os.path.splitext(fp)
            if fn_ext.lower() == '.jpg': 
                count = count + 1
                #prop_list = [fp, width, height]
                prop_list = get_properties(img_dir, fp)
                large_images[count] = prop_list        
    
    #write to index, album pages
    len_large = len(large_images)
    new_row = row_breaks(len_large)
    reg_index = open(index_page, 'a')
    reg_index.write('''\n<p><a name="thumbnails"></a></p>
    <table class="index_page" width="800" align="center">\n<tr><td colspan="5" align="center">
    Thumbnails below are linked to larger images</td></tr>\n''')
    for seq in large_images:
        fp = large_images[seq][0]
        img_dir = os.path.join(href_path, fp)
        print img_dir
        width = large_images[seq][1]
        height = large_images[seq][2] 
        thumb_width = 100
        thumb_height = 75      
        thumb_nails(new_row, reg_index, img_dir, thumb_width, thumb_height, seq)
        html_page = os.path.join(img_page, 'img_{0}.html'.format(seq))
        #large_images[seq] = [fp, img_dir, width, height]
        navigate_page(html_page, fp, width, height, seq)
        
    reg_index.close()
        
            
                
