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
    from github_module import fetch_trending_github_repos, create_fallback_github_tweet
    print("✅ GitHub modülü başarıyla import edildi")
except ImportError as e:
    print(f"❌ GitHub modülü import hatası: {e}")
    sys.exit(1)

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
    
    # GitHub API'yi test et
    test_github_api()
    
    print("\n✅ Test tamamlandı!")
    print("\nGitHub modülü kullanıma hazır. Web uygulamasında /github_repos sayfasını ziyaret edebilirsiniz.")

if __name__ == "__main__":
    main() 