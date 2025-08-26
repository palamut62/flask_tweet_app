#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere SQLite Basit Kurulum Scripti
"""

import os
import sys
import subprocess
from datetime import datetime

def print_header():
    print("🚀 PythonAnywhere SQLite Kurulum Scripti")
    print("=" * 60)
    print(f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Ortam: {'PythonAnywhere' if 'PYTHONANYWHERE_SITE' in os.environ else 'Local'}")
    print(f"📁 Dizin: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)

def check_pythonanywhere():
    """PythonAnywhere ortamını kontrol et"""
    print("\n🌐 PythonAnywhere Ortam Kontrolü:")
    
    if 'PYTHONANYWHERE_SITE' in os.environ:
        print("✅ PythonAnywhere ortamında çalışıyor")
        return True
    else:
        print("⚠️ Local ortamda çalışıyor (PythonAnywhere değil)")
        return False

def install_cryptography():
    """Cryptography kütüphanesini yükle"""
    print("\n📦 Cryptography Kütüphanesi Kurulumu:")
    
    try:
        print("📥 Cryptography yükleniyor...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "cryptography==41.0.7", "--user"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Cryptography başarıyla yüklendi")
            return True
        else:
            print(f"❌ Cryptography yükleme hatası: {result.stderr}")
            return False
                
    except Exception as e:
        print(f"❌ Yükleme hatası: {e}")
        return False

def check_sqlite():
    """SQLite desteğini kontrol et"""
    print("\n🗄️ SQLite Desteği Kontrolü:")
    
    try:
        import sqlite3
        print("✅ SQLite3 modülü mevcut")
        print(f"📊 SQLite versiyonu: {sqlite3.sqlite_version}")
        
        # Test veritabanı oluştur
        test_db = "test_sqlite.db"
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version()")
        result = cursor.fetchone()
        conn.close()
        
        # Test dosyasını sil
        if os.path.exists(test_db):
            os.remove(test_db)
        
        print(f"✅ SQLite test başarılı: {result[0]}")
        return True
        
    except ImportError:
        print("❌ SQLite3 modülü bulunamadı")
        return False
    except Exception as e:
        print(f"❌ SQLite test hatası: {e}")
        return False

def create_simple_sqlite_manager():
    """Basit SQLite SecurityManager oluştur"""
    print("\n📝 Basit SQLite SecurityManager Oluşturma:")
    
    if os.path.exists("sqlite_security_manager.py"):
        print("✅ sqlite_security_manager.py dosyası mevcut")
        return True
    
    try:
        # SQLite SecurityManager içeriği
        lines = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            '"""',
            "Basit SQLite Security Manager",
            '"""',
            "",
            "import sqlite3",
            "import os",
            "from datetime import datetime",
            "",
            "class SQLiteSecurityManager:",
            "    def __init__(self, db_path=\"passwords.db\"):",
            "        self.db_path = db_path",
            "        self.is_pythonanywhere = 'PYTHONANYWHERE_SITE' in os.environ",
            "        ",
            "        if self.is_pythonanywhere:",
            "            self.db_path = os.path.join(os.getcwd(), \"passwords.db\")",
            "            print(f\"🔍 PythonAnywhere SQLite DB: {self.db_path}\")",
            "        ",
            "        self.init_database()",
            "    ",
            "    def init_database(self):",
            "        with sqlite3.connect(self.db_path) as conn:",
            "            cursor = conn.cursor()",
            "            cursor.execute('''",
            "                CREATE TABLE IF NOT EXISTS passwords (",
            "                    id INTEGER PRIMARY KEY AUTOINCREMENT,",
            "                    user_id TEXT NOT NULL,",
            "                    site_name TEXT NOT NULL,",
            "                    username TEXT NOT NULL,",
            "                    password TEXT NOT NULL,",
            "                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "                )",
            "            ''')",
            "            conn.commit()",
            "            print(\"✅ Veritabanı başlatıldı\")",
            "    ",
            "    def save_password(self, user_id, site_name, username, password, master_password):",
            "        try:",
            "            with sqlite3.connect(self.db_path) as conn:",
            "                cursor = conn.cursor()",
            "                cursor.execute('''",
            "                    INSERT OR REPLACE INTO passwords ",
            "                    (user_id, site_name, username, password)",
            "                    VALUES (?, ?, ?, ?)",
            "                ''', (user_id, site_name, username, password))",
            "                conn.commit()",
            "                print(f\"✅ Şifre kaydedildi: {site_name}\")",
            "                return True",
            "        except Exception as e:",
            "            print(f\"❌ Şifre kaydetme hatası: {e}\")",
            "            return False",
            "    ",
            "    def get_passwords(self, user_id, master_password=None):",
            "        try:",
            "            with sqlite3.connect(self.db_path) as conn:",
            "                cursor = conn.cursor()",
            "                cursor.execute('''",
            "                    SELECT site_name, username, password, created_at",
            "                    FROM passwords WHERE user_id = ?",
            "                    ORDER BY created_at DESC",
            "                ''', (user_id,))",
            "                ",
            "                passwords = []",
            "                for row in cursor.fetchall():",
            "                    passwords.append({",
            "                        'site_name': row[0],",
            "                        'username': row[1],",
            "                        'password': row[2] if master_password else '****',",
            "                        'created_at': row[3]",
            "                    })",
            "                print(f\"✅ {len(passwords)} şifre getirildi\")",
            "                return passwords",
            "        except Exception as e:",
            "            print(f\"❌ Şifre okuma hatası: {e}\")",
            "            return []",
            "    ",
            "    def delete_password(self, user_id, site_name):",
            "        try:",
            "            with sqlite3.connect(self.db_path) as conn:",
            "                cursor = conn.cursor()",
            "                cursor.execute('''",
            "                    DELETE FROM passwords ",
            "                    WHERE user_id = ? AND site_name = ?",
            "                ''', (user_id, site_name))",
            "                conn.commit()",
            "                ",
            "                if cursor.rowcount > 0:",
            "                    print(f\"✅ Şifre silindi: {site_name}\")",
            "                    return True",
            "                else:",
            "                    print(f\"⚠️ Silinecek şifre bulunamadı: {site_name}\")",
            "                    return False",
            "        except Exception as e:",
            "            print(f\"❌ Şifre silme hatası: {e}\")",
            "            return False"
        ]
        
        content = "\n".join(lines)
        
        with open("sqlite_security_manager.py", "w", encoding="utf-8") as f:
            f.write(content)
        
        print("✅ sqlite_security_manager.py dosyası oluşturuldu")
        return True
        
    except Exception as e:
        print(f"❌ Dosya oluşturma hatası: {e}")
        return False

