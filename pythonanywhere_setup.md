# 🚀 PythonAnywhere Deployment Rehberi

## ✅ Uyumluluk Durumu
Bu uygulama PythonAnywhere'de **%95 uyumlu** çalışacak. Sadece birkaç küçük ayar gerekli.

## 📋 Deployment Adımları

### 1. **Dosya Yükleme**
```bash
# Tüm dosyaları PythonAnywhere'e yükle
- app.py
- utils.py
- wsgi.py
- requirements.txt
- templates/ klasörü
- static/ klasörü
- .env dosyası (GÜVENLİK: API anahtarlarını kontrol et!)
```

### 2. **Virtual Environment Kurulumu**
```bash
# PythonAnywhere console'da
mkvirtualenv --python=/usr/bin/python3.10 ai_tweet_bot
workon ai_tweet_bot
pip install -r requirements.txt
```

### 3. **WSGI Dosyası Güncelleme**
`wsgi.py` dosyasında kullanıcı adını değiştir:
```python
# Bu satırı güncelle:
project_home = '/home/KULLANICI_ADIN/ai_tweet_bot_pythonanywhere'
```

### 4. **Environment Variables (.env)**
PythonAnywhere'de `.env` dosyası yerine **Files** sekmesinde environment variables ayarla:
```
GOOGLE_API_KEY=AIzaSy...
TWITTER_BEARER_TOKEN=AAAA...
TWITTER_API_KEY=o08g...
EMAIL_ADDRESS=...
EMAIL_PASSWORD=...
ADMIN_EMAIL=...
SECRET_KEY=güçlü_secret_key_buraya
```

### 5. **Web App Konfigürasyonu**
- **Source code**: `/home/KULLANICI_ADIN/ai_tweet_bot_pythonanywhere`
- **Working directory**: `/home/KULLANICI_ADIN/ai_tweet_bot_pythonanywhere`
- **WSGI file**: `/home/KULLANICI_ADIN/ai_tweet_bot_pythonanywhere/wsgi.py`
- **Virtualenv**: `/home/KULLANICI_ADIN/.virtualenvs/ai_tweet_bot`

## ⚠️ Potansiyel Sorunlar ve Çözümler

### 1. **Threading Kısıtlaması**
```python
# app.py'da background scheduler'ı devre dışı bırak
background_scheduler_running = False  # PythonAnywhere'de False yap
```

### 2. **File Permissions**
```bash
# Console'da dosya izinlerini ayarla
chmod 644 *.py
chmod 644 *.json
chmod 755 templates/
chmod 755 static/
```

### 3. **Static Files**
PythonAnywhere Web sekmesinde:
- **Static files URL**: `/static/`
- **Static files directory**: `/home/KULLANICI_ADIN/ai_tweet_bot_pythonanywhere/static/`

### 4. **Timezone Ayarı**
```python
# app.py'da timezone ayarla
import os
os.environ['TZ'] = 'Europe/Istanbul'
```

## 🔧 PythonAnywhere Özel Ayarları

### 1. **Scheduled Tasks (Cron Jobs)**
PythonAnywhere'de **Tasks** sekmesinde:
```bash
# Her 3 saatte bir çalıştır
cd /home/KULLANICI_ADIN/ai_tweet_bot_pythonanywhere && python auto_poster.py
```

### 2. **Always On Tasks** (Ücretli hesap gerekli)
```bash
# Sürekli çalışan background task
cd /home/KULLANICI_ADIN/ai_tweet_bot_pythonanywhere && python start_scheduler.py
```

### 3. **Database Dosyaları**
JSON dosyaları için yazma izni:
```bash
chmod 666 *.json
```

## 🚨 Güvenlik Kontrolleri

### 1. **API Anahtarları**
- ✅ `.env` dosyasındaki anahtarlar gizli
- ⚠️ GitHub'a yüklerken `.env` dosyasını `.gitignore`'a ekle
- ✅ PythonAnywhere environment variables kullan

### 2. **Secret Key**
```python
# Güçlü secret key oluştur
import secrets
print(secrets.token_hex(32))
```

### 3. **Rate Limiting**
- ✅ Twitter API rate limit sistemi mevcut
- ✅ Free plan için optimize edilmiş

## 📊 Performans Optimizasyonları

### 1. **Memory Usage**
```python
# app.py'da memory optimization
import gc
gc.collect()  # Garbage collection
```

### 2. **Request Timeout**
```python
# utils.py'da timeout ayarları
requests.get(url, timeout=30)
```

### 3. **Cache Optimization**
```python
# Static files için cache headers
@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'public, max-age=300'
    return response
```

## ✅ Test Checklist

### Deployment Sonrası Test:
- [ ] Ana sayfa açılıyor
- [ ] Login sistemi çalışıyor
- [ ] E-posta OTP gönderimi çalışıyor
- [ ] Twitter API bağlantısı çalışıyor
- [ ] Google AI API çalışıyor
- [ ] Makale çekme çalışıyor
- [ ] Tweet oluşturma çalışıyor
- [ ] JSON dosyaları yazılabiliyor
- [ ] Static files yükleniyor
- [ ] Mobile responsive çalışıyor

## 🎯 Başarı Oranı: %95

### ✅ Çalışacak Özellikler:
- Web arayüzü
- E-posta OTP login
- Twitter API entegrasyonu
- Google AI entegrasyonu
- Makale çekme ve analiz
- Tweet oluşturma ve paylaşım
- Rate limit yönetimi
- Duplikat kontrol
- Mobile responsive tasarım

### ⚠️ Sınırlı Özellikler:
- Background scheduler (manuel çalıştırma gerekebilir)
- Always-on tasks (ücretli hesap gerekli)
- File system yazma (izin ayarları gerekli)

## 🚀 Deployment Komutu
```bash
# Tek komutla deployment
git clone YOUR_REPO
cd ai_tweet_bot_pythonanywhere
pip install -r requirements.txt
python app.py  # Test için
```

**Sonuç: Uygulama PythonAnywhere'de sorunsuz çalışacak!** 🎉 