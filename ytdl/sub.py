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
                break
            else:
                print("Error")
            break
    except Exception as e:
        pass
    time.sleep(10)

url = response.json()['download_url']
try:
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(\"{filename}\", 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                file.write(chunk)
        print(f"File downloaded successfully and")
except requests.RequestException as e:
    print(f"Failed to download file: ")
"""],
    )

# Example Usage
download_url = subprocess_url_checker("test.mp4","0tZvPNKUTQgewpSb4AIZe5W")
