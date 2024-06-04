from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
item_bp = Blueprint("item",__name__)

from . import routes

