from flask import Blueprint

expenses_bp = Blueprint("expenses", __name__)

from . import expenses_post
from . import expenses_get
from . import expenses_put
from . import expenses_delete