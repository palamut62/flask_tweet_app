# AI Tweet Bot - Python Anywhere Versiyonu

Bu, AI Tweet Bot'un Python Anywhere'de çalışacak şekilde optimize edilmiş Flask versiyonudur.

## 🚀 Özellikler

- **Otomatik Makale Çekme**: TechCrunch AI kategorisinden son haberleri çeker
- **AI Tweet Oluşturma**: Google Gemini 2.0 Flash ile akıllı tweet'ler oluşturur
- **GitHub Repo Keşfi**: Trend GitHub repolarını çeker ve tweet olarak paylaşır
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

### 2.1. Opsiyonel Gelişmiş Özellikler

Gelişmiş web scraping özellikleri için (opsiyonel):

```bash
# Opsiyonel kütüphaneleri kur
python install_optional.py
```

**Opsiyonel Kütüphaneler:**
- **requests-html**: JavaScript rendering desteği
- **selenium**: Browser automation (Chrome gerektirir)
- **pyppeteer**: Selenium alternatifi

**Not:** Bu kütüphaneler PythonAnywhere'de çalışmayabilir. Temel sistem bunlar olmadan da tam olarak çalışır.

### 3. Environment Değişkenlerini Ayarla

**⚠️ GÜVENLİK UYARISI:**
- `.env` dosyasını asla Git'e commit etmeyin
- Güçlü ve benzersiz şifreler kullanın
- Production'da `DEBUG=False` ayarlayın
- API anahtarlarınızı düzenli olarak yenileyin

PythonAnywhere Dashboard'da **Files** sekmesine git ve `.env.example` dosyasını `.env` olarak kopyalayıp düzenle:

```env
# =============================================================================
# UYGULAMA GÜVENLİĞİ
# =============================================================================
SECRET_KEY=your-secret-key-here-change-this-to-strong-random-string
SIFRE=your-admin-password-here-change-this
DEBUG=False
FLASK_ENV=production

# =============================================================================
# GOOGLE GEMINI AI API
# =============================================================================
GOOGLE_API_KEY=your-google-gemini-api-key

# =============================================================================
# TWITTER API CREDENTIALS
# =============================================================================
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
TWITTER_ACCESS_TOKEN=your-twitter-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-twitter-access-token-secret

# =============================================================================
# GITHUB API (Opsiyonel - GitHub repoları için)
# =============================================================================
GITHUB_TOKEN=your-github-personal-access-token

# =============================================================================
# TELEGRAM BOT (Opsiyonel - Bildirimler için)
# =============================================================================
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# =============================================================================
# GMAIL SMTP (Opsiyonel - E-posta bildirimleri için)
# =============================================================================
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password
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

### GitHub Repo Keşfi

GitHub modülü, trend olan açık kaynak projelerini keşfetmenizi ve bunları tweet olarak paylaşmanızı sağlar:

1. **GitHub Token (Opsiyonel)**:
   - GitHub Personal Access Token oluşturun
   - `.env` dosyasına `GITHUB_TOKEN` olarak ekleyin
   - Token olmadan da çalışır, ancak rate limit daha düşük olur

2. **GitHub Repoları Sayfası**:
   - `/github_repos` sayfasına gidin
   - **API Test** ile bağlantıyı kontrol edin
   - **Repo Çek** ile yeni repoları çekin

3. **Repo Çekme Ayarları**:
   - **Programlama Dili**: Python, JavaScript, TypeScript, Go, Rust, Java vb.
   - **Zaman Aralığı**: Günlük, haftalık veya aylık trend repolar
   - **Repo Sayısı**: Çekilecek repo sayısı (1-20 arası)

4. **Otomatik Tweet Oluşturma**:
   - Çekilen repolar otomatik olarak pending tweets'e eklenir
   - Her repo için AI ile tweet metni oluşturulur
   - Repo bilgileri (yıldız, fork, dil) tweet'e dahil edilir

5. **GitHub İstatistikleri**:
   - Toplam paylaşılan repo sayısı
   - Dil dağılımı
   - Haftalık repo paylaşım istatistikleri

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

## 🔒 Güvenlik

### Güvenlik Kontrolleri

Uygulama, güvenlik açıklarını tespit etmek için otomatik kontroller yapar:

- **Varsayılan Şifre Kontrolü**: Zayıf şifreleri tespit eder
- **Debug Modu Kontrolü**: Production'da debug modunu kontrol eder
- **API Anahtarı Kontrolü**: Örnek değerleri tespit eder
- **Secret Key Kontrolü**: Güçlü secret key kullanımını kontrol eder

### Güvenlik Sayfası

`/security_check` sayfasından güvenlik durumunuzu kontrol edebilirsiniz:

- ✅ Güvenlik durumu özeti
- ⚠️ Tespit edilen güvenlik sorunları
- 💡 Güvenlik önerileri
- 🔧 Sistem yapılandırması

### Güvenli Logging

Uygulama, hassas bilgilerin loglanmasını önler:

- API anahtarları otomatik maskelenir
- Şifreler log'larda görünmez
- Debug modunda bile hassas veriler korunur
- Production'da minimal logging

### Güvenlik Önerileri

1. **Environment Variables**:
   - `.env` dosyasını Git'e commit etmeyin
   - `.gitignore` dosyasında `.env` olduğundan emin olun

2. **Şifreler**:
   - Varsayılan şifreleri değiştirin
   - Güçlü ve benzersiz şifreler kullanın
   - Düzenli olarak şifreleri güncelleyin

3. **API Anahtarları**:
   - API anahtarlarını düzenli olarak yenileyin
   - Gereksiz izinleri kaldırın
   - Rate limit'leri ayarlayın

4. **Production Ayarları**:
   - `DEBUG=False` ayarlayın
   - `FLASK_ENV=production` kullanın
   - HTTPS kullanın

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
