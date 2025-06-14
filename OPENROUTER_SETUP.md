# OpenRouter API Kurulum Kılavuzu

## OpenRouter Nedir?

OpenRouter, çeşitli AI modellerine tek bir API üzerinden erişim sağlayan bir platformdur. Ücretsiz modeller de dahil olmak üzere birçok farklı AI modeli sunar.

### 🎯 AI Tweet Bot'ta OpenRouter'ın Rolü

OpenRouter, AI Tweet Bot'ta **yedek sistem** olarak çalışır:

1. **Ana Sistem:** Google Gemini API (birincil AI sistemi)
2. **Yedek Sistem:** OpenRouter API (Gemini başarısız olursa devreye girer)

### 🆓 Ücretsiz Modeller (2025 Güncel)

OpenRouter'da kullanabileceğiniz güncel ücretsiz modeller:
- **Qwen3 8B** (En güvenilir ve hızlı - 2025 yeni model)
- **Qwen3 30B A3B** (Güçlü performans - MoE mimarisi)
- **Qwen3 4B** (Ultra hızlı - düşük kaynak kullanımı)
- **DeepSeek Chat V3** (Konuşma odaklı - güvenilir)
- **DeepSeek R1 Zero** (Reasoning odaklı - mantıksal çıkarım)
- **DeepSeek V3 Base** (Teknik içerik için optimize)
- **DeepHermes 3 Llama 3 8B** (Fallback - genel amaçlı)

### ⚡ Otomatik Yedek Sistemi

Sistem şu şekilde çalışır:
1. Tweet oluşturulurken önce Gemini API denenir
2. Gemini başarısız olursa (API hatası, rate limit vb.) OpenRouter devreye girer
3. OpenRouter'da 4 farklı ücretsiz model sırayla denenir
4. En az bir model başarılı olursa tweet oluşturulur

## Kurulum Adımları

### 1. OpenRouter Hesabı Oluşturma

1. [OpenRouter.ai](https://openrouter.ai) adresine gidin
2. "Sign Up" butonuna tıklayın
3. Email ve şifre ile hesap oluşturun
4. Email doğrulamasını tamamlayın

### 2. API Anahtarı Alma

1. OpenRouter hesabınıza giriş yapın
2. [API Keys](https://openrouter.ai/keys) sayfasına gidin
3. "Create Key" butonuna tıklayın
4. Anahtar için bir isim verin (örn: "AI Tweet Bot")
5. API anahtarınızı kopyalayın (güvenli bir yerde saklayın)

**💡 İpucu:** OpenRouter'da ücretsiz modeller mevcut! Hesap oluşturduktan sonra hemen kullanmaya başlayabilirsiniz.

### 3. Environment Variable Ayarlama

#### PythonAnywhere için:
1. PythonAnywhere dashboard'unuza gidin
2. "Files" sekmesine tıklayın
3. `.env` dosyasını açın
4. Şu satırı ekleyin:
```
OPENROUTER_API_KEY=your_api_key_here
```

#### Yerel geliştirme için:
`.env` dosyanıza şu satırı ekleyin:
```
OPENROUTER_API_KEY=your_api_key_here
```

### 4. Ücretsiz Modeller

Sistem şu güncel ücretsiz modelleri kullanır (öncelik sırasına göre):

1. **qwen/qwen3-8b:free**
   - Alibaba'nın Qwen3 8B modeli (2025)
   - 8.2B parametre, 40K context
   - En güvenilir ve hızlı performans

2. **qwen/qwen3-30b-a3b:free**
   - Qwen3 30B A3B MoE modeli
   - 30.5B toplam, 3.3B aktif parametre
   - Güçlü reasoning ve çok dilli destek

3. **qwen/qwen3-4b:free**
   - Qwen3 4B kompakt model
   - 4B parametre, 128K context
   - Ultra hızlı ve düşük kaynak kullanımı

4. **deepseek/deepseek-chat-v3-0324:free**
   - DeepSeek Chat V3 modeli
   - Konuşma odaklı optimizasyon
   - Güvenilir dialogue management

5. **deepseek/deepseek-r1-zero:free**
   - DeepSeek R1 Zero reasoning modeli
   - Mantıksal çıkarım ve problem çözme
   - Bilimsel ve teknik görevler için

6. **deepseek/deepseek-v3-base:free**
   - DeepSeek V3 Base modeli
   - Teknik içerik ve programlama
   - Geniş domain bilgisi

7. **nousresearch/deephermes-3-llama-3-8b-preview:free**
   - Nous Research DeepHermes 3
   - Llama 3 8B tabanlı
   - Genel amaçlı fallback

## Nasıl Çalışır?

1. **Birincil Sistem**: Google Gemini API önce denenir
2. **Yedek Sistem**: Gemini başarısız olursa OpenRouter devreye girer
3. **Model Seçimi**: Ücretsiz modeller sırayla denenir
4. **Fallback**: Hiçbir model çalışmazsa "API hatası" döner

## Test Etme

### Web Arayüzü ile:
1. Ayarlar sayfasına gidin
2. "OpenRouter API Test" butonuna tıklayın
3. Sonuçları kontrol edin

### API Endpoint ile:
```
GET /test_openrouter_api
```

### Konsol Logları:
- `✅ OpenRouter başarılı! Model: model_name`
- `🔄 Gemini başarısız, OpenRouter yedek sistemi deneniyor...`
- `❌ Tüm OpenRouter modelleri başarısız`

## Avantajları

1. **Ücretsiz**: Seçilen modeller tamamen ücretsiz
2. **Yedek Sistem**: Gemini çalışmazsa otomatik devreye girer
3. **Çoklu Model**: Bir model çalışmazsa diğeri denenir
4. **Güvenilirlik**: Sistem kesintisiz çalışmaya devam eder

## Limitler

- **Günlük Limit**: Ücretsiz modellerde günlük kullanım limiti var
- **Hız Limiti**: Dakika başına istek sayısı sınırlı
- **Model Kapasitesi**: Ücretsiz modeller ücretli olanlara göre daha basit

## Sorun Giderme

### API Anahtarı Hatası:
```
⚠️ OpenRouter API anahtarı bulunamadı, yedek sistem kullanılamıyor
```
**Çözüm**: `OPENROUTER_API_KEY` environment variable'ını kontrol edin

### Model Hatası:
```
❌ OpenRouter model hatası (model_name): error_message
```
**Çözüm**: Model geçici olarak kullanılamıyor, sistem otomatik olarak diğer modeli dener

### Tüm Modeller Başarısız:
```
❌ Tüm OpenRouter modelleri başarısız
```
**Çözüm**: 
1. İnternet bağlantısını kontrol edin
2. API anahtarının geçerli olduğunu kontrol edin
3. Günlük limitin aşılmadığını kontrol edin

## Maliyet

- **Ücretsiz Modeller**: Tamamen ücretsiz (günlük limit dahilinde)
- **Ücretli Modeller**: Kullanım başına ödeme (sistem şu anda sadece ücretsiz modeller kullanır)

## Güvenlik

- API anahtarınızı kimseyle paylaşmayın
- Environment variable olarak saklayın
- Düzenli olarak yenileyin
- Kullanımı izleyin

## Destek

- [OpenRouter Dokümantasyon](https://openrouter.ai/docs)
- [OpenRouter Discord](https://discord.gg/openrouter)
- [GitHub Issues](https://github.com/OpenRouterTeam/openrouter-runner) 