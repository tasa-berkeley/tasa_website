from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

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
import collections
import io
import csv
import zipfile

from flask import Flask
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import Response
from flask import send_file

from os import listdir
from os.path import isfile, join, isdir

from tasa_website import auth
from tasa_website import fb_events
from tasa_website import helpers

from . import app
from . import FAMILY_IMAGE_FOLDER
from . import IMAGE_FOLDER
from . import OFFICER_IMAGE_FOLDER
from . import FILES_FOLDER
from . import SCRAPBOOK_FOLDER
from . import ROOT
from . import query_db

# This is kind of backwards, it's rendering a smaller template first that is
# part of the larger index version. Should fix soon.
@app.route('/')
def index():
    events = query_db('select title, time, location, link, image_url, unix_time from events order by unix_time desc')
    upcoming_events = events[:3]
    if len(upcoming_events) == 0:
        return render_template('show_latest_event.html')
    return render_template('show_latest_event.html', events=upcoming_events)

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
        if res['is_online']:
            location = "Online"
        else:
            location = res.get('place', {'name': ''})['name']

        time_str, unix_time = helpers.convert_time(res['start_time'])

        # get cover photo
        image = fb_events.get_cover_photo(res)
        # just resave it as a jpg
        image_ext = '.jpg'

        file_name = helpers.generate_random_filename(image_ext)
        image_url, image_path = helpers.create_file_paths(IMAGE_FOLDER, file_name)
        image.save(image_path, format='JPEG', quality=95, optimize=True, progressive=True)

        exists_query = 'SELECT * FROM events WHERE link = ?'
        event = query_db(exists_query, [url], True)
        if event is None:
            query = 'INSERT INTO events (title, time, location, link, image_url, unix_time)'\
                    'VALUES (?, ?, ?, ?, ?, ?)'
            query_db(query, [title, time_str, location, url ,image_url, unix_time])
            flash("New event was successfully posted.")
        else:
            query = 'UPDATE events SET title = ?, time = ?, location = ?, image_url = ?, unix_time = ? WHERE link = ?'
            query_db(query, [title, time_str, location, image_url, unix_time, url])
            flash("Event successfully updated.")

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
    leaderboard = query_db('select * from members order by checkins desc')
    lateJars = query_db('select * from late_jars order by id')

    return render_template('admin.html', events=events, officers=officers, families=families, files=files, members=members,
                        check_valid_checkin=check_valid_checkin, leaderboard=leaderboard, lateJars = lateJars)

@app.route('/rolling', methods=['POST'])
def roll():
    """Return a random easy or hard late jar."""
    auth.check_login()
    easyLateJars = ["Change your pfp to your first one for at least 3 days",
                    "Dance to https://www.youtube.com/watch?v=qqmmc7pl9Do",
                    "Everyone comment on your first pfp",
                    "Instagram live yourself for like at least 10 minutes (and tell cab beforehand when you'll do it)",
                    "Let Andrew/Daniel/Avery caption your next TASA profile pic",
                    "Let your co choose your zoom background for a day (must be appropriate)",
                    "Make a lookbook with 5 outfits -- commentary required",
                    "Make a post and compliment every single cabinet member",
                    "Lipsync a music video (low quality, 2 minutes)",
                    "Watch an anime episode with Tiff OR kdrama with steph OR loona vids with brandon and ash",
                    "Take over the tabling hour shifts of a cabinet member of your choice",
                    "Paint your nails a color of the exec's choice using nail polish / marker",
                    "Play Jeffrey or Nick or Marg's brother in a game of chess",
                    "Watch shanie's twitch stream for minimum 20 mins and be active in chat",
                    "Change zoom profile pic to picture of exec's choice for a week",
                    "Be vanessa's hype man for a day",
                    "Coffee chat with andrew",
                    "Take a shot of anything with terrance/will",
                    "Go thru marg's hinge likes and provide commentary with her"]
    hardLateJars = ["Make 5 tik toks (and share username on a social media platform of your choice)",
                    "Act a scene from a movie or drama",
                    "Write a FANFICTION and post it in Cabinet FB group",
                    "Post at least 1 short vlog a day for a week on the cabinet page",
                    "Recreate https://www.facebook.com/groups/1343933772408499/permalink/2750477481754114",
                    "Send a meme to everyone on cabinet that you think they'd like",
                    "Time lapse yourself doing a chloe ting/emi wong/blogilates workout (10 minutes minimum)",
                    "Make a video of yourself doing an impression of everyone on cab and upload to facebook group",
                    "Workout with terrance over zoom (min 10 mins)",
                    "Record yourself rapping 8 bars about anything (must be written by you)"]

    choices = None
    if request.form['level'] == 'Easy':
        choices = query_db('select * from late_jars where difficulty = "Easy" order by id')
        choices = [row[2] for row in choices]
    else:
        choices = query_db('select * from late_jars where difficulty = "Hard" order by id')
        choices = [row[2] for row in choices]
        
    rolledLateJars = ""
    chosen = []

    for i in range(int(request.form['quantity'])):
        currentNum = str(i+1)
        rolled = random.choice(choices)

        while rolled in chosen:
            rolled = random.choice(choices)
        
        rolledLateJars += "(" + currentNum + ") " + rolled + "\n"
        chosen.append(rolled)

    flash(rolledLateJars)
            
    return redirect(url_for('admin_panel'))

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