def test_sqlite_system():
    """SQLite sistemini test et"""
    print("\n🧪 SQLite Sistemi Testi:")
    
    try:
        from sqlite_security_manager import SQLiteSecurityManager
        
        # Test veritabanı oluştur
        test_db = "test_setup.db"
        if os.path.exists(test_db):
            os.remove(test_db)
        
        sm = SQLiteSecurityManager(test_db)
        
        # Test şifre kaydet
        success = sm.save_password(
            "test_user", "test_site", "test_user", 
            "test_password", "master_password"
        )
        
        if not success:
            print("❌ Test şifre kaydetme başarısız")
            return False
        
        # Test şifre oku
        passwords = sm.get_passwords("test_user", "master_password")
        
        if len(passwords) == 0:
            print("❌ Test şifre okuma başarısız")
            return False
        
        # Test veritabanını temizle
        if os.path.exists(test_db):
            os.remove(test_db)
        
        print("✅ SQLite sistemi test başarılı")
        return True
        
    except Exception as e:
        print(f"❌ SQLite test hatası: {e}")
        return False

def main():
    """Ana kurulum fonksiyonu"""
    print_header()
    
    # Kurulum adımları
    steps = [
        ("PythonAnywhere Ortam Kontrolü", check_pythonanywhere),
        ("SQLite Desteği Kontrolü", check_sqlite),
        ("Cryptography Kurulumu", install_cryptography),
        ("Basit SQLite SecurityManager Oluşturma", create_simple_sqlite_manager),
        ("SQLite Sistemi Testi", test_sqlite_system)
    ]
    
    results = []
    
    for step_name, step_func in steps:
        try:
            print(f"\n{'='*20} {step_name} {'='*20}")
            result = step_func()
            results.append((step_name, result))
            
            if result:
                print(f"✅ {step_name}: BAŞARILI")
            else:
                print(f"❌ {step_name}: BAŞARISIZ")
                
        except Exception as e:
            print(f"❌ {step_name}: HATA - {e}")
            results.append((step_name, False))
    
    # Sonuç özeti
    print("\n" + "=" * 60)
    print("📊 KURULUM SONUÇLARI:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for step_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{step_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Başarı Oranı: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed >= total - 1:
        print("\n🎉 SQLite kurulumu başarılı!")
        print("\n💡 Şimdi yapmanız gerekenler:")
        print("1. Web uygulamasını yeniden başlatın:")
        print("   - PythonAnywhere Console'da: touch /var/www/umutins62_pythonanywhere_com_wsgi.py")
        print("2. Şifre yöneticisini test edin")
        print("3. Yeni şifreler ekleyin")
    else:
        print(f"\n❌ {total-passed} adım başarısız! Sorunları çözün.")
    
    return passed >= total - 1

if __name__ == "__main__":
    try:
        success = main()
        print("\n" + "=" * 60)
        if success:
            print("✅ Kurulum tamamlandı - SQLite sistemi hazır!")
        else:
            print("❌ Kurulum tamamlandı - Sorunlar var!")
    except KeyboardInterrupt:
        print("\n\n⏹️ Kurulum kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"\n\n❌ Beklenmeyen hata: {e}")
