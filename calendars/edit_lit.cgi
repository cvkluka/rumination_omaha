#!/usr/bin/python
# coding: utf-8

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from string import Template
import sqlite3 as sqlite
import shutil
import cgi
#import cgitb
#cgitb.enable()
from types import ListType

import datetime
from datetime import timedelta
import time
from dateutil.rrule import rrule, WEEKLY
from dateutil.relativedelta import relativedelta
import calendar

import lit_mgmt
import email_out

import headers
from headers import edit_litheader
from config_cal import base_path, lit_db, HD_db, email_from, email_to, mail_path

'''Edit the liturgy calendar (Mass, Confession, Eucharistic Adoration)
   list_vals: check if they creates duplicate entries of text inputs on reload
   sub_new[key] is a list whose values appear in random order'''

form = cgi.FieldStorage()
fields = {}

form_list = ['start_date', 'end_date',  \
             'event1_name', 'event1_menu', 'event1_starttime', 'event1_endtime', 'event1_location', \
             'event2_name', 'event2_menu', 'event2_starttime', 'event2_endtime', 'event2_location', \
             'event3_name', 'event3_menu', 'event3_starttime', 'event3_endtime', 'event3_location', \
             'event4_name', 'event4_menu', 'event4_starttime', 'event4_endtime', 'event4_location', \
             'event5_name', 'event5_text', 'event5_starttime', 'event5_endtime', 'event5_location']

sub_flds = {'start_date':'', 'end_date':'',  \
            'event1_name':'event1_menu', 'event1_menu':'', 'event1_starttime':'', 'event1_endtime':'', 'event1_location':'', \
            'event2_name':'event2_menu', 'event2_menu':'', 'event2_starttime':'', 'event2_endtime':'', 'event2_location':'', \
            'event3_name':'event3_menu', 'event3_menu':'', 'event3_starttime':'', 'event3_endtime':'', 'event3_location':'', \
            'event4_name':'event4_menu', 'event4_menu':'', 'event4_starttime':'', 'event4_endtime':'', 'event4_location':'', \
            'event5_name':'event5_text', 'event5_text':'', 'event5_starttime':'', 'event5_endtime':'', 'event5_location':'' }

event_options = {'00_Select':'Select', '01_Mass_Cathedral':'Mass (Cathedral)', '02_Virtual_Mass':'Virtual Mass', \
                 '04_Hispanic_Mass':'Hispanic Mass', '05_Mass_Outdoors':'Mass (Outdoors)'}

location_options = {"00_Select":"Select", "01_SHC_Cathedral":"SHC (Cathedral)", "02_SHC_Outdoors":"SHC (Outdoors)" }

def gen_time(f1):

    # html page options
    time_tuples = []
    f1_time_start = datetime.datetime.combine(f1, datetime.time(7, 30))
    f1_time_end = datetime.datetime.combine(f1, datetime.time(23, 30))
    delta = 30

    def dt_range(f1_time_start, f1_time_end, delta):
        current = f1_time_start
        while current <= f1_time_end:
            yield current
            current += delta

    # all mass times (f1)
    for dt in dt_range(f1_time_start, f1_time_end, timedelta(minutes=30)):
        time_str = datetime.datetime.strftime(dt, '%H:%M')
        fmt_time = datetime.datetime.strftime(dt, '%-I:%M %p')
        if time_str == '10:30':
            time_tuples.append((time_str, fmt_time))
            end_edTime = datetime.datetime.combine(f1, datetime.time(10, 45))
            end_edStr = datetime.datetime.strftime(end_edTime, '%H:%M')
            fmt_endEd = datetime.datetime.strftime(end_edTime, '%-I:%M %p')
            time_tuples.append((end_edStr, fmt_endEd))
        if time_str == '12:00':
            time_tuples.append((time_str, fmt_time))
            # noon mass is at 12:10
            noon_time = datetime.datetime.combine(f1, datetime.time(12, 10))
            noon_str = datetime.datetime.strftime(noon_time, '%H:%M')
            fmt_noon = datetime.datetime.strftime(noon_time, '%-I:%M %p')
            time_tuples.append((noon_str, fmt_noon))
        else:
            time_tuples.append((time_str, fmt_time))

    time_tuples = sorted(time_tuples)
    time_tuples.insert(0, ('Select', 'Select'))

    return time_tuples

