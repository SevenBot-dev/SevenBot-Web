import os
import random
import string
import sys
import time
import urllib.parse

from dotenv import load_dotenv
from flask import (Flask, Blueprint, make_response, render_template, redirect, request)
import mimetypes
from pymongo import MongoClient
import requests

if sys.platform.lower() == "win32":
    os.system('color')
mimetypes.add_type('image/webp', '.webp')
if not os.getenv("heroku"):
    load_dotenv("../.env")
    print("[general]Not heroku, loaded .env", os.environ.get("connectstr"))
mainclient = MongoClient(os.environ.get("connectstr"))
commandscollection = mainclient.sevenbot.commands
statuscollection = mainclient.sevenbot.status_log
DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET = os.environ.get(
    "discord_client_id"), os.environ.get("discord_client_secret")

if __name__ == "__main__":
    load_dotenv("../.env")
    host = "http://localhost:5000"
else:
    host = "https://dashboard.sevenbot.jp"
ruri = host + "/callback"
login_url = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={urllib.parse.quote(ruri)}&response_type=code&scope=guilds%20identify&state={{}}"
API_ENDPOINT = 'https://discord.com/api/v9'
SCOPE = 'guilds%20identify'


def request_after(*args, **kwargs):
    res = requests.request(*args, **kwargs)
    while res.status_code == 429:
        time.sleep(res.headers["retry-after"])
        res = requests.request(*args, **kwargs)
    return res


def exchange_code(code):
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': ruri,
        'scope': SCOPE
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = request_after("POST",
                      '%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()


def refresh_token(refresh_token):
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'redirect_uri': "https://captcha.sevenbot.jp/callback",
        'scope': SCOPE
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = request_after("POST", '%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()


app = Blueprint('dashboard', __name__, template_folder='./templates', static_folder="./static")


def make_random_str(l):
    return ''.join(random.choices(string.ascii_letters, k=l))


@app.route("/")
def index():
    return render_template("dashboard/index.html")


@app.route("/login")
def login():
    return redirect(login_url.format(request.args["from"]))


@app.errorhandler(404)
def page_not_found(error):
    return make_response(render_template('dashboard/404.html'), 404)


if __name__ == "__main__":
    testapp = Flask(__name__)
    testapp.register_blueprint(app)
    testapp.secret_key = "ABCdefGHI"
    testapp.run(debug=True)
