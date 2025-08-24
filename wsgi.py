#!/usr/bin/env python3
"""
PythonAnywhere WSGI Konfigürasyonu
Bu dosya PythonAnywhere'de Flask uygulamasını çalıştırmak için kullanılır
"""

import sys
import os

# Proje dizinini Python path'ine ekle
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Environment değişkenlerini ayarla
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('PYTHONANYWHERE_MODE', 'True')

# PythonAnywhere konfigürasyonunu yükle
try:
    from pythonanywhere_config import configure_for_pythonanywhere
    is_pythonanywhere = configure_for_pythonanywhere()
    print(f"🐍 PythonAnywhere tespit edildi: {is_pythonanywhere}")
except ImportError:
    is_pythonanywhere = False
    print("ℹ️ PythonAnywhere konfigürasyonu bulunamadı")

# Flask uygulamasını import et
try:
    from app import app as application
    print("✅ Flask uygulaması başarıyla yüklendi")
except ImportError as e:
    print(f"❌ Flask uygulaması yüklenemedi: {e}")
    # Hata durumunda basit bir uygulama döndür
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return f"""
        <h1>❌ Uygulama Yüklenemedi</h1>
        <p>Hata: {e}</p>
        <p>Lütfen PythonAnywhere konsolunda şu komutları çalıştırın:</p>
        <pre>
        pip install --user -r requirements.txt
        python download_static_files.py
        </pre>
        """

# Debug bilgileri
if is_pythonanywhere:
    print("🔧 PythonAnywhere modunda çalışıyor")
    print(f"📁 Çalışma dizini: {os.getcwd()}")
    print(f"🐍 Python versiyonu: {sys.version}")
    print(f"📦 Python path: {sys.path[:3]}...")

if __name__ == "__main__":
    application.run(debug=False, host='0.0.0.0', port=5000) 