#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere SQLite Test Script
"""

import os
import sqlite3
from datetime import datetime

def check_pythonanywhere_environment():
    """PythonAnywhere ortamını kontrol et"""
    print("🔍 PythonAnywhere Ortam Kontrolü")
    print("=" * 40)
    
    # PythonAnywhere ortam değişkenleri
    is_pythonanywhere = 'PYTHONANYWHERE_SITE' in os.environ
    print(f"PythonAnywhere: {is_pythonanywhere}")
    
    if is_pythonanywhere:
        print(f"Site: {os.environ.get('PYTHONANYWHERE_SITE', 'Bilinmiyor')}")
        print(f"Username: {os.environ.get('PYTHONANYWHERE_USERNAME', 'Bilinmiyor')}")
    
    # Çalışma dizini
    cwd = os.getcwd()
    print(f"Çalışma Dizini: {cwd}")
    
    # Dosya izinleri
    print(f"Dizin yazılabilir: {os.access(cwd, os.W_OK)}")
    
    return is_pythonanywhere, cwd

def check_sqlite_availability():
    """SQLite kullanılabilirliğini kontrol et"""
    print("\n💾 SQLite Kontrolü")
    print("=" * 40)
    
    try:
        # SQLite versiyonu
        version = sqlite3.sqlite_version
        print(f"SQLite Versiyonu: {version}")
        
        # Test veritabanı oluştur
        test_db = "test_sqlite.db"
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Basit tablo oluştur
        cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER, name TEXT)")
        cursor.execute("INSERT INTO test VALUES (1, 'test')")
        result = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        # Test dosyasını sil
        os.remove(test_db)
        
        print("✅ SQLite çalışıyor")
        return True
        
    except Exception as e:
        print(f"❌ SQLite hatası: {e}")
        return False

def check_passwords_db():
    """passwords.db dosyasını kontrol et"""
    print("\n🔐 Passwords.db Kontrolü")
    print("=" * 40)
    
    db_path = "passwords.db"
    
    # Dosya varlığı
    if os.path.exists(db_path):
        print(f"✅ {db_path} mevcut")
        
        # Dosya boyutu
        size = os.path.getsize(db_path)
        print(f"Dosya boyutu: {size} bytes")
        
        # Dosya izinleri
        readable = os.access(db_path, os.R_OK)
        writable = os.access(db_path, os.W_OK)
        print(f"Okunabilir: {readable}")
        print(f"Yazılabilir: {writable}")
        
        # Veritabanı bağlantısı test et
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Tabloları listele
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tablolar: {[table[0] for table in tables]}")
            
            # Kayıt sayılarını kontrol et
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  {table_name}: {count} kayıt")
            
            conn.close()
            print("✅ Veritabanı bağlantısı başarılı")
            return True
            
        except Exception as e:
            print(f"❌ Veritabanı bağlantı hatası: {e}")
            return False
    else:
        print(f"❌ {db_path} bulunamadı")
        return False

def test_security_manager():
    """SecurityManager'ı test et"""
    print("\n🛡️ SecurityManager Testi")
    print("=" * 40)
    
    try:
        from sqlite_security_manager import SQLiteSecurityManager
        
        # SecurityManager oluştur
        sm = SQLiteSecurityManager()
        print(f"SecurityManager türü: {type(sm).__name__}")
        print(f"DB Path: {sm.db_path}")
        
        # Test kullanıcısı oluştur
        test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_site = "test_site"
        test_username = "test_user"
        test_password = "test_password_123"
        test_master_password = "master_password_123"
        
        print(f"Test kullanıcısı: {test_user_id}")
        
        # Şifre kaydet
        success = sm.save_password(test_user_id, test_site, test_username, test_password, test_master_password)
        print(f"Şifre kaydetme: {'✅ Başarılı' if success else '❌ Başarısız'}")
        
        if success:
            # Şifreleri getir
            passwords = sm.get_passwords(test_user_id, test_master_password)
            print(f"Şifre sayısı: {len(passwords)}")
            
            # Test şifresini sil
            sm.delete_password(test_user_id, test_site)
            print("✅ Test şifresi silindi")
        
        return success
        
    except Exception as e:
        print(f"❌ SecurityManager hatası: {e}")
        import traceback
        print(f"Hata detayı: {traceback.format_exc()}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🐍 PythonAnywhere SQLite Test")
    print("=" * 50)
    
    # 1. Ortam kontrolü
    is_pa, cwd = check_pythonanywhere_environment()
    
    # 2. SQLite kontrolü
    sqlite_ok = check_sqlite_availability()
    
    # 3. Passwords.db kontrolü
    db_ok = check_passwords_db()
    
    # 4. SecurityManager testi
    sm_ok = test_security_manager()
    
    # Sonuç
    print("\n📊 Test Sonuçları")
    print("=" * 40)
    print(f"PythonAnywhere: {'✅' if is_pa else '❌'}")
    print(f"SQLite: {'✅' if sqlite_ok else '❌'}")
    print(f"Passwords.db: {'✅' if db_ok else '❌'}")
    print(f"SecurityManager: {'✅' if sm_ok else '❌'}")
    
    if all([sqlite_ok, db_ok, sm_ok]):
        print("\n🎉 Tüm testler başarılı!")
    else:
        print("\n⚠️ Bazı testler başarısız. Yukarıdaki hataları kontrol edin.")

if __name__ == "__main__":
    main()