def start_time(dt, event_starttime):

    '''start_time() combines the time submitted in the form with the date (dt); example form submit: 16:30
    when launched, dt = start_date, a string; otherwise dt is a date() in gen_range list'''

    start_options = []
    if event_starttime in ['Select', '']:
        start_options.append('')

    else:
        # start value is a date string passed by arg
        if dt == start_date:
            dto = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            time_start = datetime.datetime.strptime(event_starttime, '%H:%M').time()
            dt_start = datetime.datetime.combine(dto, time_start)
            dt_starts = datetime.datetime.strftime(dt_start, '%Y-%m-%d %H:%M:%S')[:-3]
            start_options.append(dt_starts)
            # date object not used but leave this in
            start_options.append(dt_start)
        else:
            # dt is a date() object
            time_start = datetime.datetime.strptime(event_starttime, '%H:%M').time()
            dt_start = datetime.datetime.combine(dt, time_start)
            dt_starts = datetime.datetime.strftime(dt_start, '%Y-%m-%d %H:%M:%S')[:-3]
            start_options.append(dt_starts)
            # date object not used but leave this in
            start_options.append(dt_start)

    dt_starts = start_options[0]

    return dt_starts


def end_time(dt, event_endtime):

    end_options = []
    if event_endtime in ['Select', '']:
        end_options.append('')

    else:
        if dt == start_date:
            dto = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            time_end = datetime.datetime.strptime(event_endtime, '%H:%M').time()
            dt_end = datetime.datetime.combine(dto, time_end)
            dt_ends = datetime.datetime.strftime(dt_end, '%Y-%m-%d %H:%M:%S')[:-3]
            end_options.append(dt_ends)
            end_options.append(dt_end)
        else:
            # dt is a date() object, no conversion required
            time_end = datetime.datetime.strptime(event_endtime, '%H:%M').time()
            dt_end = datetime.datetime.combine(dt, time_end)
            dt_ends = datetime.datetime.strftime(dt_end, '%Y-%m-%d %H:%M:%S')[:-3]
            end_options.append(dt_ends)
            end_options.append(dt_end)

    dt_ends = end_options[0]

    return dt_ends


def gen_range(f1, f2):

    '''establish menu date options based on a predetermined date range;
    times are omitted (they differ for the 5 possible events per page)'''
    date_range = []
    for dt in rrule(WEEKLY, dtstart=f1, until=f2):
        date_range.append(dt.date())

    return date_range

def html_options(f1):

    html_range = []
    last_option = f1 + relativedelta(months=2)
    for dt in rrule(WEEKLY, dtstart=f1, until=last_option):
        html_range.append(dt.date())

    return html_range


def hd_table():

    hd_values = {}

    try:
        con = sqlite.connect(HD_db)
        cursor = con.cursor()
        cursor.execute("SELECT Holy_Day, Actual, Observed FROM hd_schedule")
        rows = cursor.fetchall()
        for row in rows:
            Holy_Day = str(row[0])
            Actual_date = str(row[1])
            Observed_date = str(row[2])
            hd_values[Holy_Day] = [Actual_date, Observed_date]
        con.commit()
        con.close()

    except IOError:
        print('Could not open database. Please contact {0}'.format(email_from))
        sys.exit(1)

    return hd_values

def load_db(dts):

    event_data = {}
    date_value = []

    try:
        if isinstance(dts, basestring):
            con = sqlite.connect(lit_db)
            cursor = con.cursor()
            cursor.execute("SELECT ID, Event_Start, Input_Name, Liturgy_Event, Event_End, \
                            Event_Location from lit_schedule WHERE Event_Start like ?", (dts+'%',))
            rows = cursor.fetchall()
            for row in rows:
                event_data[row[0]] = [row[1:]]
            con.commit()
            con.close()

    except IOError:
        print('Could not read the date! Please contact {0}'.format(email_from))
        sys.exit(1)

    # Event_Start, Holy_Day, Week_Day, Input_Name, Liturgy_Event,
    # Event_End, Event_Location
    for id_rcd in event_data:
        for tup in event_data[id_rcd]:
            str_values = []
            for v in tup:
                str_values.append(str(v))
            event_data[id_rcd] = str_values

    return event_data


