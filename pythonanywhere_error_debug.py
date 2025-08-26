#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere Şifre Kaydetme Hata Debug
"""

import os
import sys
import traceback
from datetime import datetime

def debug_password_save():
    """Şifre kaydetme işlemini debug et"""
    print("🔍 PythonAnywhere Şifre Kaydetme Debug")
    print("=" * 50)
    
    try:
        # 1. Environment kontrolü
        print("1️⃣ Environment Kontrolü:")
        print(f"   PythonAnywhere: {'PYTHONANYWHERE_SITE' in os.environ}")
        print(f"   Çalışma Dizini: {os.getcwd()}")
        print(f"   Python Versiyonu: {sys.version}")
        
        # 2. SQLite SecurityManager import
        print("\n2️⃣ SQLite SecurityManager Import:")
        try:
            from sqlite_security_manager import SQLiteSecurityManager
            print("   ✅ SQLiteSecurityManager import başarılı")
            
            # SecurityManager oluştur
            sm = SQLiteSecurityManager()
            print(f"   ✅ SecurityManager oluşturuldu: {type(sm).__name__}")
            print(f"   DB Path: {sm.db_path}")
            
        except Exception as e:
            print(f"   ❌ Import hatası: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
            return False
        
        # 3. Test şifre kaydetme
        print("\n3️⃣ Test Şifre Kaydetme:")
        test_user_id = f"debug_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_site = "debug_site"
        test_username = "debug_user"
        test_password = "debug_password_123"
        test_master_password = "debug_master_123"
        
        print(f"   Test User ID: {test_user_id}")
        print(f"   Test Site: {test_site}")
        print(f"   Test Username: {test_username}")
        
        try:
            # Şifre kaydet
            success = sm.save_password(test_user_id, test_site, test_username, test_password, test_master_password)
            print(f"   Şifre kaydetme sonucu: {success}")
            
            if success:
                # Şifreleri getir
                passwords = sm.get_passwords(test_user_id, test_master_password)
                print(f"   Getirilen şifre sayısı: {len(passwords)}")
                
                # Test şifresini sil
                sm.delete_password(test_user_id, test_site)
                print("   ✅ Test şifresi silindi")
                
                return True
            else:
                print("   ❌ Şifre kaydetme başarısız")
                return False
                
        except Exception as e:
            print(f"   ❌ Şifre kaydetme hatası: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
            return False
            
    except Exception as e:
        print(f"❌ Genel hata: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def check_file_permissions():
    """Dosya izinlerini kontrol et"""
    print("\n4️⃣ Dosya İzinleri Kontrolü:")
    
    files_to_check = [
        "passwords.db",
        "sqlite_security_manager.py",
        "app.py"
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            readable = os.access(file, os.R_OK)
            writable = os.access(file, os.W_OK)
            size = os.path.getsize(file)
            print(f"   {file}:")
            print(f"     Okunabilir: {readable}")
            print(f"     Yazılabilir: {writable}")
            print(f"     Boyut: {size} bytes")
        else:
            print(f"   {file}: ❌ Dosya bulunamadı")

def check_database_integrity():
    """Veritabanı bütünlüğünü kontrol et"""
    print("\n5️⃣ Veritabanı Bütünlük Kontrolü:")
    
    try:
        import sqlite3
        conn = sqlite3.connect("passwords.db")
        cursor = conn.cursor()
        
        # Tabloları kontrol et
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   Tablolar: {[table[0] for table in tables]}")
        
        # Her tablodaki kayıt sayısını kontrol et
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':  # Sistem tablosu
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   {table_name}: {count} kayıt")
        
        # Veritabanı bütünlük kontrolü
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        print(f"   Bütünlük kontrolü: {integrity}")
        
        conn.close()
        print("   ✅ Veritabanı bütünlük kontrolü başarılı")
        
    except Exception as e:
        print(f"   ❌ Veritabanı kontrol hatası: {e}")

def main():
    """Ana debug fonksiyonu"""
    print("🐍 PythonAnywhere Şifre Kaydetme Debug")
    print("=" * 60)
    
    # Dosya izinleri kontrolü
    check_file_permissions()
    
    # Veritabanı bütünlük kontrolü
    check_database_integrity()
    
    # Şifre kaydetme debug
    success = debug_password_save()
    
    print("\n📊 Debug Sonucu:")
    print("=" * 30)
    if success:
        print("✅ Tüm testler başarılı!")
        print("💡 Sorun web uygulamasında başka bir yerde olabilir")
    else:
        print("❌ Hata tespit edildi!")
        print("💡 Yukarıdaki hata mesajlarını kontrol edin")

if __name__ == "__main__":
    main()
