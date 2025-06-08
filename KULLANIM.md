# 🤖 AI Tweet Bot - Kullanım Kılavuzu

## 🚀 Uygulamayı Başlatma

### ✅ Tek Komut ile Tam Sistem (Önerilen - PythonAnywhere Uyumlu)
```bash
python app.py
```
- **Adres**: http://127.0.0.1:5000
- **Özellik**: Web arayüzü + Arka plan zamanlayıcısı
- **Otomatik**: Her 3 saatte bir haber kontrolü
- **PythonAnywhere**: Tek web app olarak çalışır
- **Maliyet**: Ek ücret yok

### 🔧 Alternatif: Ayrı Zamanlayıcı (Eski Yöntem)
```bash
# Terminal 1: Ana uygulama
python app.py

# Terminal 2: Ayrı zamanlayıcı
python start_scheduler.py
```
- **Kullanım**: Sadece geliştirme ortamı için
- **PythonAnywhere**: Ek scheduled task ücreti gerekir

## 📋 Sistem Çalışma Mantığı

### Entegre Sistem (app.py)
- ✅ **İlk açılış**: Hızlı ana sayfa + arka plan zamanlayıcı başlatma
- ✅ **Web arayüzü**: Tam fonksiyonel kontrol paneli
- ✅ **Manuel kontrol**: "Yeni Haber Kontrol Et" butonu ile
- ✅ **Otomatik sistem**: Arka plan thread'i ile her 3 saatte bir
- ✅ **Ayarlar**: Otomatik paylaşım ayarları
- ✅ **Tweet yönetimi**: Pending tweet'leri onaylama/reddetme
- ✅ **PythonAnywhere uyumlu**: Tek web app olarak çalışır

## 🔧 Önerilen Kullanım

### Geliştirme/Test Ortamı
```bash
# Tek komut - her şey dahil
python app.py
```

### Prodüksiyon Ortamı (PythonAnywhere)
```bash
# Tek web app olarak
python app.py
```
- ✅ **Ek maliyet yok**: Scheduled task gerekmez
- ✅ **Basit kurulum**: Tek dosya yönetimi
- ✅ **Güvenilir**: Web app sürekli çalışır

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