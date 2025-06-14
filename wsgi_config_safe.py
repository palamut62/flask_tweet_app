#!/usr/bin/python3

"""
WSGI config for AI Tweet Bot Flask application on PythonAnywhere.
Safe version with error handling for logs directory.
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
# SAFE LOGGING CONFIGURATION
# ==============================================================================

import logging

# Create logs directory if it doesn't exist
logs_dir = os.path.join(project_home, 'logs')
try:
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, 'app.log')
    
    # Test if we can write to the log file
    with open(log_file, 'a') as f:
        f.write('')  # Test write
    
    # Configure logging with file handler
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    print(f"✅ Logging configured with file: {log_file}")
    
except Exception as log_error:
    # Fallback to console-only logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    print(f"⚠️ File logging failed, using console only: {log_error}")

# ==============================================================================
# APPLICATION IMPORT AND CONFIGURATION
# ==============================================================================

try:
    # Change to project directory
    os.chdir(project_home)
    print(f"📁 Changed to directory: {os.getcwd()}")
    
    # Import Flask application
    from app import app as application
    
    # Configure application for production
    application.config['DEBUG'] = False
    application.config['TESTING'] = False
    
    # Ensure secret key is set
    if not application.config.get('SECRET_KEY'):
        application.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-production-secret-key-here')
    
    print("✅ Flask application loaded successfully")
    print(f"🐍 Python path: {sys.path[:2]}...")  # Show first 2 paths
    
except Exception as e:
    print(f"❌ Error loading Flask application: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a simple error application
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Application Error</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ background: #ffebee; padding: 20px; border-radius: 5px; }}
                .code {{ background: #f5f5f5; padding: 10px; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>🚨 Application Error</h1>
                <p>Failed to load the Flask application.</p>
                <div class="code">Error: {str(e)}</div>
                <p>Please check the error logs and WSGI configuration.</p>
                <p><strong>Common solutions:</strong></p>
                <ul>
                    <li>Check if all required files exist</li>
                    <li>Verify virtual environment path</li>
                    <li>Ensure all dependencies are installed</li>
                    <li>Check file permissions</li>
                </ul>
            </div>
        </body>
        </html>
        """.encode('utf-8')
        
        return [error_html]

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