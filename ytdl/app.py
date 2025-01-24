from flask import redirect, Flask, render_template, request, jsonify,session
from urllib.request import urlopen
from shutil import copyfileobj
import os
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
api_key = 'AIzaSyCqSJwVtcBcSyeUgizos7uKXbBWgVh-8qg'
##keyFile.readline().rstrip()
app.secret_key = keyFile.readline().rstrip()
progress = 0
status = 0
download_url = ''
localStorage = localStoragePy('pk', 'text')
config_object = configparser.ConfigParser()

def task():
  global status
  global progress
  global download_url
  data = {}
  data = localStorage.getItem('data')
  progress_data = localStorage.getItem('progress')
  if status != 1:
    id = localStorage.getItem('download_data_id')
    target_url = 'https://p.oceansaver.in/ajax/progress.php?id='+id
    response = requests.get(target_url).json()
    localStorage.setItem('progress', response)
    status = response['success']
    progress = response['progress']
    download_url = response['download_url']
    localStorage.setItem('download_url', download_url)
    progress=(int(response['progress'])/100)
  sleep(5)


@app.route('/status')
def download_status():
  global download_url

  yt_title = localStorage.getItem('yt_title')
  yt_channel = localStorage.getItem('yt_channel')
  yt_year = localStorage.getItem('yt_year')
  poster = localStorage.getItem('poster')
  video_id = localStorage.getItem('video_id')
    
  t1 = Thread(target=task)
  t1.start()
  return render_template('status2.html', yt_title=yt_title, poster=poster, yt_channel=yt_channel, yt_year=yt_year, video_id=video_id)


@app.route('/api/status', methods=['GET'])
def getStatus():
  global status
  global progress
  global download_url
  data = localStorage.getItem('data')
  statusList = {'status':status, 'progress': progress, 'download_url': download_url, 'data': data}
  return json.dumps(statusList)


@app.route('/api/ytmetadata/<id>')
def ytmetadata(id=None):
    headers = {
            'Authorization': 'Bearer your_token_here',
            'Content-Type': 'application/json'
        }
    target_url = "https://content-youtube.googleapis.com/youtube/v3/videos?id="+id+"&part=snippet,contentDetails,statistics&key="+api_key
    response = requests.get(target_url)
    return response.json()

@app.route('/api/metadata/<id>')
def metadata(id):
    data=ytmetadata(id)
    channel=data['items'][0]['snippet']['channelTitle']
    title=data['items'][0]['snippet']['title'].replace('"','')
    year=data['items'][0]['snippet']['publishedAt'].split('-',1)
    response = {}
    response = {'channel':channel,'title':title, 'year': year[0] }
    return response

@app.route('/download/<id>')
@app.route('/download/<id>/<res>')
def download(id=None,res=None):
    print(id)
    print(res)
    if res == None:
        res="480"
    else:
        res=res

    target_url = 'https://p.oceansaver.in/ajax/download.php?format='+res+'&url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D'+id
    headers =    {
        'Referer': 'https://en.loader.to/',
        'Origin': 'https://en.loader.to',
        'Content-Type': 'application/json'
    }
    download_data = {}
    download_data = requests.get(target_url).json()
    #print(download_data)
    localStorage.setItem('download_data',download_data)

    youtube_metadata = {}
    youtube_metadata = ytmetadata(id)
    #print(youtube_metadata['items'][0]['snippet']['thumbnails'])
    localStorage.setItem('metadata',youtube_metadata)

    download_id = download_data['id']
    progress_data = {} 

    localStorage.setItem('download_data_id',download_id)
    target_url = 'https://p.oceansaver.in/ajax/progress.php?id='+download_id
    progress_data = requests.get(target_url).json()
    print(progress_data)
    localStorage.setItem('progress',progress_data)

    data = {}
    data = youtube_metadata.copy()
    data.update(download_data)
    data.update(progress_data)
    localStorage.setItem('data',data)

    localStorage.setItem('yt_title',youtube_metadata['items'][0]['snippet']['title'].replace('"',""))
    localStorage.setItem('yt_channel',youtube_metadata['items'][0]['snippet']['channelTitle'])
    localStorage.setItem('yt_year',youtube_metadata['items'][0]['snippet']['publishedAt'].split('-',1)[0])
    #localStorage.setItem('yt_description',youtube_metadata['items'][0]['snippet']['description'].replace("\n","<br>"))
    localStorage.setItem('poster',youtube_metadata['items'][0]['snippet']['thumbnails']['high']['url'])
    localStorage.setItem('download_url',progress_data['download_url'])
    localStorage.setItem('video_id',id)

    #localStorage.setItem('',)
    #localStorage.setItem('',)
    #localStorage.setItem('',)
    #localStorage.setItem('',)

    return redirect('/status')

@app.route('/download_to_plex/<id>')
def pleX_dl(id=None):
    global download_url
    data = localStorage.getItem('data')
    ytdata = localStorage.getItem('metadata')
    yt_title = localStorage.getItem('yt_title')
    yt_channel = localStorage.getItem('yt_channel')
    yt_year = localStorage.getItem('yt_year')
    yt_description = localStorage.getItem('yt_description')
    if download_url == '':
        local_download_url = localStorage.getItem('download_url')
    else:
        local_download_url = download_url
    video_id = localStorage.getItem('video_id')
    poster = localStorage.getItem('poster')
    newpid = os.fork()
    file =open("config.ini","r")
    config_object.read_file(file)
    if config_object.has_section(video_id) == False:
        config_object.add_section(video_id)
        config_object.set(video_id, 'title', yt_title)
        config_object.set(video_id, 'channel', yt_channel)
        config_object.set(video_id, 'link', download_url)
        with open('config.ini', 'w') as configfile:
            config_object.write(configfile)
    else:
        print("yes")
    
    output_dict=dict()
    sections=config_object.sections()
    print(sections)
    for section in sections:
        items=config_object.items(section)
        output_dict[section]=dict(items)
    json_string=json.dumps(output_dict)
    print("The output JSON string is:")
    print(json_string)
    file.close()

    if newpid == 0:
        dl = plex_dl(id)
        print("done")

    return render_template('plex2.html',poster=poster, data=data, yt_title=yt_title, ytdata=ytdata, yt_channel=yt_channel, yt_year=yt_year, yt_description=yt_description, download_url=download_url, video_id=video_id, history=output_dict)

@app.route('/add')
def add():
    file =open("config.ini","r")
    config_object.read_file(file)

    config_object.add_section(video_id)
    config_object.set(video_id, 'title', yt_title)
    config_object.set(video_id, 'link', download_url)
    with open('config.ini', 'w') as configfile:
        config_object.write(configfile) 
    return "ok"
@app.route('/history')
def history():
    file =open("config.ini","r")
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
    file.close()
    return render_template('history.html', history=output_dict)

@app.route('/api/ytdl/<id>')
def plex_dl(id=None):
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
           response = redirect('/download/'+id+'/'+res)
        else:
           response = render_template('dl2.html')

    if request.method == 'POST':
        videoid = request.form.get('url')
        res = request.form.get('res')
        videoid=videoid.split("=")
        video_id=videoid[(len(videoid)-1)]
        url = '/download/'+video_id+'/'+res
        response = redirect(url)

    return response

if __name__ == '__app__':
    app.run(debug=True)
