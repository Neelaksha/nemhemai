# Standard library imports
import subprocess
import os
import sys
import time
import io
import base64
import json
import urllib.parse
import hashlib
import binascii
import hmac
import datetime
import shutil
import traceback
import logging
import warnings
from contextlib import redirect_stdout

# Data science and analysis imports
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from scipy import stats

# Database and ORM imports
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime, inspect
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Web framework and API imports
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends, status, Security, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse as StarletteFileResponse
from starlette.requests import Request

# Authentication and security imports
from jose import JWTError, jwt
try:
    from passlib.hash import pbkdf2_sha256, bcrypt
except Exception:
    pbkdf2_sha256 = None
    bcrypt = None
try:
    import passlib.handlers.pbkdf2
    import passlib.handlers.bcrypt
    import passlib.handlers.digests
except Exception:
    pass

# File processing imports
from typing import List, Dict, Any
from PIL import Image
import pytesseract
import PyPDF2
import docx
import chardet

# HTTP and networking imports
import requests
import random
import socket

# Environment and configuration
from dotenv import load_dotenv
load_dotenv()

# Suppress warnings including bcrypt version warnings
warnings.filterwarnings('ignore')
logging.getLogger('passlib').setLevel(logging.ERROR)