def read_form(**kw):

    fields = kw.get('fields', {})

    for field in form_list:
        value = form.getvalue(field)
        if isinstance(value, ListType):
            fields[field] = ', '.join(value)
        else:
            fields[field] = form.getvalue(field)

        if form.getvalue(field) == None:
            fields[field] = ''

        for sub in sub_flds:
            if sub == field:
                sub_flds[sub] = fields[field]

                if sub_flds[sub] != '':
                    list_vals = []
                    if isinstance(sub_flds[sub], (list,)):
                        for val in sub_flds[sub]:
                            list_vals.append(sub_flds[sub])
                        sub_flds[sub] = list_vals

    return sub_flds


def check_errors(dt, dkey, key_values):

    # key_values =
    # [event_name, event_value, event_start, event_end, event_location]
    omit = get_omitValues(sub_new, dkey)
    event_errors = []
    fmt_dt = dt.strftime("%-d %B %Y")

    if dkey not in omit and len(key_values) == 5:
        # ['event1_menu', 'Mass', '2018-12-27 09:00', '2018-12-27 07:30', 'SHC']
        event_name = key_values[0]
        event_value = key_values[1]
        event_start = key_values[2]
        event_end = key_values[3]

        if len(event_value) >= 50:
            event_errors.append('Event 5 character limit exceeded!')
        if event_value not in ['Select', ''] and event_start in ['Select', '']:
            event_errors.append('Event {0} is missing a start time on {1}'.format(dkey, fmt_dt))

        if len(event_start) == 16 and len(event_end) == 16:
            dto_start = datetime.datetime.strptime(event_start, '%Y-%m-%d %H:%M')
            dto_end = datetime.datetime.strptime(event_end, '%Y-%m-%d %H:%M')
            if dto_end < dto_start:
                event_errors.append('The ending time is scheduled before the start time for Event {0} on {1}'.format(dkey, fmt_dt))
            elif dto_end == dto_start:
                event_errors.append('The ending time is the same as the start time for Event {0} on {1}'.format(dkey, fmt_dt))

    return event_errors

def add_record(ilist):
    # ['event1_menu', 'Mass', '2018-12-03 07:30', '', 'SHC'];
    event_name = ilist[0]
    event_value = ilist[1]
    event_start = ilist[2]
    event_end = ilist[3]
    event_location = ilist[4]

    try:
        con = sqlite.connect(lit_db)
        cursor = con.cursor()
        cursor.execute('''INSERT INTO lit_schedule (Event_Start, Input_Name, Liturgy_Event, Event_End, Event_Location)
                       VALUES(?, ?, ?, ?, ?)''', (event_start, event_name, event_value, event_end, event_location))
        con.commit()
        con.close()

    except sqlite.Error as er:
        sys.exit(1)

def modify_record(mlist):

    # ['event1_menu', 'Mass', '2018-12-03 07:30', '', 'SHC', 137]
    event_name = mlist[0]
    event_value = mlist[1]
    event_start = mlist[2]
    event_end = mlist[3]
    event_location = mlist[4]
    event_id = mlist[5]

    try:
        con = sqlite.connect(lit_db)
        cursor = con.cursor()
        cursor.execute("UPDATE lit_schedule SET Event_Start=?, Liturgy_Event=?, Event_End=?, Event_Location=? \
                        WHERE Input_Name=? AND ID=?", (event_start, event_value, event_end, event_location, event_name, event_id))
        con.commit()
        con.close()

    except IOError:
        print('Could not modify the database! Please contact {0}'.format(email_from))
        sys.exit(1)

