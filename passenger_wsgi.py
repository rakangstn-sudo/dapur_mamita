"""
WSGI Entry Point untuk cPanel / CloudLinux (Passenger) & Hosting Server.
Domain: *.my.id
"""

import sys
import os

# Tambahkan path proyek ke sys.path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from app import create_app

application = create_app()
