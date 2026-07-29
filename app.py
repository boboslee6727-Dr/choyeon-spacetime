import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import os
import re
from google import genai
import time
import engine
import prompts
import json
import math
import pytz
import html_views

# 🚨 [여기서부터 3줄을 꼭 추가해 주십시오!]
import importlib
importlib.reload(html_views)  # html_views.py를 강제로 새로 읽어오라는 명령!
importlib.reload(engine)      # engine.py를 강제로 새로 읽어오라는 명령!
