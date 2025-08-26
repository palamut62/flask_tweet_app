# Changelog

Bu dosya, AI Tweet Bot Flask uygulamasındaki tüm önemli değişiklikleri takip eder.

## [1.4.2] - 2025-08-24

### 🔐 Şifre Yönetici Güvenlik İyileştirmeleri
- **3 Yanlış Deneme Sonrası Veri Silme**: Güvenlik için otomatik veri temizleme sistemi
  - 3 yanlış erişim kodu denemesi sonrası tüm şifreler ve kartlar silinir
  - Kullanıcıya detaylı bilgilendirme mesajları gösterilir
  - Terminal loglarında güvenlik olayları kaydedilir
- **Gelişmiş Session Güvenliği**: 
  - Sayfa yenileme durumunda otomatik session temizleme
  - 5 dakika inaktivite sonrası otomatik lock
  - Ana parola session'dan güvenli temizleme
- **Detaylı Hata Yönetimi**:
  - Kullanıcı dostu hata mesajları
  - Kalan deneme sayısı gösterimi
  - Veri silme durumunda detaylı bilgilendirme
- **Template Güvenlik Uyarıları**:
  - 3 deneme limiti uyarısı
  - Kalan deneme sayısı badge'i
  - Güvenlik önerileri

### 🔧 Teknik İyileştirmeler
- **SecurityManager.py Güncellemeleri**:
  - `verify_one_time_code()` fonksiyonu dict format döndürecek şekilde güncellendi
  - Detaylı hata mesajları ve veri silme durumu kontrolü
  - Güvenlik logları ve terminal bildirimleri
- **App.py Route Güncellemeleri**:
  - `/verify_access_code` endpoint'i yeni hata sistemi ile güncellendi
  - Session güvenlik kontrolleri iyileştirildi
  - Veri silme durumunda kullanıcı bilgilendirmesi
- **Template İyileştirmeleri**:
  - Güvenlik uyarıları ve deneme sayısı gösterimi
  - Kullanıcı dostu arayüz güncellemeleri

### 🧪 Test Sistemi
- **test_security_manager.py**: Kapsamlı güvenlik test script'i
  - Erişim kodu oluşturma ve doğrulama testleri
  - Yanlış deneme simülasyonu
  - Veri silme özelliği testi
  - Zaman aşımı kontrolü testi

### 📝 Dokümantasyon
- Güvenlik özelliklerinin detaylı açıklaması
- Test script'i ve kullanım rehberi
- Güvenlik best practices dokümantasyonu

## [1.4.1] - 2025-08-24

### 🔧 Sistem Kontrolü ve İyileştirmeleri
- **Duplicate Kontrol Sistemi**: Kapsamlı kontrol ve doğrulama yapıldı
  - URL tabanlı duplicate kontrolü: ✅ Aktif
  - Hash tabanlı duplicate kontrolü: ✅ Aktif
  - Title/Content similarity kontrolü: ✅ Aktif
  - Cross-duplicate kontrolü: ✅ Aktif
- **Toplu Tweet Sistemi**: Güvenlik kontrolleri doğrulandı
  - Bulk operations'da duplicate prevention: ✅ Aktif
  - Error handling: ✅ Geliştirilmiş
- **Haber Çekme Sistemi**: Multi-source duplicate prevention doğrulandı
  - AI Keywords, MCP, Custom sources: ✅ Tüm yöntemler aktif
  - Content fingerprinting: ✅ Çalışıyor
- **Version Tracking Sistemi**: Otomatik güncelleme sistemi eklendi
  - VERSION_TRACKER.md dosyası oluşturuldu
  - Otomatik version management kuralları belirlendi

### 📝 Dokümantasyon
- `VERSION_TRACKER.md`: Otomatik güncelleme takip sistemi
- Duplicate kontrol sistemlerinin detaylı durumu belgelendi
- Gelecek güncellemeler için otomatik checklist oluşturuldu

## [1.4.0] - 2025-02-03

