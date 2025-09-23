from ubuntu:latest

run apt update && apt install -y openjdk-21-jre-headless 
run mkdir /app 
workdir /app 

copy ./requirements.txt /app/

run apt install -y python3-minimal python3-venv
run python3 -m venv /app/env
run /app/env/bin/pip3 install -r ./requirements.txt
run apt install -y wget
run wget -O /app/animator.jar https://download.gpx-animator.app/gpx-animator-1.8.2-all.jar

run rm ./requirements.txt
copy ./app.py /app/ 
copy ./bot.py /app/
copy ./download.py /app/
copy ./files.py /app/
copy ./__init__.py /app/
copy ./settings.py /app/
copy ./storage.py /app/
copy ./utils.py /app/

run mkdir /app/cropper/
copy ./cropper/__init__.py /app/cropper/
copy ./cropper/cropper.py /app/cropper/

run mkdir files
run mkdir static
copy ./static/cropper.js /app/static/
copy ./static/cropper.sass /app/static/

run mkdir templates
copy ./templates/cropper.html /app/templates/

run touch /app/__in_docker
run echo "/app/env/bin/flask --app cropper run --cert=/app/fullchain.pem --key=/app/privkey.pem --host 0.0.0.0" > /app/flask.sh
run chmod +x /app/flask.sh

run chmod +x /app/env/lib/python3.12/site-packages/dartsass/./sass/linux-x64/dart-sass/sass

