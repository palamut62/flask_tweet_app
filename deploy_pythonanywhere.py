#!/usr/bin/env python3
"""
PythonAnywhere Deployment Script
Bu script PythonAnywhere'de uygulamayı deploy etmek için gerekli adımları otomatikleştirir
"""

import os
import sys
import subprocess
import json
import traceback
from pathlib import Path

def run_command(command, description=""):
    """Komut çalıştır ve sonucu döndür"""
    print(f"🔧 {description}")
    print(f"   Komut: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"   ✅ Başarılı")
            if result.stdout.strip():
                print(f"   📄 Çıktı: {result.stdout.strip()}")
        else:
            print(f"   ❌ Hata: {result.stderr.strip()}")
            
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Zaman aşımı")
        return False, "", "Timeout"
    except Exception as e:
        print(f"   ❌ Beklenmeyen hata: {e}")
        return False, "", str(e)

def check_python_version():
    """Python versiyonunu kontrol et"""
    print("\n🐍 Python Versiyonu Kontrolü")
    
    success, stdout, stderr = run_command("python --version", "Python versiyonu")
    if success:
        version = stdout.strip()
        print(f"   📋 Versiyon: {version}")
        
        # Python 3.8+ kontrolü
        if "3.8" in version or "3.9" in version or "3.10" in version or "3.11" in version:
            print("   ✅ Uyumlu Python versiyonu")
            return True
        else:
            print("   ⚠️ Python 3.8+ önerilir")
            return False
    
    return False

def check_pip():
    """pip'in çalışıp çalışmadığını kontrol et"""
    print("\n📦 Pip Kontrolü")
    
    success, stdout, stderr = run_command("pip --version", "Pip versiyonu")
    if success:
        print(f"   📋 {stdout.strip()}")
        return True
    else:
        print("   ❌ Pip bulunamadı")
        return False

def install_requirements():
    """Gerekli paketleri yükle"""
    print("\n📦 Paket Yükleme")
    
    # Önce minimal requirements'ı dene
    success, stdout, stderr = run_command(
        "pip install --user -r requirements_pythonanywhere_minimal.txt",
        "Minimal paketleri yükle"
    )
    
    if not success:
        print("   ⚠️ Minimal paketler yüklenemedi, temel paketleri dene")
        
        # Temel paketleri tek tek yükle
        basic_packages = [
            "flask==2.3.3",
            "python-dotenv==1.0.0", 
            "requests==2.31.0",
            "beautifulsoup4==4.12.2",
            "tweepy==4.14.0",
            "cryptography==41.0.7"
        ]
        
        for package in basic_packages:
            success, stdout, stderr = run_command(
                f"pip install --user {package}",
                f"{package} yükle"
            )
            if not success:
                print(f"   ❌ {package} yüklenemedi")
                return False
    
    return True

def check_file_permissions():
    """Dosya izinlerini kontrol et"""
    print("\n📁 Dosya İzinleri Kontrolü")
    
    current_dir = os.getcwd()
    print(f"   📂 Çalışma dizini: {current_dir}")
    
    # Temel dosyaları kontrol et
    essential_files = [
        "app.py",
        "wsgi.py", 
        "requirements_pythonanywhere_minimal.txt",
        "pythonanywhere_config.py"
    ]
    
    for file in essential_files:
        if os.path.exists(file):
            print(f"   ✅ {file} mevcut")
        else:
            print(f"   ❌ {file} bulunamadı")
            return False
    
    return True

def test_flask_import():
    """Flask import'unu test et"""
    print("\n🧪 Flask Import Testi")
    
    try:
        # Python path'ini ayarla
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Flask'ı import et
        import flask
        print(f"   ✅ Flask {flask.__version__} başarıyla import edildi")
        
        # Diğer temel paketleri test et
        import requests
        print(f"   ✅ Requests {requests.__version__} başarıyla import edildi")
        
        import tweepy
        print(f"   ✅ Tweepy {tweepy.__version__} başarıyla import edildi")
        
        import bs4
        print(f"   ✅ BeautifulSoup {bs4.__version__} başarıyla import edildi")
        
        import cryptography
        print(f"   ✅ Cryptography {cryptography.__version__} başarıyla import edildi")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import hatası: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Beklenmeyen hata: {e}")
        return False

def test_app_import():
    """Uygulama import'unu test et"""
    print("\n🧪 Uygulama Import Testi")
    
    try:
        # PythonAnywhere konfigürasyonunu test et
        try:
            from pythonanywhere_config import configure_for_pythonanywhere
            is_pa = configure_for_pythonanywhere()
            print(f"   ✅ PythonAnywhere konfigürasyonu: {is_pa}")
        except ImportError as e:
            print(f"   ⚠️ PythonAnywhere konfigürasyonu bulunamadı: {e}")
        
        # Flask uygulamasını import et
        from app import app
        print("   ✅ Flask uygulaması başarıyla import edildi")
        
        # Basit bir test yap
        with app.test_client() as client:
            response = client.get('/')
            print(f"   ✅ Ana sayfa testi: {response.status_code}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Uygulama import hatası: {e}")
        print(f"   🔍 Hata detayı: {traceback.format_exc()}")
        return False
    except Exception as e:
        print(f"   ❌ Beklenmeyen hata: {e}")
        print(f"   🔍 Hata detayı: {traceback.format_exc()}")
        return False

def create_deployment_summary():
    """Deployment özeti oluştur"""
    print("\n📋 Deployment Özeti")
    print("=" * 50)
    
    summary = {
        "python_version": "Bilinmiyor",
        "pip_available": False,
        "packages_installed": False,
        "file_permissions": False,
        "flask_import": False,
        "app_import": False
    }
    
    # Python versiyonu
    success, stdout, stderr = run_command("python --version", "Python versiyonu kontrol")
    if success:
        summary["python_version"] = stdout.strip()
    
    # Pip kontrolü
    success, stdout, stderr = run_command("pip --version", "Pip kontrol")
    summary["pip_available"] = success
    
    # Paket yükleme
    success, stdout, stderr = run_command("pip list | grep -E '(flask|requests|tweepy)'", "Paket kontrol")
    summary["packages_installed"] = success
    
    # Dosya izinleri
    summary["file_permissions"] = all(os.path.exists(f) for f in ["app.py", "wsgi.py"])
    
    # Flask import
    try:
        import flask
        summary["flask_import"] = True
    except:
        pass
    
    # Uygulama import
    try:
        from app import app
        summary["app_import"] = True
    except:
        pass
    
    # Özeti yazdır
    for key, value in summary.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value}")
    
    # Öneriler
    print("\n💡 Öneriler:")
    
    if not summary["pip_available"]:
        print("   - Pip yüklü değil, PythonAnywhere konsolunda kontrol edin")
    
    if not summary["packages_installed"]:
        print("   - Paketler yüklenemedi, şu komutu çalıştırın:")
        print("     pip install --user -r requirements_pythonanywhere_minimal.txt")
    
    if not summary["app_import"]:
        print("   - Uygulama import edilemiyor, hata loglarını kontrol edin")
        print("   - wsgi.py dosyasını wsgi_config_safe.py olarak değiştirin")
    
    return summary

