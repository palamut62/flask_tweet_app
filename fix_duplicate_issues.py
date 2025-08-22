#!/usr/bin/env python3
"""
Duplicate Detection System Fix Script
Aynı haberlerin birden çok tweet olarak paylaşılması sorununu çözer
"""

import json
import hashlib
from datetime import datetime, timedelta
import os

def load_json(filename, default=None):
    """JSON dosyasını yükle"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ {filename} yükleme hatası: {e}")
    return default if default is not None else []

def save_json(filename, data):
    """JSON dosyasını kaydet"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ {filename} kaydetme hatası: {e}")
        return False

def generate_hash(title):
    """Başlıktan hash oluştur"""
    if not title or not title.strip():
        return ""
    return hashlib.md5(title.strip().encode('utf-8')).hexdigest()

def create_backup(filename):
    """Dosya yedeği oluştur"""
    if os.path.exists(filename):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filename}.backup_{timestamp}"
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = f.read()
            with open(backup_name, 'w', encoding='utf-8') as f:
                f.write(data)
            print(f"✅ Yedek oluşturuldu: {backup_name}")
            return True
        except Exception as e:
            print(f"❌ Yedek oluşturma hatası: {e}")
    return False

def fix_posted_articles():
    """Posted articles dosyasındaki duplicate sorunlarını çöz"""
    print("\n🔍 Posted Articles düzeltiliyor...")
    
    # Yedek oluştur
    create_backup("posted_articles.json")
    
    articles = load_json("posted_articles.json", [])
    if not articles:
        print("⚠️ Posted articles dosyası boş")
        return
    
    print(f"📊 {len(articles)} makale bulundu")
    
    # Hash'leri düzelt ve duplicate'ları temizle
    seen_hashes = set()
    seen_urls = set()
    fixed_articles = []
    hash_fixed = 0
    duplicates_removed = 0
    
    for article in articles:
        title = article.get('title', '').strip()
        url = article.get('url', '').strip()
        hash_value = article.get('hash', '').strip()
        
        # Boş başlık kontrolü
        if not title:
            print(f"⚠️ Boş başlık atlandı: {url[:50]}...")
            continue
        
        # Hash yoksa oluştur
        if not hash_value:
            hash_value = generate_hash(title)
            article['hash'] = hash_value
            hash_fixed += 1
            print(f"🔧 Hash oluşturuldu: {title[:50]}...")
        
        # Duplicate kontrolü
        is_duplicate = False
        
        if hash_value in seen_hashes:
            print(f"🔄 Hash duplicate kaldırıldı: {title[:50]}...")
            is_duplicate = True
            duplicates_removed += 1
        elif url in seen_urls:
            print(f"🔄 URL duplicate kaldırıldı: {title[:50]}...")
            is_duplicate = True
            duplicates_removed += 1
        
        if not is_duplicate:
            fixed_articles.append(article)
            seen_hashes.add(hash_value)
            seen_urls.add(url)
    
    # Düzeltilmiş veriyi kaydet
    if save_json("posted_articles.json", fixed_articles):
        print(f"✅ Posted articles düzeltildi:")
        print(f"   - Hash düzeltilen: {hash_fixed}")
        print(f"   - Duplicate kaldırılan: {duplicates_removed}")
        print(f"   - Kalan makale: {len(fixed_articles)}")
    else:
        print("❌ Posted articles kaydetme hatası")

