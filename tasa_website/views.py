import json
import os
import random
import re
import requests
import string
import sqlite3
import time
import urllib
import yaml

from flask import Flask
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

import auth
import fb_events
import helpers

from . import app
from . import FAMILY_IMAGE_FOLDER
from . import IMAGE_FOLDER
from . import OFFICER_IMAGE_FOLDER
from . import FILES_FOLDER
from . import ROOT
from . import query_db

# This is kind of backwards, it's rendering a smaller template first that is
# part of the larger index version. Should fix soon.
@app.route('/')
def index():
    events = query_db('select title, time, location, link, image_url, unix_time from events order by unix_time desc')
    upcoming_events = filter(lambda e: e['unix_time'] > int(time.time()), events)
    if len(upcoming_events) == 0:
        return render_template('show_latest_event.html')
    upcoming_events.sort(key=lambda e: e['unix_time'])
    return render_template('show_latest_event.html', event=upcoming_events[0])

@app.route('/events', methods=['GET'])
def event_list():
    query = 'select title, time, location, link, image_url, unix_time '\
            'from events order by unix_time desc limit 24'
    events = query_db(query)
    upcoming = []
    recent = []
    current_time = int(time.time())
    for event in events:
        if event['unix_time'] > current_time:
            upcoming.append(event)
        else:
            recent.append(event)
    return render_template('events.html', recent=recent, upcoming=upcoming)

@app.route('/events', methods=['POST'])
def add_event():
    auth.check_login()
    try:
        url = request.form['link']
        # Facebook event url example:
        # https://www.facebook.com/events/1201801539835081/
        # Match the numbers between /s
        fb_event_id = re.match(r'.*/([0-9]+)/?$', url)
        if fb_event_id:
            fb_event_id = fb_event_id.group(1)
        else:
            raise Exception('Bad URL')

        res = fb_events.get_event(fb_event_id)
        title = res['name']
        location = res.get('place', {'name': ''})['name']

        time_str, unix_time = helpers.convert_time(res['start_time'])

        # another GET to get the cover photo
        image = fb_events.get_cover_photo(fb_event_id)
        # just resave it as a jpg
        image_ext = '.jpg'

        file_name = helpers.generate_random_filename(image_ext)
        image_url, image_path = helpers.create_file_paths(IMAGE_FOLDER, file_name)
        image.save(image_path, format='JPEG', quality=95, optimize=True, progressive=True)

        query = 'insert into events (title, time, location, link, image_url, unix_time)'\
                'values (?, ?, ?, ?, ?, ?)'

        query_db(query, [title, time_str, location, url, image_url, unix_time])
        flash('New event was successfully posted')
        return redirect(url_for('admin_panel'))
    except Exception as e:
        flash('Exception: ' + str(e))
        return redirect(url_for('admin_panel'))

@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    auth.check_login()
    query = 'delete from events where id = ?'
    query_db(query, (event_id,))
    return 'Deleted event'


@app.route('/admin', methods=['GET'])
def admin_panel():
    auth.check_login()
    events = query_db('select * from events order by unix_time desc')
    officers = query_db('select * from officers order by id')
    families = query_db('select * from families order by id')
    files = query_db('select * from files order by id')
    members = query_db('select * from members order by name')
    event_checkins = query_db('select * from event_checkins order by eventID')
    return render_template('admin.html', events=events, officers=officers, families=families, files=files, members=members, check_valid_checkin=check_valid_checkin)

@app.route('/officers', methods=['GET'])
def officer_list():
    query = 'select * from officers order by position'
    officers = query_db(query)
    return render_template('officers.html', officers=officers)

@app.route('/officers/<int:officer_id>', methods=['GET'])
def get_officer(officer_id):
    query = 'select * from officers where id = ?'
    officer = query_db(query, (officer_id,))[0]
    return json.dumps(dict(officer))

# This ideally should be PUT, but for simplicity on the client side
# (i.e. so we can use vanilla HTML form) we'll use POST instead.
@app.route('/officers/<int:officer_id>', methods=['POST'])
def update_officer(officer_id):
    auth.check_login()

    name = request.form['name']
    year = request.form['year']
    major = request.form['major']
    position = request.form['position']
    quote = request.form['quote']
    description = request.form['description']
    href = '#' + request.form['name']

    if helpers.check_file_in_request(request):
        try:
            image_url = helpers.save_request_file(request, OFFICER_IMAGE_FOLDER)
        except ValueError as e:
            flash('Exception: ' + str(e))
            return redirect(url_for('admin_panel'))
        query = (
            'update officers '
            'set name=?, year=?, major=?, position=?, quote=?, description=?, href=?, image_url=? '
            'where id=?'
        )
        query_db(query, [name, year, major, position, quote, description, href, image_url, officer_id])
    else:
        query = (
            'update officers '
            'set name=?, year=?, major=?, position=?, quote=?, description=?, href=? '
            'where id=?'
        )
        query_db(query, [name, year, major, position, quote, description, href, officer_id])
    flash('Updated ' + name)
    # TODO: think about doing all of these redirects javascript-side
    return redirect(url_for('admin_panel'))


@app.route('/officers/<int:officer_id>', methods=['DELETE'])
def delete_officer(officer_id):
    auth.check_login()
    query = 'delete from officers where id = ?'
    query_db(query, (officer_id,))
    return 'Deleted officer'