def get_vars(sub_flds, dt):

    sub_new = {}

    for key in range(1, 6):
        sub_new[key] = []

        for sub in sub_flds:
            if sub in ['start_date', 'end_date']:
                pass

            else:
                num = sub[5]
                if num == str(key):
                    if sub.endswith('name'):
                        if int(num) == 5:
                            sub_new[key].append('event{0}_name=event{0}_text'.format(num, num))
                        else:
                            sub_new[key].append('event{0}_name=event{0}_menu'.format(num, num))

                    elif sub == 'event{0}_starttime'.format(key):
                        event_starttime = sub_flds[sub]
                        dt_starts = start_time(dt, event_starttime)
                        sub_new[key].append('event{0}_starttime={1}'.format(num, dt_starts))

                    elif sub == 'event{0}_endtime'.format(key):
                        event_endtime = sub_flds[sub]
                        dt_ends = end_time(dt, event_endtime)
                        sub_new[key].append('event{0}_endtime={1}'.format(num, dt_ends))

                    elif sub == 'event{0}_location'.format(key):
                        if sub_flds[sub] in ['Select', '']:
                            sub_new[key].append('event{0}_location=SHC'.format(num))
                        else:
                            sub_new[key].append('event{0}_location={1}'.format(num, sub_flds[sub]))

                    else:
                        sub_new[key].append('{0}={1}'.format(sub, sub_flds[sub]))

    return sub_new


def compare_dict(event_data, dts):

    db_vals = []
    for id_rcd in event_data:
        event_date = event_data[id_rcd][0]
        event_name = event_data[id_rcd][1]
        # compare db date with dts/date str
        if event_date[:10] == dts:
            db_vals.append(event_name)

    set_add = []
    s = set(db_vals)
    for n in ['event1_menu', 'event2_menu', 'event3_menu', 'event4_menu', 'event5_text']:
        if n in s:
            pass
        else:
            set_add.append(n)

    return set_add


def get_omitValues(sub_new, dkey):

    # omit key values of event (numbers) not used
    omit = []

    for k in form_list[2:]:
        for v in sub_new[dkey]:
            vlist = v.split('=')
            if vlist[0] == k:
                if vlist[0].endswith('menu') and vlist[1] in ['Select', '']:
                    omit.append(dkey)
                elif vlist[0].endswith('text') and vlist[1] in ['Select', '']:
                    omit.append(dkey)

    return omit

def get_keyValues(sub_new, dkey):

    # sub_new list values show up in random order - order them
    key_values = []

    for k in form_list[2:]:
        for v in sub_new[dkey]:
            vlist = v.split('=')
            if vlist[0] == k:
                key_values.append(vlist[1])

    return key_values

#===================================Build html pages===================================#

def db_events(target, start_date, db_values, dkey):
    '''selected values reflect event_data or key_values;
       event_data[id_rcd] = db table: [Event_Start, Input_Name, Liturgy_Event, Event_End, Event_Location]'''
    event_start = db_values[0]
    event_name = db_values[1]
    event_value = db_values[2]
    event_end = db_values[3]
    event_location = db_values[4]

    target.write('<tr><td class="main"><b>Event {0} </b><br/>'.format(dkey))
    if event_name == 'event5_text':
        target.write('<input type="text" size="40" maxlength="50" name="event5_text" value="{0}"></td>\n'.format(event_value))
    else:
        target.write('<select class="select_menu" name="%(0)s">\n' % {'0':event_name})
        for key in sorted(event_options):
            if key[3:] == event_value:
                target.write('<option selected value="{0}">{1}</option>\n'.format(event_value, event_options[key]))
            else:
                target.write('<option value="{0}">{1}</option>\n'.format(key[3:], event_options[key]))
        target.write('</select></td>\n')

    target.write('<td class="main"><b>Start time</b><br/>\n')
    target.write('<select class="select_time" name="event{0}_starttime">\n'.format(dkey))

    for time_option, fmt_time in time_tuples:
        if event_start[-5:] == time_option:
            target.write('<option selected value="{0}">{1}</option>\n'.format(event_start[-5:], fmt_time))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(time_option, fmt_time))
    target.write('</select></td>\n')

    target.write('<td class="main"><b>End&nbsp;(Optional)</b><br/>\n')
    target.write('<select class="select_time" name="event{0}_endtime">\n'.format(dkey))
    for time_option, fmt_time in time_tuples:
        if event_end[-5:] == time_option:
            target.write('<option selected value="{0}">{1}</option>\n'.format(event_end[-5:], fmt_time))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(time_option, fmt_time))
    target.write('</select></td>\n')

    target.write('<td class="main"><b>Location </b>')
    target.write('<br/><select class="select_menu" name="event{0}_location">'.format(dkey))
    for key in sorted(location_options):
        if event_location == location_options[key]:
            target.write('<option selected value="{0}">{1}</option>\n'.format(key[3:], event_location))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(key[3:], location_options[key]))
    target.write('</select></td></tr>\n')

