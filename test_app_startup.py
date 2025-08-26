#!/usr/bin/env python3
"""
Flask Uygulama Başlatma Testi
Bu script Flask uygulamasının başlatılıp başlatılamadığını test eder
"""

import os
import sys
import traceback
from pathlib import Path

def test_imports():
    """Temel import'ları test et"""
    print("🧪 Temel Import Testleri")
    
    imports_to_test = [
        ("flask", "Flask"),
        ("requests", "HTTP istekleri"),
        ("tweepy", "Twitter API"),
        ("bs4", "BeautifulSoup"),
        ("cryptography", "Şifreleme"),
        ("dotenv", "Environment variables")
    ]
    
    results = {}
    
    for module_name, description in imports_to_test:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'Bilinmiyor')
            print(f"   ✅ {module_name} ({description}): {version}")
            results[module_name] = True
        except ImportError as e:
            print(f"   ❌ {module_name} ({description}): {e}")
            results[module_name] = False
        except Exception as e:
            print(f"   ⚠️ {module_name} ({description}): Beklenmeyen hata - {e}")
            results[module_name] = False
    
    return results

def test_config_files():
    """Konfigürasyon dosyalarını test et"""
    print("\n📁 Konfigürasyon Dosyaları Testi")
    
    config_files = [
        "pythonanywhere_config.py",
        "wsgi.py",
        "wsgi_config_safe.py",
        "requirements_pythonanywhere_minimal.txt"
    ]
    
    results = {}
    
    for file in config_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file}: {size} bytes")
            results[file] = True
        else:
            print(f"   ❌ {file}: Bulunamadı")
            results[file] = False
    
    return results

def test_app_import():
    """Flask uygulamasını import etmeyi test et"""
    print("\n🚀 Flask Uygulama Import Testi")
    
    try:
        # Python path'ini ayarla
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # PythonAnywhere konfigürasyonunu test et
        try:
            from pythonanywhere_config import configure_for_pythonanywhere
            is_pa = configure_for_pythonanywhere()
            print(f"   ✅ PythonAnywhere konfigürasyonu: {is_pa}")
        except ImportError as e:
            print(f"   ⚠️ PythonAnywhere konfigürasyonu bulunamadı: {e}")
        except Exception as e:
            print(f"   ❌ PythonAnywhere konfigürasyon hatası: {e}")
            return False
        
        # Flask uygulamasını import et
        try:
            from app import app
            print("   ✅ Flask uygulaması başarıyla import edildi")
            
            # Uygulama özelliklerini kontrol et
            print(f"   📋 Uygulama adı: {app.name}")
            print(f"   📋 Debug modu: {app.debug}")
            print(f"   📋 Secret key ayarlı: {'Evet' if app.secret_key else 'Hayır'}")
            
            return True
            
        except ImportError as e:
            print(f"   ❌ Flask uygulaması import hatası: {e}")
            print(f"   🔍 Hata detayı: {traceback.format_exc()}")
            return False
        except Exception as e:
            print(f"   ❌ Flask uygulaması yükleme hatası: {e}")
            print(f"   🔍 Hata detayı: {traceback.format_exc()}")
            return False
            
    except Exception as e:
        print(f"   ❌ Genel hata: {e}")
        print(f"   🔍 Hata detayı: {traceback.format_exc()}")
        return False

def test_app_routes():
    """Uygulama route'larını test et"""
    print("\n🛣️ Uygulama Route Testi")
    
    try:
        from app import app
        
        # Temel route'ları kontrol et
        routes = [
            ('/', 'Ana sayfa'),
            ('/login', 'Giriş sayfası'),
            ('/password-manager', 'Şifre yöneticisi')
        ]
        
        for route, description in routes:
            try:
                with app.test_client() as client:
                    response = client.get(route)
                    status = response.status_code
                    if status == 200:
                        print(f"   ✅ {route} ({description}): {status}")
                    elif status == 302:  # Redirect
                        print(f"   ⚠️ {route} ({description}): {status} (Yönlendirme)")
                    else:
                        print(f"   ❌ {route} ({description}): {status}")
            except Exception as e:
                print(f"   ❌ {route} ({description}): Hata - {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Route test hatası: {e}")
        return False

def test_security_manager():
    """Security Manager'ı test et"""
    print("\n🔐 Security Manager Testi")
    
    try:
        from security_manager import SecurityManager
        
        # Security Manager instance'ı oluştur
        sm = SecurityManager()
        print("   ✅ Security Manager başarıyla oluşturuldu")
        
        # Temel fonksiyonları test et
        test_password = "test123"
        test_data = "test data"
        
        # Şifreleme testi
        try:
            encrypted = sm._encrypt_data(test_data, test_password)
            decrypted = sm._decrypt_data(encrypted, test_password)
            
            if decrypted == test_data:
                print("   ✅ Şifreleme/çözme testi başarılı")
            else:
                print("   ❌ Şifreleme/çözme testi başarısız")
                return False
                
        except Exception as e:
            print(f"   ❌ Şifreleme testi hatası: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Security Manager import hatası: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Security Manager test hatası: {e}")
        return False

def test_static_files():
    """Static dosyaları test et"""
    print("\n📂 Static Dosyalar Testi")
    
    static_dirs = [
        "static/css",
        "static/js",
        "static/webfonts"
    ]
    
    static_files = [
        "static/css/twitter-style.css",
        "static/js/bootstrap.bundle.min.js",
        "static/favicon.ico"
    ]
    
    results = {}
    
    # Dizinleri kontrol et
    for dir_path in static_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}: Mevcut")
            results[dir_path] = True
        else:
            print(f"   ❌ {dir_path}: Bulunamadı")
            results[dir_path] = False
    
    # Dosyaları kontrol et
    for file_path in static_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file_path}: {size} bytes")
            results[file_path] = True
        else:
            print(f"   ❌ {file_path}: Bulunamadı")
            results[file_path] = False
    
    return results

def main():
    """Ana test fonksiyonu"""
    print("🧪 Flask Uygulama Başlatma Testi")
    print("=" * 50)
    
    # Testleri çalıştır
    tests = [
        ("Temel Import'lar", test_imports),
        ("Konfigürasyon Dosyaları", test_config_files),
        ("Flask Uygulama Import", test_app_import),
        ("Security Manager", test_security_manager),
        ("Static Dosyalar", test_static_files),
        ("Uygulama Route'ları", test_app_routes)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} testinde hata: {e}")
            results[test_name] = False
    
    # Özet
    print("\n" + "="*50)
    print("📋 Test Sonuçları:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Sonuç: {passed}/{total} test başarılı")
    
    if passed == total:
        print("🎉 Tüm testler başarılı! Uygulama çalışmaya hazır.")
    else:
        print("⚠️ Bazı testler başarısız. Yukarıdaki hataları düzeltin.")
        
        # Öneriler
        print("\n💡 Öneriler:")
        if not results.get("Temel Import'lar", False):
            print("   - Eksik paketleri yükleyin: pip install --user flask requests tweepy beautifulsoup4 cryptography python-dotenv")
        
        if not results.get("Flask Uygulama Import", False):
            print("   - app.py dosyasındaki hataları kontrol edin")
            print("   - PythonAnywhere konfigürasyonunu kontrol edin")
        
        if not results.get("Security Manager", False):
            print("   - security_manager.py dosyasındaki hataları kontrol edin")
        
        if not results.get("Static Dosyalar", False):
            print("   - Static dosyaların mevcut olduğundan emin olun")

if __name__ == "__main__":
    main()