def main():
    """Ana fonksiyon"""
    print("🚀 PythonAnywhere Deployment Script")
    print("=" * 50)
    
    # Kontrolleri yap
    checks = [
        ("Python Versiyonu", check_python_version),
        ("Pip Kontrolü", check_pip),
        ("Dosya İzinleri", check_file_permissions),
        ("Paket Yükleme", install_requirements),
        ("Flask Import", test_flask_import),
        ("Uygulama Import", test_app_import)
    ]
    
    results = {}
    
    for name, check_func in checks:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ {name} kontrolünde hata: {e}")
            results[name] = False
    
    # Özet oluştur
    summary = create_deployment_summary()
    
    # Sonuç
    print("\n" + "="*50)
    if all(results.values()):
        print("🎉 Tüm kontroller başarılı! Uygulama deploy edilmeye hazır.")
    else:
        print("⚠️ Bazı kontroller başarısız. Yukarıdaki önerileri takip edin.")
    
    print("\n📝 Sonraki Adımlar:")
    print("1. PythonAnywhere Web sekmesinde WSGI dosyasını wsgi_config_safe.py olarak değiştirin")
    print("2. Reload butonuna tıklayın")
    print("3. Hata alırsanız error loglarını kontrol edin")

if __name__ == "__main__":
    main()
