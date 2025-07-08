from flask import Blueprint

groups_bp = Blueprint("groups", __name__)

from . import groups_post
from . import groups_get