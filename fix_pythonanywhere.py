#!/usr/bin/env python3
"""
PythonAnywhere Hızlı Düzeltme Aracı
Bu script PythonAnywhere'deki 500 hatasını hızlıca düzeltmek için kullanılır
"""

import os
import sys
import subprocess

def print_header():
    """Başlık yazdır"""
    print("🚀 PythonAnywhere 500 Hatası Düzeltme Aracı")
    print("=" * 50)

def run_command(command, description=""):
    """Komut çalıştır"""
    print(f"🔧 {description}")
    print(f"   Komut: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Başarılı")
            return True
        else:
            print(f"   ❌ Hata: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"   ❌ Hata: {e}")
        return False

def check_python_version():
    """Python versiyonunu kontrol et"""
    print("\n🐍 Python Versiyonu Kontrolü")
    return run_command("python --version", "Python versiyonu")

def install_minimal_packages():
    """Minimal paketleri yükle"""
    print("\n📦 Minimal Paket Yükleme")
    
    packages = [
        "flask==2.3.3",
        "python-dotenv==1.0.0", 
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "tweepy==4.14.0",
        "cryptography==41.0.7",
        "fpdf2==2.8.3"
    ]
    
    success_count = 0
    for package in packages:
        if run_command(f"pip install --user {package}", f"{package} yükle"):
            success_count += 1
    
    print(f"   📊 {success_count}/{len(packages)} paket başarıyla yüklendi")
    return success_count == len(packages)

def check_essential_files():
    """Temel dosyaları kontrol et"""
    print("\n📁 Temel Dosya Kontrolü")
    
    files = [
        "app.py",
        "wsgi_config_safe.py",
        "pythonanywhere_config.py",
        "requirements_pythonanywhere_minimal.txt"
    ]
    
    missing_files = []
    for file in files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - Bulunamadı")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_flask_import():
    """Flask import'unu test et"""
    print("\n🧪 Flask Import Testi")
    
    try:
        import flask
        print(f"   ✅ Flask {flask.__version__} başarıyla import edildi")
        return True
    except ImportError as e:
        print(f"   ❌ Flask import hatası: {e}")
        return False

def show_next_steps():
    """Sonraki adımları göster"""
    print("\n📝 Sonraki Adımlar:")
    print("1. PythonAnywhere Web sekmesine gidin")
    print("2. WSGI configuration file'ı 'wsgi_config_safe.py' olarak değiştirin")
    print("3. Reload butonuna tıklayın")
    print("4. Error log'ları kontrol edin")
    print("5. Uygulamanızı test edin")

def show_troubleshooting():
    """Sorun giderme önerileri"""
    print("\n🔧 Sorun Giderme:")
    print("• Hala 500 hatası alıyorsanız:")
    print("  - Error log'larını kontrol edin")
    print("  - Paketleri tekrar yükleyin: pip install --user flask==2.3.3")
    print("  - WSGI dosyasını wsgi_config_safe.py olarak değiştirin")
    print("  - PythonAnywhere konsolunda test_app_startup.py çalıştırın")

def main():
    """Ana fonksiyon"""
    print_header()
    
    # Kontrolleri yap
    checks = [
        ("Python Versiyonu", check_python_version),
        ("Temel Dosyalar", check_essential_files),
        ("Paket Yükleme", install_minimal_packages),
        ("Flask Import", test_flask_import)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{'='*20} {name} {'='*20}")
        result = check_func()
        results.append(result)
    
    # Özet
    print("\n" + "="*50)
    success_count = sum(results)
    total_count = len(results)
    
    print(f"📊 Sonuç: {success_count}/{total_count} kontrol başarılı")
    
    if success_count == total_count:
        print("🎉 Tüm kontroller başarılı! Deployment için hazır.")
        show_next_steps()
    else:
        print("⚠️ Bazı kontroller başarısız. Sorun giderme önerilerini takip edin.")
        show_troubleshooting()

if __name__ == "__main__":
    main()
