# AI Tweet Bot - PythonAnywhere Kurulum Rehberi

Bu rehber, AI Tweet Bot uygulamasını PythonAnywhere'de nasıl kuracağınızı adım adım açıklar.

## 📋 Ön Gereksinimler

- PythonAnywhere hesabı (ücretsiz veya ücretli)
- GitHub hesabı ve bu projenin repository'si
- Gerekli API anahtarları (Twitter, Google, OpenRouter, vb.)

## 🚀 Kurulum Adımları

### 1. PythonAnywhere'de Bash Console Açın

1. PythonAnywhere dashboard'a girin
2. **"Tasks"** sekmesine tıklayın
3. **"Bash"** console açın

### 2. Projeyi GitHub'dan Klonlayın

```bash
# Ana dizine gidin
cd ~

# Projeyi klonlayın
git clone https://github.com/KULLANICI_ADINIZ/ai_tweet_bot_pythonanywhere.git flask_tweet_app

# Proje dizinine gidin
cd flask_tweet_app
```

### 3. Virtual Environment Oluşturun

```bash
# Mevcut Python sürümlerini kontrol edin
ls /usr/bin/python*

# Virtual environment oluşturun (python3.10 önerilen)
python3.10 -m venv venv

# Virtual environment'ı aktifleştirin
source venv/bin/activate

# Pip'i güncelleyin
pip install --upgrade pip
```

### 4. Dependencies Yükleyin

```bash
# Requirements dosyasından paketleri yükleyin
pip install -r requirements.txt

# Eğer hata alırsanız, tek tek yükleyin:
pip install flask python-dotenv requests beautifulsoup4 tweepy
pip install google-generativeai openai selenium webdriver-manager
pip install feedparser python-telegram-bot schedule
```

### 5. Environment Variables Ayarlayın

```bash
# .env dosyası oluşturun
nano .env
```

`.env` dosyasına şu içeriği ekleyin:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
DEBUG=False

# Google Gemini API
GOOGLE_API_KEY=your-google-api-key

# OpenRouter API
OPENROUTER_API_KEY=your-openrouter-api-key

# Twitter API v2
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
TWITTER_ACCESS_TOKEN=your-twitter-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-twitter-access-token-secret

# Telegram Bot (Opsiyonel)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

# Gmail Notifications (Opsiyonel)
GMAIL_EMAIL=your-gmail@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password

# Admin Email (Giriş için)
ADMIN_EMAIL=your-admin@email.com
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-email-app-password

# GitHub API (Opsiyonel)
GITHUB_TOKEN=your-github-token
```

**Ctrl+X** → **Y** → **Enter** ile kaydedin.

### 6. Gerekli Dizinleri Oluşturun

```bash
# Log dizini oluşturun
mkdir -p logs

# Static uploads dizini oluşturun
mkdir -p static/uploads

# JSON dosyalarını oluşturun
touch posted_articles.json
touch pending_tweets.json
touch automation_settings.json
touch news_sources.json

# Boş JSON dosyalarını başlatın
echo "[]" > posted_articles.json
echo "[]" > pending_tweets.json
echo "{}" > automation_settings.json
echo '{"sources": [], "rss_sources": []}' > news_sources.json
```

### 7. Web App Oluşturun

1. PythonAnywhere dashboard'da **"Web"** sekmesine gidin
2. **"Add a new web app"** tıklayın
3. **"Manual configuration"** seçin
4. **"Python 3.10"** seçin
5. **"Next"** tıklayın

### 8. WSGI Dosyasını Yapılandırın

1. Web sekmesinde **"WSGI configuration file"** linkine tıklayın
2. Dosyanın içeriğini tamamen silin
3. Aşağıdaki içeriği yapıştırın:

```python
#!/usr/bin/python3

import sys
import os
from dotenv import load_dotenv

# Add your project directory to the Python path
project_home = '/home/umutins62/flask_tweet_app'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Add the virtual environment site-packages to the Python path
venv_path = '/home/umutins62/flask_tweet_app/venv/lib/python3.10/site-packages'
if venv_path not in sys.path:
    sys.path = [venv_path] + sys.path

