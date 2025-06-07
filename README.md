# AI Tweet Bot - Python Anywhere Versiyonu

Bu, AI Tweet Bot'un Python Anywhere'de çalışacak şekilde optimize edilmiş Flask versiyonudur.

## 🚀 Özellikler

- **Otomatik Makale Çekme**: TechCrunch AI kategorisinden son haberleri çeker
- **AI Tweet Oluşturma**: Google Gemini 2.0 Flash ile akıllı tweet'ler oluşturur
- **Otomatik Paylaşım**: Twitter'a otomatik tweet paylaşımı
- **Manuel Onay Sistemi**: Tweet'leri paylaşmadan önce onaylama
- **Telegram Bildirimleri**: Yeni tweet'ler için bildirim
- **Web Arayüzü**: Modern ve kullanıcı dostu Flask arayüzü
- **İstatistikler**: Detaylı performans raporları
- **Otomatik Kontrol**: Belirli aralıklarla otomatik çalışma

## 📋 Gereksinimler

- Python 3.8+
- Google Gemini API anahtarı
- Twitter API anahtarları
- Telegram Bot Token (opsiyonel)

## 🛠️ Python Anywhere Kurulumu

### 1. Dosyaları Yükle

```bash
# PythonAnywhere console'da
cd ~
git clone [your-repo-url] ai_tweet_bot_pythonanywhere
cd ai_tweet_bot_pythonanywhere
```

### 2. Virtual Environment Oluştur

```bash
# PythonAnywhere console'da
mkvirtualenv --python=/usr/bin/python3.10 ai_tweet_bot
workon ai_tweet_bot
pip install -r requirements.txt
```

### 3. Environment Değişkenlerini Ayarla

PythonAnywhere Dashboard'da **Files** sekmesine git ve `.env` dosyası oluştur:

```env
# Google Gemini API
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Twitter API Credentials
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Flask Configuration
SECRET_KEY=your_secret_key_for_flask_sessions
FLASK_ENV=production
```

### 4. Web App Yapılandırması

1. **Web** sekmesine git
2. **Add a new web app** tıkla
3. **Manual configuration** seç
4. **Python 3.10** seç
5. **WSGI configuration file** düzenle:

```python
import sys
import os

# Proje dizinini ekle (kullanıcı adınızı değiştirin)
project_home = '/home/yourusername/ai_tweet_bot_pythonanywhere'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Environment değişkenlerini yükle
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Flask uygulamasını import et
from app import app as application
```

6. **Virtual environment** ayarla:
   - Path: `/home/yourusername/.virtualenvs/ai_tweet_bot`

7. **Static files** ayarla:
   - URL: `/static/`
   - Directory: `/home/yourusername/ai_tweet_bot_pythonanywhere/static/`

### 5. Scheduled Tasks (Opsiyonel)

PythonAnywhere'de **Tasks** sekmesinde otomatik kontrol için:

```bash
# Her 2 saatte bir çalışacak task
cd /home/yourusername/ai_tweet_bot_pythonanywhere && python -c "
from app import check_and_post_articles
import os
os.environ.setdefault('FLASK_ENV', 'production')
result = check_and_post_articles()
print(f'Task completed: {result}')
"
```

## 🎯 Kullanım

### Web Arayüzü

1. `https://yourusername.pythonanywhere.com` adresine git
2. **Ayarlar** sekmesinden konfigürasyonu yap
3. **Şimdi Kontrol Et** ile manuel kontrol başlat
4. **Bekleyen Tweet'ler** bölümünden onay ver

### API Endpoints

- `GET /` - Ana sayfa
- `GET /check_articles` - Manuel makale kontrolü
- `POST /post_tweet` - Tweet paylaşımı
- `POST /delete_tweet` - Tweet silme
- `GET /settings` - Ayarlar sayfası
- `POST /save_settings` - Ayarları kaydet
- `GET /statistics` - İstatistikler
- `GET /api/status` - Health check

## ⚙️ Konfigürasyon

### Otomasyon Ayarları

- **Otomatik Mod**: Otomatik makale kontrolü
- **Kontrol Aralığı**: Kaç saatte bir kontrol (1-24 saat)
- **Maksimum Makale**: Her kontrolde işlenecek makale sayısı
- **Minimum Skor**: Paylaşım için minimum etki skoru
- **Otomatik Paylaşım**: Onay beklemeden direkt paylaş
- **Manuel Onay**: Tweet'ler için onay gereksinimi
- **Rate Limit**: İşlemler arası bekleme süresi

### Telegram Bildirimleri

1. BotFather'dan bot oluştur
2. Bot token'ı `.env` dosyasına ekle
3. Bot'a mesaj gönder
4. **Chat ID Algıla** butonuna tıkla
5. **Bağlantıyı Test Et** ile kontrol et

## 📊 İstatistikler

- Toplam makale sayısı
- Paylaşılan tweet sayısı
- Bekleyen tweet sayısı
- Ortalama etki skoru
- Günlük/haftalık istatistikler
- Kategori dağılımı
- Başarı oranı

## 🔧 Sorun Giderme

### Yaygın Sorunlar

1. **Import Hatası**:
   ```bash
   # Virtual environment aktif mi kontrol et
   workon ai_tweet_bot
   which python
   ```

2. **Environment Değişkenleri**:
   ```python
   # Console'da test et
   import os
   print(os.environ.get('GOOGLE_API_KEY'))
   ```

3. **WSGI Hatası**:
   - Error log'ları kontrol et
   - Path'leri doğrula
   - Import'ları test et

4. **API Bağlantı Sorunları**:
   - API anahtarlarını kontrol et
   - Rate limit'leri kontrol et
   - Network bağlantısını test et

### Log Kontrolü

```bash
# PythonAnywhere console'da
tail -f /var/log/yourusername.pythonanywhere.com.error.log
tail -f /var/log/yourusername.pythonanywhere.com.server.log
```

## 🔄 Güncelleme

```bash
# PythonAnywhere console'da
cd ~/ai_tweet_bot_pythonanywhere
git pull origin main
workon ai_tweet_bot
pip install -r requirements.txt

# Web app'i restart et
# Dashboard > Web > Reload
```

## 📝 Notlar

- Python Anywhere free hesaplarda günlük CPU sınırı var
- Scheduled tasks sadece paid hesaplarda mevcut
- HTTPS otomatik olarak sağlanır
- Static files için ayrı konfigürasyon gerekli
- Database kullanımı için ayrı setup gerekli

## 🆘 Destek

Sorun yaşarsanız:

1. Error log'ları kontrol edin
2. Environment değişkenlerini doğrulayın
3. API anahtarlarını test edin
4. Virtual environment'ı kontrol edin

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. # flask_tweet_app
