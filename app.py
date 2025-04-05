from flask import Flask
from flask_apscheduler import APScheduler
import requests

url = 'http://127.0.0.1:8000'
# set configuration values

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())

# initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)

@scheduler.task('interval', id='send_sms', seconds = 30)
def send_sms():
    url_exam = url+r'/taskNotification'
    response =requests.get(url_exam)

scheduler.start()
