#!/usr/bin/python3

"""
WSGI config for AI Tweet Bot Flask application on PythonAnywhere.

This module contains the WSGI application used by PythonAnywhere's
web servers. It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://help.pythonanywhere.com/pages/Flask/
"""

import sys
import os
from dotenv import load_dotenv

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================

# Add your project directory to the Python path
project_home = '/home/umutins62/flask_tweet_app'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Add the virtual environment site-packages to the Python path
venv_path = '/home/umutins62/flask_tweet_app/venv/lib/python3.10/site-packages'
if venv_path not in sys.path:
    sys.path = [venv_path] + sys.path

# ==============================================================================
# ENVIRONMENT VARIABLES
# ==============================================================================

# Load environment variables from .env file
env_path = os.path.join(project_home, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Environment variables loaded from: {env_path}")
else:
    print(f"⚠️ .env file not found at: {env_path}")

# Set Flask environment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', 'False')

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/umutins62/flask_tweet_app/logs/app.log'),
        logging.StreamHandler()
    ]
)

# ==============================================================================
# APPLICATION IMPORT AND CONFIGURATION
# ==============================================================================

try:
    # Change to project directory
    os.chdir(project_home)
    
    # Import Flask application
    from app import app as application
    
    # Configure application for production
    application.config['DEBUG'] = False
    application.config['TESTING'] = False
    
    # Ensure secret key is set
    if not application.config.get('SECRET_KEY'):
        application.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-production-secret-key-here')
    
    print("✅ Flask application loaded successfully")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path[:3]}...")  # Show first 3 paths
    
except Exception as e:
    print(f"❌ Error loading Flask application: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a simple error application
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/html')]
        start_response(status, headers)
        return [f"""
        <html>
        <head><title>Application Error</title></head>
        <body>
        <h1>Application Error</h1>
        <p>Failed to load the Flask application.</p>
        <p>Error: {str(e)}</p>
        <p>Please check the error logs and WSGI configuration.</p>
        </body>
        </html>
        """.encode('utf-8')]

# ==============================================================================
# WSGI APPLICATION TEST
# ==============================================================================

if __name__ == '__main__':
    # Test the WSGI application locally
    print("🧪 Testing WSGI application...")
    try:
        from werkzeug.serving import run_simple
        run_simple('localhost', 8000, application, use_debugger=False, use_reloader=False)
    except ImportError:
        print("⚠️ Werkzeug not available for local testing")
    except Exception as e:
        print(f"❌ WSGI test error: {e}") 