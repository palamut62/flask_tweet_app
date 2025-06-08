# 🤖 AI Tweet Bot - Kullanım Kılavuzu

## 🚀 Uygulamayı Başlatma

### 1. Ana Uygulama (Web Arayüzü)
```bash
python app.py
```
- **Adres**: http://127.0.0.1:5000
- **Özellik**: Web arayüzü, manuel kontroller, ayarlar
- **Davranış**: İlk açılışta otomatik işlem yapmaz, sadece ana sayfa açılır

### 2. Otomatik Zamanlayıcı (Arka Plan)
```bash
python start_scheduler.py
```
- **Özellik**: Her 3 saatte bir otomatik haber kontrolü ve tweet paylaşımı
- **Log**: `scheduler.log` dosyasına kaydedilir
- **Durdurma**: Ctrl+C ile durdurulabilir

## 📋 Sistem Çalışma Mantığı

### Ana Uygulama (app.py)
- ✅ **İlk açılış**: Herhangi bir otomatik işlem yapmaz
- ✅ **Hızlı başlangıç**: Anında ana sayfa açılır
- ✅ **Manuel kontrol**: "Yeni Haber Kontrol Et" butonu ile
- ✅ **Ayarlar**: Otomatik paylaşım ayarları
- ✅ **Tweet yönetimi**: Pending tweet'leri onaylama/reddetme

### Otomatik Zamanlayıcı (start_scheduler.py)
- ✅ **Arka plan çalışma**: Ana uygulamadan bağımsız
- ✅ **Periyodik kontrol**: Her 3 saatte bir
- ✅ **Akıllı sistem**: Ayarları kontrol eder, devre dışıysa çalışmaz
- ✅ **Log sistemi**: Tüm işlemler loglanır

## 🔧 Önerilen Kullanım

### Geliştirme/Test Ortamı
```bash
# Terminal 1: Ana uygulama
python app.py

# Terminal 2: Otomatik zamanlayıcı (isteğe bağlı)
python start_scheduler.py
```

### Prodüksiyon Ortamı (PythonAnywhere)
```bash
# Web app olarak: app.py
# Scheduled task olarak: start_scheduler.py (günde 8 kez - her 3 saatte)
```

## ⚙️ Ayarlar

### automation_settings.json
```json
{
  "auto_post_enabled": true,          // Otomatik paylaşım aktif/pasif
  "manual_approval_required": false,  // Manuel onay gerekli mi?
  "check_interval_hours": 3,          // Kontrol aralığı (saat)
  "max_articles_per_run": 5,          // Her seferinde max makale sayısı
  "min_score_threshold": 5            // Minimum kalite skoru
}
```

## 📊 İşlem Akışı

1. **Haber Çekme**: TechCrunch AI kategorisinden yeni haberler
2. **AI Analizi**: Her makale için Gemini AI ile analiz
3. **Tweet Oluşturma**: Akıllı hashtag ve emoji ile tweet
4. **Paylaşım**: Twitter API v2 ile otomatik paylaşım
5. **Bildirim**: Telegram ile başarı/hata bildirimi

## 🛠️ Sorun Giderme

### Uygulama Yavaş Açılıyor
- ✅ **Çözüldü**: Ana sayfa artık otomatik kontrol yapmıyor
- ✅ **Hızlı açılış**: Sadece mevcut veriler gösteriliyor

### Otomatik Paylaşım Çalışmıyor
- 🔍 **Kontrol**: `automation_settings.json` dosyasındaki ayarlar
- 🔍 **Log**: `scheduler.log` dosyasını kontrol edin
- 🔍 **API**: Twitter API anahtarlarını kontrol edin

### Twitter API Hatası
- 🔧 **v2 API**: Artık Twitter API v2 kullanılıyor
- 🔧 **Erişim**: "Elevated" erişim seviyesi gerekli
- 🔧 **Fallback**: Hata durumunda pending listesine ekleniyor

## 📝 Log Dosyaları

- `scheduler.log`: Otomatik zamanlayıcı logları
- `app.py` çıktısı: Web uygulaması logları
- Terminal çıktıları: Gerçek zamanlı durum bilgisi

## 🎯 Avantajlar

- ⚡ **Hızlı başlangıç**: Ana uygulama anında açılır
- 🔄 **Sürekli çalışma**: Arka plan zamanlayıcısı kesintisiz çalışır
- 🎛️ **Tam kontrol**: Manuel ve otomatik mod seçenekleri
- 📊 **Şeffaflık**: Detaylı log ve durum bilgisi
- 🛡️ **Güvenlik**: Hata durumunda sistem durmuyor 