def sub_events(target, key_values, dkey):
    '''selected values reflect event_data or key_values;
       event_data[id_rcd] = db table: [Event_Start, Input_Name, Liturgy_Event, Event_End, Event_Location]
       key_values by date and dkey:'''
    event_name = key_values[0]
    event_value = key_values[1]
    event_start = key_values[2]
    event_end = key_values[3]
    event_location = key_values[4]

    target.write('<tr><td class="main"><b>Event {0} </b><br/>'.format(dkey))
    if event_name == 'event5_text':
        target.write('<input type="text" size="40" maxlength="50" name="event5_text" value="{0}"></td>\n'.format(event_value))
    else:
        target.write('<select class="select_menu" name="%(0)s">\n' % {'0':event_name})
        for key in sorted(event_options):
            if key[3:] == event_value:
                target.write('<option selected value="{0}">{1}</option>\n'.format(event_value, event_options[key]))
            else:
                target.write('<option value="{0}">{1}</option>\n'.format(key[3:], event_options[key]))
        target.write('</select></td>\n')

    target.write('<td class="main"><b>Start time</b><br/>\n')
    target.write('<select class="select_time" name="event{0}_starttime">\n'.format(dkey))

    for time_option, fmt_time in time_tuples:
        if event_start[-5:] == time_option:
            target.write('<option selected value="{0}">{1}</option>\n'.format(event_start[-5:], fmt_time))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(time_option, fmt_time))
    target.write('</select></td>\n')

    target.write('<td class="main"><b>End&nbsp;(Optional)</b><br/>\n')
    target.write('<select class="select_time" name="event{0}_endtime">\n'.format(dkey))
    for time_option, fmt_time in time_tuples:
        if event_end[-5:] == time_option:
            target.write('<option selected value="{0}">{1}</option>\n'.format(event_end[-5:], fmt_time))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(time_option, fmt_time))
    target.write('</select></td>\n')

    target.write('<td class="main"><b>Location </b>')
    target.write('<br/><select class="select_menu" name="event{0}_location">'.format(dkey))
    for key in sorted(location_options):
        if event_location == location_options[key]:
            target.write('<option selected value="{0}">{1}</option>\n'.format(key[3:], event_location))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(key[3:], location_options[key]))
    target.write('</select></td></tr>\n')


def get_feedback(key_values):

    '''to add or modify an event: key_values = [event_name, event_value, event_start, event_end, event_location] '''

    new_keys = []
    statements = []
    if len(key_values) == 5:
        for index, key in enumerate(key_values):
            if index == 0:
                pass
            elif '_' in key:
                k = key.replace('_', ' ')
                new_keys.append(k)
            elif index == 3 and len(key) == 16:
                k = key[-5:]
                new_keys.append(k)
            else:
                new_keys.append(key)

    statement = ' '.join(new_keys)

    return statement


