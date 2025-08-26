#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere Security Manager Test Scripti
Bu script PythonAnywhere'de şifre yöneticisini test eder
"""

import os
import sys
import json
import traceback
from datetime import datetime

def print_test_header():
    print("🧪 PythonAnywhere Security Manager Test")
    print("=" * 60)
    print(f"📅 Test Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Ortam: {'PythonAnywhere' if 'PYTHONANYWHERE_SITE' in os.environ else 'Local'}")
    print(f"📁 Dizin: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)

def test_environment():
    """Ortam testleri"""
    print("\n🌐 Ortam Testleri:")
    
    # PythonAnywhere kontrolü
    if 'PYTHONANYWHERE_SITE' in os.environ:
        print("✅ PythonAnywhere ortamında çalışıyor")
        print(f"   Site: {os.environ.get('PYTHONANYWHERE_SITE', 'Bilinmiyor')}")
    else:
        print("ℹ️ Local ortamda çalışıyor")
    
    # Dizin yazma izni
    if os.access('.', os.W_OK):
        print("✅ Proje dizini yazılabilir")
    else:
        print("❌ Proje dizini yazılamıyor")
        return False
    
    return True

def test_cryptography():
    """Cryptography kütüphanesi testi"""
    print("\n🔐 Cryptography Testi:")
    
    try:
        import cryptography
        print(f"✅ Cryptography yüklü: {cryptography.__version__}")
        
        # Fernet testi
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        fernet = Fernet(key)
        
        test_data = "test_password_123"
        encrypted = fernet.encrypt(test_data.encode())
        decrypted = fernet.decrypt(encrypted).decode()
        
        if test_data == decrypted:
            print("✅ Fernet şifreleme/çözme testi başarılı")
            return True
        else:
            print("❌ Fernet şifreleme/çözme testi başarısız")
            return False
            
    except ImportError as e:
        print(f"❌ Cryptography import hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ Cryptography test hatası: {e}")
        return False

def test_json_files():
    """JSON dosyaları testi"""
    print("\n📄 JSON Dosyaları Testi:")
    
    files_to_test = [
        "user_passwords.json",
        "user_cards.json",
        "access_codes.json"
    ]
    
    all_success = True
    
    for filename in files_to_test:
        try:
            if os.path.exists(filename):
                # Dosya okuma testi
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ {filename} okunabilir")
                
                # Dosya yazma testi
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ {filename} yazılabilir")
                
            else:
                # Dosya oluşturma testi
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
                print(f"✅ {filename} oluşturuldu")
                
        except Exception as e:
            print(f"❌ {filename} test hatası: {e}")
            all_success = False
    
    return all_success

def test_security_manager():
    """SecurityManager testi"""
    print("\n🔐 SecurityManager Testi:")
    
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
                
                # Şifre çözme testi
                if passwords[0]['password'] == test_password:
                    print("✅ Şifre çözme testi başarılı")
                else:
                    print("❌ Şifre çözme testi başarısız")
                    return False
                
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
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
        return False

def test_web_integration():
    """Web entegrasyonu testi"""
    print("\n🌐 Web Entegrasyonu Testi:")
    
    try:
        # Flask import testi
        import flask
        print("✅ Flask yüklü")
        
        # Session testi
        from flask import session
        print("✅ Flask session modülü mevcut")
        
        # Request testi
        from flask import request
        print("✅ Flask request modülü mevcut")
        
        return True
        
    except ImportError as e:
        print(f"❌ Flask import hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ Web entegrasyonu test hatası: {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print_test_header()
    
    tests = [
        ("Ortam Testi", test_environment),
        ("Cryptography Testi", test_cryptography),
        ("JSON Dosyaları Testi", test_json_files),
        ("SecurityManager Testi", test_security_manager),
        ("Web Entegrasyonu Testi", test_web_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: BAŞARILI")
            else:
                print(f"❌ {test_name}: BAŞARISIZ")
                
        except Exception as e:
            print(f"❌ {test_name}: HATA - {e}")
            results.append((test_name, False))
    
    # Sonuç özeti
    print("\n" + "=" * 60)
    print("📊 TEST SONUÇLARI:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Başarı Oranı: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 Tüm testler başarılı! Şifre yöneticisi çalışıyor.")
        print("\n💡 Şimdi yapmanız gerekenler:")
        print("1. PythonAnywhere'de 'Web' sekmesine gidin")
        print("2. 'Reload' butonuna tıklayın")
        print("3. Uygulamanızı açın ve şifre yöneticisini test edin")
        return True
    else:
        print(f"\n❌ {total-passed} test başarısız! Sorunları çözün.")
        print("\n🔧 Çözüm önerileri:")
        print("1. pythonanywhere_quick_fix.py scriptini çalıştırın")
        print("2. pythonanywhere_fix_commands.sh scriptini çalıştırın")
        print("3. Manuel olarak cryptography kütüphanesini yükleyin")
        print("4. Dosya izinlerini kontrol edin")
        return False

if __name__ == "__main__":
    try:
        success = main()
        print("\n" + "=" * 60)
        if success:
            print("✅ Test tamamlandı - Sistem hazır!")
        else:
            print("❌ Test tamamlandı - Sorunlar var!")
    except KeyboardInterrupt:
        print("\n\n⏹️ Test kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"\n\n❌ Beklenmeyen hata: {e}")
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
