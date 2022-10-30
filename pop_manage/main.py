from flask import Flask, request, redirect, url_for, render_template, send_file, jsonify, make_response
from deta import Deta
from dotenv import load_dotenv
import os
import datetime
from werkzeug.utils import secure_filename
import pytz
from flask_cors import CORS
import requests
import random
import string
load_dotenv()

app = Flask(__name__)

CORS(app)

deta = Deta(os.getenv("DETA_PROJECT_KEY"))

utc = pytz.utc
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

##### deta setting
drive = deta.Drive("Files")
db = deta.Base("UploadPopData")
db_main = deta.Base("PopData")
db_admin = deta.Base("PopAdmin")

##### for line notify #####
access_token = os.getenv('ACCESS_TOKEN')
API_URI = "https://notify-api.line.me/api/notify"
headers = {"Authorization": "Bearer " + access_token}

##### set main url #####
main_url = "https://forpopeunbin.deta.dev/"


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/uploadfile', methods=['POST'])
def uploadFile():
    try:
        file = request.files['filedata']
        filename = secure_filename(file.filename)
        date = datetime.datetime.now(utc)
        date = date.strftime("%Y%m%d%H%M%S")
        drive.put(date + filename, file)
        return {'status': 'success', 'url': main_url + date + filename}
    except:
        return {'status': 'error'}

@app.route('/submit', methods=['POST'])
def submit(): 
    try:
        data = request.get_json()
        time = datetime.datetime.now(utc)
        two_random_str = ''.join(random.SystemRandom().choice(string.ascii_letters) for _ in range(2))
        data['key'] = str(time.strftime('%s'))+two_random_str
        data['popCount'] = 0
        data['time'] = str(time)
        res = db.put(data, expire_in=604800) # 7 days = 604800 seconds
        url = main_url + 'p/' + res['key']
        params = {'message': url}
        requests.post(API_URI, headers=headers, params=params)
        return {'status': 'success', 'text': url}
    except:
        return {'status': 'error', 'text': 'Please try to submit it again!!!'} 

@app.route('/p/<key>', methods=['GET'])
def preview(key):
    res = db.get(key)
    if res != None:
        return render_template('page.html', data = res)
    else:
        return 'Not Found'

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db_res = db_admin.fetch({'name': username, 'password': password})
        if db_res.count>0:
            res = make_response(redirect('/admin'))
            # res.set_cookie('name', username)
            res.set_cookie('name', username, secure=True, httponly=True, samesite='Lax')
            return res
        else:
            return make_response(render_template('login.html'))
    else:
        name = request.cookies.get('name')
        if name:
            return redirect('/admin')
        return render_template('login.html')


@app.route('/admin', methods=['GET'])
def admin():
    name = request.cookies.get('name')
    if not name:
        return redirect('/login')
    db_res = db_admin.fetch({'name': name})
    if db_res.count==0:
        res = make_response(redirect('/login'))
        res.set_cookie('name', '', expires=0)
        return res    
    else:
        res = db.fetch()
        return render_template('admin.html', data = res.items)

@app.route('/admin/update', methods=['POST'])
def adminupdate():
    name = request.cookies.get('name')
    if not name:
        return redirect('/login')
    db_res = db_admin.fetch({'name': name})
    if db_res.count==0:
        res = make_response(redirect('/login'))
        res.set_cookie('name', '', expires=0)
        return res
    else:
        try:
            data = request.get_json()
            key = data['key']
            res_old = db.get(key)
            delete_keys = ['key', '__expires', 'time']
            for item in delete_keys:
                res_old.pop(item, None)
            
            res_main = db_main.fetch()
            two_random_str = ''.join(random.SystemRandom().choice(string.ascii_letters) for _ in range(2))

            res_old['published'] = True
            res_old['key'] = str(res_main.count+1).zfill(3)+two_random_str.lower()
            db_main.put(res_old)
            return {'status': 'success', 'text': key+ ' was added to Pop EunBin'}
        except:
            return {'status': 'error', 'text': 'Error from Server. Please try to update it again'}

@app.route('/admin/delete', methods=['POST'])
def admindelete():
    name = request.cookies.get('name')
    if not name:
        return redirect('/login')
    db_res = db_admin.fetch({'name': name})
    if db_res.count==0:
        res = make_response(redirect('/login'))
        res.set_cookie('name', '', expires=0)
        return res
    else:
        data = request.get_json()
        key = data['key']
        db.delete(key)
        return {'status': 'success', 'text': key+ ' was deleted'}

@app.route('/<name>', methods=['GET'])
def getFile(name):
    res = drive.get(name)
    return send_file(res, download_name=name)

if __name__ == "__main__":
    app.run(debug=True)