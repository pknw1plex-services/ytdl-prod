from flask import redirect, Flask, render_template, request, jsonify,session
from urllib.request import urlopen
from shutil import copyfileobj
import os
import sys
from localStoragePy import localStoragePy
import requests
import threading
import urllib.request
from threading import Thread
from time import sleep
import json
import base64
import configparser

keyFile = open('config/keys', 'r')
app = Flask(__name__)
api_key = os.getenv('youtube_api')
#keyFile.readline().rstrip()
app.secret_key = keyFile.readline().rstrip()
progress = 0
status = 0
download_url = ''
localStorage = localStoragePy('pk', 'text')
config_object = configparser.ConfigParser()
downloads = configparser.ConfigParser()

@app.route('/api/ytmetadata/<id>')
def ytmetadata(id=None):
    headers = {
            'Authorization': 'Bearer your_token_here',
            'Content-Type': 'application/json'
        }
    target_url = "https://content-youtube.googleapis.com/youtube/v3/videos?id="+id+"&part=snippet,contentDetails,statistics&key="+api_key
    print(target_url)
    response = requests.get(target_url)
    return response.json()

def get_downloads():
    file =open("config/downloads.ini","r")
    config_object.read_file(file)
    output_dict=dict()
    sections=config_object.sections()
    print(sections)
    for section in sections:
        items=config_object.items(section)
        output_dict[section]=dict(items)
    json_string=json.dumps(output_dict)
    print("The output JSON string is:")
    print(json_string)
    return output_dict

def fork_dl(data=None):
    channel = data['channel']
    title = data['title']
    year = data['year']
    video_id = data['video_id']
    resolution = data['resolution']
    try:
        download_url = data['download_url']
    except:
        download_url = ""

    pathname = '/media/youtube/'+channel
    if not os.path.exists(pathname):
        os.makedirs(pathname)
    filename = title+"-("+resolution+")-("+year+")-["+video_id+"].mp4"
    filename_clean = filename.replace("'","").replace("/","-").replace("%","")
    dl_path = pathname+'/'+filename_clean

    if not os.path.exists(pathname+"/"+filename_clean):
        with urlopen(download_url) as in_stream, open(dl_path, 'wb') as out_file:
            copyfileobj(in_stream, out_file)
        file =open("config/downloads.ini","r")
        downloads.read_file(file)
        section = video_id+'-'+resolution
        downloads.set(section, 'downloaded', dl_path)
        with open('config/downloads.ini', 'w') as configfile:
            downloads.write(configfile)
        file.close()


@app.route('/api/ytdl/<id>')
def plex_dl(data=None):
  yt_title = localStorage.getItem('yt_title')
  yt_channel = localStorage.getItem('yt_channel')
  yt_year = localStorage.getItem('yt_year')
  yt_description = localStorage.getItem('yt_description')
  download_url = localStorage.getItem('download_url')
  pathname = '/media/youtube/'+yt_channel
  if not os.path.exists(pathname):
    os.makedirs(pathname)
  filename = yt_title+"-("+yt_year+")-["+id+"].mp4".replace("'","").replace("/","-")
  dl_file = filename.replace("/","-")
  dl_path = pathname+"/"+dl_file
  print(dl_path)
  with urlopen(download_url) as in_stream, open(dl_path, 'wb') as out_file:
    copyfileobj(in_stream, out_file)
  #progress = urllib.request.urlretrieve(download_url, pathname+"/"+filename)
  if not os.path.exists(pathname+"/"+filename):
      return "There was an error"
  else:
      return "File Downloaded"

@app.route('/ytdl/<id>')
def ytdl(id):
   data = download(id)
   response = redirect('/download/'+id)
   return response

@app.route('/test/<page>')
def test(page=None):
    response = render_template(page+'.html')
    return response

def fork_status(download_id=None,section=None):
    print(os.getpid())
    target_url = 'https://p.oceansaver.in/ajax/progress.php?id='+download_id
    success = 0
    while success == 0:
        response = requests.get(target_url).json()
        success = response['success']
        if success == 0:
            print(response['progress'])
            file =open("config/downloads.ini","r")
            downloads.read_file(file)
            downloads.set(section, 'progress', str(response['progress']))
            with open('config/downloads.ini', 'w') as configfile:
                downloads.write(configfile)
            file.close()
            sleep(20)
        else:
            download_url = response['download_url']
    file =open("config/downloads.ini","r")
    downloads.read_file(file)        
    downloads.set(section, 'download_url', response['download_url'])
    downloads.set(section, 'progress', '1000')
    with open('config/downloads.ini', 'w') as configfile:
        downloads.write(configfile)
    file.close()
    print("done")


@app.route('/metube/<video_id>')
def metube(video_id=None):
    target_url = 'http://172.22.20.22:8081/add'
    target_data = {"url":video_id,"quality":"480","format":"mp4","playlist_strict_mode":False,"auto_start":True}
    response = requests.post(target_url, json=target_data).json()
    return response['status']

@app.route('/config/<video_id>')
@app.route('/config/<video_id>/<res>')
def configs(video_id=None,res=None):
    if res == None:
        res = '480'
    file =open("config/downloads.ini","r")
    downloads.read_file(file)
    section = video_id+'-'+res
    if downloads.has_section(section) == False:
        downloads.add_section(section)
        target_url = 'http://172.22.20.22:8081/add'
        target_data = {'url':video_id,'quality':'480','format':'mp4','playlist_strict_mode':False,'auto_start':True}
        response = requests.post(target_url, json=target_data).json()
        metadata = ytmetadata(video_id)
        downloads.set(section, 'title', metadata['items'][0]['snippet']['title'])
        downloads.set(section, 'title_parsed', metadata['items'][0]['snippet']['title'].replace("/","-").replace('"','').replace("%",""))
        downloads.set(section, 'video_id', video_id)
        downloads.set(section, 'resolution', res)
        downloads.set(section, 'download_id', "id" )
        downloads.set(section, 'poster', "")
        downloads.set(section, 'progress', '1000')
        metadata = ytmetadata(video_id)
        print(metadata)
        downloads.set(section, 'channel', metadata['items'][0]['snippet']['channelTitle'])
        downloads.set(section, 'year', metadata['items'][0]['snippet']['publishedAt'].split('-',1)[0])

        with open('config/downloads.ini', 'w') as configfile:
            downloads.write(configfile)
        file.close()

    return redirect('/')
     




@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        try:
          id = request.args.get('id')
          try:
             res = request.args.get('res')
          except:
             res = '480'
        except:
          id = '' 

        if id != None:
           response = redirect('/config/'+id+'/'+res)
        else:
           downloads = get_downloads()
           response = render_template('v3_home.html', downloads=downloads)

    if request.method == 'POST':
        videoid = request.form.get('url')
        res = request.form.get('res')
        videoid=videoid.split("=")
        video_id=videoid[(len(videoid)-1)]
        url = '/config/'+video_id+'/'+res
        response = redirect(url)

    downloads = get_downloads()
    for sections in downloads:
        try:
            downloaded = downloads[sections]['downloaded']
        except:
            newpid = os.fork()
            if newpid == 0:
                print(os.getpid())
                fork_dl(downloads[sections])
    return response

if __name__ == '__app__':
    app.run(debug=True)