@app.route('/officers', methods=['POST'])
def add_officer():
    auth.check_login()

    try:
        image = helpers.file_from_request(request)
    except ValueError as e:
        flash('Exception: ' + str(e))
        return redirect(url_for('admin_panel'))

    image_url = helpers.save_request_file(request, OFFICER_IMAGE_FOLDER)

    name = request.form['name']
    year = request.form['year']
    major = request.form['major']
    position = request.form['position']
    quote = request.form['quote']
    description = request.form['description']
    # TODO: this doesn't need to be part of the model
    href = '#' + request.form['name']

    query = 'insert into officers (name, year, major, quote, description, image_url, position, href)'\
            'values (?, ?, ?, ?, ?, ?, ?, ?)'
    query_db(query, [name, year, major, quote, description, image_url, position, href])
    flash('New officer successfully posted')
    return redirect(url_for('admin_panel'))

@app.route('/families', methods=['POST'])
def add_family():
    auth.check_login()

    try:
        image = helpers.file_from_request(request)
    except ValueError as e:
        flash('Exception: ' + str(e))
        return redirect(url_for('admin_panel'))

    image_url = helpers.save_request_file(request, FAMILY_IMAGE_FOLDER)

    family_name = request.form['family_name']
    family_head1 = request.form['family_head1']
    family_head2 = request.form['family_head2']
    description = request.form['description']

    query = 'insert into families (family_name, family_head1, family_head2, description, image_url)'\
            'values (?, ?, ?, ?, ?)'
    query_db(query, [family_name, family_head1, family_head2, description, image_url])
    flash('New family successfully posted')
    return redirect(url_for('admin_panel'))

@app.route('/families/<int:family_id>', methods=['POST'])
def edit_family(family_id):
    auth.check_login()

    family_name = request.form['family_name']
    family_head1 = request.form['family_head1']
    family_head2 = request.form['family_head2']
    description = request.form['description']

    if helpers.check_file_in_request(request):
        try:
            image_url = helpers.save_request_file(request, FAMILY_IMAGE_FOLDER)
        except ValueError as e:
            flash('Exception: ' + str(e))
            return redirect(url_for('admin_panel'))
        query = (
            'update families '
            'set family_name=?, family_head1=?, family_head2=?, description=?, image_url=? '
            'where id=?'
        )
        query_db(query, [family_name, family_head1, family_head2, description, image_url, family_id])
    else:
        query = (
            'update families '
            'set family_name=?, family_head1=?, family_head2=?, description=?'
            'where id=?'
        )
        query_db(query, [family_name, family_head1, family_head2, description, family_id])
    flash('Updated ' + family_name)
    return redirect(url_for('admin_panel'))

@app.route('/families/<int:family_id>', methods=['DELETE'])
def delete_family(family_id):
    auth.check_login()
    query = 'delete from families where id = ?'
    query_db(query, (family_id,))
    return 'Deleted family'

@app.route('/families', methods=['GET'])
def families():
    query = 'select family_name, family_head1, family_head2, description, image_url from families'
    families = query_db(query)
    return render_template('families.html', families=families)

@app.route('/files', methods=['POST'])
def add_file():
    auth.check_login()

    name = request.form['name']
    file_url = request.form['file_url']

    query = 'insert into files (name, file_url)'\
            'values (?, ?)'
    query_db(query, [name, file_url])
    flash('New file successfully posted')
    return redirect(url_for('admin_panel'))

@app.route('/files', methods=['GET'])
def files():
    query = 'select * from files'
    files = query_db(query)
    return render_template('files.html', files=files)

@app.route('/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    auth.check_login()

    query = 'delete from files where id = ?'
    query_db(query, (file_id,))
    return 'Deleted file'

@app.route('/members', methods=['POST'])
def add_general_member():
    auth.check_login()

    name = request.form['name']
    year = request.form['year']
    email = request.form['email']
    findable = request.form['findable']
    checkins = 0

    query = 'insert into members (name, year, email, findable, checkins) values (?, ?, ?, ?, ?)'
    query_db(query, [name, year, email, findable, checkins])
    flash('New member added')
    return redirect(url_for('admin_panel'))

@app.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    auth.check_login()
    query = 'delete from members where id = ?'
    query_db(query, (member_id,))
    return 'Deleted member'

@app.route('/members/<int:member_id>', methods=['POST'])
def update_member(member_id):
    auth.check_login()

    name = request.form['name']
    year = request.form['year']
    email = request.form['email']
    findable = request.form['findable']
    checkins = request.form['checkins']

    query = (
        'update members '
        'set name=?, year=?, email=?, findable=?, checkins=? '
        'where id=?'
    )
    query_db(query, [name, year, email, findable, checkins, member_id])
    flash('Updated ' + name)
    # TODO: think about doing all of these redirects javascript-side
    return redirect(url_for('admin_panel'))

@app.route('/checkin/<int:member_id>', methods=['POST'])
def update_checkin(member_id):
    auth.check_login()
    query = (
        'update members '
        'set checkins=checkins+1 '
        'where id=?'
    )
    query_db(query, (member_id,))
    name = request.form['name']
    checkins = str(int(request.form['checkins']) + 1)
    eventName = request.form['eventName']
    eventID = int(request.form['eventID'])
    query = (
        'insert into event_checkins values (?,?,?,?)'
    )
    query_db(query, (eventID, eventName, member_id, name))
    return "Checked in"

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/donate', methods=['GET'])
def donate():
    return render_template('donate.html')

@app.context_processor
def processor():

    def convert_position(pos_int):
        return helpers.POSITIONS[pos_int]

    return dict(convert_position=convert_position)

# a helper function which I'm putting in here because I need Jinja to use it
def check_valid_checkin(eventID, memberID):
    query = 'select * from event_checkins where eventID=? and memberID=?'
    checkins = query_db(query, (eventID, memberID))
    return len(checkins) == 0
