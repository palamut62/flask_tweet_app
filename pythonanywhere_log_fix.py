#!/usr/bin/env python3
"""
PythonAnywhere Log Hatası Çözüm Scripti
Bu script PythonAnywhere'deki log sorunlarını çözer
"""

import os
import sys
import subprocess
from datetime import datetime

def fix_pythonanywhere_logs():
    """PythonAnywhere log sorunlarını çöz"""
    print("🔧 PythonAnywhere Log Hatası Çözümü")
    print("=" * 50)
    
    # 1. Environment değişkenlerini ayarla
    print("🔧 Environment değişkenleri ayarlanıyor...")
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('DEBUG', 'False')
    os.environ.setdefault('PYTHONANYWHERE_MODE', 'True')
    
    # 2. Python path'i düzelt
    print("🐍 Python path düzeltiliyor...")
    project_home = os.getcwd()
    user_site = '/home/umutins62/.local/lib/python3.10/site-packages'
    
    if project_home not in sys.path:
        sys.path.insert(0, project_home)
        print(f"  ✅ Proje dizini eklendi: {project_home}")
    
    if user_site not in sys.path:
        sys.path.insert(0, user_site)
        print(f"  ✅ User site-packages eklendi: {user_site}")
    
    # 3. Paketleri kontrol et ve yükle
    print("\n📦 Paket kontrolü...")
    required_packages = [
        'cryptography==41.0.7',
        'fpdf2==2.8.3',
        'Flask==2.3.3',
        'requests==2.31.0',
        'tweepy==4.14.0',
        'beautifulsoup4==4.12.2'
    ]
    
    for package in required_packages:
        try:
            package_name = package.split('==')[0]
            __import__(package_name.replace('-', '_'))
            print(f"  ✅ {package_name}: Yüklü")
        except ImportError:
            print(f"  ❌ {package_name}: Yüklü değil")
            print(f"     Yükleme komutu: pip install --user {package}")
    
    # 4. WSGI dosyasını güncelle
    print("\n📄 WSGI dosyası güncelleniyor...")
    wsgi_content = '''import sys
import os

# Proje dizinini Python path'ine ekle
project_home = '/home/umutins62/flask_tweet_app'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# User site-packages dizinini ekle
user_site = '/home/umutins62/.local/lib/python3.10/site-packages'
if user_site not in sys.path:
    sys.path.insert(0, user_site)

# Environment değişkenlerini ayarla
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DEBUG', 'False')
os.environ.setdefault('PYTHONANYWHERE_MODE', 'True')

# Flask uygulamasını import et
try:
    from app import app as application
    print("✅ Flask uygulaması başarıyla yüklendi")
except ImportError as e:
    print(f"❌ Import hatası: {e}")
    # Hata durumunda basit bir uygulama döndür
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return f"""
        <h1>❌ Uygulama Hatası</h1>
        <p>Hata: {str(e)}</p>
        <p>Lütfen paketleri yükleyin: pip install --user cryptography==41.0.7</p>
        """
    @application.route('/health')
    def health_check():
        return {"status": "error", "message": str(e)}
'''
    
    with open('wsgi_fixed.py', 'w', encoding='utf-8') as f:
        f.write(wsgi_content)
    
    print("  ✅ wsgi_fixed.py oluşturuldu")
    
    # 5. Test uygulaması oluştur
    print("\n🧪 Test uygulaması oluşturuluyor...")
    test_app_content = '''from flask import Flask, jsonify
import sys
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "Test uygulaması çalışıyor",
        "python_path": sys.path[:3],
        "working_dir": os.getcwd(),
        "environment": {
            "FLASK_ENV": os.environ.get('FLASK_ENV'),
            "DEBUG": os.environ.get('DEBUG'),
            "PYTHONANYWHERE_MODE": os.environ.get('PYTHONANYWHERE_MODE')
        }
    })

@app.route('/test-imports')
def test_imports():
    results = {}
    
    # Test imports
    try:
        import flask
        results['flask'] = f"✅ {flask.__version__}"
    except ImportError as e:
        results['flask'] = f"❌ {e}"
    
    try:
        import cryptography
        results['cryptography'] = "✅ Yüklü"
    except ImportError as e:
        results['cryptography'] = f"❌ {e}"
    
    try:
        import fpdf
        results['fpdf'] = "✅ Yüklü"
    except ImportError as e:
        results['fpdf'] = f"❌ {e}"
    
    try:
        import requests
        results['requests'] = "✅ Yüklü"
    except ImportError as e:
        results['requests'] = f"❌ {e}"
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
'''
    
    with open('test_app.py', 'w', encoding='utf-8') as f:
        f.write(test_app_content)
    
    print("  ✅ test_app.py oluşturuldu")
    
    # 6. Log dosyası oluştur
    print("\n📋 Log dosyası oluşturuluyor...")
    log_content = f"""PythonAnywhere Log Hatası Çözümü - {datetime.now()}
==================================================
Bu dosya PythonAnywhere'de log hatalarını çözmek için oluşturuldu.

Adımlar:
1. PythonAnywhere Web sekmesinde WSGI dosyasını 'wsgi_fixed.py' olarak değiştirin
2. 'Reload' butonuna basın
3. Hataları kontrol edin

Paket yükleme komutları:
pip install --user cryptography==41.0.7
pip install --user fpdf2==2.8.3
pip install --user Flask==2.3.3

Test komutları:
python test_app.py
python -c "from app import app; print('✅ Uygulama import başarılı')"
"""
    
    with open('pythonanywhere_fix_log.txt', 'w', encoding='utf-8') as f:
        f.write(log_content)
    
    print("  ✅ pythonanywhere_fix_log.txt oluşturuldu")

