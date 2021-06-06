import datetime
import json
import os
import sys
import time
import urllib.parse

from dotenv import load_dotenv
from flask import (Flask, Blueprint, make_response, render_template, redirect, request, g, current_app)
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
        time.sleep(int(res.headers["retry-after"]))
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


def set_user_cache(token):
    ud = request_after("get", "%s/users/@me" % API_ENDPOINT, headers={"Authorization": "Bearer " + token})
    g = request_after("get", "%s/users/@me/guilds" % API_ENDPOINT, headers={"Authorization": "Bearer " + token})
    data = {
        "user": ud.json(),
        "guild": g.json(),
        "time": time.time()
    }
    current_app.config["user_caches"][token] = data
    return data


def get_bot_guilds():
    if current_app.config.get("bot_guild_cache") is not None and time.time() - current_app.config["bot_guild_cache_time"] > 300:
        return current_app.config["bot_guild_cache"]
    li = 0
    ret = []
    while True:
        g = request_after("get", "%s/users/@me/guilds" % API_ENDPOINT, params={"after": li}, headers={"Authorization": "Bot " + os.getenv("token")}).json()
        if not g:
            break
        ret.extend(g)
        li = int(g[-1]["id"])
    current_app.config["bot_guild_cache"] = ret
    current_app.config["bot_guild_cache_time"] = time.time()
    return ret


def can_invite(permissions):
    return bool(int(permissions) & 1 << 5)


app = Blueprint('dashboard', __name__, template_folder='./templates', static_folder="./static")


@app.before_app_request
def load_logged_in_user():
    if current_app.config.get("user_caches") is None:
        current_app.config["user_caches"] = {}
    token = request.cookies.get('token')
    refresh_token = request.cookies.get('refresh_token')
    g.cookies = {}
    if token is not None:
        uc = current_app.config["user_caches"]
        if uc.get(token) is not None:
            g.user = uc[token]
        else:
            g.user = None
    elif refresh_token is not None:
        t = refresh_token(refresh_token)
        g.cookies["access_token"] = dict(
            value=t["access_token"],
            path="/",
            expires=time.time() + t["expires_in"])
        g.cookies["refresh_token"] = dict(
            value=t["refresh_token"],
            path="/",
            expires=datetime.datetime.now() + datetime.timedelta(days=30))
        g.user = set_user_cache(t)
    else:
        g.user = None


@app.after_request
def set_g_cookie(response):
    for ck, cv in g.cookies.items():
        response.set_cookie(ck, **cv)
    return response


@app.route("/")
def index():
    if g.user is not None:
        return render_template("dashboard/index.html", logged_in=True)
    else:
        return render_template("dashboard/index.html", logged_in=False)


@app.route("/invite")
def invite():
    return redirect(f"https://discord.com/oauth2/authorize?client_id=718760319207473152&scope=bot&response_type=code&guild_id={request.args['guild_id']}&disable_guild_select=true&permissions=808840532&redirect_uri={urllib.parse.quote(host)}")


@app.route("/login")
def login():
    state = {
        "from": request.args.get("from")
    }
    return redirect(login_url.format(urllib.parse.quote(json.dumps(state))))


@app.route('/callback')
def callback():
    if "state" not in request.args.keys():
        return redirect("/")
    code = request.args['code']
    code_json = exchange_code(code)
    state = json.loads(request.args["state"])
    response = make_response(redirect(state["from"]))
    response.set_cookie(
        "token",
        value=code_json["access_token"],
        path="/",
        expires=time.time() + code_json["expires_in"])
    response.set_cookie(
        "refresh_token",
        value=code_json["refresh_token"],
        path="/",
        expires=datetime.datetime.now() + datetime.timedelta(days=30))
    set_user_cache(code_json["access_token"])
    return response


@app.get("/api/servers")
def api_servers():
    bot_guilds = get_bot_guilds()
    user_guilds = current_app.config["user_caches"][request.headers["authorization"]]
    mutual_guilds = {gu["id"] for gu in bot_guilds} & {gu["id"] for gu in user_guilds["guild"] if can_invite(gu["permissions"])}
    return {
        "manage": [gu for gu in user_guilds["guild"] if gu["id"] in mutual_guilds and can_invite(gu["permissions"])],
        "invite": [gu for gu in user_guilds["guild"] if can_invite(gu["permissions"]) and gu["id"] not in mutual_guilds]
    }


@app.errorhandler(404)
def page_not_found(error):
    return make_response(render_template('dashboard/404.html'), 404)


if __name__ == "__main__":
    testapp = Flask(__name__)
    testapp.register_blueprint(app)
    testapp.secret_key = "ABCdefGHI"
    testapp.run(debug=True)
