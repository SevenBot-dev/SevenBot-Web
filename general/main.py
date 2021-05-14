import json
import os
import random
import re
import string
import time

from dotenv import load_dotenv
from flask import (Flask, Blueprint, make_response, redirect,
                   render_template, current_app)
from jinja2.exceptions import TemplateNotFound
import mimetypes
from pymongo import MongoClient

mimetypes.add_type('image/webp', '.webp')
if not os.getenv("heroku"):
    load_dotenv("../.env")
    print("[general]Not heroku, loaded .env", os.environ.get("connectstr"))
mainclient = MongoClient(os.environ.get("connectstr"))
commandscollection = mainclient.sevenbot.commands
statuscollection = mainclient.sevenbot.status_log

app = Blueprint('general', __name__, template_folder='./templates', static_folder="./static")


def make_random_str(l):
    return ''.join(random.choices(string.ascii_letters, k=l))


REDIRECT_PATTERN = re.compile(r'redirect_to: "(.+)"')
CATEGORIES = {
    'bot': "Botの情報関連",
    'server': "サーバーの情報関連",
    'info': "その他情報",
    'panel': "パネル関連",
    'tools': "ツール",
    'fun': "ネタコマンド",
    'serverpanel': "パネル - サーバー関連",
    'moderation': "モデレーション関連",
    'global': "グローバルチャット関連",
    'settings': "設定"
}
COMMAND_DESC_PATTERNS = [
    [re.compile(r"\n"), r'<br>'],
    [re.compile(r"\*\*(.+?)\*\*"), r'<span class="bold">\1</span>'],
    [re.compile(r"```(?:\n|<br>)*(.+?)```"), r'<div class="codeblock">\1</div>'],
    [re.compile(r"`(.+?)`"), r'<span class="inline_code inline_code2">\1</span>'],
    [re.compile(r"__(.+?)__"), r'<span class="underline">\1</span>'],
    [re.compile(r"\[(.+?)\]\((.+?)\)"), r'<a href="\2">\1</a>']
]


def convert_commands(cmd):
    if cmd["syntax"] is None:
        synt = None
    else:
        synt = f'<span class="syntax_command_name">{cmd["name"]}</span> '
        for s in cmd["syntax"]:
            synt += ("<span class=\"syntax_arg_optional\">[{}]</span>" if s["optional"] else "<span class=\"syntax_arg_required\">&lt;{}&gt;</span>").format(s["name"]) + " "
        synt = synt.rstrip()
    desc = cmd["desc"]
    for p in COMMAND_DESC_PATTERNS:
        desc = p[0].sub(p[1], desc)
    if desc.count("<br>") >= 1:
        desc = desc.split("<br>", 1)[0] + '<br><span class="datail">' + desc.split("<br>", 1)[1] + '</span><span class="more">+</span>'
    return {
        "name": cmd["name"],
        "desc": desc,
        "parent": cmd["parents"],
        "syntax": synt,
        "aliases": cmd["aliases"]
    }


@app.route("/commands")
def commands():
    com = []
    if (time.time() - current_app.config.get("commands_cache_time", 0)) < 300:
        com = current_app.config.get("commands_cache")
        print("[commands]Cache is available, loaded from cache.")
    else:
        print("[commands]Cache is expired or missing, reloading.")
        for c in commandscollection.find({}, {"_id": False}):
            com.append(c)
        current_app.config["commands_cache"] = com
        current_app.config["commands_cache_time"] = time.time()
    categories = []
    for ck, cv in CATEGORIES.items():
        cmds = map(convert_commands, sorted(filter(lambda c: c["category"] == ck, com), key=lambda c: len(c["parents"]) + 100 * c["index"]))
        categories.append({

            "id": ck,
            "name": cv,
            "commands": cmds,

        })
    return render_template("general/commands.html", categories=categories)


@app.route("/status")
def status():
    com = []
    if (time.time() - current_app.config.get("status_cache_time", 0)) < 300:
        com = current_app.config.get("status_cache")
        print("[status]Cache is available, loaded from cache.")
    else:
        print("[status]Cache is expired or missing, reloading.")
        for c in statuscollection.find({}, {"_id": False}):
            com.append(c)
        current_app.config["status_cache"] = com
        current_app.config["status_cache_time"] = time.time()

    return render_template("general/status.html", data=json.dumps(com))


@app.route("/", defaults={"pagename": "index"})
@app.route("/<pagename>")
def index(pagename):
    try:
        resp = render_template(f"general/{pagename}.html")
        if REDIRECT_PATTERN.match(resp):
            uri = REDIRECT_PATTERN.match(resp)[1]
            resp = redirect(uri)
        return resp
    except TemplateNotFound:
        return render_template("general/404.html"), 404


@app.errorhandler(404)
def page_not_found(error):
    return make_response(render_template('general/404.html'), 404)


if __name__ == "__main__":
    testapp = Flask(__name__)
    testapp.register_blueprint(app)
    testapp.secret_key = "ABCdefGHI"
    testapp.run(debug=True)