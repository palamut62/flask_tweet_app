#!/usr/bin/env python3
"""
PythonAnywhere Otomatik Kurulum Scripti
Bu script PythonAnywhere'de uygulamayı otomatik olarak kurar ve yapılandırır
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Komut çalıştır ve sonucu göster"""
    print(f"🔄 {description}")
    print(f"   Komut: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Başarılı: {description}")
            if result.stdout:
                print(f"   Çıktı: {result.stdout.strip()}")
        else:
            print(f"❌ Hata: {description}")
            print(f"   Hata: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ İstisna: {description}")
        print(f"   Hata: {e}")
        return False
    
    return True

def check_python_version():
    """Python versiyonunu kontrol et"""
    print("🐍 Python versiyonu kontrol ediliyor...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 veya üstü gerekli!")
        return False
    
    print("✅ Python versiyonu uygun")
    return True

def install_requirements():
    """Gerekli paketleri yükle"""
    print("📦 Gerekli paketler yükleniyor...")
    
    # Önce temel paketleri yükle
    basic_packages = [
        "flask",
        "requests", 
        "python-dotenv",
        "tweepy",
        "beautifulsoup4"
    ]
    
    for package in basic_packages:
        if not run_command(f"pip install --user {package}", f"{package} yükleniyor"):
            return False
    
    # Sonra requirements dosyasını yükle
    if os.path.exists("requirements_pythonanywhere.txt"):
        if not run_command("pip install --user -r requirements_pythonanywhere.txt", "Requirements dosyası yükleniyor"):
            print("⚠️ Requirements dosyası yüklenemedi, temel paketlerle devam ediliyor")
    
    return True

def download_static_files():
    """Static dosyaları indir"""
    print("📁 Static dosyalar indiriliyor...")
    
    if os.path.exists("download_static_files.py"):
        if not run_command("python download_static_files.py", "Static dosyalar indiriliyor"):
            print("⚠️ Static dosyalar indirilemedi")
            return False
    else:
        print("⚠️ download_static_files.py bulunamadı")
        return False
    
    return True

def create_env_file():
    """Örnek .env dosyası oluştur"""
    print("🔧 .env dosyası oluşturuluyor...")
    
    env_content = """# PythonAnywhere Environment Variables
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-this
DEBUG=False
USE_LOCAL_ASSETS=True
PYTHONANYWHERE_MODE=True

# API Keys (Bu değerleri kendi API anahtarlarınızla değiştirin)
OPENROUTER_API_KEY=your-openrouter-api-key
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
GOOGLE_API_KEY=your-google-api-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Email Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("✅ .env dosyası oluşturuldu")
    print("⚠️ Lütfen .env dosyasındaki API anahtarlarını kendi değerlerinizle değiştirin!")
    return True

def setup_directories():
    """Gerekli dizinleri oluştur"""
    print("📁 Dizinler oluşturuluyor...")
    
    directories = [
        "static/css",
        "static/js",
        "static/webfonts", 
        "static/images",
        "logs",
        "backups",
        "data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    return True

def test_imports():
    """Gerekli modüllerin import edilebilirliğini test et"""
    print("🧪 Modül import testleri...")
    
    modules = [
        "flask",
        "requests",
        "dotenv",
        "tweepy",
        "bs4"
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            return False
    
    return True

def create_test_script():
    """Test scripti oluştur"""
    print("🧪 Test scripti oluşturuluyor...")
    
    test_content = """#!/usr/bin/env python3
\"\"\"
PythonAnywhere Test Scripti
Bu script uygulamanın doğru çalışıp çalışmadığını test eder
\"\"\"

import sys
import os

def test_basic_imports():
    \"\"\"Temel import'ları test et\"\"\"
    print("🧪 Temel import testleri...")
    
    try:
        import flask
        print("✅ Flask import edildi")
    except ImportError as e:
        print(f"❌ Flask import hatası: {e}")
        return False
    
    try:
        import requests
        print("✅ Requests import edildi")
    except ImportError as e:
        print(f"❌ Requests import hatası: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ Python-dotenv import edildi")
    except ImportError as e:
        print(f"❌ Python-dotenv import hatası: {e}")
        return False
    
    return True

def test_app_import():
    \"\"\"Ana uygulamayı import etmeyi test et\"\"\"
    print("🧪 Uygulama import testi...")
    
    try:
        from app import app
        print("✅ Ana uygulama import edildi")
        return True
    except ImportError as e:
        print(f"❌ Ana uygulama import hatası: {e}")
        return False

def test_static_files():
    \"\"\"Static dosyaların varlığını test et\"\"\"
    print("🧪 Static dosya testi...")
    
    required_files = [
        "static/css/bootstrap.min.css",
        "static/css/all.min.css",
        "static/js/bootstrap.bundle.min.js"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} bulunamadı")
            return False
    
    return True

def main():
    \"\"\"Ana test fonksiyonu\"\"\"
    print("🚀 PythonAnywhere Test Scripti Başlatılıyor...")
    
    tests = [
        test_basic_imports,
        test_app_import,
        test_static_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Sonuçları: {passed}/{total} başarılı")
    
    if passed == total:
        print("🎉 Tüm testler başarılı! Uygulama hazır.")
        return True
    else:
        print("⚠️ Bazı testler başarısız. Lütfen hataları kontrol edin.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""
    
    with open("test_pythonanywhere.py", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    print("✅ Test scripti oluşturuldu")
    return True

def main():
    """Ana kurulum fonksiyonu"""
    print("🚀 PythonAnywhere Otomatik Kurulum Başlatılıyor...")
    print("=" * 50)
    
    # Kurulum adımları
    steps = [
        ("Python versiyonu kontrol ediliyor", check_python_version),
        ("Dizinler oluşturuluyor", setup_directories),
        ("Gerekli paketler yükleniyor", install_requirements),
        ("Static dosyalar indiriliyor", download_static_files),
        ("Environment dosyası oluşturuluyor", create_env_file),
        ("Test scripti oluşturuluyor", create_test_script),
        ("Modül import testleri", test_imports)
    ]
    
    successful_steps = 0
    total_steps = len(steps)
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if step_func():
            successful_steps += 1
        else:
            print(f"❌ {step_name} başarısız!")
            break
    
    print("\n" + "=" * 50)
    print(f"📊 Kurulum Sonucu: {successful_steps}/{total_steps} adım başarılı")
    
    if successful_steps == total_steps:
        print("🎉 Kurulum tamamlandı!")
        print("\n📋 Sonraki Adımlar:")
        print("1. .env dosyasındaki API anahtarlarını güncelleyin")
        print("2. python test_pythonanywhere.py komutunu çalıştırın")
        print("3. PythonAnywhere Web sekmesinde Reload butonuna tıklayın")
        print("4. Uygulamanızı test edin")
        return True
    else:
        print("⚠️ Kurulum tamamlanamadı. Lütfen hataları kontrol edin.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
