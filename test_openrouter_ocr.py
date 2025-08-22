#!/usr/bin/env python3
"""
OpenRouter OCR Test Script
Bu script OpenRouter vision modelleri ile OCR işlevini test eder.
"""

import os
import sys
import base64
import requests
from datetime import datetime

def test_openrouter_ocr_api():
    """OpenRouter OCR API'sini test et"""
    
    # OpenRouter API anahtarını kontrol et
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY environment variable bulunamadı!")
        print("Lütfen .env dosyanızda OPENROUTER_API_KEY'i ayarlayın.")
        return False
    
    print(f"🔑 API Key bulundu: {api_key[:10]}...")
    
    # Test için basit bir metin oluştur
    test_text = "Bu bir test metnidir. OpenRouter OCR sistemi çalışıyor!"
    
    # Base64 encoded test image (basit bir metin görseli simülasyonu)
    # Gerçek uygulamada bu bir resim dosyası olacak
    print("🧪 OpenRouter vision modelleri test ediliyor...")
    
    # Vision modelleri listesi
    vision_models = [
        "qwen/qwen2-vl-7b:free",
        "qwen/qwen2-vl-2b:free", 
        "microsoft/phi-3-vision-128k-instruct:free",
        "llava/llava-v1.6-vicuna-7b:free"
    ]
    
    for model in vision_models:
        print(f"\n🔍 Model test ediliyor: {model}")
        
        try:
            # Basit bir API çağrısı testi (resim olmadan)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ai-tweet-bot.pythonanywhere.com",
                "X-Title": "AI Tweet Bot Test"
            }
            
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Merhaba! Bu bir test mesajıdır. Lütfen 'Test başarılı' yanıtını ver."
                    }
                ],
                "max_tokens": 50,
                "temperature": 0.1
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"].strip()
                    print(f"✅ {model} - Başarılı! Yanıt: {content[:50]}...")
                else:
                    print(f"⚠️ {model} - Yanıt formatı beklenmiyor")
            elif response.status_code == 429:
                print(f"⚠️ {model} - Rate limited, diğer model deneniyor")
                continue
            else:
                print(f"❌ {model} - Hata: {response.status_code}")
                print(f"   Yanıt: {response.text[:100]}...")
                
        except Exception as e:
            print(f"❌ {model} - Exception: {str(e)}")
            continue
    
    print("\n🎯 Test tamamlandı!")
    return True

def test_ocr_with_image(image_path):
    """Gerçek resim ile OCR testi"""
    
    if not os.path.exists(image_path):
        print(f"❌ Test resmi bulunamadı: {image_path}")
        return False
    
    print(f"📷 Resim ile OCR testi: {image_path}")
    
    # utils modülünü import et
    try:
        from utils import openrouter_ocr_image_enhanced
    except ImportError:
        print("❌ utils modülü import edilemedi!")
        return False
    
    # OCR testi yap
    try:
        ocr_result = openrouter_ocr_image_enhanced(image_path)
        
        if ocr_result and len(ocr_result.strip()) > 5:
            print(f"✅ OCR başarılı!")
            print(f"📝 Çıkarılan metin: {ocr_result[:200]}...")
            print(f"📊 Karakter sayısı: {len(ocr_result)}")
            return True
        else:
            print(f"❌ OCR sonucu yetersiz: {ocr_result}")
            return False
            
    except Exception as e:
        print(f"❌ OCR hatası: {str(e)}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 OpenRouter OCR Test Script")
    print("=" * 50)
    
    # API testi
    api_success = test_openrouter_ocr_api()
    
    if not api_success:
        print("\n❌ API testi başarısız! OCR testi yapılamıyor.")
        return
    
    # Resim ile test (opsiyonel)
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"\n📷 Resim ile OCR testi: {image_path}")
        ocr_success = test_ocr_with_image(image_path)
        
        if ocr_success:
            print("\n🎉 Tüm testler başarılı!")
        else:
            print("\n⚠️ OCR testi başarısız, ama API çalışıyor.")
    else:
        print("\n💡 Resim ile test için: python test_openrouter_ocr.py <resim_yolu>")
        print("   Örnek: python test_openrouter_ocr.py static/uploads/test.png")

if __name__ == "__main__":
    main()
