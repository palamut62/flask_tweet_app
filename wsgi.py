#!/usr/bin/env python3
"""
WSGI config for AI Tweet Bot on PythonAnywhere

Bu dosya PythonAnywhere'de Flask uygulamasını çalıştırmak için kullanılır.
"""

import sys
import os

# Proje dizinini Python path'ine ekle
project_home = '/home/yourusername/ai_tweet_bot_pythonanywhere'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Environment değişkenlerini yükle
os.environ.setdefault('FLASK_ENV', 'production')

# Flask uygulamasını import et
from app import app as application

if __name__ == "__main__":
    application.run() 