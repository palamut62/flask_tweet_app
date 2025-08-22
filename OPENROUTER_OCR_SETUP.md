# OpenRouter OCR Entegrasyonu

## 🎯 Genel Bakış

AI Tweet Bot projesine OpenRouter'ın ücretsiz vision modelleri ile OCR (Optical Character Recognition) özelliği entegre edilmiştir. Bu sistem, resimlerden metin çıkarma işlemini gerçekleştirir ve çıkarılan metni kullanarak tweet oluşturur.

## 🤖 Kullanılan Vision Modelleri

### Ücretsiz Modeller (Sıralama Önceliği):
1. **qwen/qwen2-vl-7b:free** - En güvenilir ve doğru
2. **qwen/qwen2-vl-2b:free** - Daha hızlı işlem
3. **microsoft/phi-3-vision-128k-instruct:free** - Microsoft'un vision modeli
4. **llava/llava-v1.6-vicuna-7b:free** - LLaVA vision modeli

### Model Özellikleri:
- **Çok Dilli Destek:** 90+ dil desteği (Qwen2-VL)
- **Yüksek Doğruluk:** Gelişmiş OCR yetenekleri
- **Hızlı İşlem:** 2B model ile hızlı sonuç
- **Fallback Sistemi:** Bir model başarısız olursa diğeri denenir

## 🔧 Kurulum

### 1. OpenRouter API Anahtarı

1. [OpenRouter.ai](https://openrouter.ai) adresine gidin
2. Hesap oluşturun veya giriş yapın
3. [API Keys](https://openrouter.ai/keys) sayfasından yeni anahtar oluşturun
4. Anahtarınızı `.env` dosyasına ekleyin:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
```

### 2. Gerekli Python Paketleri

```bash
pip install requests pillow
```

## 🚀 Kullanım

### 1. Web Arayüzü ile OCR

1. Ana sayfada "Tweet Oluştur" bölümüne gidin
2. "Resim" seçeneğini seçin
3. Bir resim dosyası yükleyin
4. Tema seçin (bilgilendirici, eğlenceli, mizahi, vb.)
5. "Tweet Oluştur" butonuna tıklayın

### 2. API Endpoint ile OCR

```bash
POST /ocr_image
Content-Type: multipart/form-data

Parameters:
- image: Resim dosyası
- theme: Tweet teması (opsiyonel, varsayılan: bilgilendirici)

Response:
{
    "success": true,
    "text": "Oluşturulan tweet metni",
    "theme": "bilgilendirici",
    "char_count": 280,
    "ocr_text": "Çıkarılan OCR metni...",
    "ocr_method": "openrouter_vision_enhanced",
    "ocr_char_count": 150
}
```

### 3. Programatik Kullanım

```python
from utils import openrouter_ocr_image_enhanced, generate_ai_tweet_with_content

# OCR işlemi
ocr_text = openrouter_ocr_image_enhanced("path/to/image.jpg")

# Tweet oluşturma
article_data = {
    'title': ocr_text[:100],
    'content': ocr_text,
    'url': '',
    'lang': 'en'
}

tweet_data = generate_ai_tweet_with_content(article_data, api_key, "bilgilendirici")
tweet_text = tweet_data['tweet']
```

## 🧪 Test

### 1. Test Script'i Çalıştırma

```bash
# API testi
python test_openrouter_ocr.py

# Resim ile test
python test_openrouter_ocr.py static/uploads/test.png
```

### 2. Web Test Endpoint'i

```
GET /test_openrouter_ocr
```

## 📊 Sistem Akışı

```
Resim Yükleme → OpenRouter Vision Model → OCR İşlemi → Tweet Oluşturma
     ↓                    ↓                    ↓              ↓
  Dosya Kontrolü    Model Seçimi         Metin Çıkarma   AI Tweet
     ↓                    ↓                    ↓              ↓
  Boyut Kontrolü    Fallback Sistemi     Kalite Kontrolü  Tema Uygulama
```

## 🔄 Fallback Sistemi

1. **İlk Deneme:** qwen/qwen2-vl-7b:free
2. **İkinci Deneme:** qwen/qwen2-vl-2b:free
3. **Üçüncü Deneme:** microsoft/phi-3-vision-128k-instruct:free
4. **Dördüncü Deneme:** llava/llava-v1.6-vicuna-7b:free
5. **Son Çare:** Google Gemini OCR (mevcut sistem)

## ⚙️ Yapılandırma

### Environment Variables

```bash
# Gerekli
OPENROUTER_API_KEY=sk-or-v1-your-api-key

# Opsiyonel (fallback için)
GOOGLE_API_KEY=your-google-api-key
```

### Dosya Limitleri

- **Maksimum Dosya Boyutu:** 10MB
- **Desteklenen Formatlar:** JPEG, PNG, GIF, WebP
- **Önerilen Çözünürlük:** 1920x1080 ve altı

## 🎨 Tweet Temaları

OCR sonucu ile oluşturulan tweet'ler şu temalarda olabilir:

1. **Bilgilendirici:** Profesyonel ve eğitici
2. **Eğlenceli:** Eğlenceli ve ilgi çekici
3. **Mizahi:** Komik ve eğlenceli
4. **Resmi:** Ciddi ve resmi
5. **Heyecanlı:** Enerjik ve heyecan verici
6. **Meraklı:** Merak uyandırıcı ve sorgulayıcı

## 📈 Performans

### Hız Karşılaştırması:
- **Qwen2-VL-2B:** ~2-3 saniye
- **Qwen2-VL-7B:** ~4-6 saniye
- **Phi-3-Vision:** ~3-5 saniye
- **LLaVA:** ~5-8 saniye

### Doğruluk Karşılaştırması:
- **Qwen2-VL-7B:** En yüksek doğruluk
- **Qwen2-VL-2B:** Orta doğruluk, hızlı
- **Phi-3-Vision:** Yüksek doğruluk
- **LLaVA:** İyi doğruluk

## 🛠️ Sorun Giderme

### Yaygın Hatalar:

1. **"OpenRouter API anahtarı bulunamadı"**
   - `.env` dosyasında `OPENROUTER_API_KEY` kontrol edin
   - API anahtarının doğru formatta olduğundan emin olun

2. **"OCR işlemi başarısız"**
   - Resim dosyasının geçerli olduğunu kontrol edin
   - Dosya boyutunun 10MB altında olduğundan emin olun
   - Resimde okunabilir metin olduğunu kontrol edin

3. **"Rate limit aşıldı"**
   - Birkaç dakika bekleyin
   - Farklı bir model otomatik olarak denenir

4. **"Model yanıt vermedi"**
   - İnternet bağlantınızı kontrol edin
   - OpenRouter servis durumunu kontrol edin

### Debug Modu:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Gelecek Geliştirmeler

- [ ] Video OCR desteği
- [ ] Handwriting recognition
- [ ] Tablo ve formül tanıma
- [ ] Çoklu dil desteği geliştirme
- [ ] Batch processing
- [ ] OCR sonuçlarının cache'lenmesi

## 📞 Destek

Sorun yaşarsanız:
1. Test script'ini çalıştırın
2. Log dosyalarını kontrol edin
3. OpenRouter API durumunu kontrol edin
4. GitHub Issues'da sorun bildirin

---

**Not:** Bu sistem OpenRouter'ın ücretsiz modellerini kullanır. Yüksek kullanım için ücretli planlara geçiş yapabilirsiniz.
