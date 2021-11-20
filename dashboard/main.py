import datetime
from hashlib import sha256
import itertools
import json
import os
import redis
import sys
import time
import urllib.parse

from dotenv import load_dotenv
from flask import Flask, Blueprint, make_response, render_template, redirect, request, g, current_app, jsonify
import mimetypes
from pymongo import MongoClient
import requests


if sys.platform.lower() == "win32":
    os.system("color")
mimetypes.add_type("image/webp", ".webp")
if os.getenv("heroku"):
    host = "https://dashboard.sevenbot.jp"
else:
    load_dotenv("../.env")
    print("[dashboard]Not heroku, loaded .env")
    host = "http://local.host:5000"
mainclient = MongoClient(os.environ.get("connectstr"))
redis_client = redis.from_url(os.environ.get("REDIS_URL"))
settings_collection = mainclient.sevenbot.guild_settings
DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET = os.environ.get("discord_client_id"), os.environ.get("discord_client_secret")
SIDEBAR_STRUCTURE = [{"name": "自動返信", "url": "autoreply", "icon": "autoreply"}]


def check_setting_update(guild_id: int):
    if f"{guild_id};{request.method}" in current_app.config["dash_ratelimit"]:
        if (remain := (current_app.config["dash_ratelimit"][f"{guild_id};{request.method}"]) - time.time()) > 0:
            return (
                jsonify(
                    {
                        "message": f"操作頻度が高すぎます。\n{round(remain)}秒後に再度お試しください。",
                        "code": "ratelimit",
                        "success": False,
                        "retry_after": round(remain, 2),
                    }
                ),
                429,
            )
    if request.method == "GET":
        current_app.config["dash_ratelimit"][f"{guild_id};{request.method}"] = time.time() + 1
    else:
        current_app.config["dash_ratelimit"][f"{guild_id};{request.method}"] = time.time() + 5
    user_info = get_user_cache(request.headers["authorization"])
    if user_info is None:
        return jsonify({"message": "認証に失敗しました。", "code": "auth", "success": False}), 401
    guild = [g for g in user_info["guild"] if g["id"] == str(guild_id)][0]
    mutual_guilds = get_mutual_guilds(user_info["guild"])
    if str(guild_id) not in mutual_guilds:
        return (
            jsonify(
                {
                    "message": "このサーバーの設定は出来ません。",
                    "code": "not_in_guild",
                    "success": False,
                }
            ),
            403,
        )
    elif not can_manage(guild):
        return (
            jsonify(
                {
                    "message": "このサーバーの設定は出来ません。",
                    "code": "no_permission",
                    "success": False,
                }
            ),
            403,
        )

    return None


ruri = host + "/callback"
login_url = (
    "https://discord.com/api/oauth2/authorize?"
    f"client_id={DISCORD_CLIENT_ID}&redirect_uri={urllib.parse.quote(ruri)}&"
    "response_type=code&scope=guilds%20identify&state={}"
)
API_ENDPOINT = "https://discord.com/api/v9"
SCOPE = "guilds+identify"


def request_after(*args, **kwargs):
    print(f"[request_after] Sending {args[0]} to {args[1]}")
    res = requests.request(*args, **kwargs)
    while res.status_code == 429:
        print(f"[request_after] {res.status_code} {res.headers['Retry-After']}")
        time.sleep(int(res.headers["retry-after"]))
        res = requests.request(*args, **kwargs)
    return res


