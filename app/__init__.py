# -*- coding: utf-8 -*-

import os
from flask import Flask

engine = Flask(__name__)

engine.config["JSON_AS_ASCII"] = False
engine.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
engine.config["DEBUG"] = False

engine.config["PORT"] = 9600

ABSPATH = os.path.dirname(__file__)
DATA_FOLDER = os.path.join(ABSPATH,"data")

from .views import *
