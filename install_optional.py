#!/usr/bin/env python3
"""
Opsiyonel Web Scraping Kütüphaneleri Kurulum Scripti
Bu script, gelişmiş web scraping özelliklerini etkinleştirmek için
opsiyonel kütüphaneleri kurar.
"""

import subprocess
import sys
import os

def install_package(package_name, description=""):
    """Paketi kur ve sonucu döndür"""
    try:
        print(f"📦 {package_name} kuruluyor... {description}")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], capture_output=True, text=True, check=True)
        
        print(f"✅ {package_name} başarıyla kuruldu!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} kurulumu başarısız: {e}")
        print(f"   Hata detayı: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ {package_name} kurulumu sırasında beklenmeyen hata: {e}")
        return False

def check_package(package_name):
    """Paketin kurulu olup olmadığını kontrol et"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def main():
    """Ana kurulum fonksiyonu"""
    print("🚀 AI Tweet Bot - Opsiyonel Kütüphaneler Kurulum Scripti")
    print("=" * 60)
    
    # Kurulacak opsiyonel paketler
    optional_packages = [
        {
            "name": "requests-html",
            "version": "0.10.0",
            "description": "(JavaScript rendering desteği)",
            "import_name": "requests_html"
        },
        {
            "name": "selenium",
            "version": "4.15.0", 
            "description": "(Browser automation - Chrome gerektirir)",
            "import_name": "selenium"
        },
        {
            "name": "pyppeteer",
            "version": "1.0.2",
            "description": "(Selenium alternatifi)",
            "import_name": "pyppeteer"
        }
    ]
    
    installed_count = 0
    total_count = len(optional_packages)
    
    for package in optional_packages:
        package_spec = f"{package['name']}=={package['version']}"
        
        # Önce kurulu mu kontrol et
        if check_package(package['import_name']):
            print(f"✅ {package['name']} zaten kurulu")
            installed_count += 1
            continue
        
        # Kurulmamışsa kur
        if install_package(package_spec, package['description']):
            installed_count += 1
        
        print()  # Boş satır
    
    print("=" * 60)
    print(f"📊 Kurulum Özeti: {installed_count}/{total_count} paket başarılı")
    
    if installed_count == total_count:
        print("🎉 Tüm opsiyonel paketler başarıyla kuruldu!")
        print("   Artık gelişmiş web scraping özelliklerini kullanabilirsiniz.")
    elif installed_count > 0:
        print("⚠️  Bazı paketler kuruldu, bazıları başarısız.")
        print("   Temel işlevsellik çalışacak, bazı gelişmiş özellikler olmayabilir.")
    else:
        print("❌ Hiçbir opsiyonel paket kurulamadı.")
        print("   Temel işlevsellik çalışacak ama gelişmiş özellikler olmayacak.")
    
    print("\n📝 Not:")
    print("   - requests-html: Modern JavaScript siteler için")
    print("   - selenium: Chrome browser automation için (Chrome kurulu olmalı)")
    print("   - pyppeteer: Selenium alternatifi (otomatik Chrome indirir)")
    
    print("\n🔧 PythonAnywhere'de kullanım:")
    print("   Bu paketler PythonAnywhere'de çalışmayabilir.")
    print("   Temel scraping sistemi her durumda çalışacaktır.")

if __name__ == "__main__":
    main() 