import os
import random
import string

from flask import Flask, request, jsonify, make_response, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import mimetypes

from api.main import app as api_app
from captcha.main import app as captcha_app
from general.main import app as general_app
from dashboard.main import app as dashboard_app

mimetypes.add_type("image/webp", ".webp")


def make_random_str(length):
    return "".join(random.choices(string.ascii_letters, k=length))


app = Flask(__name__, static_folder="./general/static")
limiter = Limiter(app, key_func=get_remote_address, default_limits=["1/10second", "120/hour"])


@limiter.request_filter
def limiter_whitelist():
    return not request.host.startswith("api.")


app.config["SERVER_NAME"] = "sevenbot.jp" if os.getenv("heroku") else "local.host:5000"
app.secret_key = make_random_str(10)
app.register_blueprint(general_app)
app.register_blueprint(general_app, subdomain="www", name="www_general")
app.register_blueprint(api_app, subdomain="api")
app.register_blueprint(captcha_app, subdomain="captcha")
app.register_blueprint(dashboard_app, subdomain="dashboard")


@app.errorhandler(404)
def notfound(ex):
    if request.host.startswith("api."):
        return make_response(
            jsonify({"message": "Unknown endpoint. Make sure your url is correct.", "code": "not_found"}), 404
        )
    elif request.host.startswith("captcha."):
        return make_response(render_template("captcha/404.html"), 404)
    else:
        return make_response(render_template("general/404.html"), 404)


@app.errorhandler(405)
def methodnotallowed(_):
    return make_response(
        jsonify(
            {"message": "Invalid request type. Make sure your request type is correct.", "code": "wrong_request_type"}
        ),
        405,
    )


@app.errorhandler(429)
def ratelimit_handler(e):
    return make_response(jsonify({"error_description": "You are being rate limited.", "ratelimit": e.description}), 429)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=(5000 or os.getenv("PORT")), debug=not bool(os.getenv("heroku")))
