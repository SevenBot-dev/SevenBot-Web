import datetime
import hashlib
import json
import os
import random
import string
import time

from dotenv import load_dotenv
from flask import (Flask, Blueprint, jsonify, make_response, redirect,
                   render_template, request, session)
from pymongo import MongoClient
import requests
if __name__ == "__main__":
    load_dotenv("../.env")
mainclient = MongoClient(os.environ.get("connectstr"))
maincollecton = mainclient.sevenbot.captcha
DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET = os.environ.get(
    "discord_client_id"), os.environ.get("discord_client_secret")
app = Blueprint('captcha', __name__, template_folder='./templates', static_folder='./static')

API_ENDPOINT = 'https://discord.com/api/v8'
SCOPE = 'guilds%20identify'


def exchange_code(code):
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': "https://captcha.sevenbot.jp/callback",
        'scope': SCOPE
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(
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
    r = requests.post(
        '%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()


def make_random_str(l):
    return ''.join(random.choices(string.ascii_letters, k=l))


app.secret_key = make_random_str(10)


@app.route("/")
def index():
    return render_template("captcha/index.html")


@app.route('/test', subdomain="test")
def test_test():
    return "Test"


@app.route('/verify')
def captcha():

    sessionid = request.args.get("id")
    if not sessionid:
        return render_template(
            'captcha/session.html',
            timeout=False
        )

    def show_login():
        r = make_response(render_template(
            'captcha/login.html',
            url="https://discord.com/api/oauth2/authorize?client_id=718760319207473152&redirect_uri=https%3A%2F%2Fcaptcha.sevenbot.jp%2Fcallback&response_type=code&scope=guilds%20identify"
        ), 200)
        session["sessionid"] = sessionid
        return r
    if not maincollecton.find_one({"sid": sessionid}):
        return render_template(
            'captcha/session.html',
            timeout=False
        )
    elif time.time() - float(maincollecton.find_one({"sid": sessionid})["time"]) > 300:
        maincollecton.delete_one({"sid": sessionid})
        return render_template(
            'captcha/session.html',
            timeout=True
        )
    elif request.cookies.get('token'):
        r = requests.get("https://discord.com/api/v8/users/@me", headers={"authorization": "Bearer " + str(request.cookies.get('token'))})
        if r.status_code == 401:
            return show_login()
        if r.json()["id"] != str(maincollecton.find_one({"sid": sessionid})["uid"]):
            return render_template("captcha/wrong_user.html", url="https://discord.com/api/oauth2/authorize?client_id=718760319207473152&redirect_uri=https%3A%2F%2Fcaptcha.sevenbot.jp%2Fcallback&response_type=code&scope=guilds%20identify")
        r = make_response(render_template("captcha/login.html", url=None), 200)
        session["sessionid"] = sessionid
        return r
    else:
        return show_login()


@app.route('/callback')
def callback():
    if "sessionid" not in session.keys():
        return render_template(
            'captcha/session.html',
            timeout=False
        )
    code = request.args['code']
    code_json = exchange_code(code)
    response = make_response(redirect('https://captcha.sevenbot.jp/verify?id=' + session["sessionid"]))
    response.set_cookie(
        "token",
        value=code_json["access_token"],
        path="/",
        expires=datetime.datetime.now() + datetime.timedelta(days=7))
    response.set_cookie(
        "refresh_token",
        value=code_json["refresh_token"],
        path="/",
        expires=datetime.datetime.now() + datetime.timedelta(days=30))
    return response


@app.route('/check', methods=["post"])
def check_ok():
    data = {
        'response': request.args["token"],
        'secret': os.environ.get("hcaptcha_secret"),
        'sitekey': os.environ.get("sitekey")
    }
    r = requests.post('https://hcaptcha.com/siteverify', data=data)
    print(r.text)
    if r.json()["success"]:
        rc = maincollecton.find_one({"sid": request.args["sessionid"]})
        print(rc)
        uid, gid, rid = rc["uid"], rc["gid"], rc["rid"]
        requests.put(f"https://discord.com/api/v8/guilds/{gid}/members/{uid}/roles/{rid}", headers={"authorization": "Bot " + os.environ.get("token")})
        dm = requests.post("https://discord.com/api/v8/users/@me/channels",
                           headers={"authorization": "Bot " + os.environ.get("token")},
                           json={"recipient_id": uid}
                           )

        g = requests.get(f"https://discord.com/api/v8/guilds/{gid}",
                         headers={"authorization": "Bot " + os.environ.get("token")})
        gname = g.json()["name"]
        requests.post("https://discord.com/api/v8/channels/" + dm.json()["id"] + "/messages",
                      headers={"authorization": "Bot " + os.environ.get("token")},
                      json={"content": f"{gname} での認証が完了しました。"}
                      )

        # /guilds/{guild.id}/members/{user.id}/roles/{role.id}
    return make_response(r.text, r.status_code)


@app.route('/session', methods=["post"])
def make_session():
    res = json.loads(request.data.decode("utf8"))
    if res.get("password") != os.environ.get("password"):
        return make_response(
            jsonify({
                "message": "You cannot access this endpoint."
            }), 403)

    hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:16]
    maincollecton.insert_one({"sid": hash, "uid": res['uid'], "gid": res['gid'], "rid": res['rid'], "time": time.time()})
    return make_response(jsonify({"message": hash}), 201)


@app.route('/index')
def index2():
    return redirect("https://captcha.sevenbot.jp/")


@app.route('/success')
def success():
    return render_template('captcha/success.html')


@app.errorhandler(404)
def page_not_found(error):
    return make_response(render_template('captcha/404.html'), 404)


if __name__ == "__main__":
    testapp = Flask(__name__)
    testapp.register_blueprint(app)
    testapp.secret_key = "ABCdefGHI"
    testapp.run(debug=True)