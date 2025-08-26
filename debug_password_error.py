#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere Şifre Kaydetme Hatası Ayıklama Scripti
Bu script şifre kaydetme sorununu detaylı olarak analiz eder
"""

import os
import sys
import json
import traceback
from datetime import datetime

def print_debug_header():
    print("🔍 PythonAnywhere Şifre Kaydetme Hatası Ayıklama")
    print("=" * 70)
    print(f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Ortam: {'PythonAnywhere' if 'PYTHONANYWHERE_SITE' in os.environ else 'Local'}")
    print(f"📁 Dizin: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 70)

def check_environment():
    """Ortam kontrolü"""
    print("\n🌐 ORTAM KONTROLÜ:")
    
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
    
    # Gerekli dosyalar
    required_files = ["app.py", "security_manager.py"]
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} mevcut")
        else:
            print(f"❌ {file} bulunamadı")
            return False
    
    return True

def check_cryptography():
    """Cryptography kütüphanesi kontrolü"""
    print("\n🔐 CRYPTOGRAPHY KONTROLÜ:")
    
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

def check_json_files():
    """JSON dosyaları kontrolü"""
    print("\n📄 JSON DOSYALARI KONTROLÜ:")
    
    files_to_check = [
        "user_passwords.json",
        "user_cards.json",
        "access_codes.json"
    ]
    
    all_success = True
    
    for filename in files_to_check:
        try:
            if os.path.exists(filename):
                # Dosya boyutu kontrolü
                file_size = os.path.getsize(filename)
                print(f"📁 {filename} mevcut ({file_size} bytes)")
                
                # Dosya okuma testi
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ {filename} okunabilir")
                
                # Dosya yazma testi
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ {filename} yazılabilir")
                
                # İzin kontrolü
                if os.access(filename, os.W_OK):
                    print(f"✅ {filename} yazma izni var")
                else:
                    print(f"❌ {filename} yazma izni yok")
                    all_success = False
                
            else:
                print(f"📄 {filename} mevcut değil, oluşturuluyor...")
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=2)
                    os.chmod(filename, 0o644)
                    print(f"✅ {filename} oluşturuldu")
                except Exception as e:
                    print(f"❌ {filename} oluşturma hatası: {e}")
                    all_success = False
                
        except json.JSONDecodeError as e:
            print(f"❌ {filename} JSON parse hatası: {e}")
            all_success = False
        except Exception as e:
            print(f"❌ {filename} test hatası: {e}")
            all_success = False
    
    return all_success

def test_security_manager_detailed():
    """SecurityManager detaylı testi"""
    print("\n🔐 SECURITYMANAGER DETAYLI TESTİ:")
    
    try:
        from security_manager import SecurityManager
        
        # Instance oluştur
        print("🔍 SecurityManager instance oluşturuluyor...")
        sm = SecurityManager()
        print("✅ SecurityManager instance oluşturuldu")
        
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
        
        # Şifre kaydetme testi
        print("\n🔐 Şifre kaydetme testi başlatılıyor...")
        success = sm.save_password(test_user_id, test_site, test_username, test_password, test_master_password)
        
        if success:
            print("✅ Test şifresi başarıyla kaydedildi")
            
            # Şifre okuma testi
            print("🔓 Şifre okuma testi başlatılıyor...")
            passwords = sm.get_passwords(test_user_id, test_master_password)
            
            if passwords and len(passwords) > 0:
                print(f"✅ Test şifresi başarıyla okundu: {passwords[0]['site_name']}")
                
                # Şifre çözme testi
                if passwords[0]['password'] == test_password:
                    print("✅ Şifre çözme testi başarılı")
                else:
                    print("❌ Şifre çözme testi başarısız")
                    print(f"   Beklenen: {test_password}")
                    print(f"   Alınan: {passwords[0]['password']}")
                    return False
                
                # Test verilerini temizle
                print("🗑️ Test verileri temizleniyor...")
                sm.delete_password(test_user_id, test_site)
                print("✅ Test verileri temizlendi")
                
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

def check_file_permissions():
    """Dosya izinleri kontrolü"""
    print("\n🔐 DOSYA İZİNLERİ KONTROLÜ:")
    
    files_to_check = [
        "user_passwords.json",
        "user_cards.json",
        "access_codes.json",
        "security_manager.py",
        "app.py"
    ]
    
    for filename in files_to_check:
        if os.path.exists(filename):
            try:
                # Dosya izinlerini al
                stat_info = os.stat(filename)
                mode = stat_info.st_mode
                
                # İzinleri kontrol et
                readable = os.access(filename, os.R_OK)
                writable = os.access(filename, os.W_OK)
                executable = os.access(filename, os.X_OK)
                
                print(f"📁 {filename}:")
                print(f"   Okunabilir: {'✅' if readable else '❌'}")
                print(f"   Yazılabilir: {'✅' if writable else '❌'}")
                print(f"   Çalıştırılabilir: {'✅' if executable else '❌'}")
                print(f"   Boyut: {stat_info.st_size} bytes")
                
                if not writable:
                    print(f"   ⚠️ {filename} yazılamıyor!")
                    
            except Exception as e:
                print(f"❌ {filename} izin kontrolü hatası: {e}")
        else:
            print(f"📄 {filename} mevcut değil")

def simulate_password_save():
    """Şifre kaydetme işlemini simüle et"""
    print("\n🧪 ŞİFRE KAYDETME SİMÜLASYONU:")
    
    try:
        from security_manager import SecurityManager
        
        # Test verileri
        test_user_id = "debug_test_user"
        test_site = "debug_test_site"
        test_username = "debug_user"
        test_password = "debug_password_123"
        test_master_password = "debug_master_123"
        
        print("🔍 Simülasyon başlatılıyor...")
        print(f"   Test User ID: {test_user_id}")
        print(f"   Test Site: {test_site}")
        
        # SecurityManager instance
        sm = SecurityManager()
        
        # JSON dosyasını kontrol et
        print("\n📄 JSON dosyası kontrol ediliyor...")
        if os.path.exists(sm.passwords_file):
            with open(sm.passwords_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            print(f"✅ Mevcut veri: {len(current_data)} kullanıcı")
        else:
            print("📄 JSON dosyası mevcut değil, oluşturulacak")
            current_data = {}
        
        # Şifre kaydetme simülasyonu
        print("\n🔐 Şifre kaydetme simülasyonu...")
        success = sm.save_password(test_user_id, test_site, test_username, test_password, test_master_password)
        
        if success:
            print("✅ Simülasyon başarılı!")
            
            # Sonucu kontrol et
            passwords = sm.get_passwords(test_user_id, test_master_password)
            if passwords and len(passwords) > 0:
                print("✅ Kaydedilen şifre doğrulandı")
                
                # Temizlik
                sm.delete_password(test_user_id, test_site)
                print("✅ Test verileri temizlendi")
                
                return True
            else:
                print("❌ Kaydedilen şifre doğrulanamadı")
                return False
        else:
            print("❌ Simülasyon başarısız!")
            return False
            
    except Exception as e:
        print(f"❌ Simülasyon hatası: {e}")
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
        return False

def main():
    """Ana fonksiyon"""
    print_debug_header()
    
    # Test listesi
    tests = [
        ("Ortam Kontrolü", check_environment),
        ("Cryptography Kontrolü", check_cryptography),
        ("JSON Dosyaları Kontrolü", check_json_files),
        ("Dosya İzinleri Kontrolü", check_file_permissions),
        ("SecurityManager Detaylı Testi", test_security_manager_detailed),
        ("Şifre Kaydetme Simülasyonu", simulate_password_save)
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
    print("\n" + "=" * 70)
    print("📊 AYIKLAMA SONUÇLARI:")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Başarı Oranı: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 Tüm testler başarılı! Sistem çalışıyor.")
        print("\n💡 Öneriler:")
        print("1. Web uygulamasını yeniden başlatın")
        print("2. Şifre yöneticisini test edin")
        print("3. Hala sorun varsa, error loglarını kontrol edin")
    else:
        print(f"\n❌ {total-passed} test başarısız! Sorunları çözün.")
        print("\n🔧 Çözüm önerileri:")
        print("1. Cryptography kütüphanesini yeniden yükleyin:")
        print("   pip install cryptography==41.0.7 --user")
        print("2. JSON dosya izinlerini düzeltin:")
        print("   chmod 644 *.json")
        print("3. Uygulamayı yeniden başlatın")
        print("4. Error loglarını kontrol edin")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        print("\n" + "=" * 70)
        if success:
            print("✅ Ayıklama tamamlandı - Sistem hazır!")
        else:
            print("❌ Ayıklama tamamlandı - Sorunlar tespit edildi!")
    except KeyboardInterrupt:
        print("\n\n⏹️ Ayıklama kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"\n\n❌ Beklenmeyen hata: {e}")
        print(f"🔍 Hata detayı: {traceback.format_exc()}")
