#!/usr/bin/env python
from flask import Flask, jsonify, abort, request, make_response, url_for, render_template, redirect, flash, send_from_directory, make_response
from gevent.pywsgi import WSGIServer
from gevent import monkey

# need to patch sockets to make requests async
# you may also need to call this before importing other packages that setup ssl
monkey.patch_all()
from datetime import datetime
import signal
import sys
import os
import string
import configparser
import random 
import string
import json
import requests
import math
import re
import sys
#from pyproj import Proj, transform
#import logging

app = Flask(__name__, static_url_path='/static')

@app.before_request
def before_request():
    # When you import jinja2 macros, they get cached which is annoying for local
    # development, so wipe the cache every request.
    if 'localhost' in request.host_url or '0.0.0.0' in request.host_url:
        app.jinja_env.cache = {}

app.before_request(before_request)

#log = logging.getLogger('werkzeug')
#log.setLevel(logging.ERROR)

config = configparser.ConfigParser()
config.read('config.ini')
app.secret_key = config['GENERAL']['SECRET_KEY']

import sqlite3

# if database isn't exist, then create one with random filename
import uuid
if not config['GENERAL']['SQLITE_PATH'] or not os.path.exists(config['GENERAL']['SQLITE_PATH']):
    
    uuid = str(uuid.uuid4()).split('-')[0]
    config['GENERAL']['SQLITE_PATH'] = "db_{}.sqlite".format(uuid)

    # write new sqlite filename inside our config
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

conn = sqlite3.connect(config['GENERAL']['SQLITE_PATH'], check_same_thread=False)
conn.execute("PRAGMA foreign_keys = 1")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

import flask_login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class User(flask_login.UserMixin):
    pass


def remove_dirty_form(dirtylist,number=False):
    dirtylist=dirtylist.replace(']', '')
    dirtylist=dirtylist.replace('[', '')

    splitlist = dirtylist.split (',')
    for index,value in enumerate(splitlist):
        if len(value)<=0:
            continue
        value=value.strip()
        if value[0]=='u':
            value=value[1:]
        value=value.replace("'", "")
        if number:
            value=re.sub("[A-Za-z]","",value)
        splitlist[index]=value
    return splitlist

#######################################################################################################################################################
########################################################         LOGIN MANAGEMENT          ############################################################
#######################################################################################################################################################

@login_manager.user_loader
def user_loader(username):
    lock.acquire(True)
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    lock.release()

    
    entry = cursor.fetchone()

    if entry is None:
        return
    else :
        user = User()
        user.id = username
        return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    print(username)
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry is None:
        return
    elif request.form['password'] != entry['password']:
        redirect(url_for('login'))
    else :
        user = User()
        user.id = username
        user.is_authenticated = request.form['password'] == entry['password']

        return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'GET':
        return render_template('dash/login_page.html')

    username = request.form['username']
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry :
        if request.form['password'] == entry['password']:
            user = User()
            user.id = username
            flask_login.login_user(user)
            if entry['privilage']==7:
                flash('You were successfully logged in')
                return redirect(url_for('show_admin'))
            flash('You were successfully logged in as user')
            return redirect(url_for('show_map'))

    error = 'Wrong Username or Password. Try again!'
    
    return render_template('dash/login_page.html', error=error)

@app.route('/loginadmin', methods=['GET', 'POST'])
def loginadmin():
    if request.method == 'GET':
        return render_template('dash/adminlogin.html')
        return '''
               <form action='login' method='POST'>
                <input type='text' name='username' id='username' placeholder='username'/>
                <input type='password' name='password' id='password' placeholder='password'/>
                <input type='submit' name='submit'/>
               </form>
               '''

    username = request.form['username']
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry :
        if request.form['password'] == entry['password']:
            user = User()
            user.id = username
            flask_login.login_user(user)
            if entry['privilage']==7:
                flash('You were successfully logged in')
                return redirect(url_for('show_admin'))
            return ("Wrong")

    return redirect(url_for('loginadmin'))


#Render template for template

@app.route('/regtemplate')
def regtemplate():
    None
    return render_template('dash/register.html')

@app.route('/adminlogin')
def adminlogin():
    None
    return render_template('dash/adminlogin.html')

@app.route('/userlogin')
def userlogin():
    None
    return render_template('dash/login_page.html')

# END OF render template for template

def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