@app.route('/members/delete_all', methods=['DELETE'])
def delete_all_members():
    auth.check_login()
    query_db('delete from members')
    query_db('delete from event_checkins')
    return "Reset general members"

@app.route('/members/download', methods=['GET'])
def download_checkin_info():
    auth.check_login()
    query = 'SELECT e.eventName, m.name FROM event_checkins as e, members as m WHERE m.id = e.memberID'
    lst = query_db(query)
    event_dict = collections.defaultdict(list)
    member_dict = collections.defaultdict(list)
    for entry in lst:
        event_dict[entry[0]].append(entry[1])
        member_dict[entry[1]].append(entry[0])
    
    event_lst = []
    member_lst = []
    for k,v in event_dict.items():
        event_lst.append([k] + v)
    for k,v in member_dict.items():
        member_lst.append([k] + v)
    
    event_csv_string = []
    member_csv_string = []
    for csvLine in event_lst:
        event_csv_string += [",".join(csvLine)]

    for csvLine in member_lst:
        member_csv_string += [",".join(csvLine)]

    event_csv_string = "\n".join(event_csv_string)
    member_csv_string = "\n".join(member_csv_string)
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        data = zipfile.ZipInfo('membersperevent.csv')
        data.date_time = time.localtime(time.time())[:6]
        data.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(data, event_csv_string)

        data = zipfile.ZipInfo('eventspermember.csv')
        data.date_time = time.localtime(time.time())[:6]
        data.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(data, member_csv_string)
    memory_file.seek(0)
    return send_file(memory_file, attachment_filename='checkins.zip', as_attachment=True)

@app.route('/checkin', methods=['GET'])
def get_checkins():
    search = request.args.get('searchbarText', '')
    if search:
        query = 'select * from members where name like ? and findable="yes"'
        members = query_db(query, ('%' + search + '%',))
    else:
        members = []
    query = 'select * from event_checkins'
    event_checkins = query_db(query)
    return render_template('checkins.html', members=members, event_checkins=event_checkins)

@app.route('/checkin/<int:member_id>', methods=['POST'])
def update_checkin(member_id):
    auth.check_login()

    name = request.form['name']
    checkins = request.form['checkins']
    returning = (int(checkins) > 0)
    eventName = request.form['eventName']
    eventID = int(request.form['eventID'])
    if check_valid_checkin(eventID, member_id):
        query = (
            'update members '
            'set checkins=checkins+1 '
            'where id=?'
        )
        query_db(query, (member_id,))

        query = (
            'insert into event_checkins values (?,?,?,?)'
        )
        query_db(query, (eventID, eventName, member_id, name))
        if returning:
            query = (
                'update events '
                'set attendance=attendance+1, returning_attendance=returning_attendance+1 '
                'where id=?'
            )
        else:
            query = (
                'update events '
                'set attendance=attendance+1, new_attendance=new_attendance+1 '
                'where id=?'
            )
        query_db(query, (eventID,))

        return "Checked in"
    return "Already checked in for this event"

