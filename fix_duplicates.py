#!/usr/bin/env python3
"""
Duplicate Fix Script for Flask Tweet App
This script fixes duplicate entries in posted_articles.json and pending_tweets.json
"""

import json
import hashlib
from datetime import datetime
from collections import defaultdict

def load_json(filename, default=None):
    """Load JSON file safely"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else []

def save_json(filename, data):
    """Save JSON file safely"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        return False

def generate_hash(title):
    """Generate hash from title"""
    if not title:
        return ""
    return hashlib.md5(title.encode('utf-8')).hexdigest()

def clean_posted_articles():
    """Clean duplicate entries from posted_articles.json"""
    print("🔍 Cleaning posted_articles.json...")
    
    articles = load_json("posted_articles.json", [])
    if not articles:
        print("⚠️ No articles found in posted_articles.json")
        return
    
    print(f"📊 Found {len(articles)} articles")
    
    # Track unique entries by URL and hash
    seen_urls = set()
    seen_hashes = set()
    cleaned_articles = []
    duplicates_removed = 0
    
    for article in articles:
        url = article.get('url', '').strip()
        title = article.get('title', '').strip()
        hash_value = article.get('hash', '').strip()
        
        # Generate hash if missing
        if not hash_value and title:
            hash_value = generate_hash(title)
            article['hash'] = hash_value
        
        # Check for duplicates
        is_duplicate = False
        
        if url and url in seen_urls:
            print(f"🔄 Duplicate URL removed: {title[:50]}...")
            is_duplicate = True
        elif hash_value and hash_value in seen_hashes:
            print(f"🔄 Duplicate hash removed: {title[:50]}...")
            is_duplicate = True
        
        if not is_duplicate:
            cleaned_articles.append(article)
            if url:
                seen_urls.add(url)
            if hash_value:
                seen_hashes.add(hash_value)
        else:
            duplicates_removed += 1
    
    # Save cleaned data
    if save_json("posted_articles.json", cleaned_articles):
        print(f"✅ Cleaned posted_articles.json: {len(cleaned_articles)} articles kept, {duplicates_removed} duplicates removed")
    else:
        print("❌ Failed to save cleaned posted_articles.json")

def clean_pending_tweets():
    """Clean duplicate entries from pending_tweets.json"""
    print("🔍 Cleaning pending_tweets.json...")
    
    tweets = load_json("pending_tweets.json", [])
    if not tweets:
        print("⚠️ No pending tweets found")
        return
    
    print(f"📊 Found {len(tweets)} pending tweets")
    
    # Track unique entries by URL and hash
    seen_urls = set()
    seen_hashes = set()
    cleaned_tweets = []
    duplicates_removed = 0
    
    for tweet in tweets:
        article = tweet.get('article', {})
        url = article.get('url', '').strip()
        title = article.get('title', '').strip()
        hash_value = article.get('hash', '').strip()
        
        # Generate hash if missing
        if not hash_value and title:
            hash_value = generate_hash(title)
            article['hash'] = hash_value
            tweet['article'] = article
        
        # Check for duplicates
        is_duplicate = False
        
        if url and url in seen_urls:
            print(f"🔄 Duplicate URL removed: {title[:50]}...")
            is_duplicate = True
        elif hash_value and hash_value in seen_hashes:
            print(f"🔄 Duplicate hash removed: {title[:50]}...")
            is_duplicate = True
        
        if not is_duplicate:
            cleaned_tweets.append(tweet)
            if url:
                seen_urls.add(url)
            if hash_value:
                seen_hashes.add(hash_value)
        else:
            duplicates_removed += 1
    
    # Save cleaned data
    if save_json("pending_tweets.json", cleaned_tweets):
        print(f"✅ Cleaned pending_tweets.json: {len(cleaned_tweets)} tweets kept, {duplicates_removed} duplicates removed")
    else:
        print("❌ Failed to save cleaned pending_tweets.json")