def fix_pending_tweets():
    """Pending tweets dosyasındaki duplicate sorunlarını çöz"""
    print("\n🔍 Pending Tweets düzeltiliyor...")
    
    # Yedek oluştur
    create_backup("pending_tweets.json")
    
    tweets = load_json("pending_tweets.json", [])
    if not tweets:
        print("⚠️ Pending tweets dosyası boş")
        return
    
    print(f"📊 {len(tweets)} pending tweet bulundu")
    
    # Hash'leri düzelt ve duplicate'ları temizle
    seen_hashes = set()
    seen_urls = set()
    fixed_tweets = []
    hash_fixed = 0
    duplicates_removed = 0
    
    for tweet in tweets:
        article = tweet.get('article', {})
        title = article.get('title', '').strip()
        url = article.get('url', '').strip()
        hash_value = article.get('hash', '').strip()
        
        # Boş başlık kontrolü
        if not title:
            print(f"⚠️ Boş başlık atlandı: {url[:50]}...")
            continue
        
        # Hash yoksa oluştur
        if not hash_value:
            hash_value = generate_hash(title)
            article['hash'] = hash_value
            tweet['article'] = article
            hash_fixed += 1
            print(f"🔧 Hash oluşturuldu: {title[:50]}...")
        
        # Duplicate kontrolü
        is_duplicate = False
        
        if hash_value in seen_hashes:
            print(f"🔄 Hash duplicate kaldırıldı: {title[:50]}...")
            is_duplicate = True
            duplicates_removed += 1
        elif url in seen_urls:
            print(f"🔄 URL duplicate kaldırıldı: {title[:50]}...")
            is_duplicate = True
            duplicates_removed += 1
        
        if not is_duplicate:
            fixed_tweets.append(tweet)
            seen_hashes.add(hash_value)
            seen_urls.add(url)
    
    # Düzeltilmiş veriyi kaydet
    if save_json("pending_tweets.json", fixed_tweets):
        print(f"✅ Pending tweets düzeltildi:")
        print(f"   - Hash düzeltilen: {hash_fixed}")
        print(f"   - Duplicate kaldırılan: {duplicates_removed}")
        print(f"   - Kalan tweet: {len(fixed_tweets)}")
    else:
        print("❌ Pending tweets kaydetme hatası")

def remove_cross_duplicates():
    """Posted articles ve pending tweets arasındaki cross-duplicate'ları temizle"""
    print("\n🔍 Cross-duplicate'lar temizleniyor...")
    
    posted_articles = load_json("posted_articles.json", [])
    pending_tweets = load_json("pending_tweets.json", [])
    
    if not posted_articles or not pending_tweets:
        print("⚠️ Cross-duplicate kontrolü için yeterli veri yok")
        return
    
    # Posted articles'dan hash ve URL'leri topla
    posted_hashes = set()
    posted_urls = set()
    
    for article in posted_articles:
        hash_value = article.get('hash', '').strip()
        url = article.get('url', '').strip()
        if hash_value:
            posted_hashes.add(hash_value)
        if url:
            posted_urls.add(url)
    
    # Pending tweets'den cross-duplicate'ları kaldır
    fixed_pending = []
    cross_duplicates_removed = 0
    
    for tweet in pending_tweets:
        article = tweet.get('article', {})
        hash_value = article.get('hash', '').strip()
        url = article.get('url', '').strip()
        title = article.get('title', '').strip()
        
        is_cross_duplicate = False
        
        if hash_value in posted_hashes:
            print(f"🔄 Cross-duplicate (hash) kaldırıldı: {title[:50]}...")
            is_cross_duplicate = True
            cross_duplicates_removed += 1
        elif url in posted_urls:
            print(f"🔄 Cross-duplicate (URL) kaldırıldı: {title[:50]}...")
            is_cross_duplicate = True
            cross_duplicates_removed += 1
        
        if not is_cross_duplicate:
            fixed_pending.append(tweet)
    
    # Düzeltilmiş pending tweets'i kaydet
    if save_json("pending_tweets.json", fixed_pending):
        print(f"✅ Cross-duplicate'lar temizlendi: {cross_duplicates_removed} kaldırıldı")
    else:
        print("❌ Cross-duplicate temizleme hatası")

def enhance_duplicate_detection():
    """Duplicate detection sistemini geliştir"""
    print("\n🔧 Duplicate detection sistemi geliştiriliyor...")
    
    # Automation settings'i güncelle
    settings = load_json("automation_settings.json", {})
    
    # Duplicate detection ayarlarını optimize et
    settings.update({
        "enable_duplicate_detection": True,
        "title_similarity_threshold": 0.85,
        "content_similarity_threshold": 0.75,
        "hash_based_detection": True,
        "url_based_detection": True,
        "title_based_detection": True,
        "cross_check_enabled": True
    })
    
    if save_json("automation_settings.json", settings):
        print("✅ Automation settings güncellendi")
    else:
        print("❌ Automation settings güncelleme hatası")