# Load environment variables
env_path = os.path.join(project_home, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Set Flask environment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', 'False')

# Change to project directory
os.chdir(project_home)

# Import Flask application
from app import app as application

# Configure application for production
application.config['DEBUG'] = False
application.config['TESTING'] = False
```

4. **"Save"** tıklayın

### 9. Static Files Yapılandırın

Web sekmesinde **"Static files"** bölümünde:

- **URL**: `/static/`
- **Directory**: `/home/umutins62/flask_tweet_app/static/`

**"Save"** tıklayın.

### 10. Virtual Environment Ayarlayın

Web sekmesinde **"Virtualenv"** bölümünde:

- **Path**: `/home/umutins62/flask_tweet_app/venv/`

**"Save"** tıklayın.

### 11. Uygulamayı Başlatın

1. Web sekmesinde **"Reload"** butonuna tıklayın
2. **"Configuration"** sekmesinde yeşil **"Reload"** butonuna tıklayın
3. Uygulamanızın URL'sine gidin: `https://umutins62.pythonanywhere.com`

## 🔧 Sorun Giderme

### Yaygın Hatalar ve Çözümleri

#### 1. "ModuleNotFoundError"
```bash
# Virtual environment'ı aktifleştirin
source ~/flask_tweet_app/venv/bin/activate

# Eksik modülü yükleyin
pip install module-name
```

#### 2. "Permission Denied"
```bash
# Dosya izinlerini düzeltin
chmod +x ~/flask_tweet_app/app.py
chmod +x ~/flask_tweet_app/wsgi_config.py
```

#### 3. ".env dosyası bulunamadı"
```bash
# .env dosyasının varlığını kontrol edin
ls -la ~/flask_tweet_app/.env

# Yoksa oluşturun
touch ~/flask_tweet_app/.env
```

#### 4. "Static files yüklenmiyor"
- Web sekmesinde Static files ayarlarını kontrol edin
- Directory path'in doğru olduğundan emin olun

### Error Log Kontrolü

```bash
# Uygulama loglarını kontrol edin
tail -f ~/flask_tweet_app/logs/app.log

# PythonAnywhere error loglarını kontrol edin
tail -f /var/log/umutins62.pythonanywhere.com.error.log
```

### Manuel Test

```bash
# Bash console'da uygulamayı test edin
cd ~/flask_tweet_app
source venv/bin/activate
python app.py
```

## 🔄 Güncelleme Süreci

Uygulamanızı güncellemek için:

```bash
# Proje dizinine gidin
cd ~/flask_tweet_app

# Git'ten güncellemeleri çekin
git pull origin main

# Virtual environment'ı aktifleştirin
source venv/bin/activate

# Yeni dependencies varsa yükleyin
pip install -r requirements.txt

# Web app'i yeniden başlatın (PythonAnywhere dashboard'dan)
```

## 🌐 Domain ve SSL

### Özel Domain (Ücretli hesap gerekli)
1. Web sekmesinde **"Add a new web app"**
2. Kendi domain'inizi girin
3. DNS ayarlarını yapılandırın

### SSL Sertifikası
- PythonAnywhere otomatik olarak Let's Encrypt SSL sağlar
- Özel domain için manuel SSL yapılandırması gerekebilir

## 📊 Performans Optimizasyonu

### 1. Caching
```python
# app.py'de cache ayarları
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
```

### 2. Database Optimizasyonu
- JSON dosyaları yerine SQLite kullanmayı düşünün
- Büyük veriler için PostgreSQL (ücretli hesap)

### 3. Background Tasks
- PythonAnywhere'de scheduled tasks kullanın
- Celery ile asenkron işlemler (ücretli hesap)

## 🔒 Güvenlik

### 1. Environment Variables
- Hassas bilgileri asla kod'a yazmayın
- .env dosyasını .gitignore'a ekleyin

### 2. Secret Key
- Güçlü bir SECRET_KEY kullanın
- Production'da farklı key kullanın

### 3. API Rate Limits
- API çağrılarını sınırlayın
- Error handling ekleyin

## 📞 Destek

Sorun yaşarsanız:

1. **PythonAnywhere Help**: https://help.pythonanywhere.com/
2. **Error Logs**: Web sekmesinde error log linkini kontrol edin
3. **Forum**: PythonAnywhere forum'da soru sorun
4. **GitHub Issues**: Proje repository'sinde issue açın

## ✅ Kurulum Kontrol Listesi

- [ ] GitHub'dan proje klonlandı
- [ ] Virtual environment oluşturuldu
- [ ] Dependencies yüklendi
- [ ] .env dosyası oluşturuldu ve dolduruldu
- [ ] Gerekli dizinler oluşturuldu
- [ ] JSON dosyaları başlatıldı
- [ ] Web app oluşturuldu
- [ ] WSGI dosyası yapılandırıldı
- [ ] Static files ayarlandı
- [ ] Virtual environment path ayarlandı
- [ ] Uygulama başarıyla yüklendi
- [ ] Giriş sistemi test edildi
- [ ] API'ler test edildi

Kurulum tamamlandıktan sonra uygulamanız `https://umutins62.pythonanywhere.com` adresinde çalışacaktır! 