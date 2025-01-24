#FROM python:3.14.0a2-alpine3.20
FROM pknw1/ytdl-prod-base
#RUN apk update
#RUN apk add g++
COPY ./ytdl /
#RUN pip install -r requirements.txt
ENTRYPOINT ["flask", "run", "--host=0.0.0.0", "--port=8080"]
