from flask import redirect, Flask, render_template, request, jsonify,session
import os
from localStoragePy import localStoragePy
import requests
import threading
import urllib.request
from threading import Thread
from time import sleep
import json
import base64

keyFile = open('config/keys', 'r')
app = Flask(__name__)
api_key = keyFile.readline().rstrip()
app.secret_key = keyFile.readline().rstrip()
progress = 0
status = 0

localStorage = localStoragePy('pk', 'text')

def task():
  global status
  global progress
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
    progress=(int(response['progress'])/100)
  sleep(5)


@app.route('/status')
def download_status():
  data = localStorage.getItem('data')
  ytdata = {}
  ytdata = localStorage.getItem('metadata')
  yt_title = localStorage.getItem('yt_title')
  yt_channel = localStorage.getItem('yt_channel')
  yt_year = localStorage.getItem('yt_year')
  yt_description = localStorage.getItem('yt_description')
  download_url = localStorage.getItem('download_url')
  video_id = localStorage.getItem('video_id')
    
  t1 = Thread(target=task)
  t1.start()
  return render_template('d.html',data=data, yt_title=yt_title, ytdata=ytdata, yt_channel=yt_channel, yt_year=yt_year, yt_description=yt_description, download_url=download_url, video_id=video_id)


@app.route('/api/status', methods=['GET'])
def getStatus():
  global status
  global progress
  data = localStorage.getItem('data')
  statusList = {'status':status, 'progress': progress, 'data': data}
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
@app.route('/api/download/<id>')
@app.route('/api/download/<id>/<res>')
def download(id=None,res=None):

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
    localStorage.setItem('download_data',download_data)

    youtube_metadata = {}
    youtube_metadata = ytmetadata(id)
    localStorage.setItem('metadata',youtube_metadata)

    download_id = download_data['id']
    progress_data = {} 

    localStorage.setItem('download_data_id',download_id)
    target_url = 'https://p.oceansaver.in/ajax/progress.php?id='+download_id
    progress_data = requests.get(target_url).json()
    localStorage.setItem('progress',progress_data)

    data = {}
    data = youtube_metadata.copy()
    data.update(download_data)
    data.update(progress_data)
    localStorage.setItem('data',data)

    localStorage.setItem('yt_title',youtube_metadata['items'][0]['snippet']['title'].replace('"',""))
    localStorage.setItem('yt_channel',youtube_metadata['items'][0]['snippet']['channelTitle'])
    localStorage.setItem('yt_year',youtube_metadata['items'][0]['snippet']['publishedAt'].split('-',1)[0])
    localStorage.setItem('yt_description',youtube_metadata['items'][0]['snippet']['description'].replace("\n","<br>"))
    localStorage.setItem('download_url',progress_data['download_url'])
    localStorage.setItem('video_id',id)

    #localStorage.setItem('',)
    #localStorage.setItem('',)
    #localStorage.setItem('',)
    #localStorage.setItem('',)

    return redirect('/status')

@app.route('/download_to_plex/<id>')
def pleX_dl(id=None):
    data = localStorage.getItem('data')
    ytdata = localStorage.getItem('metadata')
    yt_title = localStorage.getItem('yt_title')
    yt_channel = localStorage.getItem('yt_channel')
    yt_year = localStorage.getItem('yt_year')
    yt_description = localStorage.getItem('yt_description')
    download_url = localStorage.getItem('download_url')
    video_id = localStorage.getItem('video_id')
    newpid = os.fork()
    if newpid == 0:
        dl = plex_dl(id)
        print("done")
    return render_template('plex.html',data=data, yt_title=yt_title, ytdata=ytdata, yt_channel=yt_channel, yt_year=yt_year, yt_description=yt_description, download_url=download_url, video_id=video_id)

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
  filename = yt_title+"-("+yt_year+")-["+id+"].mp4".replace("'","")
  print(filename)
  progress = urllib.request.urlretrieve(download_url, pathname+"/"+filename)
  if not os.path.exists(pathname+"/"+filename):
      return "There was an error"
  else:
      return "File Downloaded"

@app.route('/ytdl/<id>')
def ytdl(id):
   data = download(id)
   response = redirect('/download/'+id)
   return response



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        videoid = request.form.get('videoid')
        resolution = request.form.get('resolution')
        print(videoid)
        target_url = "https://yt.pknw1.co.uk/ytdl"
        videoid=videoid.split("=")
        video_id=videoid[(len(videoid)-1)]
        headers = {
            'Content-Type': 'application/json'
        }

        payload = {
            'videoid': videoid,
            'resolution': resolution
        }

        url = target_url+'/'+video_id
        return redirect(url)
    return render_template('form.html')


if __name__ == '__app__':
    app.run(debug=True)
