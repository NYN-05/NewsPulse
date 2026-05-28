#!/usr/bin/env python3
"""
Legacy dashboard entry point. Redirects to the modular dashboard.
Run: streamlit run dashboard/app.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dashboard.app import *
