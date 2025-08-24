#!/usr/bin/env python3
"""
PythonAnywhere Durum Kontrol Scripti
Bu script PythonAnywhere'deki sorunları tespit eder ve çözüm önerir
"""

import os
import sys
import requests
from pathlib import Path

def check_pythonanywhere_environment():
    """PythonAnywhere ortamını kontrol et"""
    print("🔍 PythonAnywhere Ortam Kontrolü")
    print("=" * 40)
    
    # PythonAnywhere tespiti
    is_pythonanywhere = (
        'PYTHONANYWHERE_SITE' in os.environ or
        'PYTHONANYWHERE_DOMAIN' in os.environ or
        '/home/' in os.getcwd() or
        'pythonanywhere' in os.getcwd().lower()
    )
    
    print(f"🐍 PythonAnywhere Ortamı: {'✅ Evet' if is_pythonanywhere else '❌ Hayır'}")
    print(f"📁 Çalışma Dizini: {os.getcwd()}")
    print(f"🐍 Python Versiyonu: {sys.version}")
    
    return is_pythonanywhere

def check_static_files():
    """Static dosyaları kontrol et"""
    print("\n📁 Static Dosya Kontrolü")
    print("=" * 40)
    
    static_files = {
        "static/css/bootstrap.min.css": "Bootstrap CSS",
        "static/css/all.min.css": "Font Awesome CSS", 
        "static/css/twitter-style.css": "Twitter Style CSS",
        "static/js/bootstrap.bundle.min.js": "Bootstrap JS",
        "static/webfonts/fa-solid-900.woff2": "Font Awesome Solid",
        "static/webfonts/fa-regular-400.woff2": "Font Awesome Regular",
        "static/webfonts/fa-brands-400.woff2": "Font Awesome Brands"
    }
    
    missing_files = []
    existing_files = []
    
    for file_path, description in static_files.items():
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            existing_files.append((file_path, description, file_size))
            print(f"✅ {description}: {file_path} ({file_size:,} bytes)")
        else:
            missing_files.append((file_path, description))
            print(f"❌ {description}: {file_path} (BULUNAMADI)")
    
    return existing_files, missing_files

def check_environment_variables():
    """Environment variables'ları kontrol et"""
    print("\n🔧 Environment Variables Kontrolü")
    print("=" * 40)
    
    env_vars = {
        'FLASK_ENV': 'Flask Environment',
        'SECRET_KEY': 'Secret Key',
        'USE_LOCAL_ASSETS': 'Use Local Assets',
        'PYTHONANYWHERE_MODE': 'PythonAnywhere Mode',
        'DEBUG': 'Debug Mode'
    }
    
    missing_vars = []
    existing_vars = []
    
    for var, description in env_vars.items():
        value = os.environ.get(var)
        if value:
            existing_vars.append((var, description, value))
            print(f"✅ {description}: {var} = {value}")
        else:
            missing_vars.append((var, description))
            print(f"❌ {description}: {var} (AYARLANMAMIŞ)")
    
    return existing_vars, missing_vars

def check_template_configuration():
    """Template konfigürasyonunu kontrol et"""
    print("\n📄 Template Konfigürasyon Kontrolü")
    print("=" * 40)
    
    # base.html dosyasını kontrol et
    base_html_path = "templates/base.html"
    if os.path.exists(base_html_path):
        with open(base_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("Bootstrap CSS", "bootstrap.min.css" in content),
            ("Font Awesome CSS", "all.min.css" in content),
            ("Bootstrap JS", "bootstrap.bundle.min.js" in content),
            ("PythonAnywhere Detection", "is_pythonanywhere" in content),
            ("Local Assets", "USE_LOCAL_ASSETS" in content)
        ]
        
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {'Mevcut' if result else 'Eksik'}")
        
        return True
    else:
        print("❌ templates/base.html bulunamadı!")
        return False

