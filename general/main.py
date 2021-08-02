from glob import glob
import json
import os
import re
import sys
import time

from dotenv import load_dotenv
from flask import Flask, Blueprint, make_response, redirect, render_template, current_app, request
from jinja2.exceptions import TemplateNotFound
import mimetypes
from pymongo import MongoClient
import werkzeug
import yaml

if sys.platform.lower() == "win32":
    os.system("color")
mimetypes.add_type("image/webp", ".webp")
if not os.getenv("heroku"):
    load_dotenv("../.env")
    print("[general]Not heroku, loaded .env", os.environ.get("connectstr"))
mainclient = MongoClient(os.environ.get("connectstr"))
commandscollection = mainclient.sevenbot.commands
statuscollection = mainclient.sevenbot.status_log

app = Blueprint("general", __name__, template_folder="./templates", static_folder="./static")


REDIRECT_PATTERN = re.compile(r'redirect_to: "(.+)"')
CATEGORIES = {
    "bot": "Botの情報関連",
    "server": "サーバーの情報関連",
    "info": "その他情報",
    "panel": "パネル関連",
    "tools": "ツール",
    "fun": "ネタコマンド",
    "serverpanel": "パネル - サーバー関連",
    "moderation": "モデレーション関連",
    "global": "グローバルチャット関連",
    "settings": "設定",
}
COMMAND_DESC_PATTERNS = [
    [re.compile(r"\n"), r"<br>"],
    [re.compile(r"\*\*(.+?)\*\*"), r'<span class="bold">\1</span>'],
    [re.compile(r"```(?:\n|<br>)*(.+?)```"), r'<div class="codeblock">\1</div>'],
    [re.compile(r"`(.+?)`"), r'<span class="inline-code inline-code2">\1</span>'],
    [re.compile(r"__(.+?)__"), r'<span class="underline">\1</span>'],
    [re.compile(r"\[(.+?)\]\((.+?)\)"), r'<a href="\2">\1</a>'],
]
SYNTAX_DESC_PATTERNS = [
    [re.compile(r"\n"), r"<br>"],
    [re.compile(r"\*\*(.+?)\*\*"), r'<span class="bold">\1</span>'],
    [re.compile(r"```(?:\n|<br>)*(.+?)```"), r'<div class="codeblock">\1</div>'],
    [re.compile(r"`(.+?)`"), r'<span class="inline-code">\1</span>'],
    [re.compile(r"__(.+?)__"), r'<span class="underline">\1</span>'],
    [re.compile(r"\[(.+?)\]\((.+?)\)"), r'<a href="\2">\1</a>'],
]

SYNTAX_PATTERNS = [
    [re.compile(r"&lt;([^&]+)(&gt;|$)"), r'<span class="syntax-arg-required">&lt;\1\2</span>'],
    [re.compile(r"\[([^\]]+)(\]|$)"), r'<span class="syntax-arg-optional">[\1\2</span>'],
    [re.compile(r"(sb(?:#|\. ?)|^)([^ [<\s]+)"), r'\1<span class="syntax-command-name">\2</span>'],
    [re.compile(r"^(sb(?:#|\. ?))"), r'<span class="syntax-prefix">\1</span>'],
]

SYNTAX_PATTERN_INPUT = [
    [re.compile(r"&lt;([^&]+)&gt;"), r'<span class="syntax-arg-required">\1</span>'],
    [re.compile(r"\[([^\]]+)]"), r'<span class="syntax-arg-optional">\1</span>'],
    [re.compile(r"(sb(?:#|\. ?)|^)([^ [<\s]+)"), r'\1<span class="syntax-command-name">\2</span>'],
    [re.compile(r"^(sb(?:#|\. ?))"), r'<span class="syntax-prefix">\1</span>'],
]
MD_MASTER_PATTERN = re.compile(r"---\n([\s\S]+)\n---([\s\S]+)$")
DARK_SWITCH_TAG = r"""<picture>
    <source srcset="/static/tutorial-imgs/!image-dark.webp" type="image/webp" media="(prefers-color-scheme: dark)">
    <source srcset="/static/tutorial-imgs/!image-dark.png" type="image/png" media="(prefers-color-scheme: dark)">
    <source srcset="/static/tutorial-imgs/!image.webp" type="image/webp">
    <img src="/static/tutorial-imgs/!image.png" class="tutorial-image">
</picture>"""
WEBP_SWITCH_TAG = r"""<picture>
    <source srcset="/static/tutorial-imgs/!image.webp" type="image/webp">
    <img src="/static/tutorial-imgs/!image.png" class="tutorial-image">
</picture>"""


