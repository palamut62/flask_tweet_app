#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere SQLite Security Manager
Bu modül PythonAnywhere'de çalışacak şekilde optimize edilmiştir
"""

import sqlite3
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
import base64

# Cryptography için güvenli import
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    hashes = None
    PBKDF2HMAC = None

class SQLiteSecurityManager:
    def __init__(self, db_path="passwords.db"):
        self.db_path = db_path
        self.is_pythonanywhere = 'PYTHONANYWHERE_SITE' in os.environ
        
        # PythonAnywhere için özel ayarlar
        if self.is_pythonanywhere:
            # PythonAnywhere'de dosya yolu
            self.db_path = os.path.join(os.getcwd(), "passwords.db")
            print(f"🔍 PythonAnywhere SQLite DB: {self.db_path}")
        
        self.init_database()
        
    def _log(self, message, level="info"):
        """Logging sistemi"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        prefix = f"[{timestamp}] [SQLiteSecurityManager]"
        
        if level == "error":
            print(f"❌ {prefix} {message}")
        elif level == "warning":
            print(f"⚠️ {prefix} {message}")
        elif level == "success":
            print(f"✅ {prefix} {message}")
        else:
            print(f"ℹ️ {prefix} {message}")
    
    def init_database(self):
        """Veritabanını başlat ve tabloları oluştur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # PythonAnywhere için timeout ayarı
                conn.execute("PRAGMA busy_timeout = 30000")
                
                cursor = conn.cursor()
                
                # Users tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Passwords tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS passwords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        site_name TEXT NOT NULL,
                        username TEXT NOT NULL,
                        encrypted_data TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        UNIQUE(user_id, site_name)
                    )
                ''')
                
                # Cards tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        card_name TEXT NOT NULL,
                        encrypted_number TEXT NOT NULL,
                        masked_number TEXT NOT NULL,
                        expiry_date TEXT NOT NULL,
                        cardholder_name TEXT NOT NULL,
                        cvv TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        UNIQUE(user_id, card_name)
                    )
                ''')
                
                # Access codes tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS access_codes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        code_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        used BOOLEAN DEFAULT FALSE,
                        attempts INTEGER DEFAULT 0,
                        verified_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                ''')
                
                conn.commit()
                self._log("Veritabanı başarıyla başlatıldı", "success")
                
        except Exception as e:
            self._log(f"Veritabanı başlatma hatası: {e}", "error")
            raise
    
    def get_or_create_user(self, session_id):
        """Kullanıcıyı al veya oluştur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA busy_timeout = 30000")
                cursor = conn.cursor()
                
                # Kullanıcıyı kontrol et
                cursor.execute('SELECT id FROM users WHERE session_id = ?', (session_id,))
                user = cursor.fetchone()
                
                if user:
                    return user[0]
                else:
                    # Yeni kullanıcı oluştur
                    cursor.execute('INSERT INTO users (session_id) VALUES (?)', (session_id,))
                    conn.commit()
                    user_id = cursor.lastrowid
                    self._log(f"Yeni kullanıcı oluşturuldu: {user_id}", "success")
                    return user_id
                    
        except Exception as e:
            self._log(f"Kullanıcı oluşturma hatası: {e}", "error")
            raise
    
    def _generate_key_from_password(self, password: str, salt: bytes) -> bytes:
        if not CRYPTOGRAPHY_AVAILABLE:
            self._log("Cryptography kütüphanesi yüklü değil", "error")
            raise ImportError("Cryptography kütüphanesi yüklü değil")
        
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return key
        except Exception as e:
            self._log(f"Anahtar oluşturma hatası: {e}", "error")
            raise
    
    def _encrypt_data(self, data: str, password: str) -> dict:
        if not CRYPTOGRAPHY_AVAILABLE:
            self._log("Cryptography kütüphanesi yüklü değil", "error")
            raise ImportError("Cryptography kütüphanesi yüklü değil")
        
        try:
            salt = os.urandom(16)
            key = self._generate_key_from_password(password, salt)
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data.encode())
            
            result = {
                'encrypted_data': base64.b64encode(encrypted_data).decode(),
                'salt': base64.b64encode(salt).decode(),
                'created_at': datetime.now().isoformat()
            }
            
            self._log("Veri başarıyla şifrelendi", "success")
            return result
            
        except Exception as e:
            self._log(f"Şifreleme hatası: {e}", "error")
            raise
    
    def _decrypt_data(self, encrypted_dict: dict, password: str) -> str:
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                self._log("Cryptography kütüphanesi yüklü değil", "error")
                raise ImportError("Cryptography kütüphanesi yüklü değil")
            
            encrypted_data = base64.b64decode(encrypted_dict['encrypted_data'])
            salt = base64.b64decode(encrypted_dict['salt'])
            
            key = self._generate_key_from_password(password, salt)
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            return decrypted_data.decode()
            
        except Exception as e:
            self._log(f"Şifre çözme hatası: {e}", "error")
            raise
    
    def save_password(self, user_session_id: str, site_name: str, username: str, password: str, master_password: str) -> bool:
        """Şifreyi SQLite'a kaydet"""
        try:
            self._log(f"Şifre kaydetme başlatıldı - User: {user_session_id[:8]}..., Site: {site_name}", "info")
            
            # Parametre kontrolü
            if not all([user_session_id, site_name, username, password, master_password]):
                self._log("Eksik parametreler", "error")
                return False
            
            user_id = self.get_or_create_user(user_session_id)
            encrypted_data = self._encrypt_data(password, master_password)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA busy_timeout = 30000")
                cursor = conn.cursor()
                
                # Şifreyi kaydet veya güncelle
                cursor.execute('''
                    INSERT OR REPLACE INTO passwords 
                    (user_id, site_name, username, encrypted_data, salt, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, site_name, username, 
                    encrypted_data['encrypted_data'], 
                    encrypted_data['salt'],
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                self._log(f"Şifre başarıyla kaydedildi: {site_name}", "success")
                return True
                
        except Exception as e:
            self._log(f"Şifre kaydetme hatası: {e}", "error")
            import traceback
            self._log(f"Hata detayı: {traceback.format_exc()}", "error")
            return False
    
    def get_passwords(self, user_session_id: str, master_password: str = None) -> list:
        """Kullanıcının şifrelerini getir"""
        try:
            user_id = self.get_or_create_user(user_session_id)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA busy_timeout = 30000")
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT site_name, username, encrypted_data, salt, created_at, updated_at
                    FROM passwords WHERE user_id = ?
                    ORDER BY updated_at DESC
                ''', (user_id,))
                
                passwords = []
                for row in cursor.fetchall():
                    site_name, username, encrypted_data, salt, created_at, updated_at = row
                    
                    # Şifre çözme kontrolü
                    if master_password:
                        try:
                            decrypted_password = self._decrypt_data({
                                'encrypted_data': encrypted_data,
                                'salt': salt
                            }, master_password)
                            password_display = decrypted_password
                            self._log(f"Şifre çözüldü: {site_name}", "success")
                        except Exception as e:
                            password_display = "****"
                            self._log(f"Şifre çözme hatası {site_name}: {e}", "error")
                    else:
                        password_display = "****"
                        self._log(f"Şifre maskelendi: {site_name}", "info")
                    
                    passwords.append({
                        'site_name': site_name,
                        'username': username,
                        'password': password_display,
                        'created_at': created_at,
                        'updated_at': updated_at
                    })
                
                self._log(f"{len(passwords)} şifre getirildi", "success")
                return passwords
                
        except Exception as e:
            self._log(f"Şifre okuma hatası: {e}", "error")
            return []
    
    def delete_password(self, user_session_id: str, site_name: str) -> bool:
        """Şifreyi sil"""
        try:
            user_id = self.get_or_create_user(user_session_id)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA busy_timeout = 30000")
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM passwords 
                    WHERE user_id = ? AND site_name = ?
                ''', (user_id, site_name))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self._log(f"Şifre silindi: {site_name}", "success")
                    return True
                else:
                    self._log(f"Silinecek şifre bulunamadı: {site_name}", "warning")
                    return False
                    
        except Exception as e:
            self._log(f"Şifre silme hatası: {e}", "error")
            return False
    
    def save_card(self, user_session_id: str, card_name: str, card_number: str, expiry_date: str, cardholder_name: str, cvv: str = None, notes: str = None, master_password: str = None) -> bool:
        """Kart bilgilerini kaydet"""
        try:
            user_id = self.get_or_create_user(user_session_id)
            encrypted_number = self._encrypt_data(card_number, master_password)
            masked_number = "**** **** **** " + card_number[-4:] if len(card_number) >= 4 else card_number
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA busy_timeout = 30000")
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cards 
                    (user_id, card_name, encrypted_number, masked_number, expiry_date, cardholder_name, cvv, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, card_name, encrypted_number['encrypted_data'], 
                    masked_number, expiry_date, cardholder_name, cvv, notes,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                self._log(f"Kart kaydedildi: {card_name}", "success")
                return True
                
        except Exception as e:
            self._log(f"Kart kaydetme hatası: {e}", "error")
            return False
    
    def get_cards(self, user_session_id: str, master_password: str = None) -> list:
        """Kullanıcının kartlarını getir"""
        try:
            user_id = self.get_or_create_user(user_session_id)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA busy_timeout = 30000")
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT card_name, encrypted_number, masked_number, expiry_date, cardholder_name, cvv, notes, created_at, updated_at
                    FROM cards WHERE user_id = ?
                    ORDER BY updated_at DESC
                ''', (user_id,))
                
                cards = []
                for row in cursor.fetchall():
                    card_name, encrypted_number, masked_number, expiry_date, cardholder_name, cvv, notes, created_at, updated_at = row
                    
                    # Kart numarası çözme kontrolü
                    if master_password:
                        try:
                            decrypted_number = self._decrypt_data({
                                'encrypted_data': encrypted_number,
                                'salt': ''  # Salt ayrı saklanmıyor, basit şifreleme
                            }, master_password)
                            display_number = decrypted_number
                            self._log(f"Kart çözüldü: {card_name}", "success")
                        except:
                            display_number = masked_number
                            self._log(f"Kart çözme hatası: {card_name}", "error")
                    else:
                        display_number = masked_number
                        self._log(f"Kart maskelendi: {card_name}", "info")
                    
                    cards.append({
                        'card_name': card_name,
                        'card_number': display_number,
                        'masked_number': masked_number,
                        'expiry_date': expiry_date,
                        'cardholder_name': cardholder_name,
                        'cvv': cvv,
                        'notes': notes,
                        'created_at': created_at,
                        'updated_at': updated_at
                    })
                
                self._log(f"{len(cards)} kart getirildi", "success")
                return cards
                
        except Exception as e:
            self._log(f"Kart okuma hatası: {e}", "error")
            return []
    
    def delete_card(self, user_session_id: str, card_name: str) -> bool:
        """Kartı sil"""
        try:
            user_id = self.get_or_create_user(user_session_id)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA busy_timeout = 30000")
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM cards 
                    WHERE user_id = ? AND card_name = ?
                ''', (user_id, card_name))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self._log(f"Kart silindi: {card_name}", "success")
                    return True
                else:
                    self._log(f"Silinecek kart bulunamadı: {card_name}", "warning")
                    return False
                    
        except Exception as e:
            self._log(f"Kart silme hatası: {e}", "error")
            return False
    
    def generate_one_time_code(self, user_session_id: str) -> str:
        """Erişim kodu oluştur"""
        try:
            user_id = self.get_or_create_user(user_session_id)
            code = secrets.token_hex(16)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA busy_timeout = 30000")
                cursor = conn.cursor()
                
                # Eski kodu temizle
                cursor.execute('DELETE FROM access_codes WHERE user_id = ?', (user_id,))
                
                # Yeni kod oluştur
                cursor.execute('''
                    INSERT INTO access_codes 
                    (user_id, code_hash, expires_at)
                    VALUES (?, ?, ?)
                ''', (
                    user_id, 
                    hashlib.sha256(code.encode()).hexdigest(),
                    (datetime.now() + timedelta(hours=24)).isoformat()
                ))
                
                conn.commit()
                self._log("Erişim kodu oluşturuldu", "success")
                return code
                
        except Exception as e:
            self._log(f"Kod oluşturma hatası: {e}", "error")
            return None
    
    def verify_one_time_code(self, user_session_id: str, code: str) -> dict:
        """Erişim kodunu doğrula"""
        try:
            user_id = self.get_or_create_user(user_session_id)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA busy_timeout = 30000")
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT code_hash, expires_at, used, attempts
                    FROM access_codes WHERE user_id = ?
                ''', (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return {
                        'success': False,
                        'error': 'no_code',
                        'message': 'Hiç erişim kodunuz yok'
                    }
                
                code_hash, expires_at, used, attempts = result
                
                # Kod kullanıldı mı kontrol et
                if used:
                    return {
                        'success': False,
                        'error': 'used_code',
                        'message': 'Bu kod zaten kullanılmış'
                    }
                
                # Süre doldu mu kontrol et
                expires_at_dt = datetime.fromisoformat(expires_at)
                if datetime.now() > expires_at_dt:
                    cursor.execute('UPDATE access_codes SET used = TRUE WHERE user_id = ?', (user_id,))
                    conn.commit()
                    return {
                        'success': False,
                        'error': 'expired_code',
                        'message': 'Kod süresi dolmuş'
                    }
                
                # 3 yanlış denemeden sonra kodu geçersiz kıl
                if attempts >= 3:
                    cursor.execute('UPDATE access_codes SET used = TRUE WHERE user_id = ?', (user_id,))
                    conn.commit()
                    return {
                        'success': False,
                        'error': 'max_attempts',
                        'message': 'Çok fazla yanlış deneme. Kod iptal edildi.'
                    }
                
                # Kodu kontrol et
                code_hash_check = hashlib.sha256(code.encode()).hexdigest()
                if code_hash_check == code_hash:
                    # DOĞRU KOD - başarıyla doğrulandı
                    cursor.execute('''
                        UPDATE access_codes 
                        SET used = TRUE, verified_at = ? 
                        WHERE user_id = ?
                    ''', (datetime.now().isoformat(), user_id))
                    conn.commit()
                    return {
                        'success': True,
                        'message': 'Kod başarıyla doğrulandı'
                    }
                else:
                    # YANLIŞ KOD - deneme sayısını artır
                    cursor.execute('''
                        UPDATE access_codes 
                        SET attempts = attempts + 1 
                        WHERE user_id = ?
                    ''', (user_id,))
                    conn.commit()
                    
                    remaining_attempts = 3 - (attempts + 1)
                    return {
                        'success': False,
                        'error': 'wrong_code',
                        'message': f'Yanlış kod. Kalan deneme: {remaining_attempts}',
                        'remaining_attempts': remaining_attempts
                    }
                    
        except Exception as e:
            self._log(f"Kod doğrulama hatası: {e}", "error")
            return {
                'success': False,
                'error': 'system_error',
                'message': 'Sistem hatası oluştu'
            }
    
    def clear_user_data(self, user_session_id: str) -> dict:
        """Kullanıcının tüm verilerini temizle"""
        try:
            user_id = self.get_or_create_user(user_session_id)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA busy_timeout = 30000")
                cursor = conn.cursor()
                
                # Şifreleri say
                cursor.execute('SELECT COUNT(*) FROM passwords WHERE user_id = ?', (user_id,))
                passwords_count = cursor.fetchone()[0]
                
                # Kartları say
                cursor.execute('SELECT COUNT(*) FROM cards WHERE user_id = ?', (user_id,))
                cards_count = cursor.fetchone()[0]
                
                # Tüm verileri sil
                cursor.execute('DELETE FROM passwords WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM cards WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM access_codes WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                
                conn.commit()
                
                deleted_data = {
                    'passwords_count': passwords_count,
                    'cards_count': cards_count,
                    'access_codes_cleared': True
                }
                
                self._log(f"Kullanıcı verileri temizlendi: {deleted_data}", "success")
                return deleted_data
                
        except Exception as e:
            self._log(f"Veri temizleme hatası: {e}", "error")
            return {
                'passwords_count': 0,
                'cards_count': 0,
                'access_codes_cleared': False
            }
    
    def get_database_info(self) -> dict:
        """Veritabanı bilgilerini getir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Kullanıcı sayısı
                cursor.execute('SELECT COUNT(*) FROM users')
                users_count = cursor.fetchone()[0]
                
                # Şifre sayısı
                cursor.execute('SELECT COUNT(*) FROM passwords')
                passwords_count = cursor.fetchone()[0]
                
                # Kart sayısı
                cursor.execute('SELECT COUNT(*) FROM cards')
                cards_count = cursor.fetchone()[0]
                
                # Dosya boyutu
                file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    'users_count': users_count,
                    'passwords_count': passwords_count,
                    'cards_count': cards_count,
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'db_path': self.db_path,
                    'is_pythonanywhere': self.is_pythonanywhere
                }
                
        except Exception as e:
            self._log(f"Veritabanı bilgi hatası: {e}", "error")
            return {
                'error': str(e),
                'db_path': self.db_path,
                'is_pythonanywhere': self.is_pythonanywhere
            }
