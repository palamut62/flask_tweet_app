#!/usr/bin/env python3
"""
PythonAnywhere Log Kontrol Scripti
Bu script PythonAnywhere'de log durumunu kontrol eder
"""

import os
import sys
import subprocess
from datetime import datetime

def check_pythonanywhere_logs():
    """PythonAnywhere log durumunu kontrol et"""
    print("🔍 PythonAnywhere Log Kontrolü")
    print("=" * 50)
    
    # 1. Çalışma dizini kontrolü
    print(f"📁 Çalışma dizini: {os.getcwd()}")
    
    # 2. Python versiyonu
    print(f"🐍 Python versiyonu: {sys.version}")
    
    # 3. Environment değişkenleri
    print("\n🔧 Environment Değişkenleri:")
    env_vars = ['PYTHONANYWHERE_SITE', 'PYTHONANYWHERE_DOMAIN', 'FLASK_ENV', 'DEBUG']
    for var in env_vars:
        value = os.environ.get(var, 'Tanımlı değil')
        print(f"  {var}: {value}")
    
    # 4. WSGI dosyası kontrolü
    wsgi_files = ['wsgi.py', 'wsgi_config_safe.py']
    print("\n📄 WSGI Dosyaları:")
    for wsgi_file in wsgi_files:
        if os.path.exists(wsgi_file):
            size = os.path.getsize(wsgi_file)
            print(f"  ✅ {wsgi_file}: {size} bytes")
        else:
            print(f"  ❌ {wsgi_file}: Bulunamadı")
    
    # 5. Log dosyaları kontrolü
    print("\n📋 Log Dosyaları:")
    log_files = [
        'scheduler.log',
        'app.log',
        'error.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            print(f"  ✅ {log_file}: {size} bytes (Son güncelleme: {mtime})")
            
            # Son 5 satırı göster
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"    Son 5 satır:")
                        for line in lines[-5:]:
                            print(f"      {line.strip()}")
            except Exception as e:
                print(f"    ❌ Log okuma hatası: {e}")
        else:
            print(f"  ❌ {log_file}: Bulunamadı")
    
    # 6. PythonAnywhere özel log yolları
    print("\n🌐 PythonAnywhere Web Log Yolları:")
    pythonanywhere_logs = [
        '/var/log/umutins62_pythonanywhere_com.error.log',
        '/var/log/umutins62_pythonanywhere_com.access.log',
        '/var/log/umutins62_pythonanywhere_com.server.log'
    ]
    
    for log_path in pythonanywhere_logs:
        if os.path.exists(log_path):
            size = os.path.getsize(log_path)
            mtime = datetime.fromtimestamp(os.path.getmtime(log_path))
            print(f"  ✅ {log_path}: {size} bytes (Son güncelleme: {mtime})")
        else:
            print(f"  ❌ {log_path}: Erişim yok veya bulunamadı")
    
    # 7. Flask uygulama durumu
    print("\n🚀 Flask Uygulama Durumu:")
    try:
        import flask
        print(f"  ✅ Flask versiyonu: {flask.__version__}")
    except ImportError as e:
        print(f"  ❌ Flask import hatası: {e}")
    
    # 8. WSGI test
    print("\n🔧 WSGI Test:")
    try:
        sys.path.insert(0, os.getcwd())
        from app import app
        print("  ✅ Flask uygulaması başarıyla import edildi")
        print(f"  📋 Debug modu: {app.debug}")
        print(f"  🔑 Secret key ayarlı: {'Evet' if app.secret_key else 'Hayır'}")
    except Exception as e:
        print(f"  ❌ WSGI test hatası: {e}")
        print(f"  🔍 Hata detayı: {type(e).__name__}")

def create_log_monitor():
    """Log izleme scripti oluştur"""
    monitor_script = '''#!/usr/bin/env python3
"""
PythonAnywhere Log İzleyici
Bu script sürekli olarak log dosyalarını izler
"""

import os
import time
import subprocess
from datetime import datetime

def monitor_logs():
    """Log dosyalarını sürekli izle"""
    print("👀 Log İzleme Başlatıldı...")
    print("Ctrl+C ile durdurun")
    
    # İzlenecek dosyalar
    log_files = [
        'scheduler.log',
        'app.log',
        'error.log'
    ]
    
    # Dosya pozisyonları
    positions = {}
    
    while True:
        try:
            for log_file in log_files:
                if os.path.exists(log_file):
                    current_size = os.path.getsize(log_file)
                    
                    if log_file not in positions:
                        positions[log_file] = current_size
                        print(f"📄 {log_file} izleniyor...")
                    elif current_size > positions[log_file]:
                        # Yeni içerik var
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(positions[log_file])
                            new_content = f.read()
                            if new_content.strip():
                                print(f"\\n🆕 {log_file} - {datetime.now()}:")
                                print(new_content)
                        
                        positions[log_file] = current_size
            
            time.sleep(2)  # 2 saniye bekle
            
        except KeyboardInterrupt:
            print("\\n⏹️ Log izleme durduruldu")
            break
        except Exception as e:
            print(f"❌ Log izleme hatası: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_logs()
'''
    
    with open('log_monitor.py', 'w', encoding='utf-8') as f:
        f.write(monitor_script)
    
    print("✅ log_monitor.py oluşturuldu")
    print("Kullanım: python log_monitor.py")

if __name__ == "__main__":
    check_pythonanywhere_logs()
    print("\n" + "=" * 50)
    create_log_monitor()
    
    print("\n📋 Öneriler:")
    print("1. PythonAnywhere Web sekmesinde 'Log files' bölümünü kontrol edin")
    print("2. 'Reload' butonuna basın ve hataları izleyin")
    print("3. Konsol'da 'python log_monitor.py' çalıştırın")
    print("4. WSGI dosyasını 'wsgi_config_safe.py' olarak değiştirin")