def enable_duplicate_detection():
    """Enable duplicate detection in automation settings"""
    print("🔧 Enabling duplicate detection...")
    
    settings = load_json("automation_settings.json", {})
    
    # Update settings
    settings['enable_duplicate_detection'] = True
    settings['title_similarity_threshold'] = 0.85  # Slightly stricter
    settings['content_similarity_threshold'] = 0.75  # Slightly stricter
    settings['last_updated'] = datetime.now().isoformat()
    
    if save_json("automation_settings.json", settings):
        print("✅ Duplicate detection enabled in automation settings")
        print("   - enable_duplicate_detection: true")
        print("   - title_similarity_threshold: 0.85")
        print("   - content_similarity_threshold: 0.75")
    else:
        print("❌ Failed to update automation settings")

def check_cross_duplicates():
    """Check for duplicates between posted_articles.json and pending_tweets.json"""
    print("🔍 Checking for cross-duplicates...")
    
    posted_articles = load_json("posted_articles.json", [])
    pending_tweets = load_json("pending_tweets.json", [])
    
    # Get URLs and hashes from posted articles
    posted_urls = {article.get('url', '') for article in posted_articles if article.get('url')}
    posted_hashes = {article.get('hash', '') for article in posted_articles if article.get('hash')}
    
    # Check pending tweets for duplicates
    cross_duplicates = []
    
    for tweet in pending_tweets:
        article = tweet.get('article', {})
        url = article.get('url', '')
        hash_value = article.get('hash', '')
        title = article.get('title', '')
        
        if url in posted_urls or hash_value in posted_hashes:
            cross_duplicates.append({
                'title': title,
                'url': url,
                'hash': hash_value,
                'reason': 'URL in posted' if url in posted_urls else 'Hash in posted'
            })
    
    if cross_duplicates:
        print(f"⚠️ Found {len(cross_duplicates)} cross-duplicates:")
        for dup in cross_duplicates:
            print(f"   - {dup['title'][:50]}... ({dup['reason']})")
        
        # Remove cross-duplicates from pending tweets
        cleaned_pending = []
        for tweet in pending_tweets:
            article = tweet.get('article', {})
            url = article.get('url', '')
            hash_value = article.get('hash', '')
            
            if url not in posted_urls and hash_value not in posted_hashes:
                cleaned_pending.append(tweet)
        
        if save_json("pending_tweets.json", cleaned_pending):
            print(f"✅ Removed {len(cross_duplicates)} cross-duplicates from pending tweets")
    else:
        print("✅ No cross-duplicates found")

def main():
    """Main function to run all cleanup operations"""
    print("🚀 Starting duplicate cleanup process...")
    print("=" * 50)
    
    # Create backup
    print("💾 Creating backups...")
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        shutil.copy2("posted_articles.json", f"posted_articles_backup_{timestamp}.json")
        shutil.copy2("pending_tweets.json", f"pending_tweets_backup_{timestamp}.json")
        shutil.copy2("automation_settings.json", f"automation_settings_backup_{timestamp}.json")
        print("✅ Backups created successfully")
    except Exception as e:
        print(f"⚠️ Backup creation failed: {e}")
    
    print("=" * 50)
    
    # Run cleanup operations
    clean_posted_articles()
    print("-" * 30)
    
    clean_pending_tweets()
    print("-" * 30)
    
    check_cross_duplicates()
    print("-" * 30)
    
    enable_duplicate_detection()
    print("=" * 50)
    
    print("🎉 Duplicate cleanup completed!")
    print("\n📋 Summary of changes:")
    print("1. Removed duplicate entries from posted_articles.json")
    print("2. Removed duplicate entries from pending_tweets.json")
    print("3. Removed cross-duplicates between posted and pending")
    print("4. Enabled duplicate detection in automation settings")
    print("5. Generated missing hash values")
    print("\n💡 Recommendations:")
    print("- Monitor the application for a few days to ensure no new duplicates appear")
    print("- Consider running this script periodically (weekly/monthly)")
    print("- Check the automation settings to ensure duplicate detection remains enabled")

if __name__ == "__main__":
    main()
