#!/usr/bin/env python3
"""
Şifre Yönetici Güvenlik Testi
Bu script, güvenlik yöneticisinin tüm özelliklerini test eder.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# SecurityManager'ı import et
try:
    from security_manager import SecurityManager
    print("✅ SecurityManager başarıyla import edildi")
except ImportError as e:
    print(f"❌ SecurityManager import hatası: {e}")
    sys.exit(1)

def test_security_manager():
    """Güvenlik yöneticisini test et"""
    print("\n🔐 Şifre Yönetici Güvenlik Testi Başlatılıyor...")
    print("=" * 60)
    
    # Test için geçici dosyalar
    test_data_dir = "test_security_data"
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir)
    
    # SecurityManager instance oluştur
    sm = SecurityManager(test_data_dir)
    test_user_id = "test_user_123"
    
    print(f"📁 Test veri dizini: {test_data_dir}")
    print(f"👤 Test kullanıcı ID: {test_user_id}")
    
    # Test 1: Erişim kodu oluşturma
    print("\n🧪 Test 1: Erişim Kodu Oluşturma")
    print("-" * 40)
    
    try:
        access_code = sm.generate_one_time_code(test_user_id)
        print(f"✅ Erişim kodu oluşturuldu: {len(access_code)} karakter")
        print(f"📝 Kod (ilk 8 karakter): {access_code[:8]}...")
        
        # Kod durumunu kontrol et
        has_active = sm.has_active_access_code(test_user_id)
        remaining = sm.get_remaining_attempts(test_user_id)
        print(f"🔍 Aktif kod var mı: {has_active}")
        print(f"🔢 Kalan deneme: {remaining}")
        
    except Exception as e:
        print(f"❌ Kod oluşturma hatası: {e}")
        return False
    
    # Test 2: Doğru kod doğrulama
    print("\n🧪 Test 2: Doğru Kod Doğrulama")
    print("-" * 40)
    
    try:
        result = sm.verify_one_time_code(test_user_id, access_code)
        if result['success']:
            print("✅ Doğru kod başarıyla doğrulandı")
        else:
            print(f"❌ Kod doğrulama başarısız: {result['message']}")
            return False
    except Exception as e:
        print(f"❌ Kod doğrulama hatası: {e}")
        return False
    
    # Test 3: Yanlış kod denemeleri
    print("\n🧪 Test 3: Yanlış Kod Denemeleri")
    print("-" * 40)
    
    # Yeni kod oluştur (önceki kullanıldı)
    new_code = sm.generate_one_time_code(test_user_id)
    
    # 2 yanlış deneme
    for i in range(2):
        wrong_code = "wrong_code_" + str(i)
        result = sm.verify_one_time_code(test_user_id, wrong_code)
        remaining = sm.get_remaining_attempts(test_user_id)
        print(f"❌ Yanlış kod denemesi {i+1}: {result['message']}")
        print(f"🔢 Kalan deneme: {remaining}")
    
    # Test 4: 3. yanlış deneme (veri silme)
    print("\n🧪 Test 4: 3. Yanlış Deneme (Veri Silme)")
    print("-" * 40)
    
    # Önce test verisi ekle
    test_password = "test123"
    sm.save_password(test_user_id, "test_site", "test_user", "test_pass", test_password)
    sm.save_card(test_user_id, "test_card", "1234567890123456", "12/25", "TEST USER", test_password)
    
    print("📝 Test verileri eklendi (1 şifre, 1 kart)")
    
    # 3. yanlış deneme
    wrong_code = "final_wrong_code"
    result = sm.verify_one_time_code(test_user_id, wrong_code)
    
    if result.get('data_deleted', False):
        deleted_data = result.get('deleted_data', {})
        print(f"🚨 3. yanlış deneme sonrası veriler silindi!")
        print(f"🗑️ Silinen şifreler: {deleted_data.get('passwords_count', 0)}")
        print(f"🗑️ Silinen kartlar: {deleted_data.get('cards_count', 0)}")
        print("✅ Güvenlik özelliği çalışıyor!")
    else:
        print(f"❌ Veri silme özelliği çalışmıyor: {result}")
        return False
    
    # Test 5: Yeni kod oluşturma
    print("\n🧪 Test 5: Yeni Kod Oluşturma")
    print("-" * 40)
    
    try:
        final_code = sm.generate_one_time_code(test_user_id)
        print(f"✅ Yeni kod oluşturuldu: {len(final_code)} karakter")
        
        # Doğru kod ile test
        result = sm.verify_one_time_code(test_user_id, final_code)
        if result['success']:
            print("✅ Yeni kod başarıyla doğrulandı")
        else:
            print(f"❌ Yeni kod doğrulama başarısız: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Yeni kod oluşturma hatası: {e}")
        return False
    
    # Test 6: Zaman aşımı kontrolü
    print("\n🧪 Test 6: Zaman Aşımı Kontrolü")
    print("-" * 40)
    
    # Test için geçici dosya oluştur
    test_expired_user = "expired_user"
    expired_code = sm.generate_one_time_code(test_expired_user)
    
    # Dosyayı manuel olarak süresi dolmuş olarak işaretle
    access_codes = sm._load_json(sm.access_codes_file, {})
    if test_expired_user in access_codes:
        access_codes[test_expired_user]['expires_at'] = (datetime.now() - timedelta(hours=1)).isoformat()
        sm._save_json(sm.access_codes_file, access_codes)
        print("⏰ Test kodu süresi dolmuş olarak işaretlendi")
        
        # Süresi dolmuş kodu test et
        result = sm.verify_one_time_code(test_expired_user, expired_code)
        if result['error'] == 'expired_code':
            print("✅ Zaman aşımı kontrolü çalışıyor")
        else:
            print(f"❌ Zaman aşımı kontrolü çalışmıyor: {result}")
            return False
    
    # Temizlik
    print("\n🧹 Test Verilerini Temizleme")
    print("-" * 40)
    
    try:
        # Test dosyalarını sil
        import shutil
        if os.path.exists(test_data_dir):
            shutil.rmtree(test_data_dir)
            print(f"✅ Test veri dizini silindi: {test_data_dir}")
    except Exception as e:
        print(f"⚠️ Temizlik hatası (önemli değil): {e}")
    
    print("\n🎉 Tüm Testler Başarıyla Tamamlandı!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_security_manager()
    if success:
        print("\n✅ Güvenlik Yöneticisi tüm testleri geçti!")
        sys.exit(0)
    else:
        print("\n❌ Güvenlik Yöneticisi testlerde başarısız!")
        sys.exit(1)