@app.route('/register', methods=['POST'])
def register():
    if not request.json or not 'username' or not 'password' in request.json:
        abort(400)

    username = request.json['username']
    password = request.json['password']
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry :
        if password == entry['password']:
            randomid=id_generator()
            cursor.execute('UPDATE user_table SET randomid = ? WHERE username= ? ',(randomid,username))
            conn.commit()
            return jsonify({'randomid': randomid}), 200
        else :
            abort(400, " wrong password")
    else :
        abort(400, " username was not registered")


@app.route('/validate', methods=['POST'])
def validate():
    if not request.json or not 'randomid' in request.json:
        abort(400)

    randomid = request.json['randomid']
    cursor.execute('SELECT * FROM user_table WHERE randomid=? ', (randomid,))
    entry = cursor.fetchone()

    if entry :
        return jsonify({'registered': 'true'}), 200
    else :
        abort(400, " username was not registered")



@app.route('/protected')
@flask_login.login_required
def protected():
    return 'Logged in as: ' + flask_login.current_user.id

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

@auth.get_password
def get_password(username):
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry is None:
        return None
    else :
        return entry['password']

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)

#######################################################################################################################################################
########################################################           DB MANAGEMENT           ############################################################
#######################################################################################################################################################


def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_table
    (username   TEXT    PRIMARY KEY,
    password    TEXT    NOT NULL,
    privilage   INT     NOT NULL,
    randomid    TEXT,
    enabled     BOOLEAN NOT NULL,
    date_created    TIMESTAMP   NOT NULL)''')      

    #insert root account to add, edit and remove user. 
    cursor.execute('SELECT * FROM user_table WHERE username=? ', ('root',))
    entry = cursor.fetchone()

    if entry is None:
        cursor.execute('INSERT INTO user_table (username,password,privilage,enabled,date_created) VALUES (?,?,?,?,?)', ('root', 'root', '7', True, datetime.today().strftime('%Y-%m-%d')))

    cursor.execute('''CREATE TABLE IF NOT EXISTS data_table
    (id INTEGER PRIMARY KEY,
    altitude        TEXT    NOT NULL,
    latitude        TEXT    NOT NULL,
    longitude       TEXT    NOT NULL,
    image           TEXT    NOT NULL,
    date_taken      TIMESTAMP    NOT NULL,
    username        TEXT    NOT NULL,
    FOREIGN KEY (username) REFERENCES user_table (username))''')
    conn.commit()


def fetchall_data(query,param=None):
    try:
        lock.acquire(True)
        if param:
            cursor.execute(query, param)
        else:
            cursor.execute(query)
        entry = cursor.fetchall()
    finally:
        lock.release()
        return entry

#######################################################################################################################################################
########################################################           MAP MANAGEMENT          ############################################################
#######################################################################################################################################################
user_request = {}

def create_marker(date=None,username=None,bbox=None):
    marker={}
    entry={}
    i=0
    if username and date:
        entry=fetchall_data('SELECT * FROM data_table WHERE username=? AND date_taken LIKE ?', (username,date+"%",))
    elif username and bbox:
        entry=fetchall_data('SELECT * FROM data_table WHERE latitude>? AND latitude<? AND longitude>? AND longitude<? AND username=?', (bbox['min1'], bbox['min2'], bbox['max1'], bbox['max2'],username,))
    elif date:
        entry=fetchall_data('SELECT * FROM data_table WHERE date_taken LIKE ?', (date+"%",))
    elif bbox:
        entry=fetchall_data('SELECT * FROM data_table WHERE latitude>? AND latitude<? AND longitude>? AND longitude<?', (bbox['min1'], bbox['min2'], bbox['max1'], bbox['max2'],))
    elif username=="all":
        entry=fetchall_data('SELECT * FROM data_table')
    elif username:
        entry=fetchall_data('SELECT * FROM data_table WHERE username=?', (username,))

    if entry:
        for row in entry:
            altitude = row['altitude']
            latitude = row['latitude']
            longitude = row['longitude']
            image = row['image']
            date_taken = row['date_taken']
            user= row['username']

            description2 = ('<img src="data:image/png;base64,'+str(image)+'"/>'+
                            '<br><b>Latitude</b>: '+str(latitude)+
                            '<br><b>Longitude</b>: '+str(longitude)+
                            '<br><b>Date Taken</b>: '+str(date_taken)+
                            '<br><b>Taken by</b>: '+str(user))

            objectstreetlight = 'object'+str(i)
            marker.update({objectstreetlight:{'lat':latitude, 'lng':longitude,'description':description2}})
            i+=1
    return marker

@app.route('/map')
@flask_login.login_required
def show_map():
    username=flask_login.current_user.id
    cursor.execute('SELECT * FROM data_table WHERE username=? ', (username,))
    entry = cursor.fetchall()

    if entry is None:
        flask_login.logout_user()
        return redirect(url_for('login'))
    elif not entry:
        flask_login.logout_user()
        return render_template('empty_map.html')
    else :
        return redirect(url_for('userdash'))

@app.route('/')
def index():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
        entry = cursor.fetchone()

        if entry :
            if entry['privilage']==7:
                return redirect(url_for('show_admin'))
            return redirect(url_for('show_map'))
    else:
        return redirect(url_for('login'))

@app.route('/pushadmin', methods=['GET'])
@flask_login.login_required
def pushadmin():
    if flask_login.current_user.is_authenticated:
        date = request.args.get('date')
        date = str(date)
        username = flask_login.current_user.id
        global user_request
    else:
        return redirect(url_for('login'))

    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry :
        if entry['privilage']==7:
            if date:
                streetlight_timebased = create_marker(date=date)
                user_request[username]={'data':json.dumps(streetlight_timebased),'sent':False}
                return ('', 204)
            else:
                return ('', 204)
        else:
            return redirect(url_for('login'))

@app.route('/streamadmin')
@flask_login.login_required
def streamadmin():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        global user_request
        if not username in user_request:
            response = app.response_class(
            response="data:no data\n\n",
            status=200,
            mimetype='text/event-stream'
            )
        elif not user_request[username]['sent']:
            response = app.response_class(
            response="data:%s\n\n"% user_request[username]['data'],
            status=200,
            mimetype='text/event-stream'
            )
            user_request[username]['sent']=True
        elif user_request[username]['sent']:
            response = app.response_class(
            response="data:no data\n\n",
            status=200,
            mimetype='text/event-stream'
            )
        return response
    else:
        return redirect(url_for('login'))

@app.route('/push', methods=['GET'])
@flask_login.login_required
def push():
    if flask_login.current_user.is_authenticated:
        date = request.args.get('date')
        date = str(date)
        username = flask_login.current_user.id
        global user_request
    else:
        return redirect(url_for('login'))

    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry :
        if entry['privilage']==0:
            if date:
                streetlight_timebased = create_marker(date=date,username=username)
                user_request[username]={'data':json.dumps(streetlight_timebased),'sent':False}
                return ('', 204)
            else:
                return ('', 204)
        else:
            return redirect(url_for('login'))
    

@app.route('/stream')
@flask_login.login_required
def stream():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        global user_request
        if not username in user_request:
            response = app.response_class(
            response="data:no data\n\n",
            status=200,
            mimetype='text/event-stream'
            )
        elif not user_request[username]['sent']:
            response = app.response_class(
            response="data:%s\n\n"% user_request[username]['data'],
            status=200,
            mimetype='text/event-stream'
            )
            user_request[username]['sent']=True
        elif user_request[username]['sent']:
            response = app.response_class(
            response="data:no data\n\n",
            status=200,
            mimetype='text/event-stream'
            )
        return response
    else:
        return redirect(url_for('login'))

def findCenterLonLat (geolocations): # ( (12,23),(23,23),(43,45) )
    x,y,z =0,0,0
    #print(geolocations)

    for lat, lon in (geolocations):
        #print('\n\n')
        #print(lat)
        #print(lon)
        #print('\n\n')
        lat = math.radians(float(lat))
        lon = math.radians(float(lon))
        x += math.cos(lat) * math.cos(lon)
        y += math.cos(lat) * math.sin(lon)
        z += math.sin(lat)

    x = float(x / len(geolocations))
    y = float(y / len(geolocations))
    z = float(z / len(geolocations)) 
    
    center_lon = (math.atan2(y, x))
    center_lat = math.atan2(z, math.sqrt(x * x + y * y))

    return (math.degrees(center_lat), math.degrees(center_lon))
    
global min1, min2, max1, max2, dname
min1,min2,max1,max2=0,0,0,0
dname = "View All State"

@app.route('/mapbox_proxy', methods=['GET'])
@flask_login.login_required
def mapbox_proxy():
    #this route provide proxy to prevent client side known the API token for generate Mapbox tile to our map. We want to keep it secret right?
    if flask_login.current_user.is_authenticated:
        filename = str(request.args.get('location'))+".png"
        url = "https://api.tiles.mapbox.com/v4/mapbox.streets/"+filename

        querystring = {"access_token":"pk.eyJ1IjoiZ21ueCIsImEiOiJjanhhNHU1NmYwdGpkM29ucnY4Y3dxczg1In0.XnxeD-dYEPyirXYK8zKfcw"}

        payload = ""
        headers = {
            'cache-control': "no-cache",
            'Postman-Token': "40ebb8bc-d6fd-49b0-9d61-9608ca8ae1a3"
            }
        filename=filename.replace("/", "")
        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
        reply = make_response(response.content)
        reply.headers.set('Content-Type', 'image/png')
        reply.headers.set(
            'Content-Disposition', 'attachment', filename=filename)
        return reply
    else:
        return redirect(url_for('login'))

@app.route('/adminmap')
@flask_login.login_required
def adminmap():
    if not flask_login.current_user.is_authenticated:
        return redirect(url_for('login'))
    username=flask_login.current_user.id
    marker={}
    streetlight_areabased = None
    streetlight_timebased = None
    listdate = []
    listusername = []

    #Query marker Area Based
    min1 = request.args.get("min1") #minlat
    min2 = request.args.get("min2") #minlon
    max1 = request.args.get("max1") #maxlat
    max2 = request.args.get("max2") #maxlon
    dname = request.args.get("dname")

    if (min1 is None):
        min1, min2, max1, max2 = 0,0,0,0
    else :
        min1, min2, max1, max2 = min1, min2, max1, max2
        
        bbox = {"min1":min1, "min2":min2, "max1":max1, "max2":max2}
        streetlight_areabased = create_marker(bbox=bbox)

    if streetlight_areabased:
        object_names = set()
        for key in streetlight_areabased:
            object_names.add(key)
            latlon_list=[(streetlight_areabased[key]['lat'],streetlight_areabased[key]['lng'])]

        flash('Focus on {} with {} streetlight'.format(dname, len(object_names)))
        error = str("Focus on {} with {} streetlight".format(dname,len(object_names)))
        center_lat,center_lon = findCenterLonLat(latlon_list)

    #Query marker Time Based
    try:
        lock.acquire(True)
        cursor.execute('SELECT date_taken,username FROM data_table')
        entry = cursor.fetchall()
    finally:
        lock.release()
    for i in entry:
        date_taken = i['date_taken']
        user = i['username']
        date_only = str(datetime.strptime(date_taken,'%Y-%m-%d %H:%M:%S').date())
        if not date_only in listdate:
            listdate.append(date_only)
        if not user in listusername:
            listusername.append(user)
    if listdate:
        max_date = max(listdate)
        streetlight_timebased = create_marker(date=max_date)

    if streetlight_timebased:
        for key in streetlight_timebased:
            latlon_list=[(streetlight_timebased[key]['lat'],streetlight_timebased[key]['lng'])]
        center_lat,center_lon = findCenterLonLat(latlon_list)

    #Choose the area based if any
    if min1==0:
        streetlight=streetlight_timebased
    else :
        streetlight=streetlight_areabased
        
    return render_template('/dash/admin-maps3.html', clat = center_lat, clon = center_lon, telco=streetlight, dname=dname, min1=min1, min2=min2, max1=max1, max2=max2, data=json.dumps(listdate), marker=marker, username=username, user=listusername)



@app.route('/usermap')
@flask_login.login_required
def usermap():
    if not flask_login.current_user.is_authenticated:
        return redirect(url_for('login'))
    username=flask_login.current_user.id
    marker={} 

    #Query marker Area Based
    min1 = request.args.get("min1") #minlat
    min2 = request.args.get("min2") #minlon
    max1 = request.args.get("max1") #maxlat
    max2 = request.args.get("max2") #maxlon
    dname = request.args.get("dname")

    streetlight_areabased = None
    streetlight_timebased = None

    if (min1 is None):
        min1, min2, max1, max2 = 0,0,0,0
    else :
        min1, min2, max1, max2 = min1, min2, max1, max2
        
        bbox = {"min1":min1, "min2":min2, "max1":max1, "max2":max2}
        streetlight_areabased = create_marker(username=username,bbox=bbox)

    if streetlight_areabased:
        object_names = set()
        for key in streetlight_areabased:
            object_names.add(key)
            latlon_list=[(streetlight_areabased[key]['lat'],streetlight_areabased[key]['lng'])]

        flash('Focus on {} with {} streetlight'.format(dname, len(object_names)))
        error = str("Focus on {} with {} streetlight".format(dname,len(object_names)))
        center_lat,center_lon = findCenterLonLat(latlon_list)

    #Query marker Time Based
    listdate = []
    for i in fetchall_data('SELECT date_taken FROM data_table WHERE username=? ', (username,)):
        date_taken = i['date_taken']
        date_only = str(datetime.strptime(date_taken,'%Y-%m-%d %H:%M:%S').date())
        if not date_only in listdate:
            listdate.append(date_only)
    if listdate:
        max_date = max(listdate)
        streetlight_timebased = create_marker(username=username,date=max_date)

    if streetlight_timebased:
        for key in streetlight_timebased:
            latlon_list=[(streetlight_timebased[key]['lat'],streetlight_timebased[key]['lng'])]
        center_lat,center_lon = findCenterLonLat(latlon_list)

    #Choose the area based if any
    if min1==0:
        streetlight=streetlight_timebased
    else :
        streetlight=streetlight_areabased
    return render_template('/dash/user-map3.html',telco=streetlight, clat = center_lat, clon = center_lon, dname=dname,min1=min1, min2=min2, max1=max1, max2=max2, marker=marker, username=username, data=json.dumps(listdate))

@app.route('/searchloc',methods=['POST'])
@flask_login.login_required
def searchloc():
    if not flask_login.current_user.is_authenticated:
        return redirect(url_for('login'))
    username=flask_login.current_user.id
    
    if flask_login.current_user.is_authenticated:
        loc = request.form.get('state')
    print loc
    if loc=="Choose State":
        return ('', 204)
    
    if (' ' in loc) :
        splitted    = loc.split()
        first       = splitted[0]
        second      = splitted[1]
        locnew      = ("{}%20{}".format(first,second))
    else :
        locnew = loc

    url = "https://nominatim.openstreetmap.org/search/"+locnew+"?format=json&addressdetails=1&limit=1"
    print(url)

    data = requests.get(url=url).text
    data = json.loads(data)
    
    if ('putrajaya' in loc) :
        minlat, minlon, maxlat, maxlon = "2.876833", "2.982444", "101.659687", "101.732682"
        dname = ('{}'.format("Putrajaya"))
    
    else:
        for i in data:
            #bounding = ('{},{},{},{}'.format(i['boundingbox'][0],i['boundingbox'][1],i['boundingbox'][2],i['boundingbox'][3]))
            minlat    = ('{}'.format(i['boundingbox'][0]))
            minlon    = ('{}'.format(i['boundingbox'][1]))
            maxlat    = ('{}'.format(i['boundingbox'][2]))
            maxlon    = ('{}'.format(i['boundingbox'][3]))

            #minlat, minlon, maxlat, maxlon = "2.876833", "2.982444", "101.659687", "101.732682"
            
            dname = ('{}'.format(i['display_name']))
    
    cursor.execute('SELECT privilage FROM user_table WHERE username=?', (username,))
    entry = cursor.fetchone()

    if entry['privilage']==7:
        return redirect(url_for('adminmap', min1=minlat, min2=minlon, max1=maxlat, max2=maxlon, dname=dname))
    elif entry['privilage']==0:
        return redirect(url_for('usermap', min1=minlat, min2=minlon, max1=maxlat, max2=maxlon, dname=dname))
    else :
        return "Error!"

@app.route('/getAssetUsername', methods=['POST'])
def getAssetUsername():
    if flask_login.current_user.is_authenticated:
        username =  request.form['username']
    else:
        return redirect(url_for('login'))

    cursor.execute('SELECT * FROM user_table WHERE username=? ', (flask_login.current_user.id,))
    entry = cursor.fetchone()
    

    if entry :
        if entry['privilage']==7:
            if username:
                streetlight_userbased = create_marker(username=username)
                return jsonify({'marker': json.dumps(streetlight_userbased)}), 200 
            else:
                return ('', 204)
        else:
            return redirect(url_for('login'))

#######################################################################################################################################################
########################################################       DASHBOARD MANAGEMENT        ############################################################
#######################################################################################################################################################

@app.route('/admin')
@flask_login.login_required
def show_admin():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
        entry = cursor.fetchone()

        if entry :
            if entry['privilage']==7:
                return render_template('dash/adminboard.html')
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/userdash')
@flask_login.login_required
def userdash():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
        entry = cursor.fetchone()

        lenadmin = fetchall_data('SELECT * FROM user_table WHERE privilage = 7 ')

        lenuser = fetchall_data('SELECT * FROM user_table WHERE privilage = 0 ')

        if entry :
            if entry['privilage']==0:
                return render_template('dash/dashboard.html', lenadmin=lenadmin, lenuser=lenuser) #user dashboard
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/update_admin')
@flask_login.login_required
def update_admin():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
        entry = cursor.fetchone()

        if entry :
            if entry['privilage']==7:
                cursor.execute('SELECT * FROM user_table')
                entry = cursor.fetchall()
                return render_template('dash/table.html', users=entry)
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/userlist')
@flask_login.login_required
def show_userlist():
    
    user=[]
    passs=[]

    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
        entry= cursor.fetchone()

        if entry :
            if entry['privilage']==7:
                cursor.execute('SELECT * FROM user_table')
                entry = cursor.fetchall()
               
                return render_template('dash/table.html', users=entry, username=username)
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/userprofile')
@flask_login.login_required
def show_userprofile():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
        entry = cursor.fetchone()

        password=entry['password']
        username=entry['username']
        privilage=entry['privilage']
        date_created=entry['date_created']

        if privilage == 7:
            privilagelabel = "Admin"
        else:
            privilagelabel = "User"

        if entry :
            if entry['privilage']==7:
                cursor.execute('SELECT * FROM user_table')
                entry = cursor.fetchall()
                return render_template('dash/user.html', users=entry, username=username, password=password, privilagel=privilagelabel, privilage=privilage, date_created=date_created)
                flask_login.logout_user()
            
            else :
                cursor.execute('SELECT * FROM user_table')
                entry = cursor.fetchall()
                return render_template('dash/userprof.html', users=entry, username=username, password=password, privilagel=privilagelabel, privilage=privilage, date_created=date_created)
            flask_login.logout_user()
    else:
        return redirect(url_for('login'))


@app.route('/getUserData', methods=['GET'])
def getUserData():
    lenuser = fetchall_data('SELECT * FROM user_table WHERE privilage = 0 ')
    lenuser = len(lenuser)

    lenadmin = fetchall_data('SELECT * FROM user_table WHERE privilage = 7 ')
    lenadmin = len(lenadmin)

    return jsonify({'lenuserdata': lenuser, 'lenadmindata':lenadmin}), 200 

@app.route('/getAllAssetData', methods=['GET'])
def getAllAssetData():
    lenasset = fetchall_data('SELECT * FROM data_table')
    lenasset = len(lenasset)

    return jsonify({'lenasset':lenasset}), 200

@app.route('/getAssetData', methods=['GET'])
def getAssetData():
    lenasset = fetchall_data('SELECT * FROM data_table WHERE username=? ', (flask_login.current_user.id,))
    lenasset = len(lenasset)

    return jsonify({'lenasset':lenasset}), 200

#######################################################################################################################################################
########################################################          API MANAGEMENT           ############################################################
#######################################################################################################################################################

@app.route('/insert', methods=['POST'])
def create_record():
    if not request.json or not 'altitude' or not 'latitude' or not 'longitude' or not 'image' or not 'date_taken' or not 'username' in request.json:
        abort(400)
    
    altitude = request.json['altitude'].replace(" ", "")
    latitude = request.json['latitude'].replace(" ", "")
    longitude = request.json['longitude'].replace(" ", "")
    image = request.json['image'].replace(" ", "")
    date_taken = request.json['date_taken'].replace(" ", "")
    username = request.json['username'].replace(" ", "")

    if not (altitude and longitude and latitude and image and date_taken and username):
        abort(400," some parameter is empty")

    cursor.execute('SELECT * FROM data_table WHERE (date_taken=? AND username=?)', (date_taken, username,))
    entry = cursor.fetchone()

    if not entry:
        try:
            cursor.execute('INSERT INTO data_table (altitude,latitude,longitude,image,date_taken,username) VALUES (?,?,?,?,?,?)', (altitude, latitude, longitude, image, date_taken, username))
            conn.commit()
            return jsonify({'status': 'received'}), 201
        except Exception as e:
            abort(400, e.message+" fail to insert data")
    else :
        return jsonify({'error': 'data already inserted'}), 400
   
@app.route('/reg', methods=['POST'])
def reg():
    username    = request.form.get('username')
    password    = request.form.get('password')
    #print(username)
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()
    #print(entry)

    if entry is None:
        cursor.execute('INSERT INTO user_table (username,password,privilage,enabled,date_created) VALUES (?,?,?,?,?)', (username, password, 0, True, datetime.today().strftime('%Y-%m-%d')))
        conn.commit()
        flash('Welcome {}! You can login now.'.format(username))
        return redirect(url_for('login'))
        
    else:
        flash('Invalid username / Duplicate')
        return redirect(url_for('login'))   

@app.route('/adduser', methods=['POST'])
@flask_login.login_required
def create_user():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
        entry = cursor.fetchone()
        

        if entry :
            if entry['privilage']==7:                
                username    = request.form.get('username')
                password    = request.form.get('password')
                privilage   = request.form.get('privilage')

                if not username or not password or not privilage:
                    abort(400)

                cursor.execute('SELECT * FROM user_table WHERE username=?', (username,))
                entry = cursor.fetchone()

                if entry is None:
                    try:
                        cursor.execute('INSERT INTO user_table (username,password,privilage,enabled,date_created) VALUES (?,?,?,?,?)', (username, password, privilage, True, datetime.today().strftime('%Y-%m-%d')))
                        conn.commit()
                        cursor.execute('SELECT * FROM user_table')
                        entry = cursor.fetchall()
                        flash('You were successfully add new user')
                        return render_template('dash/table.html', users=entry)
                    except Exception as e:
                        print(error)
                else :
                    return jsonify({'status': 'user already recorded'}), 200
                
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/updateuser', methods=['POST'])
@flask_login.login_required
def updateuser():
    if flask_login.current_user.is_authenticated:
        username = request.form.get('username')
        password = request.form.get('password')
        repassword = request.form.get('repassword')
        privilage = request.form.get('privilage')

        if password == repassword:
            cursor.execute('UPDATE user_table SET privilage = ?, password = ? WHERE username = ?', (privilage,password,username))
            flash('You were successfully update user')
            conn.commit()
        else:
            flash('Not saved. Please enter the valid password.')

        

        return redirect(url_for('show_userlist'))

@app.route('/updateuserprof', methods=['POST'])
@flask_login.login_required
def updateuserprof():
    if flask_login.current_user.is_authenticated:
        username = request.form.get('username')
        password = request.form.get('password')
        repassword = request.form.get('repassword')
        privilage = request.form.get('privilage')

        if password == repassword :
            cursor.execute('UPDATE user_table SET privilage = ?, password = ? WHERE username = ?', (privilage,password,username))
            conn.commit()
            flash('You were successfully update password')
        else :
            flash('Password not saved. Try again.')

        print("{} done".format(password))
        print("{} done".format(repassword))
        print("{} done".format(privilage))
        print("{} done".format(username))

        return redirect(url_for('show_userprofile'))

@app.route('/deleteuser', methods=['POST'])
@flask_login.login_required
def deleteuser():

    if flask_login.current_user.is_authenticated:
        username = request.form.get('username')
        
        cursor.execute('SELECT * FROM data_table WHERE username=? ', (username,))
        entry = cursor.fetchone()

        if entry is not None:
            cursor.execute('DELETE from data_table WHERE username = ?', (username,))
            cursor.execute('DELETE from user_table WHERE username = ?', (username,))
            conn.commit()

        else :
            cursor.execute('DELETE from user_table WHERE username = ?', (username,))
            conn.commit()

        flash('You were successfully delete user')
            

        return redirect(url_for('update_admin'))
    

@app.errorhandler(400)
def custom400(error):
    response = jsonify({'message': error.description})
    return response, 400

def kill_server():
        print('You pressed Ctrl+C!')
        http_server.stop()
        sys.exit(0)



##### Data for Chart.js
import threading
lock = threading.Lock()




if __name__ == '__main__':
    init_db()
    http_server = WSGIServer((config['WEB-SERVER']['HOST'], int(config['WEB-SERVER']['PORT'])), app.wsgi_app)
    print("\nRunning on {}:{}...\n".format(config['WEB-SERVER']['HOST'], config['WEB-SERVER']['PORT']))
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        kill_server()