def edit_day(start_date, title_msg, action):

    '''event_data retrieves liturgical events for this day/dt from the form (if populated) or the db table
       event_data[id_rcd] = db table: [Event_Start, Input_Name, Liturgy_Event, Event_End, Event_Location]
       key_values by dt and # = ['event1_name', 'event1_menu', 'event1_start', 'event1_end', 'event1_location']
       set_add and event_data are global vars;edit_lithead is returned by headers.edit_litheader(edit_path)'''
    target = open(lit_edit, 'w')
    target.write(edit_lithead)
    target.write('''<tr><td colspan="4" class="filler" align="center"><b>{0}</b></td></tr>\n<tr><td class="main" colspan="2"><b>Start date</b>: {1} {2}</td><td class="main" colspan="2"><b>End date</b>: {3} \n<select class="select_menu" name="end_date">\n'''.format(title_msg, f1_weekday, fmt_start, f1_weekday))
    for dt in html_range:
        fmt_date = dt.strftime("%d %b %Y")
        dt_str = datetime.datetime.strftime(dt, '%Y-%m-%d')
        if start_date == dt_str:
            target.write('<option selected value="{0}">{1}</option>\n'.format(dt, fmt_date))
        else:
            target.write('<option value="{0}">{1}</option>\n'.format(dt, fmt_date))
    target.write('</select></td></tr>\n')

    for dkey in sub_new:
        key_values = get_keyValues(sub_new, dkey)
        if action == 'start':
            for id_rcd in sorted(event_data):
                # db columns:[Event_Start, Input_Name, Liturgy_Event, Event_End, Event_Location]
                if event_data[id_rcd][1] == key_values[0]:
                    event_start = event_data[id_rcd][0] #why is event start also defined on 676?
                    dto_db = datetime.datetime.strptime(event_start, '%Y-%m-%d %H:%M')
                    if dto_db.date() == f1.date():
                        db_values = event_data[id_rcd]
                        if len(db_values) == 5:
                            db_events(target, start_date, db_values, dkey)

            # key_values empty, no db entry, use defaults;
            for k in sorted(set_add):
                if k == key_values[0]:
                    sub_events(target, key_values, dkey)

        elif action == 'reload':
            # use defaults;
            for k in ['event1_menu', 'event2_menu', 'event3_menu', 'event4_menu', 'event5_text']:
                if k == event_name:
                    sub_events(target, key_values, dkey)

    target.write('''<tr><td class="main" colspan="4" align="center">
        <input type="hidden" name="start_date" value="{0}">
        <input type="submit" name="modify" value="Update"/></td></tr>
        </form>\n<form action="{1}" method="post">
        <tr><td class="noborder" colspan="4">
        <input type="submit" name="Cancel" value="Cancel"/></td>
        </tr></table></form>\n</body></html>'''.format(start_date, litcon_this_month))
    target.close()

    try:
        t = Template(open(lit_edit).read())
        print(t.substitute(start_date=start_date, litcon_this_month=litcon_this_month))

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)


def confirm_page(f1, f2, title_msg):

    lit_confirm = os.path.join(base_path, 'calendar/control/liturgy/lit_confirm.html')
    confirm_litheader = os.path.join(base_path, 'calendar/forms/confirm_litheader.html')

    target = open(lit_confirm, 'w')

    try:
        shutil.copyfileobj(open(confirm_litheader, 'rb'), target)

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)

    # redirect the user from the confirmation page back to the calendar page
    target.write('''<tr><td class="filler" colspan="3" align="center">{0}</td></tr>
    <tr><td class="main" colspan="3" align="center">Reload the calendar month page(s)
    as needed to view your changes.</td></tr>\n<tr><td colspan="3" align="center">\n
    <form action="{1}" method="post">
    <input type="submit" name="Submit" value="Return"></td></tr></form>\n
    </table></body></html>\n'''.format(title_msg, litcon_this_month))
    target.close()

    try:
        t = Template(open(lit_confirm).read())
        print(t.substitute(title_msg=title_msg, litcon_this_month=litcon_this_month))

    except IOError:
        print('Could not read the form! Please contact {0}'.format(email_from))
        sys.exit(1)

    for m in [f1, f2]:
        # limited to 2 months, enough for now
        dtg = m.replace(day=1)
        date_start = datetime.datetime.strftime(dtg, '%Y-%m-%d')
        # lit_mgmt will copy the headers and retrieve sqlite data
        lit_mgmt.copy_header(dtg, date_start)

    email_envoi = open(mail_path, 'w')
    email_subject = 'Change in Liturgy Schedule'
    email_string = '\n'.join(full_list)
    email_message = '{0}\n'.format(email_string)
    email_envoi.write(email_message)
    email_envoi.close()
    email_out.send_email(email_from, email_to, email_subject)