@app.route('/lateJars', methods=['POST'])
def add_late_jars():
    auth.check_login()
    difficulty = request.form['difficulty']
    jar = request.form['newLateJar']
    query = 'insert into late_jars (difficulty, jar) values (?, ?)'
    query_db(query, [difficulty, jar])
    flash('New late jar added')
    return redirect(url_for('admin_panel'))

@app.route('/lateJars/<int:jar_id>', methods=['DELETE'])
def delete_jar(jar_id):
    auth.check_login()
    query = 'delete from late_jars where id = ?'
    query_db(query, (jar_id,))
    return 'Deleted Late Jar'

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/donate', methods=['GET'])
def donate():
    return render_template('donate.html')

@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

@app.route('/scrapbook/<semester>', methods=['GET'])
def scrapbookPage(semester):
    """
    The scrapbook main page displays carousels for each semester with various event images.
    Returns a dictionary of lists containing the IDs of the images to be displayed in the
    semesters' carousels.
    """
    serviceID = driveAPI_authentication()
    service = serviceID["service"]
    id = serviceID["id"]
    semDictionary = {'sp20': 'Spring 2020', 'fa19': 'Fall 2019'}
    specifiedSem = semDictionary[semester]

    # Search for the specified semester folder in the scrapbook folder
    semFolders = fileSearch(service, "'" + id + "' in parents and trashed=false and name='" + specifiedSem + "' ")

    # Grabs the names of the semester folder
    semFolderNameIDs = {}   # {name of semester folder: ID of folder}
    for f in range(0, len(semFolders)):
        semFolderName = semFolders[f].get('name')
        semFolderNameIDs[semFolderName] = semFolders[f].get('id')

    # Get the IDs of 9 image files in the semester folder
    imgIDsToPass = {}   # {semester: [IDs of semester images]}
    for semester, semFolderID in semFolderNameIDs.items():
        imgIDs = fileSearch(service, "'" + semFolderID + "' in parents and trashed=false", 
                                pageSize = 9, fieldsParameters = "nextPageToken, files(id)")

        semImgIDs = []
        for id in range(0, len(imgIDs)):
            semImgIDs.append(imgIDs[id].get('id'))
        imgIDsToPass[semester] = semImgIDs

    return render_template('scrapbook.html', imgIDsToPass=imgIDsToPass)

def driveAPI_authentication():
    """
    Helper function that handles authentication for the Google Drive API.
    Returns the ID of the Scrapbook Folder.
    """
    SCOPES = 'https://www.googleapis.com/auth/drive.readonly.metadata'
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        args, unknown = tools.argparser.parse_known_args()
        args.noauth_local_webserver = True
        creds = tools.run_flow(flow, store, args)
    service = discovery.build('drive', 'v3', http=creds.authorize(Http()))

    # Call the Drive v3 API and search for Scrapbook folder
    folderId = service.files().list(q = "mimeType = 'application/vnd.google-apps.folder' and name = 'Website Scrapbook Images'", 
                                    pageSize=10, fields="nextPageToken, files(id, name)").execute()
    folderIdResult = folderId.get('files', [])
    id = folderIdResult[0].get('id')

    serviceID = {"service": service, "id": id}
    return serviceID

def fileSearch(service, queryParameters, pageSize = None, fieldsParameters = None):
    """
    A helper function that searches for all files within a given Drive folder ID.
    Returns a list of file IDs and their respective names.
    """
    if not pageSize and not fieldsParameters:
        results = service.files().list(q = queryParameters, 
                                fields = "nextPageToken, files(id, name)").execute()
    elif not pageSize and fieldsParameters:
        results = service.files().list(q = queryParameters, 
                                        fields = fieldsParameters).execute()
    elif pageSize and not fieldsParameters:
        results = service.files().list(q = queryParameters, pageSize = pageSize, 
                                        fields = "nextPageToken, files(id, name)").execute()
    else:
        results = service.files().list(q = queryParameters, pageSize = pageSize,
                                        fields = fieldsParameters).execute()

    filesToReturn = results.get('files', [])
    return filesToReturn

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

    


