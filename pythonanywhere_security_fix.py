#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere Security Manager Fix Script
Bu script PythonAnywhere'de security manager sorunlarını çözer
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def check_cryptography():
    """Cryptography kütüphanesinin yüklü olup olmadığını kontrol et"""
    print("🔍 Cryptography kütüphanesi kontrol ediliyor...")
    
    try:
        import cryptography
        print(f"✅ Cryptography yüklü: {cryptography.__version__}")
        return True
    except ImportError:
        print("❌ Cryptography yüklü değil")
        return False

def install_cryptography():
    """Cryptography kütüphanesini yükle"""
    print("📦 Cryptography yükleniyor...")
    
    try:
        # pip ile yükle
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "cryptography==41.0.7"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Cryptography başarıyla yüklendi")
            return True
        else:
            print(f"❌ Cryptography yükleme hatası: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Yükleme hatası: {e}")
        return False

def check_file_permissions():
    """Dosya izinlerini kontrol et ve düzelt"""
    print("\n🔍 Dosya izinleri kontrol ediliyor...")
    
    files_to_check = [
        "user_passwords.json",
        "user_cards.json",
        "access_codes.json"
    ]
    
    for filename in files_to_check:
        try:
            if os.path.exists(filename):
                # Dosya izinlerini kontrol et
                if os.access(filename, os.W_OK):
                    print(f"✅ {filename} yazılabilir")
                else:
                    print(f"⚠️ {filename} yazılamıyor, izinler düzeltiliyor...")
                    # İzinleri düzelt (sadece owner için)
                    os.chmod(filename, 0o644)
                    print(f"✅ {filename} izinleri düzeltildi")
            else:
                print(f"📄 {filename} mevcut değil, oluşturuluyor...")
                # Boş JSON dosyası oluştur
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                print(f"✅ {filename} oluşturuldu")
                
        except Exception as e:
            print(f"❌ {filename} işlem hatası: {e}")

def test_security_manager():
    """SecurityManager'ı test et"""
    print("\n🔍 SecurityManager test ediliyor...")
    
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

def create_backup():
    """Mevcut dosyaların yedeğini al"""
    print("\n💾 Mevcut dosyaların yedeği alınıyor...")
    
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        files_to_backup = [
            "user_passwords.json",
            "user_cards.json", 
            "access_codes.json"
        ]
        
        for filename in files_to_backup:
            if os.path.exists(filename):
                import shutil
                shutil.copy2(filename, os.path.join(backup_dir, filename))
                print(f"✅ {filename} yedeklendi")
            else:
                print(f"⚠️ {filename} yedeklenmedi (mevcut değil)")
                
        print(f"📁 Yedek dizini: {backup_dir}")
        return backup_dir
        
    except Exception as e:
        print(f"❌ Yedekleme hatası: {e}")
        return None

def fix_security_manager():
    """SecurityManager sorunlarını düzelt"""
    print("🔧 SecurityManager sorunları düzeltiliyor...")
    
    # 1. Yedek al
    backup_dir = create_backup()
    
    # 2. Cryptography kontrol et
    if not check_cryptography():
        print("📦 Cryptography yükleniyor...")
        if not install_cryptography():
            print("❌ Cryptography yüklenemedi!")
            return False
    
    # 3. Dosya izinlerini kontrol et
    check_file_permissions()
    
    # 4. SecurityManager'ı test et
    if test_security_manager():
        print("\n🎉 SecurityManager başarıyla düzeltildi!")
        return True
    else:
        print("\n❌ SecurityManager düzeltilemedi!")
        return False

def main():
    """Ana fonksiyon"""
    print("🚀 PythonAnywhere Security Manager Fix Başlatılıyor...")
    print("=" * 60)
    
    # PythonAnywhere ortamını kontrol et
    print(f"🌐 PythonAnywhere ortamı: {os.environ.get('PYTHONANYWHERE_SITE', 'Hayır')}")
    print(f"📁 Çalışma dizini: {os.getcwd()}")
    print(f"🐍 Python versiyonu: {sys.version}")
    
    # Sorunları düzelt
    success = fix_security_manager()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Tüm sorunlar çözüldü! Şifre kaydetme artık çalışmalı.")
    else:
        print("❌ Bazı sorunlar çözülemedi. Manuel kontrol gerekli.")
    
    print("\n💡 Öneriler:")
    print("1. PythonAnywhere'de 'Files' sekmesinden dosya izinlerini kontrol edin")
    print("2. 'Consoles' sekmesinden pip install cryptography komutunu çalıştırın")
    print("3. Uygulamayı yeniden başlatın")

if __name__ == "__main__":
    main()
