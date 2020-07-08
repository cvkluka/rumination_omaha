#!/usr/bin/python

import sqlite3 as sqlite
import os, sys
import shutil

import calendar
import datetime
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

from ConfigParser import SafeConfigParser
from config_cal import email_from, base_path, web_path, lit_db, HD_db, months_ini
import headers
from headers import page_header, weekday_cols

'''launched by cal_months.py or edit_lit.cgi; date_start is passed; calendar page headers are read from months.ini'''

def run_copy(current_month, current_default):

    target = open(current_default, 'w')
    try:
        shutil.copy(current_month, current_default)

    except IOError:
        print('Could not read the management form! Please contact {0}'.format(email_from))
        sys.exit(1)

    target.close()


def hd_table():

    hd_data = {}

    try:
        con = sqlite.connect(HD_db)
        cursor = con.cursor()
        cursor.execute("SELECT Holy_Day, Actual, Observed FROM hd_schedule")
        rows = cursor.fetchall()
        for row in rows:
            Holy_Day = str(row[0])
            Actual_date = str(row[1])
            Observed_date = str(row[2])
            hd_data[Holy_Day] = [Actual_date, Observed_date]
        con.commit()
        con.close()

    except IOError:
        print('Could not open database. Please contact {0}'.format(email_from))
        sys.exit(1)

    return hd_data

def read_litdb():

    event_tuple = []
    try:
        con = sqlite.connect(lit_db)
        cursor = con.cursor()
        cursor.execute('SELECT Event_Start, Liturgy_Event, Event_End, Event_Location from lit_schedule')
        rows = cursor.fetchall()
        for row in rows:
            event_tuple.append(row[0:])

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)

    con.commit()
    con.close()

    return event_tuple

def get_eventEnd(dt, event_time):

    end_options = []
    if event_time in ['Select', '']:
        end_options.append('')

    else:
        strip_time = event_time[-5:]
        time_end = datetime.datetime.strptime(strip_time, '%H:%M').time()
        if isinstance(dt, datetime.date):
            dt_end = datetime.datetime.combine(dt, time_end)
            time_endfmt = datetime.datetime.strftime(dt_end, '%-I:%M %p')
            end_options.append(time_endfmt)

    time_endfmt = end_options[0]

    return time_endfmt

def cell_content(cal_path, cal_day, cur_day):

    content_list = []
    hd_data = hd_table()
    event_tuple = read_litdb()

    for hd in hd_data:
        holy_day = hd[:-5].replace('_', ' ')
        actual_date = datetime.datetime.strptime(hd_data[hd][0], '%Y-%m-%d').date()
        observed_date = datetime.datetime.strptime(hd_data[hd][1], '%Y-%m-%d').date()
        if actual_date == cal_day:
            content_list.append('<b><font color="#9e0909">{0}</font></b><br/><br/>\n'.format(holy_day))

        elif observed_date == cal_day:
            content_list.append('<b><font color="#9e0909">{0} (Observed)</font></b><br/><br/>\n'.format(holy_day))

    for event_group in sorted(event_tuple):
        #(u'2018-10-07 13:00', u'Mass_(Hispanic)', u'', u'SHC')
        event_start = event_group[0]
        dtge = datetime.datetime.strptime(event_start, "%Y-%m-%d %H:%M")
        if dtge.date() == cal_day:
            #print(cal_day, 'in event_group') #ok
            dtg_arg = event_start.replace(' ', '_')
            time_starts = event_start[-5:]
            time_startfmt = datetime.datetime.strftime(dtge, "%-I:%M %p")
            value_list = event_group[1:]
            if value_list:
                dt = dtge.date()
                event = value_list[0]
                event_name = event.replace('_', ' ')
                if len(value_list) == 3:
                    event_time = value_list[1]
                    location = value_list[2]
                    time_endfmt = get_eventEnd(dt, event_time)

                    if cal_day >= cur_day:
                        content_list.append('{0} - {1} {2}<br/>\n'.format(time_startfmt, time_endfmt, event_name))

                    else:
                        #event is in the past; italicize
                        content_list.append('<i>{0} - {1}</i><br/>'.format(time_startfmt, event_name))


    if 'control' in cal_path:
        month_object = cur_day.replace(day=1)
        if cal_day >= month_object:
            if len(content_list) > 0:
                content_list.append('<a class="page" href="/shc/akc/edit_lit.cgi?start_date={0}">Edit</a>\
                                    or '.format(cal_day))
                content_list.append('<a class="page" href="/shc/akc/del_lit.cgi?start_date={0}">Delete</a>\
                                    <br/>\n'.format(cal_day))
            else:
                content_list.append('<br/><a class="page" href="/shc/akc/edit_lit.cgi?start_date={0}">Add</a>\
                                    <br/>\n'.format(cal_day))

    return content_list