def create_deployment_guide():
    """Deployment rehberi oluştur"""
    guide_content = """# PythonAnywhere Deployment Rehberi

## 🚀 Adım Adım Deployment

### 1. Paketleri Yükleyin
```bash
pip install --user cryptography==41.0.7
pip install --user fpdf2==2.8.3
pip install --user Flask==2.3.3
pip install --user requests==2.31.0
pip install --user tweepy==4.14.0
pip install --user beautifulsoup4==4.12.2
```

### 2. WSGI Dosyasını Değiştirin
PythonAnywhere Web sekmesinde:
- Code bölümünde WSGI dosyasını `wsgi_fixed.py` olarak değiştirin
- Reload butonuna basın

### 3. Test Edin
```bash
python test_app.py
```

### 4. Log Hatalarını Kontrol Edin
- PythonAnywhere Web sekmesinde "Log files" bölümüne gidin
- "Error log" linkine tıklayın
- Hataları inceleyin

### 5. Sorun Giderme
Eğer hala hata alıyorsanız:
1. Konsol'da `python -c "import cryptography; print('OK')"` çalıştırın
2. WSGI dosyasını `wsgi_config_safe.py` olarak deneyin
3. PythonAnywhere'de "Files" sekmesinde dosyaları kontrol edin

## 🔧 Hata Çözümleri

### ModuleNotFoundError: No module named 'cryptography'
```bash
pip install --user cryptography==41.0.7
```

### ModuleNotFoundError: No module named 'fpdf'
```bash
pip install --user fpdf2==2.8.3
```

### 500 Internal Server Error
1. WSGI dosyasını kontrol edin
2. Python path'i düzeltin
3. Paketleri yeniden yükleyin

## 📞 Destek
Sorun devam ederse:
1. PythonAnywhere error loglarını kontrol edin
2. Konsol'da test komutlarını çalıştırın
3. WSGI dosyasını basitleştirin
"""
    
    with open('PYTHONANYWHERE_DEPLOYMENT_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ PYTHONANYWHERE_DEPLOYMENT_GUIDE.md oluşturuldu")

if __name__ == "__main__":
    fix_pythonanywhere_logs()
    create_deployment_guide()
    
    print("\n" + "=" * 50)
    print("🎯 SONRAKI ADIMLAR:")
    print("1. PythonAnywhere Web sekmesinde WSGI dosyasını 'wsgi_fixed.py' olarak değiştirin")
    print("2. 'Reload' butonuna basın")
    print("3. 'Log files' bölümünde hataları kontrol edin")
    print("4. Konsol'da 'python test_app.py' çalıştırın")
    print("5. Eğer hala sorun varsa: pip install --user cryptography==41.0.7")