def test_duplicate_detection():
    """Duplicate detection sistemini test et"""
    print("\n🧪 Duplicate detection sistemi test ediliyor...")
    
    posted_articles = load_json("posted_articles.json", [])
    pending_tweets = load_json("pending_tweets.json", [])
    
    # Hash kontrolü
    posted_hashes = [article.get('hash', '') for article in posted_articles]
    pending_hashes = [tweet.get('article', {}).get('hash', '') for tweet in pending_tweets]
    
    empty_hashes_posted = sum(1 for h in posted_hashes if not h)
    empty_hashes_pending = sum(1 for h in pending_hashes if not h)
    
    print(f"📊 Hash durumu:")
    print(f"   - Posted articles: {len(posted_articles)} makale, {empty_hashes_posted} boş hash")
    print(f"   - Pending tweets: {len(pending_tweets)} tweet, {empty_hashes_pending} boş hash")
    
    # Duplicate kontrolü
    posted_urls = [article.get('url', '') for article in posted_articles]
    pending_urls = [tweet.get('article', {}).get('url', '') for tweet in pending_tweets]
    
    posted_duplicates = len(posted_urls) - len(set(posted_urls))
    pending_duplicates = len(pending_urls) - len(set(pending_urls))
    
    print(f"📊 Duplicate durumu:")
    print(f"   - Posted articles: {posted_duplicates} duplicate")
    print(f"   - Pending tweets: {pending_duplicates} duplicate")
    
    # Cross-duplicate kontrolü
    posted_url_set = set(posted_urls)
    pending_url_set = set(pending_urls)
    cross_duplicates = len(posted_url_set.intersection(pending_url_set))
    
    print(f"📊 Cross-duplicate durumu:")
    print(f"   - Cross-duplicate: {cross_duplicates} adet")
    
    # Öneriler
    print(f"\n💡 Öneriler:")
    if empty_hashes_posted > 0 or empty_hashes_pending > 0:
        print(f"   - Boş hash'ler var, hash oluşturma gerekli")
    if posted_duplicates > 0 or pending_duplicates > 0:
        print(f"   - Duplicate'lar var, temizlik gerekli")
    if cross_duplicates > 0:
        print(f"   - Cross-duplicate'lar var, temizlik gerekli")
    if empty_hashes_posted == 0 and empty_hashes_pending == 0 and posted_duplicates == 0 and pending_duplicates == 0 and cross_duplicates == 0:
        print(f"   - ✅ Sistem sağlıklı görünüyor!")

def main():
    """Ana fonksiyon"""
    print("🚀 Duplicate Detection System Fix")
    print("=" * 50)
    
    # 1. Posted articles düzelt
    fix_posted_articles()
    
    # 2. Pending tweets düzelt
    fix_pending_tweets()
    
    # 3. Cross-duplicate'ları temizle
    remove_cross_duplicates()
    
    # 4. Duplicate detection sistemini geliştir
    enhance_duplicate_detection()
    
    # 5. Test et
    test_duplicate_detection()
    
    print("\n✅ Duplicate detection sistemi düzeltildi!")
    print("\n📋 Yapılan işlemler:")
    print("   1. Boş hash'ler oluşturuldu")
    print("   2. Duplicate makaleler temizlendi")
    print("   3. Cross-duplicate'lar kaldırıldı")
    print("   4. Duplicate detection ayarları optimize edildi")
    print("   5. Sistem test edildi")
    
    print("\n🔧 Önerilen sonraki adımlar:")
    print("   - Sistemi yeniden başlatın")
    print("   - Yeni makalelerin duplicate kontrolünü izleyin")
    print("   - Haftalık olarak test_duplicate_detection.py çalıştırın")

if __name__ == "__main__":
    main()