def month_content(dtg, month_name, cal_path):

    #read holy day information from sql table
    cur_day = datetime.date.today()
    calendar.setfirstweekday(6)
    calobject = calendar.monthcalendar(dtg.year, dtg.month)
    nweeks = len(calobject)
    target = open(cal_path, 'a')

    for w in range(0,nweeks):
        week = calobject[w]
        target.write('</tr><tr>')

        for x in xrange(0,7):
            day = week[x]
            if day == 0:
                target.write('<td align="center"><table width="140"><tr><td class="num"></td></tr>\n')
                target.write('<tr><td class="weekday">&nbsp;</td></tr></table></td>\n')

            else:
                #fix day definition later (month and year)
                cal_day = datetime.date(dtg.year, dtg.month, day)
                content_list = cell_content(cal_path, cal_day, cur_day)
                if content_list and len(content_list) > 0:
                    content_str = ''.join(content_list)
                    if cal_day == cur_day:
                        # set day number in red;
                        target.write('<td align="center"><table width="140"><tr><td class="number">{0}</td></tr>\
                                    \n<tr><td class="weekday">{1}</td></tr></table></td>\n'
                                     .format(day, content_str))
                    else:
                        target.write('<td align="center"><table width="140"><tr><td class="num">{0}</td></tr>\
                                    <tr><td class="weekday">{1}</td></tr></table></td>\n'
                                     .format(day, content_str))

                else:
                    #no events
                    target.write('<td align="center"><table width="140"><tr><td class="num">{0}</td></tr>\n'
                                 .format(day))
                    target.write('<tr><td class="weekday"></td></tr></table></td>\n')

    target.write('</table><br/></body></html>')
    target.close()

    #if the month == current month, copy to ../current_month.html
    if dtg.year == cur_day.year and dtg.month == cur_day.month:
        current_control = os.path.join(base_path, 'calendar/control/liturgy/{0}/{1}.html'
                                       .format(dtg.year, month_name))
        default_control = os.path.join(base_path, 'calendar/control/liturgy/current_month.html')
        run_copy(current_month=current_control, current_default=default_control)

        current_open = os.path.join(base_path, 'calendar/liturgy/{0}/{1}.html'.format(dtg.year, month_name))
        default_open = os.path.join(base_path, 'calendar/liturgy/current_month.html')
        run_copy(current_month=current_open, current_default=default_open)

def copy_header(dtg, month_start):

    #month_start is strftime for dtg, first day of month
    month_name = dtg.strftime("%B")
    parser = SafeConfigParser()
    parser.read(months_ini)

    html_header = headers.page_header(label='Liturgy')
    assoc_paths = {'litopen_abs':'litopen_head', 'litcon_abs':'litcon_head'}

    for cal_path in assoc_paths:
        for section_date in parser.sections():
            if section_date == month_start:
                abs_path = parser.get(section_date, cal_path)
                header_path = parser.get(section_date, assoc_paths[cal_path])

                target = open(abs_path, 'w')

                try:
                    shutil.copyfileobj(open(header_path, 'rb'), target)

                except IOError:
                    print('Could not read the form! Please contact {0}'.format(email_from))
                    sys.exit(1)

                target.close()

                month_content(dtg, month_name, cal_path=abs_path)

