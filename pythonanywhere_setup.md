# PythonAnywhere Kurulum ve Sorun Giderme Rehberi

## 🚀 PythonAnywhere'de Uygulama Kurulumu

### 1. Dosya Yükleme
```bash
# PythonAnywhere Files sekmesinde:
# - Tüm proje dosyalarını yükleyin
# - static/ klasörünün doğru yüklendiğinden emin olun
# - templates/ klasörünün doğru yüklendiğinden emin olun
```

### 2. Python Paketleri Kurulumu
```bash
# PythonAnywhere Bash Console'da:
pip install --user flask
pip install --user python-dotenv
pip install --user tweepy
pip install --user beautifulsoup4
pip install --user requests
pip install --user feedparser
```

### 3. Web App Konfigürasyonu
```python
# PythonAnywhere Web sekmesinde:
# Source code: /home/kullaniciadi/flask_tweet_app
# Working directory: /home/kullaniciadi/flask_tweet_app
# WSGI configuration file: /var/www/kullaniciadi_pythonanywhere_com_wsgi.py
```

### 4. WSGI Dosyası Düzenleme
```python
# /var/www/kullaniciadi_pythonanywhere_com_wsgi.py dosyasını düzenleyin:

import sys
import os

# Proje dizinini Python path'ine ekle
path = '/home/kullaniciadi/flask_tweet_app'
if path not in sys.path:
    sys.path.append(path)

# Environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'true'
os.environ['USE_LOCAL_ASSETS'] = 'true'
os.environ['DEBUG'] = 'False'

# Flask app'i import et
from app import app as application

# Production ayarları
application.config['PREFERRED_URL_SCHEME'] = 'https'
application.config['SESSION_COOKIE_SECURE'] = True
application.config['SESSION_COOKIE_HTTPONLY'] = True
```

## 🔧 Yaygın Sorunlar ve Çözümleri

### 1. CDN Erişim Sorunları
**Sorun:** Bootstrap/Font Awesome yüklenmiyor
**Çözüm:** 
- CDN fallback sistemi otomatik olarak devreye girer
- Eğer hala sorun varsa, local assets kullanın

### 2. Static Dosya Sorunları
**Sorun:** CSS/JS dosyaları yüklenmiyor
**Çözüm:**
```bash
# PythonAnywhere Files sekmesinde:
# static/ klasörünün doğru konumda olduğunu kontrol edin
# Dosya izinlerini kontrol edin (644)
```

### 3. Environment Variables
**Sorun:** .env dosyası çalışmıyor
**Çözüm:**
```python
# WSGI dosyasında environment variables'ları manuel olarak set edin:
os.environ['TWITTER_BEARER_TOKEN'] = 'your_token_here'
os.environ['OPENROUTER_API_KEY'] = 'your_key_here'
# ... diğer API anahtarları
```

### 4. Database/JSON Dosya Sorunları
**Sorun:** JSON dosyaları yazılamıyor
**Çözüm:**
```bash
# Dosya izinlerini kontrol edin:
chmod 644 *.json
chmod 755 /home/kullaniciadi/flask_tweet_app
```

## 📁 Dosya Yapısı Kontrolü

PythonAnywhere'de dosya yapınız şöyle olmalı:
```
/home/kullaniciadi/flask_tweet_app/
├── app.py
├── utils.py
├── pythonanywhere_config.py
├── requirements.txt
├── .env
├── static/
│   ├── css/
│   │   └── twitter-style.css
│   ├── favicon.ico
│   └── ...
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   └── ...
└── *.json (veri dosyaları)
```

## 🔒 Güvenlik Ayarları

### 1. HTTPS Zorunluluğu
```python
# app.py'de:
if is_pythonanywhere:
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SESSION_COOKIE_SECURE'] = True
```

### 2. Environment Variables
```bash
# Hassas bilgileri .env dosyasında saklayın:
TWITTER_BEARER_TOKEN=your_token
OPENROUTER_API_KEY=your_key
SECRET_KEY=your_secret_key
```

## 🚀 Performans Optimizasyonu

### 1. Static Dosya Caching
```python
# app.py'de:
@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response
```

### 2. Gzip Compression
```python
# PythonAnywhere otomatik olarak gzip compression sağlar
# Ek konfigürasyon gerekmez
```

## 📊 Monitoring ve Debugging

### 1. Error Logs
```bash
# PythonAnywhere Web sekmesinde:
# Error log'ları kontrol edin
# Server log'ları kontrol edin
```

### 2. Debug Mode
```python
# Production'da debug mode'u kapatın:
DEBUG_MODE = False
```

## 🔄 Güncelleme Süreci

### 1. Kod Güncellemesi
```bash
# 1. Yeni dosyaları yükleyin
# 2. Web app'i reload edin
# 3. Error log'ları kontrol edin
```

### 2. Paket Güncellemesi
```bash
# Bash Console'da:
pip install --user --upgrade package_name
```

## 📞 Destek

Sorun yaşarsanız:
1. PythonAnywhere Error Log'larını kontrol edin
2. Console'da test edin
3. Dosya izinlerini kontrol edin
4. Environment variables'ları kontrol edin

## ✅ Kontrol Listesi

- [ ] Tüm dosyalar doğru yüklendi
- [ ] Python paketleri kuruldu
- [ ] WSGI dosyası düzenlendi
- [ ] Environment variables set edildi
- [ ] Web app reload edildi
- [ ] Error log'ları kontrol edildi
- [ ] HTTPS çalışıyor
- [ ] Static dosyalar yükleniyor
- [ ] CDN fallback sistemi çalışıyor 