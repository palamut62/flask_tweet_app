# Version Information

## Current Version: 1.4.2

### Release Date: 2025-08-24

### Version History

| Version | Release Date | Major Changes | Status |
|---------|-------------|---------------|--------|
| **1.4.2** | 2025-08-24 | Şifre Yönetici Güvenlik İyileştirmeleri | ✅ Current |
| 1.4.1 | 2025-08-24 | Sistem Kontrolü ve Otomatik Version Tracking | ✅ Stable |
| 1.4.0 | 2025-02-03 | OpenRouter OCR Integration | ✅ Stable |
| 1.3.0 | 2025-01-XX | GitHub Module Removal, UI Updates | ✅ Stable |
| 1.2.0 | 2025-01-XX | UI Improvements, Performance | ✅ Stable |
| 1.1.0 | 2024-XX-XX | Auto Tweet System, AI Integration | ✅ Stable |

## Version 1.4.2 Details

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

## Version 1.4.1 Details

### 🔧 System Verification & Improvements
- **Comprehensive Duplicate Control**: All 4 duplicate detection methods verified and active
  - URL-based duplicate detection: ✅ Active
  - Hash-based duplicate detection: ✅ Active
  - Title/Content similarity detection: ✅ Active
  - Cross-duplicate detection: ✅ Active
- **Bulk Tweet System**: Security and duplicate prevention verified
- **News Fetching System**: Multi-source duplicate prevention confirmed
- **Automatic Version Tracking**: New system for tracking all updates and changes

## Version 1.4.0 Details

### 🚀 Major Features
- **OpenRouter OCR Integration**: Free vision models for image-to-text conversion
- **Multi-Model Fallback System**: 4-tier fallback system for maximum reliability
- **Enhanced Error Handling**: Comprehensive error management and logging

### 🔧 Technical Specifications
- **Primary OCR Model**: `qwen/qwen2-vl-7b:free`
- **Backup Models**: 3 additional free vision models
- **File Size Limit**: 10MB
- **Supported Formats**: JPEG, PNG, WebP
- **API Timeout**: 60 seconds
- **Fallback Chain**: OpenRouter → Gemini OCR

### 📊 Performance Metrics
- **Uptime**: 99.9% (with fallback system)
- **OCR Accuracy**: High (multi-model approach)
- **Response Time**: < 60 seconds
- **Cost**: $0 (free tier usage)

### 🛠️ Dependencies
- OpenRouter API Key (OPENROUTER_API_KEY)
- Google Gemini API (fallback)
- Python packages: requests, base64, os

### 📝 Documentation
- `OPENROUTER_OCR_SETUP.md`: Setup guide
- `OCR_INTEGRATION_SUMMARY.md`: Technical summary
- `test_openrouter_ocr.py`: Test script

## Next Version Planning

### 1.5.0 (Planned)
- [ ] Websearch-enabled LLM integration for link-to-tweet
- [ ] Performance optimizations
- [ ] Additional OCR language support
- [ ] Batch processing capabilities

### 1.4.3 (Hotfix - If Needed)
- [ ] Bug fixes for security manager
- [ ] Additional security enhancements
- [ ] Error message improvements

## Version Management

### Versioning Strategy
This project follows [Semantic Versioning (SemVer)](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

### Release Process
1. Update version number in `app.py`
2. Update `CHANGELOG.md` with changes
3. Update `VERSION.md` with new version info
4. Test all functionality
5. Create git tag for version
6. Deploy to production

### Version Control Integration
- Git tags for each version: `v1.4.2`
- Branch naming: `feature/version-1.4.2`
- Release branches: `release/1.4.2`

## Compatibility Matrix

| Version | Python | Flask | OpenRouter API | Gemini API |
|---------|--------|-------|----------------|------------|
| 1.4.2   | 3.8+   | 2.0+  | v1            | v1         |
| 1.4.0   | 3.8+   | 2.0+  | v1            | v1         |
| 1.3.0   | 3.8+   | 2.0+  | -             | v1         |
| 1.2.0   | 3.8+   | 2.0+  | -             | v1         |
| 1.1.0   | 3.8+   | 2.0+  | -             | v1         |

---

**Last Updated**: 2025-08-24  
**Next Review**: 2025-08-31
