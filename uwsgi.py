from flask import abort
from flask import url_for
from flask import redirect
from flask import request
from flask import session
from flask import current_app
from flask import render_template
from flask import send_from_directory
from flask import make_response
from werkzeug.exceptions import HTTPException

import time
import json
import random
import re
import os

from app import app
from app import db
from app import utility
from app.routes import market, user
# from app import login_manager
# from app import admin_permission, user_permission, admin_user_permission
from app.models.models import *


# from flask_login import current_user, login_user, logout_user, login_required
# from flask_principal import identity_loaded, RoleNeed, UserNeed, IdentityContext, Permission


# @app.errorhandler(403)
# def site_forbidden(e):
#     return "403"
#
#
# @app.errorhandler(404)
# def page_not_found(e):
#     return "404"
#
#
# @app.errorhandler(500)
# def internal_server_error(e):
#     return "500"


@app.errorhandler(Exception)
def handle_exception(e):
    data = {
        "code": -1,
        "msg": str(type(e)),
        "desc": str(e),
    }

    response = make_response(json.dumps(data), 200)
    response.content_type = "application/json"
    return response


@app.route('/')
def index():
    return 'Hello World!'


@app.before_first_request
def activate_job():
    from app import db
    import app.models.models
    # db.drop_all()
    db.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
