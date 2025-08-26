#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere Şifre Yöneticisi Hızlı Düzeltme Scripti
Bu script PythonAnywhere'de şifre kaydetme sorunlarını çözer
"""

import os
import sys
import json
import subprocess
from datetime import datetime

def print_header():
    print("🔐 PythonAnywhere Şifre Yöneticisi Düzeltme Scripti")
    print("=" * 60)
    print(f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Ortam: {'PythonAnywhere' if 'PYTHONANYWHERE_SITE' in os.environ else 'Local'}")
    print(f"📁 Dizin: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)

def check_and_install_cryptography():
    """Cryptography kütüphanesini kontrol et ve yükle"""
    print("\n🔍 Cryptography kütüphanesi kontrol ediliyor...")
    
    try:
        import cryptography
        print(f"✅ Cryptography zaten yüklü: {cryptography.__version__}")
        return True
    except ImportError:
        print("❌ Cryptography yüklü değil, yükleniyor...")
        
        try:
            # pip ile yükle
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "cryptography==41.0.7"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Cryptography başarıyla yüklendi")
                return True
            else:
                print(f"❌ Cryptography yükleme hatası: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Cryptography yükleme zaman aşımı")
            return False
        except Exception as e:
            print(f"❌ Cryptography yükleme hatası: {e}")
            return False

def create_json_files():
    """Gerekli JSON dosyalarını oluştur"""
    print("\n📄 JSON dosyaları kontrol ediliyor...")
    
    files_to_create = [
        "user_passwords.json",
        "user_cards.json", 
        "access_codes.json"
    ]
    
    for filename in files_to_create:
        try:
            if os.path.exists(filename):
                # Dosya mevcut, izinleri kontrol et
                if os.access(filename, os.W_OK):
                    print(f"✅ {filename} mevcut ve yazılabilir")
                else:
                    print(f"⚠️ {filename} yazılamıyor, izinler düzeltiliyor...")
                    os.chmod(filename, 0o644)
                    print(f"✅ {filename} izinleri düzeltildi")
            else:
                # Dosya yok, oluştur
                print(f"📄 {filename} oluşturuluyor...")
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
                os.chmod(filename, 0o644)
                print(f"✅ {filename} oluşturuldu")
                
        except Exception as e:
            print(f"❌ {filename} işlem hatası: {e}")

def test_security_manager():
    """SecurityManager'ı test et"""
    print("\n🧪 SecurityManager test ediliyor...")
    
    try:
        from security_manager import SecurityManager
        
        # Instance oluştur
        sm = SecurityManager()
        print("✅ SecurityManager instance oluşturuldu")
        
        # Test verileri
        test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_site = "test_site"
        test_username = "test_user"
        test_password = "test_password_123"
        test_master_password = "master_password_123"
        
        # Şifre kaydetme testi
        print("🔐 Test şifresi kaydediliyor...")
        success = sm.save_password(test_user_id, test_site, test_username, test_password, test_master_password)
        
        if success:
            print("✅ Test şifresi başarıyla kaydedildi")
            
            # Şifre okuma testi
            print("🔓 Test şifresi okunuyor...")
            passwords = sm.get_passwords(test_user_id, test_master_password)
            
            if passwords and len(passwords) > 0:
                print(f"✅ Test şifresi başarıyla okundu: {passwords[0]['site_name']}")
                
                # Test verilerini temizle
                sm.delete_password(test_user_id, test_site)
                print("🗑️ Test verileri temizlendi")
                
                return True
            else:
                print("❌ Test şifresi okunamadı")
                return False
        else:
            print("❌ Test şifresi kaydedilemedi")
            return False
            
    except Exception as e:
        print(f"❌ SecurityManager test hatası: {e}")
        import traceback
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
        return False

def check_environment():
    """PythonAnywhere ortamını kontrol et"""
    print("\n🌐 Ortam kontrol ediliyor...")
    
    # PythonAnywhere kontrolü
    if 'PYTHONANYWHERE_SITE' in os.environ:
        print("✅ PythonAnywhere ortamında çalışıyor")
        print(f"   Site: {os.environ.get('PYTHONANYWHERE_SITE', 'Bilinmiyor')}")
    else:
        print("ℹ️ Local ortamda çalışıyor")
    
    # Dizin kontrolü
    current_dir = os.getcwd()
    print(f"📁 Çalışma dizini: {current_dir}")
    
    # Gerekli dosyaların varlığı
    required_files = ["app.py", "security_manager.py"]
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} mevcut")
        else:
            print(f"❌ {file} bulunamadı")

def main():
    """Ana fonksiyon"""
    print_header()
    
    # 1. Ortam kontrolü
    check_environment()
    
    # 2. Cryptography kontrol et ve yükle
    if not check_and_install_cryptography():
        print("\n❌ Cryptography yüklenemedi! Manuel olarak yüklemeyi deneyin:")
        print("   pip install cryptography==41.0.7")
        return False
    
    # 3. JSON dosyalarını oluştur
    create_json_files()
    
    # 4. SecurityManager'ı test et
    if test_security_manager():
        print("\n🎉 Tüm testler başarılı! Şifre yöneticisi çalışıyor.")
        print("\n💡 Şimdi yapmanız gerekenler:")
        print("1. PythonAnywhere'de 'Web' sekmesine gidin")
        print("2. 'Reload' butonuna tıklayın")
        print("3. Uygulamanızı açın ve şifre yöneticisini test edin")
        return True
    else:
        print("\n❌ Test başarısız! Manuel kontrol gerekli.")
        print("\n🔧 Manuel çözüm adımları:")
        print("1. PythonAnywhere Console'da şu komutları çalıştırın:")
        print("   cd /home/kullaniciadi/flask_tweet_app")
        print("   pip install cryptography==41.0.7")
        print("   chmod 644 *.json")
        print("2. Uygulamayı yeniden başlatın")
        return False

if __name__ == "__main__":
    try:
        success = main()
        print("\n" + "=" * 60)
        if success:
            print("✅ Düzeltme başarılı!")
        else:
            print("❌ Düzeltme başarısız!")
    except KeyboardInterrupt:
        print("\n\n⏹️ İşlem kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"\n\n❌ Beklenmeyen hata: {e}")
        import traceback
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