def exchange_code(code):
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": ruri,
        "scope": SCOPE,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = request_after("POST", "%s/oauth2/token" % API_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()


def request_refresh_token(refresh_token):
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": ruri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = request_after("POST", "%s/oauth2/token" % API_ENDPOINT, data=data, headers=headers)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        return None
    else:
        return r.json()


def get_user_cache(token):
    if token is None:
        return None
    val = redis_client.get("user_" + token)

    if val is None:
        return None
    return json.loads(val)


def set_user_cache(token_data):
    if token_data is None:
        g.cookies["token"] = dict(value="", expires=0)
        g.cookies["refresh_token"] = dict(value="", expires=0)
        return None
    access_token = token_data["access_token"]
    token_hash = sha256(access_token.encode("utf-8")).hexdigest()
    g.cookies["token"] = dict(value=token_hash, path="/", expires=time.time() + token_data["expires_in"])
    g.cookies["refresh_token"] = dict(
        value=token_data["refresh_token"],
        path="/",
        expires=datetime.datetime.now() + datetime.timedelta(days=30),
    )

    ud = request_after("get", "%s/users/@me" % API_ENDPOINT, headers={"Authorization": "Bearer " + access_token})
    guilds = request_after(
        "get", "%s/users/@me/guilds" % API_ENDPOINT, headers={"Authorization": "Bearer " + access_token}
    ).json()
    for gu in guilds:
        if gu["icon"] is None:
            gu["icon_url"] = f"https://cdn.discordapp.com/embed/avatars/{int(gu['id']) % 6}.png"
        else:
            if "animated_icon" in gu["features"] and gu["icon"].startswith("a_"):
                ext = ".gif"
            else:
                ext = ".webp"
            gu["icon_url"] = f"https://cdn.discordapp.com/icons/{gu['id']}/{gu['icon']}{ext}"

    data = {"user": ud.json(), "guild": guilds, "time": time.time(), "token": access_token}
    redis_client.set("user_" + token_hash, json.dumps(data))
    return data


def get_bot_guilds():
    if (
        current_app.config.get("bot_guild_cache") is not None
        and time.time() - current_app.config["bot_guild_cache_time"] < 300
    ):
        return current_app.config["bot_guild_cache"]
    li = 0
    ret = []
    while True:
        g = request_after(
            "get",
            "%s/users/@me/guilds" % API_ENDPOINT,
            params={"after": li},
            headers={"Authorization": "Bot " + os.getenv("token")},
        ).json()
        if not g:
            break
        ret.extend(g)
        li = int(g[-1]["id"])
    current_app.config["bot_guild_cache"] = ret
    current_app.config["bot_guild_cache_time"] = time.time()
    return ret


def get_mutual_guilds(guilds):
    guilds = list(
        settings_collection.find(
            {
                "gid": {"$in": [int(guild["id"]) for guild in guilds if can_invite(guild["permissions"])]},
            }
        )
    )

    return [str(g["gid"]) for g in guilds]


def can_invite(permissions):
    return bool(int(permissions) & 1 << 5)


def can_manage(guild_data):
    return bool(int(guild_data["permissions"]) & 1 << 5)


app = Blueprint("dashboard", __name__, template_folder="./templates", static_folder="./static")


@app.before_request
def load_logged_in_user():
    if current_app.config.get("dash_user_caches") is None:
        current_app.config["dash_user_caches"] = {}
    if current_app.config.get("dash_ratelimit") is None:
        current_app.config["dash_ratelimit"] = {}
    g.cookies = {}
    g.user = None
    if request.path.startswith("/static") or request.path.startswith("/api"):
        return
    if not (token := request.cookies.get("token")):
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token is not None:
            g.user = set_user_cache(request_refresh_token(refresh_token))
            if g.user is None:
                return redirect("/?popup=ログインの更新に失敗しました。")
            return
        if request.path.startswith("/manage"):
            return redirect("/?popup=ログインしていません。")
        return
    if not get_user_cache(token):
        if request.cookies.get("refresh_token") is None:
            g.cookies["token"] = dict(value="", path="/", expires=0)
            return redirect("/?popup=Cookieが異常です。")
        if not set_user_cache(request_refresh_token(request.cookies.get("refresh_token"))):
            return redirect("/?popup=ログインの更新に失敗しました。")
    if token is not None:
        token_data = get_user_cache(token)
        if token_data is None:
            return redirect("/?popup=ログインを確認出来ませんでした。")
        g.user = token_data.get("user")
        return


@app.after_request
def set_g_cookie(response):
    for ck, cv in g.cookies.items():
        response.set_cookie(ck, **cv)
    if request.path.startswith("/static"):
        return response
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/")
def index():
    if g.user is not None:
        return render_template("dashboard/index.html", logged_in=True)
    else:
        return render_template("dashboard/index.html", logged_in=False)


@app.route("/manage/<int:guild_id>")
def manage(guild_id):
    if not (user_info := get_user_cache(request.cookies.get("token"))):
        return redirect("/?popup=ログインしていません。")
    guild_data = [gi for gi in user_info["guild"] if gi["id"] == str(guild_id)][0]
    data = {"guild": guild_data}
    return render_template(
        "dashboard/manage/root.html",
        data=json.dumps(data),
        raw_data=data,
        sidebar_items=SIDEBAR_STRUCTURE,
        guild_id=guild_id,
        current="root",
    )


@app.route("/manage/<int:guild_id>/<string:feature>")
def manage_feat(guild_id, feature):
    if not (user_info := get_user_cache(request.cookies.get("token"))):
        return redirect("/?popup=ログインしていません。")
    guild_data = [gi for gi in user_info["guild"] if gi["id"] == str(guild_id)][0]
    data = {"guild": guild_data}
    return render_template(
        f"dashboard/manage/{feature}.html",
        data=json.dumps(data),
        raw_data=data,
        sidebar_items=SIDEBAR_STRUCTURE,
        guild_id=guild_id,
        current=feature,
    )


@app.route("/invite")
def invite():
    return redirect(
        "https://discord.com/oauth2/authorize?client_id=718760319207473152&scope=bot&"
        f"response_type=code&guild_id={request.args['guild_id']}&"
        f"disable_guild_select=true&permissions=808840532&redirect_uri={urllib.parse.quote(host)}"
    )


@app.route("/login")
def login():
    state = {"from": request.args.get("from")}
    return redirect(login_url.format(urllib.parse.quote(json.dumps(state))))


@app.route("/logout")
def logout():
    g.cookies["token"] = dict(value="", path="/", expires=0)
    g.cookies["refresh_token"] = dict(value="", path="/", expires=0)
    return redirect("/?popup=ログアウトしました。")


@app.route("/callback")
def callback():
    if "state" not in request.args.keys():
        return redirect("/")
    code = request.args["code"]
    code_json = exchange_code(code)
    state = json.loads(request.args["state"])
    response = make_response(redirect(state["from"]))
    set_user_cache(code_json)
    return response


@app.get("/api/servers")
def api_servers():
    user_info = get_user_cache(request.headers["authorization"])
    if not user_info:
        return json.dumps({"message": "ログインしていません。", "code": "not_logged_in", "success": False}), 401
    # mutual_guilds = {gu["id"] for gu in bot_guilds} & {
    #     gu["id"] for gu in user_info["guild"] if can_invite(gu["permissions"])
    # }
    mutual_guilds = get_mutual_guilds(user_info["guild"])
    return {
        "manage": [gu for gu in user_info["guild"] if gu["id"] in mutual_guilds and can_invite(gu["permissions"])],
        "invite": [gu for gu in user_info["guild"] if can_invite(gu["permissions"]) and gu["id"] not in mutual_guilds],
    }


@app.get("/api/guilds/<int:guild_id>/settings")
def api_settings(guild_id):
    if fail_response := check_setting_update(guild_id):
        return fail_response
    return settings_collection.find_one({"gid": guild_id}, {"_id": False})


@app.post("/api/guilds/<int:guild_id>/settings/autoreply")
def api_settings_get(guild_id):
    if fail_response := check_setting_update(guild_id):
        return fail_response
    if len(request.json["data"]) > 500:
        return {
            "message": "自動返信の数は500個以下である必要があります。",
            "success": False,
            "code": "too_many_replies",
        }, 400
    failures = []
    for aid, (rtarget, rreply) in request.json["data"]:
        target, reply = rtarget.strip(), rreply.strip()
        if set(aid) - set("0123456789abcdef"):
            failures.append((aid, "id", "IDの文字列に設定出来ない文字が含まれています。"))
        if len(aid) != 8:
            failures.append((aid, "id", "IDの文字列は8文字である必要があります。"))
        if not isinstance(target, str):
            failures.append((aid, "target", "条件には文字列で指定してください。"))
        if len(target) > 1023 or len(target) < 1:
            failures.append((aid, "target", "条件は1文字以上1023文字以下で指定してください。"))
        if not isinstance(reply, str):
            failures.append((aid, "reply", "応答には文字列で指定してください。"))
        if len(reply) > 1023 or len(reply) < 1:
            failures.append((aid, "reply", "応答は1文字以上1023文字以下で指定してください。"))
    if failures:
        failures.sort(key=lambda x: x[0])
        return {
            "message": "データが無効です。",
            "code": "invalid_data",
            "failures": dict([k, list(v)] for k, v in itertools.groupby(failures, key=lambda x: x[0])),
            "success": False,
        }, 422
    data = dict(request.json["data"])
    settings_collection.update_one({"gid": guild_id}, {"$set": {"autoreply": data}})
    return {
        "message": "設定を更新しました。",
        "code": "success",
        "success": True,
    }


@app.errorhandler(404)
def page_not_found(error):
    return make_response(render_template("dashboard/404.html"), 404)


@app.get("/api/hidden/sessions")
def api_hidden_sessions():
    if request.args["pass"] != os.getenv("password"):
        return json.dumps({"success": False}), 401
    return jsonify(
        {
            "config": current_app.config["dash_user_caches"],
            "objid": id(current_app.config["dash_user_caches"]),
        }
    )


if __name__ == "__main__":
    testapp = Flask(__name__)
    testapp.register_blueprint(app)
    testapp.secret_key = "ABCdefGHI"
    testapp.run(debug=True, host="0.0.0.0")
