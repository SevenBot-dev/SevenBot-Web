import datetime
# import hashlib
import json
import os
import random
# import re
import secrets
import time
import urllib.parse

import authlib.integrations.requests_client as auth_requests
import pymongo
import requests
from dotenv import load_dotenv
from flask import (Blueprint, Flask, jsonify, make_response, redirect,
                   render_template, request, session, current_app)
from selenium import webdriver


DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET = os.environ.get(
    "discord_client_id"), os.environ.get("discord_client_secret")

API_ENDPOINT = 'https://discord.com/api/v8'
SCOPE = 'guilds%20identify'

allowed_scopes = {
    "afk": "AFKにアクセスできるようになります。"
}


def exchange_code(code):
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': ("https://api.sevenbot.jp/oauth2/callback" if os.getenv("heroku") else "http://localhost:5000/oauth2/callback"),
        'scope': SCOPE
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(
        '%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()


# Define a new client.
if not os.getenv("heroku"):
    load_dotenv("../.env")
    print("[api]Not heroku, loaded .env", os.environ.get("connectstr"))
client = pymongo.MongoClient(os.getenv("connectstr"))
# mongodb+srv://sevenbot:<password>@cluster0.3ns84.mongodb.net/<dbname>?retryWrites=true&w=majority
guild_collection = client.sevenbot.guild_settings
afk_collection = client.sevenbot.afks
afk_key_collection = client.sevenbot.afk_keys
commands_collection = client.sevenbot.commands
twitter_collection = client.sevenbot.twitter_keys
twitter_text_collection = client.sevenbot.afk_twitter_text
application_collection = client.sevenbot.applications
refresh_collection = client.sevenbot.refresh_tokens
app = Blueprint('api', __name__, template_folder='./templates', static_folder='./static')


def request_after(*args, **kwargs):
    res = requests.request(*args, **kwargs)
    while res.status_code == 429:
        time.sleep(res.headers["retry-after"])
        res = requests.request(*args, **kwargs)
    return res


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


def can_access(password, gid):
    if password == os.environ.get("password"):
        return True

    guilds = request_after("get",
                           "discord.com/api/users/@me/guilds",
                           headers={
                               "password": "Bearer " + password
                           }).json()
    g = list(filter(lambda item: item["id"] == str(gid), guilds))
    if not g:
        return False
    g = request_after("get",
                      f"discord.com/api/guilds/{gid}",
                      headers={
                          "password": "Bot " + os.environ.get("token")
                      }).json()
    if g.status_code == 403:
        return False
    elif g["unavailable"]:
        return False
    # pprint(r.json())
    r = request_after("get",
                      API_ENDPOINT + f'/guilds/{gid}/members/686547120534454315',
                      headers={"password": "Bot " + os.environ.get("token")})
    uroles = r.json()["roles"]
    r = request_after("get",
                      API_ENDPOINT + f'/guilds/{gid}/roles',
                      headers={"password": "Bot " + os.environ.get("token")})
    groles = r.json()
    res = {}
    for r in uroles:
        res[int(r)] = [r2 for r2 in groles if r2["id"] == r][0]

    for r in res:
        if bin(int(r["permissions"]))[2:].zfill(31)[-6] == "1":
            return True

    return False


@app.route('/')
def base():
    return jsonify({"message": "Welcome to SevenBot API! You can see docs in https://sevenbot.jp/api"})


@app.route('/webshot', methods=["post"])
def webshot():
    try:
        res = json.loads(request.data.decode("utf8"))
        if res.get("password") != os.environ.get("password"):
            return make_response(
                jsonify({
                    "error_description": "You cannot access this endpoint.",
                    "code": "forbidden"
                }), 403)
    except Exception:
        return make_response(jsonify({
            "error_description": "You cannot access this endpoint.",
            "code": "forbidden"
        }), 403)
    option = webdriver.ChromeOptions()
    option.add_argument('--headless')
    option.add_argument('--lang=ja-JP,ja')
    option.add_experimental_option('prefs', {'intl.accept_languages': 'ja,ja_JP'})
    driver = webdriver.Chrome(options=option)

    # driver = webdriver.Firefox()
    # driver.set_preference("intl.accept_languages", "ja")

    driver.get(res["url"])

    driver.set_window_size(1280, 720)

    time.sleep(2)

    response = make_response(driver.get_screenshot_as_png())
    response.headers.set('Content-Type', 'image/png')
    driver.quit()
    return response


@app.route('/afk', methods=["get"])
def afk_key():
    try:
        key = afk_key_collection.find_one({
            "uid": int(request.headers["authorization"].split(" ")[0]),
            "hash": request.headers["authorization"].split(" ")[1]
        })
    except KeyError:
        return make_response(jsonify({"error_description": "authorization header is missing. Please specify authorization header.", "code": "invalid_request"}), 401)
    except (IndexError, ValueError):
        return make_response(jsonify({"error_description": "authorization header must follor sbtoken format.", "code": "invalid_authorization"}), 401)

    if key is None:
        return make_response(jsonify({"error_description": "API key or user ID is incorrect. Please recheck your user ID and your API key.", "code": "invalid_client"}), 401)
    elif key["oauth"]:
        return make_response(jsonify({"error_description": "You can't use OAuth token in this endpoint.", "code": "invalid_request"}), 401)
    if not request.args.get("userid"):
        return make_response(jsonify({"error_description": "userid is a required argument.", "code": "invalid_request"}), 400)
    try:
        res = afk_collection.find_one({
            "uid": int(request.args.get("userid")),
        })
    except ValueError:
        return make_response(jsonify({"error_description": "userid muse be numbers.", "code": "bad_argument"}), 400)
    if res is None:
        return make_response(jsonify({"error_description": False}), 200)
    else:
        return make_response(jsonify({"error_description": True, "reason": res["reason"]}), 200)


@app.route('/afk', methods=["post", "put"])
def afk_post():
    inp = request.json or request.form
    try:
        check = afk_key_collection.find_one({
            "uid": int(request.headers["authorization"].split(" ")[0]),
            "hash": request.headers["authorization"].split(" ")[1]
        })
    except KeyError:
        return make_response(jsonify({"error_description": "authorization header is missing. Please specify authorization header.", "code": "invalid_request"}), 401)
    except (IndexError, ValueError):
        return make_response(jsonify({"error_description": "authorization header must follor sbtoken format.", "code": "invalid_authorization"}), 401)

    if check is None:
        return make_response(jsonify({"error_description": "API key or user ID is incorrect. Please recheck your user ID and your API key.", "code": "invalid_client"}), 401)

    afk_collection.delete_one({"uid": int(request.headers["authorization"].split(" ")[0])})
    afk_collection.insert_one({
        "uid": int(request.headers["authorization"].split(" ")[0]),
        "reason": inp.get("reason"),
        "urls": []
    })
    t = twitter_collection.find_one({"uid": int(request.headers["authorization"].split(" ")[0])})
    res = {"message": "You're now AFK. Your AFK will be lifted when you say something in discord."}
    res["tweet"] = None
    if t is not None:
        tx = twitter_text_collection.find_one({"uid": int(request.headers["authorization"].split(" ")[0])})
        txt = tx["activate"].replace("!reason", inp.get("reason", "なし")).replace("!user", "@" + t["name"])
        auth = auth_requests.OAuth1Auth(os.environ.get("twitter_consumer_key"), os.environ.get("twitter_consumer_secret"), t["token"], t["secret"])
        resp = requests.post("https://api.twitter.com/1.1/statuses/update.json", params={"status": txt}, auth=auth)
        if resp.status_code == 200:
            j = resp.json()
            res["tweet"] = f'https://twitter.com/{j["user"]["screen_name"]}/status/{j["id"]}'
        else:
            res["tweet"] = False
    return make_response(jsonify(res), 200)


@app.route('/afk', methods=["delete"])
def afk_delete():
    try:
        check = afk_key_collection.find_one({
            "uid": int(request.headers["authorization"].split(" ")[0]),
            "hash": request.headers["authorization"].split(" ")[1]
        })
    except KeyError:
        return make_response(jsonify({"error_description": "authorization header is missing. Please specify authorization header.", "code": "invalid_request"}), 401)
    except (IndexError, ValueError):
        return make_response(jsonify({"error_description": "authorization header must follor sbtoken format.", "code": "invalid_authorization"}), 401)

    if check is None:
        return make_response(jsonify({"error_description": "API key or user ID is incorrect. Please recheck your user ID and your API key.", "code": "invalid_client"}), 401)

    f = afk_collection.find_one_and_delete({"uid": int(request.headers["authorization"].split(" ")[0])})
    if f is None:
        return make_response(jsonify({"message": "You're not AFK.", "code": "not_afk"}), 200)
    else:
        t = twitter_collection.find_one({"uid": int(request.headers["authorization"].split(" ")[0])})
        res = {"message": f"You are no longer AFK. You got pinged {len(f['urls'])} times.", "urls": f['urls'], "tweet": None}
        if t is not None:
            tx = twitter_text_collection.find_one({"uid": int(request.headers["authorization"].split(" ")[0])})
            txt = tx["deactivate"].replace("!user", "@" + t["name"])
            auth = auth_requests.OAuth1Auth(os.environ.get("twitter_consumer_key"), os.environ.get("twitter_consumer_secret"), t["token"], t["secret"])
            resp = requests.post("https://api.twitter.com/1.1/statuses/update.json", params={"status": txt}, auth=auth)
            if resp.status_code == 200:
                j = resp.json()
                res["tweet"] = f'https://twitter.com/{j["user"]["screen_name"]}/status/{j["id"]}'
            else:
                res["tweet"] = False
        return make_response(jsonify(res), 200)


@app.route('/teapot', methods=["get"])
def teapot():
    return make_response(jsonify({"message": "I'm not a teapot.", "code": "not_teapot"}), 418)


@app.route('/dbl', methods=["get", "post"])
def dbl():
    requests.post("https://canary.discord.com/api/webhooks/773443377147936778/wdDFijmd9G0dVict2qpP-3rOP9i2i3e-LDcAlWSRCVF5WwTJziLoMVETMb8Ldy5qCONP",
                  json={"content": f"<@!{request.json['user']}> さんが高評価をしてくれました！",
                        "allowed_mentions": {
                            "parse": []
                        }
                        })

    return make_response("", 204)


@app.errorhandler(404)
def notfound(_):
    return jsonify({"message": "Unknown endpoint. Make sure your url is correct.", "code": "not_found"})


@app.route('/oauth2/authorize')
def oauth2_authorize():
    global auth_tokens, tmp_tokens
    tmp_token = secrets.token_urlsafe(16)
    session["sessionid"] = tmp_token
    required_args = {"client_id", "response_type", "scope"}
    if not current_app.config.get("auth_tokens"):
        current_app.config["auth_tokens"] = {}
    auth_tokens = current_app.config["auth_tokens"]

    if not current_app.config.get("tmp_tokens"):
        current_app.config["tmp_tokens"] = {}
    tmp_tokens = current_app.config["tmp_tokens"]
    if required_args - set(request.args.keys()):
        return make_response(render_template("oauth/error.html", error_desc=f"パラメータが不足しています。（{', '.join(required_args - set(request.args.keys()))}）"), 400)
    elif request.args["response_type"] != "code":
        return make_response(render_template("oauth/error.html", error_desc="レスポンスのタイプが違います。（codeである必要があります）"), 400)
    app = application_collection.find_one({"id": request.args["client_id"]})
    if not app:
        return make_response(render_template("oauth/error.html", error_desc="不明なアプリです。"), 400)
    # elif request.args["response_type"] == "code":
    #     if "redirect_uri" not in request.args.keys():
    #         return make_response(render_template("oauth/error.html", error_desc="レスポンスのタイプがcodeの場合、redirect_uriを指定する必要があります。"), 400)
    elif set(request.args["scope"].split()) - set(allowed_scopes.keys()):
        return make_response(render_template("oauth/error.html", error_desc=f"不明なスコープです。（{', '.join(request.args['scope'].split() - set(allowed_scopes.keys()))}）"), 400)
    if "redirect_uri" in request.args.keys():
        if request.args["redirect_uri"] not in app["redirect_uris"]:
            return make_response(render_template("oauth/error.html", error_desc="リダイレクト先が登録されていません。"), 400)
    else:
        if not app["enable_pin"]:
            return make_response(render_template("oauth/error.html", error_desc="PIN認証がオフです。"), 400)
    sc = []
    for s in request.args['scope'].split():
        sc.append(allowed_scopes[s])
    tmp_tokens[tmp_token] = {"params": request.args, "app": app}

    def show_login():
        r = make_response(render_template(
            'oauth/login.html',
            url="https://discord.com/api/oauth2/authorize?client_id=718760319207473152&redirect_uri=https%3A%2F%2Fapi.sevenbot.jp%2Foauth2%2Fcallback&response_type=code&scope=guilds%20identify"
        ), 200)

        return r

    if request.cookies.get('token'):
        r = request_after("GET", "https://discord.com/api/v8/users/@me", headers={"authorization": "Bearer " + str(request.cookies.get('token'))})
        if r.status_code == 401:
            return show_login()
        tmp_tokens[tmp_token]["user"] = r.json()
        return render_template("oauth/authorize.html", app_name=app["name"], app_icon=app["icon"], app_scopes=sc)

    else:
        return show_login()


@app.route('/oauth2/callback')
def oauth2_callback():
    code = request.args['code']
    print(session)
    if not session.get("sessionid"):
        response = make_response(render_template("oauth/error_user.html", error_desc="セッションが切れました。"), 404)
        return response
    code_json = exchange_code(code)
    response = make_response(redirect('/oauth2/authorize?' + urllib.parse.urlencode(tmp_tokens[session["sessionid"]]["params"])))
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


@app.route('/oauth2/accept')
def oauth2_accept():
    if "sessionid" not in session.keys():
        response = make_response(render_template("oauth/error_user.html", error_desc="セッションが切れました。"), 404)
        return response
    sid = session["sessionid"]
    if "refirect_uri" not in tmp_tokens[sid]["params"].keys():
        session.clear()
        t = str(random.randrange(0, 1000000)).zfill(7)
        auth_tokens[t] = {"params": tmp_tokens[sid]["params"], "timestamp": int(time.time()), "user": tmp_tokens[sid]["user"]}
        return render_template("oauth/pin.html", pin=t, app_name=tmp_tokens[sid]["app"]["name"])
    else:
        t = secrets.token_urlsafe(32)
        auth_tokens[t] = {"params": tmp_tokens[sid]["params"], "timestamp": int(time.time()), "user": tmp_tokens[sid]["user"]}
    return redirect(tmp_tokens[sid]["params"]["redirect_uri"] + "?code=" + t + "&expires_in=300")


@app.route('/oauth2/deny')
def oauth2_deny():
    if not session.get("sessionid"):
        response = make_response(render_template("oauth/error_user.html", error_desc="セッションが切れました。"), 404)
        return response
    return redirect(tmp_tokens[session["sessionid"]]["params"]["redirect_uri"] + "?error=access_denied")


@app.route('/oauth2/token', methods=["post"])
def oauth2_token():
    required_args = {'client_id', 'client_secret', 'grant_type', 'code', 'scope'}
    form = {k: v for k, v in request.form.items() if v}
    if required_args - set(form.keys()):
        return make_response(jsonify({"error_description": "Missing required params.", "code": "invalid_request", "required": list(required_args)}), 400)
    elif form["grant_type"] != "authorization_code":
        return make_response(jsonify({"error_description": "grant_type must be 'authorization_code'.", "code": "unsupported_grant_type"}), 400)
    app = application_collection.find_one({"id": form["client_id"]})

    if not app:
        return make_response(jsonify({"error_description": "Unknown applicaion.", "code": "invalid_client"}), 400)
    if "redirect_uri" in form:
        if form["redirect_uri"] not in app["redirect_uris"]:
            return make_response(jsonify({"error_description": "Unknown redirect_uri.", "code": "invalid_request"}), 400)
    else:
        if not app["enable_pin"]:
            return make_response(jsonify({"error_description": "PIN authorization is disabled for this application.", "code": "invalid_request"}), 400)

    if form["code"] not in auth_tokens.keys():
        return make_response(jsonify({"error_description": "Invalid grant code.", "code": "invalid_grant"}), 404)
    auth_data = auth_tokens[form["code"]]
    if set(form["scope"].split()) - set(allowed_scopes.keys()):
        return make_response(jsonify({"error_description": "Unknown scope.", "code": "invalid_scope"}), 400)
    if app["secret"] != form["client_secret"]:
        return make_response(jsonify({"error_description": "client secret doesn't match.", "code": "invalid_client"}), 401)
    if set(form["scope"].split()) - set(auth_data["params"]["scope"].split()):
        return make_response(jsonify({"error_description": "scope exceeds code's scope.", "code": "invalid_scope"}), 401)
    token = secrets.token_urlsafe(32)
    res = {
        "access_token": token,
        "token_type": "sbuauth",
        "scope": form["scope"],
        "expires_in": 60 * 60 * 24,
        "user_id": int(auth_data["user"]["id"])
    }
    for s in form["scope"].split():
        if s == "afk":
            afk_key_collection.insert_one({"uid": int(auth_data["user"]["id"]), "hash": token, "oauth": True})

    return res


@app.route('/header')
def header():
    return render_template('share/header.html')


@app.route('/footer')
def footer2():
    return render_template('share/footer.html')


@app.errorhandler(405)
def methodnotallowed(_):
    return jsonify({"message": "Invalid request type. Make sure your request type is correct.", "code": "wrong_request_type"})


if __name__ == "__main__":
    load_dotenv("../.env")
    testapp = Flask("api")
    testapp.register_blueprint(app)
    testapp.secret_key = "ABCdefGHI"
    testapp.run(debug=True)
