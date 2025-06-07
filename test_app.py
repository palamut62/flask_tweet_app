#!/usr/bin/env python3
"""
AI Tweet Bot - Python Anywhere Test Script

Bu script Python Anywhere'de uygulamanın doğru çalışıp çalışmadığını test eder.
"""

import os
import sys
import json
from datetime import datetime

def test_imports():
    """Gerekli modüllerin import edilip edilemediğini test et"""
    print("🔍 Import testleri başlatılıyor...")
    
    try:
        import flask
        print(f"✅ Flask: {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask import hatası: {e}")
        return False
    
    try:
        import requests
        print(f"✅ Requests: {requests.__version__}")
    except ImportError as e:
        print(f"❌ Requests import hatası: {e}")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup4: OK")
    except ImportError as e:
        print(f"❌ BeautifulSoup4 import hatası: {e}")
        return False
    
    try:
        import tweepy
        print(f"✅ Tweepy: {tweepy.__version__}")
    except ImportError as e:
        print(f"❌ Tweepy import hatası: {e}")
        return False
    
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI: OK")
    except ImportError as e:
        print(f"❌ Google Generative AI import hatası: {e}")
        return False
    
    return True

def test_environment_variables():
    """Environment değişkenlerini test et"""
    print("\n🔍 Environment değişkenleri kontrol ediliyor...")
    
    required_vars = [
        'GOOGLE_API_KEY',
        'TWITTER_BEARER_TOKEN',
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET',
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET'
    ]
    
    optional_vars = [
        'TELEGRAM_BOT_TOKEN',
        'SECRET_KEY'
    ]
    
    missing_required = []
    
    for var in required_vars:
        if os.environ.get(var):
            print(f"✅ {var}: Mevcut")
        else:
            print(f"❌ {var}: Eksik")
            missing_required.append(var)
    
    for var in optional_vars:
        if os.environ.get(var):
            print(f"✅ {var}: Mevcut (opsiyonel)")
        else:
            print(f"⚠️ {var}: Eksik (opsiyonel)")
    
    return len(missing_required) == 0

def test_file_permissions():
    """Dosya izinlerini test et"""
    print("\n🔍 Dosya izinleri kontrol ediliyor...")
    
    test_files = [
        'posted_articles.json',
        'pending_tweets.json',
        'automation_settings.json',
        'accounts.json'
    ]
    
    for filename in test_files:
        try:
            # Dosya varsa oku, yoksa oluştur
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ {filename}: Okunabilir")
            else:
                # Test dosyası oluştur
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                print(f"✅ {filename}: Oluşturuldu")
                
            # Yazma testi
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print(f"✅ {filename}: Yazılabilir")
            
        except Exception as e:
            print(f"❌ {filename}: Hata - {e}")
            return False
    
    return True

def test_api_connections():
    """API bağlantılarını test et"""
    print("\n🔍 API bağlantıları test ediliyor...")
    
    # Google Gemini API testi
    try:
        import google.generativeai as genai
        api_key = os.environ.get('GOOGLE_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content("Test message")
            print("✅ Google Gemini API: Çalışıyor")
        else:
            print("⚠️ Google Gemini API: API anahtarı eksik")
    except Exception as e:
        print(f"❌ Google Gemini API: Hata - {e}")
    
    # Twitter API testi
    try:
        import tweepy
        bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
        if bearer_token:
            client = tweepy.Client(bearer_token=bearer_token)
            # Basit bir test sorgusu
            print("✅ Twitter API: Bearer token mevcut")
        else:
            print("⚠️ Twitter API: Bearer token eksik")
    except Exception as e:
        print(f"❌ Twitter API: Hata - {e}")
    
    # Telegram API testi (opsiyonel)
    try:
        import requests
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if bot_token:
            response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
            if response.status_code == 200:
                print("✅ Telegram API: Çalışıyor")
            else:
                print("❌ Telegram API: Bağlantı hatası")
        else:
            print("⚠️ Telegram API: Bot token eksik (opsiyonel)")
    except Exception as e:
        print(f"❌ Telegram API: Hata - {e}")

def test_flask_app():
    """Flask uygulamasını test et"""
    print("\n🔍 Flask uygulaması test ediliyor...")
    
    try:
        from app import app
        
        # Test client oluştur
        with app.test_client() as client:
            # Ana sayfa testi
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Ana sayfa: Çalışıyor")
            else:
                print(f"❌ Ana sayfa: HTTP {response.status_code}")
            
            # API status testi
            response = client.get('/api/status')
            if response.status_code == 200:
                print("✅ API Status: Çalışıyor")
            else:
                print(f"❌ API Status: HTTP {response.status_code}")
            
            # Ayarlar sayfası testi
            response = client.get('/settings')
            if response.status_code == 200:
                print("✅ Ayarlar sayfası: Çalışıyor")
            else:
                print(f"❌ Ayarlar sayfası: HTTP {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask uygulaması: Hata - {e}")
        return False

def test_utils_functions():
    """Utils fonksiyonlarını test et"""
    print("\n🔍 Utils fonksiyonları test ediliyor...")
    
    try:
        from utils import load_json, save_json, load_automation_settings
        
        # JSON işlemleri testi
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        save_json("test_file.json", test_data)
        loaded_data = load_json("test_file.json")
        
        if loaded_data == test_data:
            print("✅ JSON işlemleri: Çalışıyor")
        else:
            print("❌ JSON işlemleri: Veri uyumsuzluğu")
        
        # Temizlik
        if os.path.exists("test_file.json"):
            os.remove("test_file.json")
        
        # Automation settings testi
        settings = load_automation_settings()
        print("✅ Automation settings: Yüklendi")
        
        return True
        
    except Exception as e:
        print(f"❌ Utils fonksiyonları: Hata - {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 AI Tweet Bot - Python Anywhere Test Başlatılıyor")
    print("=" * 60)
    
    test_results = []
    
    # Testleri çalıştır
    test_results.append(("Import Testleri", test_imports()))
    test_results.append(("Environment Değişkenleri", test_environment_variables()))
    test_results.append(("Dosya İzinleri", test_file_permissions()))
    test_results.append(("Utils Fonksiyonları", test_utils_functions()))
    test_results.append(("Flask Uygulaması", test_flask_app()))
    
    # API testleri (hata olsa da devam et)
    print("\n🔍 API bağlantıları test ediliyor...")
    test_api_connections()
    
    # Sonuçları özetle
    print("\n" + "=" * 60)
    print("📊 TEST SONUÇLARI")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nToplam: {passed}/{total} test başarılı")
    
    if passed == total:
        print("\n🎉 Tüm testler başarılı! Uygulama Python Anywhere'de çalışmaya hazır.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test başarısız. Lütfen hataları düzeltin.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 