#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite Security Manager Test Scripti
Bu script SQLite tabanlı şifre yönetimi sistemini test eder
"""

import os
import sys
import traceback
from datetime import datetime

def print_test_header():
    print("🧪 SQLite Security Manager Test")
    print("=" * 60)
    print(f"📅 Test Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Ortam: {'PythonAnywhere' if 'PYTHONANYWHERE_SITE' in os.environ else 'Local'}")
    print(f"📁 Dizin: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)

def test_sqlite_import():
    """SQLite SecurityManager import testi"""
    print("\n🔍 SQLite SecurityManager Import Testi:")
    
    try:
        from sqlite_security_manager import SQLiteSecurityManager
        print("✅ SQLiteSecurityManager başarıyla import edildi")
        return True
    except ImportError as e:
        print(f"❌ SQLiteSecurityManager import hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ Beklenmeyen import hatası: {e}")
        return False

def test_database_creation():
    """Veritabanı oluşturma testi"""
    print("\n🗄️ Veritabanı Oluşturma Testi:")
    
    try:
        from sqlite_security_manager import SQLiteSecurityManager
        
        # Test veritabanı oluştur
        test_db_path = "test_passwords.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        sm = SQLiteSecurityManager(test_db_path)
        print("✅ SQLiteSecurityManager instance oluşturuldu")
        
        # Veritabanı bilgilerini kontrol et
        db_info = sm.get_database_info()
        print(f"📊 Veritabanı bilgileri: {db_info}")
        
        # Test veritabanını temizle
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Veritabanı oluşturma hatası: {e}")
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
        return False

def test_password_operations():
    """Şifre işlemleri testi"""
    print("\n🔐 Şifre İşlemleri Testi:")
    
    try:
        from sqlite_security_manager import SQLiteSecurityManager
        
        # Test veritabanı oluştur
        test_db_path = "test_passwords.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        sm = SQLiteSecurityManager(test_db_path)
        
        # Test verileri
        test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_site = "test_site"
        test_username = "test_user"
        test_password = "test_password_123"
        test_master_password = "master_password_123"
        
        print(f"🔍 Test verileri hazırlandı:")
        print(f"   User ID: {test_user_id}")
        print(f"   Site: {test_site}")
        print(f"   Username: {test_username}")
        print(f"   Password: {'*' * len(test_password)}")
        print(f"   Master Password: {'*' * len(test_master_password)}")
        
        # 1. Şifre kaydetme testi
        print("\n📝 Şifre kaydetme testi...")
        success = sm.save_password(test_user_id, test_site, test_username, test_password, test_master_password)
        
        if not success:
            print("❌ Şifre kaydetme başarısız")
            return False
        
        print("✅ Şifre başarıyla kaydedildi")
        
        # 2. Şifre okuma testi (maskeli)
        print("\n👁️ Şifre okuma testi (maskeli)...")
        passwords = sm.get_passwords(test_user_id)
        
        if not passwords or len(passwords) == 0:
            print("❌ Şifre okuma başarısız")
            return False
        
        print(f"✅ {len(passwords)} şifre okundu")
        print(f"   İlk şifre: {passwords[0]['site_name']} - {passwords[0]['username']}")
        
        # 3. Şifre okuma testi (çözülmüş)
        print("\n🔓 Şifre okuma testi (çözülmüş)...")
        passwords = sm.get_passwords(test_user_id, test_master_password)
        
        if not passwords or len(passwords) == 0:
            print("❌ Şifre çözme başarısız")
            return False
        
        # Şifre doğrulama
        if passwords[0]['password'] == test_password:
            print("✅ Şifre doğru çözüldü")
        else:
            print("❌ Şifre yanlış çözüldü")
            print(f"   Beklenen: {test_password}")
            print(f"   Alınan: {passwords[0]['password']}")
            return False
        
        # 4. Şifre silme testi
        print("\n🗑️ Şifre silme testi...")
        delete_success = sm.delete_password(test_user_id, test_site)
        
        if not delete_success:
            print("❌ Şifre silme başarısız")
            return False
        
        print("✅ Şifre başarıyla silindi")
        
        # 5. Silme doğrulama
        passwords_after_delete = sm.get_passwords(test_user_id)
        if len(passwords_after_delete) == 0:
            print("✅ Şifre silme doğrulandı")
        else:
            print("❌ Şifre silme doğrulanamadı")
            return False
        
        # Test veritabanını temizle
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Şifre işlemleri hatası: {e}")
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
        return False

def test_card_operations():
    """Kart işlemleri testi"""
    print("\n💳 Kart İşlemleri Testi:")
    
    try:
        from sqlite_security_manager import SQLiteSecurityManager
        
        # Test veritabanı oluştur
        test_db_path = "test_cards.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        sm = SQLiteSecurityManager(test_db_path)
        
        # Test verileri
        test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_card_name = "Test Kart"
        test_card_number = "1234567890123456"
        test_expiry_date = "12/25"
        test_cardholder = "Test User"
        test_cvv = "123"
        test_notes = "Test kartı"
        test_master_password = "master_password_123"
        
        print(f"🔍 Test kart verileri hazırlandı:")
        print(f"   Card Name: {test_card_name}")
        print(f"   Card Number: {'*' * (len(test_card_number) - 4)} + {test_card_number[-4:]}")
        print(f"   Expiry: {test_expiry_date}")
        print(f"   Cardholder: {test_cardholder}")
        
        # 1. Kart kaydetme testi
        print("\n📝 Kart kaydetme testi...")
        success = sm.save_card(
            test_user_id, test_card_name, test_card_number, 
            test_expiry_date, test_cardholder, test_cvv, 
            test_notes, test_master_password
        )
        
        if not success:
            print("❌ Kart kaydetme başarısız")
            return False
        
        print("✅ Kart başarıyla kaydedildi")
        
        # 2. Kart okuma testi (maskeli)
        print("\n👁️ Kart okuma testi (maskeli)...")
        cards = sm.get_cards(test_user_id)
        
        if not cards or len(cards) == 0:
            print("❌ Kart okuma başarısız")
            return False
        
        print(f"✅ {len(cards)} kart okundu")
        print(f"   İlk kart: {cards[0]['card_name']} - {cards[0]['masked_number']}")
        
        # 3. Kart okuma testi (çözülmüş)
        print("\n🔓 Kart okuma testi (çözülmüş)...")
        cards = sm.get_cards(test_user_id, test_master_password)
        
        if not cards or len(cards) == 0:
            print("❌ Kart çözme başarısız")
            return False
        
        # Kart doğrulama
        if cards[0]['card_number'] == test_card_number:
            print("✅ Kart doğru çözüldü")
        else:
            print("❌ Kart yanlış çözüldü")
            print(f"   Beklenen: {test_card_number}")
            print(f"   Alınan: {cards[0]['card_number']}")
            return False
        
        # 4. Kart silme testi
        print("\n🗑️ Kart silme testi...")
        delete_success = sm.delete_card(test_user_id, test_card_name)
        
        if not delete_success:
            print("❌ Kart silme başarısız")
            return False
        
        print("✅ Kart başarıyla silindi")
        
        # Test veritabanını temizle
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Kart işlemleri hatası: {e}")
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
        return False

def test_access_code_operations():
    """Erişim kodu işlemleri testi"""
    print("\n🔑 Erişim Kodu İşlemleri Testi:")
    
    try:
        from sqlite_security_manager import SQLiteSecurityManager
        
        # Test veritabanı oluştur
        test_db_path = "test_access_codes.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        sm = SQLiteSecurityManager(test_db_path)
        
        # Test verileri
        test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 1. Kod oluşturma testi
        print("\n🔑 Kod oluşturma testi...")
        code = sm.generate_one_time_code(test_user_id)
        
        if not code:
            print("❌ Kod oluşturma başarısız")
            return False
        
        print(f"✅ Kod oluşturuldu: {code[:8]}...")
        
        # 2. Kod doğrulama testi (doğru kod)
        print("\n✅ Kod doğrulama testi (doğru kod)...")
        result = sm.verify_one_time_code(test_user_id, code)
        
        if not result['success']:
            print(f"❌ Kod doğrulama başarısız: {result['message']}")
            return False
        
        print("✅ Kod başarıyla doğrulandı")
        
        # 3. Kod doğrulama testi (yanlış kod)
        print("\n❌ Kod doğrulama testi (yanlış kod)...")
        result = sm.verify_one_time_code(test_user_id, "wrong_code")
        
        if result['success']:
            print("❌ Yanlış kod doğrulandı (hata)")
            return False
        
        print(f"✅ Yanlış kod reddedildi: {result['message']}")
        
        # Test veritabanını temizle
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Erişim kodu işlemleri hatası: {e}")
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
        return False

def test_performance():
    """Performans testi"""
    print("\n⚡ Performans Testi:")
    
    try:
        from sqlite_security_manager import SQLiteSecurityManager
        import time
        
        # Test veritabanı oluştur
        test_db_path = "test_performance.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        sm = SQLiteSecurityManager(test_db_path)
        
        # Test verileri
        test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_master_password = "master_password_123"
        
        # Çoklu şifre kaydetme testi
        print("📝 Çoklu şifre kaydetme testi...")
        start_time = time.time()
        
        for i in range(10):
            site_name = f"site_{i}"
            username = f"user_{i}"
            password = f"password_{i}"
            
            success = sm.save_password(test_user_id, site_name, username, password, test_master_password)
            if not success:
                print(f"❌ Şifre {i} kaydetme başarısız")
                return False
        
        save_time = time.time() - start_time
        print(f"✅ 10 şifre {save_time:.2f} saniyede kaydedildi")
        
        # Şifre okuma testi
        print("👁️ Şifre okuma testi...")
        start_time = time.time()
        
        passwords = sm.get_passwords(test_user_id, test_master_password)
        
        read_time = time.time() - start_time
        print(f"✅ {len(passwords)} şifre {read_time:.2f} saniyede okundu")
        
        # Veritabanı bilgileri
        db_info = sm.get_database_info()
        print(f"📊 Veritabanı boyutu: {db_info['file_size_mb']} MB")
        
        # Test veritabanını temizle
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Performans testi hatası: {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print_test_header()
    
    # Test listesi
    tests = [
        ("SQLite Import Testi", test_sqlite_import),
        ("Veritabanı Oluşturma Testi", test_database_creation),
        ("Şifre İşlemleri Testi", test_password_operations),
        ("Kart İşlemleri Testi", test_card_operations),
        ("Erişim Kodu İşlemleri Testi", test_access_code_operations),
        ("Performans Testi", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
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
        print("\n🎉 Tüm testler başarılı! SQLite sistemi çalışıyor.")
        print("\n💡 Şimdi yapmanız gerekenler:")
        print("1. Web uygulamasını yeniden başlatın")
        print("2. Şifre yöneticisini test edin")
        print("3. Gerçek verilerle test yapın")
    else:
        print(f"\n❌ {total-passed} test başarısız! Sorunları çözün.")
        print("\n🔧 Çözüm önerileri:")
        print("1. Cryptography kütüphanesini kontrol edin")
        print("2. Dosya izinlerini kontrol edin")
        print("3. SQLite desteğini kontrol edin")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        print("\n" + "=" * 60)
        if success:
            print("✅ Test tamamlandı - SQLite sistemi hazır!")
        else:
            print("❌ Test tamamlandı - Sorunlar var!")
    except KeyboardInterrupt:
        print("\n\n⏹️ Test kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"\n\n❌ Beklenmeyen hata: {e}")
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
