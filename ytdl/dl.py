import subprocess
import requests
import time

def subprocess_url_checker(filename,download_id):
    process = subprocess.Popen(
        ["python3", "-c", f"""
import requests
import time

while True:
    try:
        target_url = "https://p.oceansaver.in/ajax/progress.php?id="
        response = requests.get(target_url+\"{download_id}\")
        if response.json()['success'] == 1:
            if response.json()['download_url'] != None:
                print(response.json()['download_url'])
                break
            else:
                print("Error")
            break
        if response.json()['success'] == 0:
            print(response.json()['progress'])
    except Exception as e:
        pass
    time.sleep(10)

url = response.json()['download_url']
print(f"URL :"+url)
if url != None:
    try:
        with requests.get(url, stream=True) as response:
            print(url)
            response.raise_for_status()
            with open(\"{filename}\", 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                    file.write(chunk)
            print(f"File downloaded successfully")
    except requests.RequestException as e:
        print(f"Failed to download file: ")
else:
    print(f"Failed to download file: ")

"""],
    )
# Example Usage
video_id="vBo7ahKYniQ"
res="480"
download_url = "https://p.oceansaver.in/ajax/download.php?copyright=0&format="+res+"&url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D"+video_id+"&api=dfcb6d76f2f6a9894gjkege8a4ab232222"
download_id = requests.get(download_url).json()
download_id="pjRTiNMO3nAwoMBWsoKU0B0"
print(download_id)
download_url = subprocess_url_checker("test.mp4",download_id)
