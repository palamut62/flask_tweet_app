#!/usr/bin/env python3
"""
GitHub Modülü Test Scripti
Bu script GitHub modülünün çalışıp çalışmadığını test eder.
"""

import os
import sys
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# GitHub modülünü test et
try:
    from github_module import (
        fetch_trending_github_repos, create_fallback_github_tweet, generate_github_tweet,
        load_github_settings, save_github_settings, search_github_repos_by_topics
    )
    print("✅ GitHub modülü başarıyla import edildi")
except ImportError as e:
    print(f"❌ GitHub modülü import hatası: {e}")
    sys.exit(1)

def test_github_settings():
    """GitHub ayarları kaydetme ve yükleme test et"""
    print("\n🔧 GitHub ayarları testi başlıyor...")
    
    # Test ayarları
    test_settings = {
        "default_language": "python",
        "default_time_period": "weekly",
        "default_limit": 5,
        "search_topics": ["ai", "machine-learning", "openai"],
        "custom_search_queries": ["chatbot", "neural network"],
        "languages": ["python", "javascript", "typescript"],
        "time_periods": ["daily", "weekly", "monthly"]
    }
    
    # Ayarları kaydet
    print("💾 Test ayarları kaydediliyor...")
    if save_github_settings(test_settings):
        print("✅ Ayarlar başarıyla kaydedildi")
    else:
        print("❌ Ayarlar kaydedilemedi")
        return False
    
    # Ayarları yükle
    print("📂 Ayarlar yükleniyor...")
    loaded_settings = load_github_settings()
    
    if loaded_settings:
        print("✅ Ayarlar başarıyla yüklendi")
        print(f"   Dil: {loaded_settings.get('default_language')}")
        print(f"   Dönem: {loaded_settings.get('default_time_period')}")
        print(f"   Limit: {loaded_settings.get('default_limit')}")
        print(f"   Konular: {loaded_settings.get('search_topics')}")
        return True
    else:
        print("❌ Ayarlar yüklenemedi")
        return False

def test_topics_search():
    """Konulara göre GitHub arama test et"""
    print("\n🔍 Konulara göre GitHub arama testi başlıyor...")
    
    # Test konuları
    test_topics = ["ai", "machine-learning"]
    
    print(f"📋 Test konuları: {test_topics}")
    
    repos = search_github_repos_by_topics(
        topics=test_topics,
        language="python",
        time_period="weekly",
        limit=3
    )
    
    if repos:
        print(f"✅ {len(repos)} repo bulundu (konular: {test_topics}):")
        for i, repo in enumerate(repos, 1):
            print(f"  {i}. {repo['name']} - ⭐ {repo['stars']} stars")
            print(f"     Konular: {repo.get('topics', [])}")
            print(f"     Arama konuları: {repo.get('search_topics', [])}")
            print(f"     {repo['url']}")
            print()
        return True
    else:
        print(f"❌ Konulara göre repo bulunamadı: {test_topics}")
        return False

def test_github_api():
    """GitHub API'yi test et"""
    print("\n🔍 GitHub API testi başlıyor...")
    
    # Test parametreleri
    test_languages = ["python", "javascript"]
    
    for language in test_languages:
        print(f"\n📋 {language} repoları çekiliyor...")
        
        repos = fetch_trending_github_repos(
            language=language,
            time_period="weekly",
            limit=3
        )
        
        if repos:
            print(f"✅ {len(repos)} {language} repo bulundu:")
            for i, repo in enumerate(repos, 1):
                print(f"  {i}. {repo['name']} - ⭐ {repo['stars']} stars")
                description = repo.get('description') or 'Açıklama yok'
                print(f"     {description[:80]}...")
                print(f"     {repo['url']}")
                
                # Fallback tweet test et
                tweet = create_fallback_github_tweet(repo)
                print(f"     Tweet: {tweet[:100]}...")
                print()
        else:
            print(f"❌ {language} için repo bulunamadı")

def test_environment():
    """Çevre değişkenlerini test et"""
    print("\n🔧 Çevre değişkenleri kontrol ediliyor...")
    
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        print("✅ GITHUB_TOKEN mevcut")
        print(f"   Token: {github_token[:10]}...{github_token[-4:] if len(github_token) > 14 else github_token}")
    else:
        print("⚠️ GITHUB_TOKEN bulunamadı (opsiyonel)")
        print("   GitHub API rate limit'i daha düşük olacak")

def main():
    """Ana test fonksiyonu"""
    print("🚀 GitHub Modülü Test Scripti")
    print("=" * 50)
    
    # Çevre değişkenlerini test et
    test_environment()
    
    # GitHub ayarları test et
    settings_ok = test_github_settings()
    
    # Konulara göre arama test et
    topics_ok = test_topics_search()
    
    # GitHub API'yi test et
    test_github_api()
    
    print("\n" + "=" * 50)
    print("📊 Test Sonuçları:")
    print(f"   Ayarlar: {'✅ Başarılı' if settings_ok else '❌ Başarısız'}")
    print(f"   Konu Araması: {'✅ Başarılı' if topics_ok else '❌ Başarısız'}")
    
    if settings_ok and topics_ok:
        print("\n✅ Tüm testler başarılı!")
        print("GitHub modülü kullanıma hazır. Web uygulamasında /github_repos sayfasını ziyaret edebilirsiniz.")
    else:
        print("\n⚠️ Bazı testler başarısız oldu. Lütfen hataları kontrol edin.")

if __name__ == "__main__":
    main() 