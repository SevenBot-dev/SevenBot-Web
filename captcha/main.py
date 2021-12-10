import asyncio
import datetime
import json
import os
import secrets
import time
import urllib.parse

import aioredis
import httpx
from dotenv import load_dotenv
from quart import (Blueprint, g, jsonify, make_response, redirect,
                   render_template, request)

if __name__ == "__main__":
    load_dotenv("../.env")
    host = "http://localhost:5000"
else:
    host = "https://captcha.sevenbot.jp"
ruri = host + "/callback"
redis_client = aioredis.from_url(os.environ.get("REDIS_URL"))
DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET = os.environ.get("discord_client_id"), os.environ.get("discord_client_secret")
app = Blueprint("captcha", __name__, template_folder="./templates", static_folder="./static")

login_url = (
    "https://discord.com/api/oauth2/authorize?"
    f"client_id={DISCORD_CLIENT_ID}&redirect_uri={urllib.parse.quote(ruri)}&"
    "response_type=code&scope=guilds%20identify&state={}"
)
API_ENDPOINT = "https://discord.com/api/v9"
SCOPE = "guilds%20identify"


async def exchange_code(code):
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": ruri,
        "scope": SCOPE,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = await g.httpx_session.post("%s/oauth2/token" % API_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()


async def refresh_token(refresh_token):
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": "https://captcha.sevenbot.jp/callback",
        "scope": SCOPE,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = await g.httpx_session.post("%s/oauth2/token" % API_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()


async def request_after(*args, **kwargs) -> httpx.Response:
    print(f"[request_after] Sending {args[0]} to {args[1]}")
    res = await g.httpx_session.request(*args, **kwargs)
    while res.status_code == 429:
        print(f"[request_after] {res.status_code} {res.headers['Retry-After']}")
        await asyncio.sleep(int(res.headers["retry-after"]))
        res = await g.httpx_session.request(*args, **kwargs)
    return res


@app.before_request
async def before_request():
    g.httpx_session = httpx.AsyncClient()


@app.after_request
async def after_request(response):
    await g.httpx_session.aclose()
    return response


@app.route("/")
async def index():
    return await render_template("captcha/index.html")


@app.route("/verify")
async def captcha():
    sessionid = "captcha_" + request.args.get("id")
    if not sessionid:
        return await render_template("captcha/session.html", timeout=False)

    async def show_login():
        r = await make_response(
            await render_template(
                "captcha/login.html",
                url=login_url.format(sessionid.removeprefix("captcha_")),
            ),
            200,
        )
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return r

    if not await redis_client.exists(sessionid):
        r = await make_response(await render_template("captcha/session.html", timeout=False))
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return r
    elif time.time() - float(json.loads(await redis_client.get(sessionid))["time"]) > 300:
        await redis_client.delete(sessionid)
        r = await make_response(await render_template("captcha/session.html", timeout=True))
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return r
    elif request.cookies.get("token"):
        r = await request_after(
            "GET",
            "https://discord.com/api/v9/users/@me",
            headers={"authorization": "Bearer " + str(request.cookies.get("token"))},
        )
        if r.status_code == 401:
            return await show_login()
        if r.json()["id"] != str(json.loads(await redis_client.get(sessionid))["uid"]):
            r = await make_response(await render_template("captcha/wrong_user.html", url=login_url.format(sessionid)))
            r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return r
        r = await make_response(await render_template("captcha/login.html", url=None), 200)
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return r
    else:
        return await show_login()


@app.route("/callback")
async def callback():
    if "state" not in request.args.keys():
        return await render_template("captcha/session.html", timeout=False)
    code = request.args["code"]
    code_json = await exchange_code(code)
    response = await make_response(redirect(host + "/verify?id=" + request.args["state"]))
    response.set_cookie(
        "token", value=code_json["access_token"], path="/", expires=datetime.datetime.now() + datetime.timedelta(days=7)
    )
    response.set_cookie(
        "refresh_token",
        value=code_json["refresh_token"],
        path="/",
        expires=datetime.datetime.now() + datetime.timedelta(days=30),
    )
    return response


@app.route("/check", methods=["post"])
async def check_ok():
    data = {
        "response": (await request.json)["token"],
        "secret": os.environ.get("hcaptcha_secret"),
        "sitekey": os.environ.get("sitekey"),
    }
    r = await g.httpx_session.post("https://hcaptcha.com/siteverify", data=data)
    if r.json()["success"]:
        rc = json.loads(await redis_client.get("captcha:" + (await request.json)["id"]))
        uid, gid, rid = rc["uid"], rc["gid"], rc["rid"]
        await request_after(
            "PUT",
            f"https://discord.com/api/v9/guilds/{gid}/members/{uid}/roles/{rid}",
            headers={"authorization": "Bot " + os.environ.get("token")},
        )
        dm = await request_after(
            "POST",
            "https://discord.com/api/v9/users/@me/channels",
            headers={"authorization": "Bot " + os.environ.get("token")},
            json={"recipient_id": uid},
        )

        gu = await request_after(
            "GET",
            f"https://discord.com/api/v9/guilds/{gid}",
            headers={"authorization": "Bot " + os.environ.get("token")},
        )
        gname = gu.json()["name"]
        await request_after(
            "POST",
            "https://discord.com/api/v9/channels/" + dm.json()["id"] + "/messages",
            headers={"authorization": "Bot " + os.environ.get("token")},
            json={"content": f"{gname} での認証が完了しました。"},
        )
        await redis_client.delete("captcha:" + (await request.json)["id"])
        # /guilds/{guild.id}/members/{user.id}/roles/{role.id}
    return await make_response(r.text, r.status_code)


@app.route("/session", methods=["post"])
async def make_session():
    res = await request.json
    if res.get("password") != os.environ.get("password"):
        return await make_response(jsonify({"message": "You cannot access this endpoint."}), 403)

    shash = secrets.token_urlsafe(32)
    await redis_client.set(
        "captcha:" + shash, json.dumps({"uid": res["uid"], "gid": res["gid"], "rid": res["rid"], "time": time.time()}),
        ex=300,
    )
    return await make_response(jsonify({"message": shash}), 201)


@app.route("/index")
async def index2():
    return redirect(host)


@app.route("/success")
async def success():
    return await render_template("captcha/success.html")


@app.errorhandler(404)
async def page_not_found(error):
    return await make_response(await render_template("captcha/404.html"), 404)


if __name__ == "__main__":
    from quart import Quart

    testapp = Quart(__name__)
    testapp.register_blueprint(app)
    testapp.secret_key = "ABCdefGHI"
    testapp.run(debug=True)