def check_wsgi_configuration():
    """WSGI konfigürasyonunu kontrol et"""
    print("\n⚙️ WSGI Konfigürasyon Kontrolü")
    print("=" * 40)
    
    wsgi_path = "wsgi.py"
    if os.path.exists(wsgi_path):
        with open(wsgi_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("PythonAnywhere Config Import", "pythonanywhere_config" in content),
            ("Environment Variables", "FLASK_ENV" in content),
            ("Error Handling", "ImportError" in content),
            ("Debug Info", "PythonAnywhere" in content)
        ]
        
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {'Mevcut' if result else 'Eksik'}")
        
        return True
    else:
        print("❌ wsgi.py bulunamadı!")
        return False

def generate_fix_commands():
    """Düzeltme komutlarını oluştur"""
    print("\n🔧 Düzeltme Komutları")
    print("=" * 40)
    
    commands = [
        "python setup_pythonanywhere.py",
        "python download_static_files.py", 
        "python test_pythonanywhere.py"
    ]
    
    print("PythonAnywhere konsolunda şu komutları sırayla çalıştırın:")
    for i, cmd in enumerate(commands, 1):
        print(f"{i}. {cmd}")

def check_web_access():
    """Web erişimini kontrol et"""
    print("\n🌐 Web Erişim Kontrolü")
    print("=" * 40)
    
    try:
        # PythonAnywhere'de static dosyalara erişimi test et
        test_urls = [
            "/static/css/bootstrap.min.css",
            "/static/css/all.min.css",
            "/static/js/bootstrap.bundle.min.js"
        ]
        
        print("⚠️ Bu test PythonAnywhere'de çalıştırılmalıdır")
        print("PythonAnywhere konsolunda şu komutu çalıştırın:")
        print("python -c \"import requests; print(requests.get('https://yourusername.pythonanywhere.com/static/css/bootstrap.min.css').status_code)\"")
        
    except Exception as e:
        print(f"❌ Web erişim testi başarısız: {e}")

def main():
    """Ana kontrol fonksiyonu"""
    print("🚀 PythonAnywhere Durum Kontrolü Başlatılıyor...")
    print("=" * 50)
    
    # Kontrolleri yap
    is_pa = check_pythonanywhere_environment()
    existing_files, missing_files = check_static_files()
    existing_vars, missing_vars = check_environment_variables()
    template_ok = check_template_configuration()
    wsgi_ok = check_wsgi_configuration()
    
    # Sonuçları özetle
    print("\n📊 ÖZET")
    print("=" * 50)
    
    total_checks = 0
    passed_checks = 0
    
    # Dosya kontrolleri
    total_checks += len(existing_files) + len(missing_files)
    passed_checks += len(existing_files)
    
    # Environment kontrolleri
    total_checks += len(existing_vars) + len(missing_vars)
    passed_checks += len(existing_vars)
    
    # Template ve WSGI kontrolleri
    total_checks += 2
    if template_ok:
        passed_checks += 1
    if wsgi_ok:
        passed_checks += 1
    
    print(f"✅ Başarılı Kontroller: {passed_checks}")
    print(f"❌ Başarısız Kontroller: {total_checks - passed_checks}")
    print(f"📊 Toplam Başarı Oranı: {(passed_checks/total_checks)*100:.1f}%")
    
    # Sorun tespiti
    if missing_files:
        print(f"\n⚠️ {len(missing_files)} static dosya eksik!")
        print("Çözüm: python download_static_files.py")
    
    if missing_vars:
        print(f"\n⚠️ {len(missing_vars)} environment variable eksik!")
        print("Çözüm: .env dosyasını kontrol edin")
    
    if not is_pa:
        print("\n⚠️ PythonAnywhere ortamı tespit edilemedi!")
        print("Bu script PythonAnywhere'de çalıştırılmalıdır")
    
    # Düzeltme komutları
    if missing_files or missing_vars:
        generate_fix_commands()
    
    # Web erişim kontrolü
    check_web_access()
    
    print("\n🎯 ÖNERİLER:")
    print("1. PythonAnywhere'de bu scripti çalıştırın")
    print("2. Eksik dosyalar varsa download_static_files.py çalıştırın")
    print("3. Environment variables'ları kontrol edin")
    print("4. PythonAnywhere Web sekmesinde Reload yapın")
    print("5. Browser cache'ini temizleyin")

if __name__ == "__main__":
    main()
