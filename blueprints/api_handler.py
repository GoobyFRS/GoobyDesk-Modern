#!/usr/bin/env python3
# API Ingest blueprint for handling external webhook integrations
import json
import logging
from datetime import datetime
from typing import Callable

from flask import Blueprint
from flask import Response
from flask import jsonify
from flask import request