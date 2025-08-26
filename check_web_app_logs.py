#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere Web Uygulaması Log Kontrolü
"""

import os
import sys
from datetime import datetime

def check_web_app_status():
    """Web uygulaması durumunu kontrol et"""
    print("🌐 PythonAnywhere Web Uygulaması Kontrolü")
    print("=" * 50)
    
    # Environment değişkenleri
    print("1️⃣ Environment Değişkenleri:")
    print(f"   PYTHONANYWHERE_SITE: {os.environ.get('PYTHONANYWHERE_SITE', 'Yok')}")
    print(f"   PYTHONANYWHERE_USERNAME: {os.environ.get('PYTHONANYWHERE_USERNAME', 'Yok')}")
    print(f"   FLASK_ENV: {os.environ.get('FLASK_ENV', 'Yok')}")
    print(f"   DEBUG: {os.environ.get('DEBUG', 'Yok')}")
    
    # Çalışma dizini
    print(f"\n2️⃣ Çalışma Dizini:")
    print(f"   Mevcut: {os.getcwd()}")
    
    # Dosya varlığı kontrolü
    print(f"\n3️⃣ Kritik Dosyalar:")
    critical_files = [
        "app.py",
        "sqlite_security_manager.py", 
        "passwords.db",
        "wsgi.py"
    ]
    
    for file in critical_files:
        exists = os.path.exists(file)
        size = os.path.getsize(file) if exists else 0
        print(f"   {file}: {'✅' if exists else '❌'} ({size} bytes)")
    
    # Flask uygulaması test
    print(f"\n4️⃣ Flask Uygulaması Test:")
    try:
        from app import app
        print("   ✅ Flask app import başarılı")
        
        # SecurityManager kontrolü
        from app import security_manager
        print(f"   ✅ SecurityManager: {type(security_manager).__name__}")
        
        # Test route kontrolü
        with app.test_client() as client:
            response = client.get('/')
            print(f"   ✅ Ana sayfa erişimi: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Flask test hatası: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

def check_error_logs():
    """Hata loglarını kontrol et"""
    print(f"\n5️⃣ Hata Log Kontrolü:")
    
    # PythonAnywhere log dosyaları
    log_files = [
        "error.log",
        "access.log", 
        "scheduler.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"   {log_file}: ✅ ({size} bytes)")
            
            # Son 5 satırı göster
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"     Son 3 satır:")
                        for line in lines[-3:]:
                            print(f"       {line.strip()}")
            except Exception as e:
                print(f"     Log okuma hatası: {e}")
        else:
            print(f"   {log_file}: ❌ Bulunamadı")

def test_password_manager_route():
    """Password manager route'unu test et"""
    print(f"\n6️⃣ Password Manager Route Test:")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Password manager sayfası
            response = client.get('/password_manager')
            print(f"   Password Manager Sayfası: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Password manager sayfası erişilebilir")
            else:
                print(f"   ❌ Password manager hatası: {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Route test hatası: {e}")

def main():
    """Ana kontrol fonksiyonu"""
    print("🐍 PythonAnywhere Web Uygulaması Kontrolü")
    print("=" * 60)
    
    # Web uygulaması durumu
    check_web_app_status()
    
    # Hata logları
    check_error_logs()
    
    # Route test
    test_password_manager_route()
    
    print(f"\n📊 Kontrol Tamamlandı!")
    print("💡 Eğer hala sorun varsa, PythonAnywhere konsolunda:")
    print("   python3 pythonanywhere_error_debug.py")
    print("   komutunu çalıştırın")

if __name__ == "__main__":
    main()
