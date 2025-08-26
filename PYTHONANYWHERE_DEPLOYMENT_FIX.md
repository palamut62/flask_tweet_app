# PythonAnywhere Deployment Fix Guide

## 🚨 500 Internal Server Error Çözümü

Bu rehber PythonAnywhere'de yaşanan 500 Internal Server Error'ını çözmek için hazırlanmıştır.

## 📋 Sorun Analizi

Kullanıcı şu hataları bildirdi:
- `500 Internal Server Error`
- `Uncaught (in promise) The message port closed before a response was received`
- `Failed to load resource: the server responded with a status of 500`

**Tespit Edilen Sorun**: `fpdf` modülü eksik

## 🔧 Çözüm Adımları

### 1. PythonAnywhere Konsolunda Paket Yükleme

```bash
# Önce eksik fpdf2 paketini yükle
pip install --user fpdf2==2.8.3

# Sonra minimal paketleri yükle
pip install --user -r requirements_pythonanywhere_minimal.txt

# Eğer yukarıdaki çalışmazsa, tek tek yükle
pip install --user flask==2.3.3
pip install --user python-dotenv==1.0.0
pip install --user requests==2.31.0
pip install --user beautifulsoup4==4.12.2
pip install --user tweepy==4.14.0
pip install --user cryptography==41.0.7
pip install --user fpdf2==2.8.3
```

### 2. WSGI Dosyasını Değiştirme

PythonAnywhere Web sekmesinde:

1. **WSGI configuration file** bölümünde
2. **wsgi.py** yerine **wsgi_config_safe.py** kullanın
3. **Reload** butonuna tıklayın

### 3. Dosya İzinlerini Kontrol Etme

```bash
# Dosya izinlerini kontrol et
ls -la

# Gerekli dosyaların varlığını kontrol et
ls -la app.py wsgi_config_safe.py pythonanywhere_config.py
```

### 4. Error Loglarını Kontrol Etme

PythonAnywhere Web sekmesinde:
- **Error log** bölümünü kontrol edin
- Hata mesajlarını okuyun

### 5. Test Script'ini Çalıştırma

```bash
# Test script'ini çalıştır
python test_app_startup.py

# Eğer hala hata varsa, hızlı düzeltme aracını çalıştır
python fix_pythonanywhere.py
```

## 🛠️ Yeni Dosyalar

### wsgi_config_safe.py
- Güvenli WSGI konfigürasyonu
- Hata yakalama ve raporlama
- Detaylı hata mesajları

### requirements_pythonanywhere_minimal.txt
- Sadece gerekli paketler (fpdf2 dahil)
- Versiyon çakışmalarını önler
- Minimal bağımlılık

### deploy_pythonanywhere.py
- Otomatik deployment kontrolü
- Paket yükleme
- Hata teşhisi

### test_app_startup.py
- Uygulama başlatma testi
- Import kontrolü
- Route testi

### fix_pythonanywhere.py
- Hızlı düzeltme aracı
- Otomatik paket yükleme
- Sorun giderme

## 🔍 Olası Hata Nedenleri

### 1. Paket Versiyon Uyumsuzluğu
- **Çözüm**: `requirements_pythonanywhere_minimal.txt` kullanın

### 2. Import Hataları
- **Çözüm**: `wsgi_config_safe.py` kullanın

### 3. Eksik Paketler (fpdf2)
- **Çözüm**: `pip install --user fpdf2==2.8.3`

### 4. Dosya İzinleri
- **Çözüm**: Dosya izinlerini kontrol edin

### 5. Python Versiyonu
- **Çözüm**: Python 3.8+ kullanın

### 6. Environment Variables
- **Çözüm**: `.env` dosyasını kontrol edin

## 📝 Adım Adım Deployment

### Adım 1: Dosyaları Yükle
```bash
# Tüm dosyaları PythonAnywhere'e yükle
git clone <repository_url>
cd flask_tweet_app
```

### Adım 2: Paketleri Yükle
```bash
# Önce eksik fpdf2 paketini yükle
pip install --user fpdf2==2.8.3

# Sonra minimal paketleri yükle
pip install --user -r requirements_pythonanywhere_minimal.txt
```

### Adım 3: WSGI Ayarla
- PythonAnywhere Web sekmesine git
- WSGI dosyasını `wsgi_config_safe.py` olarak değiştir
- Reload butonuna tıkla

### Adım 4: Test Et
```bash
# Test script'ini çalıştır
python test_app_startup.py
```

### Adım 5: Hata Loglarını Kontrol Et
- Error log'ları oku
- Gerekirse ek düzeltmeler yap

## 🚀 Hızlı Düzeltme

Eğer hala 500 hatası alıyorsanız:

1. **Eksik paketi yükleyin**:
   ```bash
   pip install --user fpdf2==2.8.3
   ```

2. **WSGI dosyasını değiştirin**:
   ```python
   # wsgi.py yerine wsgi_config_safe.py kullanın
   ```

3. **Paketleri yeniden yükleyin**:
   ```bash
   pip install --user flask==2.3.3 python-dotenv==1.0.0 requests==2.31.0 fpdf2==2.8.3
   ```

4. **Reload yapın**:
   - PythonAnywhere Web sekmesinde Reload butonuna tıklayın

5. **Error log'ları kontrol edin**:
   - Detaylı hata mesajlarını okuyun

## 📞 Destek

Eğer sorun devam ederse:
1. Error log'larını paylaşın
2. Test script çıktısını paylaşın
3. PythonAnywhere konsol çıktısını paylaşın

## ✅ Başarı Kriterleri

Deployment başarılı olduğunda:
- ✅ Ana sayfa yüklenir (200 OK)
- ✅ Şifre yöneticisi sayfası çalışır
- ✅ Static dosyalar yüklenir
- ✅ Error log'ları temizdir
- ✅ Tüm import'lar başarılı

## 🔄 Güncelleme Notları

- **v1.0**: İlk deployment fix guide
- **v1.1**: wsgi_config_safe.py eklendi
- **v1.2**: Minimal requirements eklendi
- **v1.3**: Test script'leri eklendi
- **v1.4**: fpdf2 paketi eklendi ve güvenli import'lar yapıldı
