import datetime
import mimetypes
import os
import random
import string

from dotenv import load_dotenv
from quart import Quart, jsonify, make_response, render_template, request
from quart_rate_limiter import RateLimiter, limit_blueprint

from api.main import app as api_app
from captcha.main import app as captcha_app
from dashboard.main import app as dashboard_app
from general.main import app as general_app

mimetypes.add_type("image/webp", ".webp")
load_dotenv()


def make_random_str(length):
    return "".join(random.choices(string.ascii_letters, k=length))


app = Quart(__name__, static_folder="./general/static")
limiter = RateLimiter(app)


app.config["SERVER_NAME"] = "sevenbot.jp" if os.getenv("heroku") else "localhost:5000"
app.secret_key = make_random_str(10)
app.register_blueprint(general_app)
app.register_blueprint(general_app, subdomain="www", name="www_general")
app.register_blueprint(api_app, subdomain="api")
app.register_blueprint(captcha_app, subdomain="captcha")
app.register_blueprint(dashboard_app, subdomain="dashboard")
limit_blueprint(api_app, 1, datetime.timedelta(seconds=5))


@app.errorhandler(404)
async def notfound(ex):
    if request.host.startswith("api."):
        return await make_response(
            jsonify({"message": "Unknown endpoint. Make sure your url is correct.", "code": "not_found"}), 404
        )
    elif request.host.startswith("captcha."):
        return await make_response(await render_template("captcha/404.html"), 404)
    elif request.host.startswith("dashboard."):
        return await make_response(await render_template("dashboard/404.html"), 404)
    else:
        return await make_response(await render_template("general/404.html"), 404)


@app.errorhandler(405)
async def methodnotallowed(_):
    return await make_response(
        jsonify(
            {"message": "Invalid request type. Make sure your request type is correct.", "code": "wrong_request_type"}
        ),
        405,
    )


@app.errorhandler(429)
async def ratelimit_handler(e):
    return await make_response(
        jsonify({"error_description": "You are being rate limited.", "ratelimit": e.description}), 429
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=(5000 or os.getenv("PORT")), debug=not bool(os.getenv("heroku")))