def convert_sbmd(match):
    cmd, content = match.groups()
    content = content.replace("<", "&lt;").replace(">", "&gt;")
    if cmd == "syntax":
        for pattern, sub in SYNTAX_PATTERNS:
            content = pattern.sub(sub, content)
        content = '<span class="inline-code">{}</span>'.format(content)
    elif cmd == "syntax-input":
        for pattern, sub in SYNTAX_PATTERN_INPUT:
            content = pattern.sub(sub, content)
        content = '<span class="inline-code">{}</span>'.format(content)
    elif cmd == "asset-image":
        content = WEBP_SWITCH_TAG.replace("!image", content)
    elif cmd == "dark-asset-image":
        content = DARK_SWITCH_TAG.replace("!image", content)
    elif cmd == "command-ref":
        command = convert_commands(
            next((c for c in current_app.config["commands_cache"] if c["name"] == content), None)
        )
        content = '<a href="/commands#{}"><span class="inline-code command-syntax">{}</span></a>'.format(
            command["name"].replace(" ", "-"), command["syntax"]
        )
    else:
        content = match[0]
    return content


raw_md_patterns = [
    [r"^(#+) (.+)$", lambda m: f"<h{len(m[1])}>{m[2]}</h{len(m[1])}>"],
    [r"\*\*(.+?)\*\*", r'<span class="bold">\1</a>'],
    [r"```(?:\n|<br>)*(.+?)```", r'<div class="codeblock">\1</div>'],
    [r"`(.+?)`", r'<span class="inline-code">\1</span>'],
    [r"__(.+?)__", r'<span class="underline">\1</span>'],
    [r"!\[(.+?)\]\((.+?)\)", r'<img src="\2" alt="\1">'],
    [r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>'],
    [r"\{([^|]+)\|([^}]+)\}", convert_sbmd],
    [r"  $", "<br>"],
    [r"\n\n", "\n<br>\n"],
]
tmp_patterns = []
for pattern, sub in raw_md_patterns:
    tmp_patterns.append((re.compile(pattern, flags=re.MULTILINE), sub))

MD_PATTERNS = tmp_patterns
MENTION_PATTERN = re.compile(r"\{([^\}]+)}")
TYPE_PATTERN = re.compile(r".+（([^、]+)(?:、.+)?）")


def parse_md(d):
    if isinstance(d, str):
        return d
    for dk, dv in d.items():
        if isinstance(dv, dict):
            d[dk] = parse_md(dv)
        if isinstance(dv, list):
            for i, l in enumerate(dv):
                d[dk][i] = parse_md(l)
        elif isinstance(dv, str):
            desc = dv.replace("<", "&lt;").replace(">", "&gt;")
            desc = MENTION_PATTERN.sub(r'<span class="mention">\1</span>', desc)
            for p in SYNTAX_DESC_PATTERNS:
                desc = p[0].sub(p[1], desc)
            if desc.startswith("##"):
                desc = desc.replace("#", "")
                for p in SYNTAX_PATTERN_INPUT:
                    desc = p[0].sub(p[1], desc)
            elif desc.startswith("#"):
                desc = desc.replace("#", "")
                for p in SYNTAX_PATTERNS:
                    desc = p[0].sub(p[1], desc)
            d[dk] = desc
    return d


def convert_commands(cmd):
    if cmd["syntax"] is None:
        synt = None
    else:
        synt = f'<span class="syntax-command-name">{cmd["name"]}</span> '
        for s in cmd["syntax"]:
            synt += '<span class="syntax-arg-optional">[' if s["optional"] else '<span class="syntax-arg-required">&lt;'
            synt += s["name"]
            m = TYPE_PATTERN.match(s["detail"])
            if m is not None:
                synt += f'<span class="syntax-arg-type">:{m.group(1)}</span>'
            if s["variable"]:
                synt += "..."
            if not s["kwarg"]:
                synt += "]</span>" if s["optional"] else "&gt;</span>"
                synt += " "
        synt = synt.rstrip()
    desc = cmd["desc"]
    for p in COMMAND_DESC_PATTERNS:
        desc = p[0].sub(p[1], desc)
    if desc.count("<br>") >= 1:
        desc = (
            desc.split("<br>", 1)[0]
            + '<br><span class="datail">'
            + desc.split("<br>", 1)[1]
            + '</span><span class="more">+</span>'
        )
    return {
        "name": cmd["name"],
        "desc": desc,
        "parent": cmd["parents"],
        "syntax": synt,
        "aliases": cmd["aliases"],
        "is_parent": bool([co for co in current_app.config["commands_cache"] if co["parents"] == cmd["name"]]),
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
        cmds = list(map(convert_commands, sorted(filter(lambda c: c["category"] == ck, com), key=lambda c: c["index"])))
        sorted_cmds = []

        def get_cmd(p):
            for c in [co for co in cmds if co["parent"] == p]:
                sorted_cmds.append(c)
                if [co for co in cmds if co["parent"] == c["name"]]:
                    get_cmd(c["name"])

        get_cmd("")
        categories.append(
            {
                "id": ck,
                "name": cv,
                "commands": sorted_cmds,
            }
        )
    return render_template("general/commands.html", categories=categories)


@app.route("/api")
def api():
    with open("general/data/api.json", "r") as f:
        api_info = json.load(f)
    return render_template("general/api.html", endpoints=api_info["categories"], auths=api_info["authorization"])


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
@app.route("/<path:pagename>")
def index(pagename):
    try:
        resp = render_template(werkzeug.utils.safe_join("general/", pagename + ".html"))
        return resp
    except (TemplateNotFound, werkzeug.exceptions.NotFound):
        path = werkzeug.utils.safe_join("general/templates/general", pagename + ".json")
        if os.path.exists(path):
            with open(path, "r") as f:
                raw_resp = json.load(f)
            if raw_resp["type"] == "redirect":
                if "compatible;" in request.headers.get("user-agent", "") or "Twitterbot" in request.headers.get(
                    "user-agent", ""
                ):
                    return render_template(
                        "general/embed.html",
                        title=raw_resp["embed"]["title"],
                        description=raw_resp["embed"]["description"],
                    )
                else:
                    return redirect(raw_resp["url"])
        else:
            return render_template("general/404.html"), 404


@app.route("/tutorial")
def tutorials_index():
    mds = glob("general/tutorials/*.md")
    datas = []
    for md in mds:
        with open(md) as f:
            raw_md = f.read()
        head_md, _ = MD_MASTER_PATTERN.match(raw_md).groups()
        datas.append((os.path.basename(md).removesuffix(".md"), yaml.safe_load(head_md)))
    return render_template("general/tutorial-index.html", data=sorted(datas, key=lambda d: d[1]["index"]))


@app.route("/tutorial/<path:path>")
def tutorials(path):
    com = []
    if (time.time() - current_app.config.get("commands_cache_time", 0)) < 300:
        com = current_app.config.get("commands_cache")
        print("[tutorial]Cache is available, loaded from cache.")
    else:
        print("[tutorial]Cache is expired or missing, reloading.")
        for c in commandscollection.find({}, {"_id": False}):
            com.append(c)
        current_app.config["commands_cache"] = com
        current_app.config["commands_cache_time"] = time.time()
    try:
        with open(werkzeug.utils.safe_join("general/tutorials/", path + ".md")) as f:
            raw_md = f.read()
    except (werkzeug.exceptions.NotFound, FileNotFoundError):
        return render_template("general/404.html"), 404
    else:
        head_md, body_md = MD_MASTER_PATTERN.match(raw_md).groups()
        for pattern, sub in MD_PATTERNS:
            body_md = pattern.sub(sub, body_md)
        md_data = yaml.safe_load(head_md)
        if md_data.get("json"):
            extra_datas = {}
            for j in md_data["json"]:
                with open(f"general/data/{j}.json", "r") as f:
                    extra_datas[j] = parse_md(json.load(f))
            md_data["data"] = extra_datas
        for ih in re.finditer(r"\{import-html\|([^(\]]+?)\}", body_md):
            body_md = body_md.replace(ih[0], render_template(f"tutorial-html/{ih[1]}.html", **md_data))
        return render_template("general/tutorial.html", body=body_md, **md_data)


@app.errorhandler(404)
def page_not_found(error):
    return make_response(render_template("general/404.html"), 404)


if __name__ == "__main__":
    testapp = Flask(__name__)
    testapp.register_blueprint(app)
    testapp.secret_key = "ABCdefGHI"
    testapp.run("0.0.0.0", debug=True)