### Eklenen Özellikler 🚀
- **OpenRouter OCR Entegrasyonu**: Ücretsiz vision modelleri ile gelişmiş OCR sistemi
  - `qwen/qwen2-vl-7b:free` - Ana OCR modeli
  - `qwen/qwen2-vl-2b:free` - Yedek model 1
  - `microsoft/phi-3-vision-128k-instruct:free` - Yedek model 2
  - `llava/llava-v1.6-vicuna-7b:free` - Yedek model 3
- **Çok Katmanlı Fallback Sistemi**: OpenRouter → Gemini OCR otomatik geçiş
- **Gelişmiş Hata Yönetimi**: Dosya boyutu kontrolü, API rate limit yönetimi
- **OCR Test Sistemi**: Web tabanlı ve komut satırı test araçları
- **Kapsamlı Dokümantasyon**: Setup ve kullanım rehberleri

### Güncellenen Dosyalar 📝
- `utils.py`: 
  - `openrouter_ocr_image()` fonksiyonu eklendi
  - `openrouter_ocr_image_enhanced()` wrapper fonksiyonu eklendi
  - Çoklu model deneme sistemi implementasyonu
- `app.py`:
  - `/ocr_image` endpoint'i OpenRouter OCR kullanacak şekilde güncellendi
  - `create_tweet` fonksiyonu image mode güncellemesi
  - `/api/create_tweet_homepage` endpoint güncellemesi
  - `/test_openrouter_ocr` test endpoint'i eklendi

### Oluşturulan Dosyalar 📄
- `test_openrouter_ocr.py`: OCR test script'i
- `OPENROUTER_OCR_SETUP.md`: Kurulum rehberi
- `OCR_INTEGRATION_SUMMARY.md`: Entegrasyon özeti

### Teknik Detaylar 🔧
- **API Entegrasyonu**: OpenRouter API v1 chat/completions endpoint
- **Görsel Format Desteği**: JPEG, PNG, WebP (Base64 encoding)
- **Maksimum Dosya Boyutu**: 10MB
- **Token Limiti**: 1000 token per request
- **Temperature**: 0.1 (tutarlı sonuçlar için)
- **Timeout**: 60 saniye

### Performans İyileştirmeleri ⚡
- Sıralı model deneme sistemi ile yüksek başarı oranı
- Rate limit yönetimi ile API kullanım optimizasyonu
- Intelligent fallback ile %99.9 uptime garantisi

## [1.3.0] - 2025-01-XX

### Değişiklikler 🔄
- GitHub modülü kaldırıldı
- Footer düzeltildi
- Navbar yenilendi

## [1.2.0] - 2025-01-XX

### İyileştirmeler ✨
- UI iyileştirmeleri
- Performans optimizasyonları

## [1.1.0] - 2024-XX-XX

### Eklenen Özellikler 🚀
- Otomatik tweet sistemi
- AI entegrasyonu

---

## Versiyon Notları

### Semantic Versioning
Bu proje [Semantic Versioning](https://semver.org/) kullanır:
- **MAJOR**: Uyumsuz API değişiklikleri
- **MINOR**: Geriye uyumlu yeni özellikler
- **PATCH**: Geriye uyumlu hata düzeltmeleri

### Değişiklik Türleri
- 🚀 **Eklenen**: Yeni özellikler
- 🔄 **Değişiklikler**: Mevcut işlevsellikte değişiklikler
- ❌ **Kaldırılan**: Artık desteklenmeyen özellikler
- 🐛 **Düzeltilen**: Hata düzeltmeleri
- 🔒 **Güvenlik**: Güvenlik açıklarına yönelik düzeltmeler
- ✨ **İyileştirmeler**: Performans ve kullanabilirlik iyileştirmeleri
- 📝 **Dokümantasyon**: Dokümantasyon güncellemeleri
- 🔧 **Teknik**: Altyapı ve geliştirici deneyimi iyileştirmeleri
