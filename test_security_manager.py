#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere Security Manager Test Script
Bu script PythonAnywhere'de security manager'ın çalışıp çalışmadığını test eder
"""

import os
import sys
import json
import traceback
from datetime import datetime

def test_cryptography_import():
    """Cryptography kütüphanesinin yüklü olup olmadığını test et"""
    print("🔍 Cryptography kütüphanesi test ediliyor...")
    
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        print("✅ Cryptography kütüphanesi başarıyla import edildi")
        return True
    except ImportError as e:
        print(f"❌ Cryptography import hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ Cryptography genel hata: {e}")
        return False

def test_file_permissions():
    """Dosya yazma izinlerini test et"""
    print("\n🔍 Dosya yazma izinleri test ediliyor...")
    
    test_files = [
        "user_passwords.json",
        "user_cards.json", 
        "access_codes.json"
    ]
    
    for filename in test_files:
        try:
            # Dosya var mı kontrol et
            if os.path.exists(filename):
                print(f"📁 {filename} mevcut")
                
                # Yazma izni kontrol et
                if os.access(filename, os.W_OK):
                    print(f"✅ {filename} yazılabilir")
                else:
                    print(f"❌ {filename} yazılamıyor")
            else:
                print(f"📄 {filename} mevcut değil, oluşturulacak")
                
                # Test dosyası oluştur
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump({}, f)
                    print(f"✅ {filename} başarıyla oluşturuldu")
                    
                    # Test dosyasını sil
                    os.remove(filename)
                    print(f"🗑️ {filename} test dosyası silindi")
                except Exception as e:
                    print(f"❌ {filename} oluşturulamadı: {e}")
                    
        except Exception as e:
            print(f"❌ {filename} kontrol hatası: {e}")

def test_security_manager():
    """SecurityManager sınıfını test et"""
    print("\n🔍 SecurityManager test ediliyor...")
    
    try:
        # SecurityManager'ı import et
        from security_manager import SecurityManager
        
        # Instance oluştur
        sm = SecurityManager()
        print("✅ SecurityManager instance oluşturuldu")
        
        # Test verileri
        test_user_id = "test_user_123"
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
            else:
                print("❌ Test şifresi okunamadı")
        else:
            print("❌ Test şifresi kaydedilemedi")
            
    except Exception as e:
        print(f"❌ SecurityManager test hatası: {e}")
        print(f"🔍 Hata detayı: {traceback.format_exc()}")

def test_environment():
    """PythonAnywhere ortamını test et"""
    print("\n🔍 PythonAnywhere ortamı test ediliyor...")
    
    print(f"📁 Çalışma dizini: {os.getcwd()}")
    print(f"🐍 Python versiyonu: {sys.version}")
    print(f"📦 Python path: {sys.path[:3]}...")  # İlk 3 path'i göster
    
    # PythonAnywhere özel değişkenleri
    pythonanywhere_vars = [
        'PYTHONANYWHERE_SITE',
        'PYTHONANYWHERE_DOMAIN', 
        'PYTHONANYWHERE_MODE'
    ]
    
    for var in pythonanywhere_vars:
        value = os.environ.get(var, 'Tanımlı değil')
        print(f"🌐 {var}: {value}")

def main():
    """Ana test fonksiyonu"""
    print("🚀 PythonAnywhere Security Manager Test Başlatılıyor...")
    print("=" * 60)
    
    # Ortam testi
    test_environment()
    
    # Cryptography testi
    crypto_ok = test_cryptography_import()
    
    # Dosya izinleri testi
    test_file_permissions()
    
    # SecurityManager testi (sadece cryptography yüklüyse)
    if crypto_ok:
        test_security_manager()
    else:
        print("\n⚠️ Cryptography yüklü olmadığı için SecurityManager test edilmedi")
        print("💡 Çözüm: pip install cryptography")
    
    print("\n" + "=" * 60)
    print("🏁 Test tamamlandı")

if __name__ == "__main__":
    main()