if __name__ == "__main__":

    print("Content-type: text/html; charset=utf-8\n")

    start_date = form.getvalue('start_date')
    f1 = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    start_month = f1.replace(day=1)  # 2019-12-01 00:00:00
    month_name = f1.strftime("%B")
    abs_paths = ['litopen_abs', 'litcon_abs']
    edit_lithead = headers.edit_litheader(edit_path='/shc/akc/edit_lit.cgi')
    lit_edit = os.path.join(base_path, 'calendar/control/liturgy/lit_edit.html')
    litcon_this_month = '/shc/calendar/control/liturgy/{0}/{1}.html'.format(f1.year, month_name)
    sub_flds = read_form(fields=fields)
    sub_new = get_vars(sub_flds, dt=start_date)
    event_data = load_db(dts=start_date)
    html_range = html_options(f1)
    set_add = compare_dict(event_data, dts=start_date)
    time_tuples = gen_time(f1)

    f1_weekday = calendar.day_name[f1.weekday()]
    fmt_start = f1.strftime("%-d %B %Y")
    hd_values = hd_table()
    full_list = []

    if 'modify' in form:
        # update if event exists and if not, add;
        end_date = sub_flds['end_date']
        f2 = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        fmt_end = f2.strftime("%-d %B %Y")
        date_range = gen_range(f1, f2)
        errors = []
        mod_list = []
        insert_list = []

        if len(date_range) > 0:
            for dt in date_range:
                dts = datetime.datetime.strftime(dt, '%Y-%m-%d')
                event_data = load_db(dts)
                # compare the db table contents for each day with event_name list
                set_add = compare_dict(event_data, dts)
                sub_new = get_vars(sub_flds, dt)
                for dkey in sorted(sub_new):
                    key_values = get_keyValues(sub_new, dkey)

                    omit = get_omitValues(sub_new, dkey)
                    if dkey not in omit:
                        if len(key_values) == 5:
                            event_name = key_values[0]
                            # check for event_name key in event_data;
                            # event_name = event1_menu == Input_Name
                            for id_rcd in event_data:
                                # db columns: [Event_Start, Input_Name,
                                # Liturgy_Event, Event_End, Event_Location]
                                db_start = event_data[id_rcd][0]
                                event_record = event_data[id_rcd][1]
                                db_value = event_data[id_rcd][2]
                                if event_record == event_name:
                                    dto_db = datetime.datetime.strptime(db_start, '%Y-%m-%d %H:%M')
                                    if dto_db.date() == dt:
                                        event_errors = check_errors(dt, dkey, key_values)
                                        errors.append(event_errors)
                                        statement = get_feedback(key_values)
                                        # full_list statement omits '_'
                                        update_statement = 'Update {0}'.format(statement)

                                        if update_statement not in full_list:
                                            full_list.append(update_statement)
                                            key_values.append(id_rcd)
                                            mod_list.append(key_values)

                            for k in set_add:
                                if k == event_name:
                                    event_errors = check_errors(dt, dkey, key_values)
                                    errors.append(event_errors)
                                    statement = get_feedback(key_values)
                                    insert_statement = 'Insert {0}'.format(statement)
                                    if insert_statement not in full_list:
                                        full_list.append(insert_statement)
                                        insert_list.append(key_values)

        all_errors = []
        for e in errors:
            if e == []:
                pass
            else:
                for l in e:
                    all_errors.append(l)

        if len(all_errors) > 0:
            title_msg = '<br/>'.join(all_errors)
            edit_day(start_date, title_msg, action='reload')


        else:
            full_list = sorted(full_list)
            title_msg = '<br/>'.join(full_list)

            for mlist in mod_list:
                if len(mlist) == 6:
                    modify_record(mlist)

            for ilist in insert_list:
                if len(ilist) == 5:
                    add_record(ilist)

            confirm_page(f1, f2, title_msg)

    else:
        headers = []

        for hd in hd_values:
            date_hd = hd_values[hd][0]
            if date_hd == start_date:
                headers.append(hd[:-5].replace('_', ' '))

        if len(headers) > 0:
            hd_header = headers[0]
            # Account for Holy Days
            title_msg = ('''You may edit the liturgy schedule starting on
            {0} {1} ({2}). <br/><br/>Please select / complete
            all liturgical activities that apply.'''
            .format(f1_weekday, fmt_start, hd_header))
            edit_day(start_date, title_msg, action='start')

        else:
            title_msg = ('''You may edit the liturgy schedule starting on
            {0} {1}.<br/><br/>Please select / complete all liturgical
            activities that apply.'''.format(f1_weekday, fmt_start))
            edit_day(start_date, title_msg, action='start')
