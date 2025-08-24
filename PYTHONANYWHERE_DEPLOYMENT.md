# PythonAnywhere Deployment Rehberi

## 🚀 PythonAnywhere'de AI Tweet Bot Kurulumu

### 1. **Hesap Oluşturma**
- [PythonAnywhere.com](https://www.pythonanywhere.com) adresine gidin
- Ücretsiz hesap oluşturun

### 2. **Proje Yükleme**
```bash
# PythonAnywhere konsolunda
cd ~
git clone https://github.com/your-username/flask_tweet_app.git
cd flask_tweet_app
```

### 3. **Gerekli Paketleri Yükleme**
```bash
pip install --user -r requirements.txt
```

### 4. **Otomatik Kurulum Scripti Çalıştırma**
```bash
python setup_pythonanywhere.py
```

Bu script otomatik olarak:
- Gerekli paketleri yükler
- Static dosyaları indirir
- Environment dosyası oluşturur
- Test scripti oluşturur
- Tüm kontrolleri yapar

### 5. **Manuel Static Dosyaları İndirme (Alternatif)**
```bash
python download_static_files.py
```

### 6. **Environment Variables Ayarlama**
PythonAnywhere konsolunda:
```bash
# .env dosyası oluştur
nano .env
```

Aşağıdaki değişkenleri ekleyin:
```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
OPENROUTER_API_KEY=your-openrouter-api-key
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
GOOGLE_API_KEY=your-google-api-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
USE_LOCAL_ASSETS=true
```

### 7. **WSGI Dosyası Ayarlama**
PythonAnywhere Web sekmesinde:
- **Source code**: `/home/yourusername/flask_tweet_app`
- **Working directory**: `/home/yourusername/flask_tweet_app`

WSGI dosyasını düzenleyin:
```python
#!/usr/bin/env python3
import sys
import os

# Proje dizinini Python path'ine ekle
project_home = '/home/yourusername/flask_tweet_app'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Environment değişkenlerini yükle
os.environ.setdefault('FLASK_ENV', 'production')

# Flask uygulamasını import et
from app import app as application

if __name__ == "__main__":
    application.run()
```

### 8. **Static Files Ayarlama**
PythonAnywhere Web sekmesinde:
- **URL**: `/static/`
- **Directory**: `/home/yourusername/flask_tweet_app/static`

### 9. **Uygulamayı Başlatma**
- **Reload** butonuna tıklayın
- Uygulama `https://yourusername.pythonanywhere.com` adresinde çalışacak

## 🔧 Sorun Giderme

### **Tasarım Sorunları**
1. **Static dosyalar yüklenmiyor**: Static files ayarlarını kontrol edin
2. **CDN bağlantı sorunları**: Local dosyalar kullanılıyor, CDN'e gerek yok
3. **Font Awesome ikonları görünmüyor**: Webfonts klasörünü kontrol edin

### **Yaygın Hatalar**
- **Import Error**: Python path'ini kontrol edin
- **Environment Variables**: .env dosyasını kontrol edin
- **Static Files 404**: Static files mapping'ini kontrol edin

## 📁 Dosya Yapısı
```
flask_tweet_app/
├── app.py
├── wsgi.py
├── requirements.txt
├── .env
├── static/
│   ├── css/
│   │   ├── bootstrap.min.css
│   │   ├── all.min.css (Font Awesome)
│   │   └── twitter-style.css
│   ├── js/
│   │   └── bootstrap.bundle.min.js
│   └── webfonts/
│       ├── fa-solid-900.woff2
│       ├── fa-regular-400.woff2
│       └── fa-brands-400.woff2
└── templates/
    ├── base.html
    ├── index.html
    └── ...
```

## ✅ Kontrol Listesi
- [ ] Git repository klonlandı
- [ ] Otomatik kurulum scripti çalıştırıldı (`python setup_pythonanywhere.py`)
- [ ] Test scripti başarılı (`python test_pythonanywhere.py`)
- [ ] Environment variables ayarlandı
- [ ] WSGI dosyası düzenlendi
- [ ] Static files mapping yapıldı
- [ ] Uygulama reload edildi
- [ ] Tasarım doğru görünüyor
- [ ] API'ler çalışıyor

## 🆘 Destek
Sorun yaşarsanız:
1. PythonAnywhere konsol loglarını kontrol edin
2. Web sekmesindeki error loglarını kontrol edin
3. Static files mapping'ini doğrulayın
4. Environment variables'ları kontrol edin
