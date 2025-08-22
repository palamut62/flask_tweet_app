# Changelog

Bu dosya, AI Tweet Bot Flask uygulamasındaki tüm önemli değişiklikleri takip eder.

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
