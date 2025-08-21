#!/usr/bin/env python3
"""
Fix Empty Hashes Script
This script generates hash values for articles that are missing them
"""

import json
import hashlib
from datetime import datetime

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

def fix_posted_articles_hashes():
    """Fix empty hashes in posted_articles.json"""
    print("🔧 Fixing empty hashes in posted_articles.json...")
    
    articles = load_json("posted_articles.json", [])
    if not articles:
        print("⚠️ No articles found in posted_articles.json")
        return
    
    fixed_count = 0
    skipped_count = 0
    
    for article in articles:
        title = article.get('title', '').strip()
        hash_value = article.get('hash', '').strip()
        
        # Skip if already has hash
        if hash_value:
            skipped_count += 1
            continue
        
        # Skip if no title
        if not title:
            print(f"⚠️ Article with no title found: {article.get('url', 'No URL')[:50]}...")
            skipped_count += 1
            continue
        
        # Generate hash
        new_hash = generate_hash(title)
        article['hash'] = new_hash
        fixed_count += 1
        
        print(f"✅ Generated hash for: {title[:50]}...")
    
    # Save updated data
    if save_json("posted_articles.json", articles):
        print(f"✅ Fixed {fixed_count} articles, skipped {skipped_count} articles")
    else:
        print("❌ Failed to save updated posted_articles.json")

def fix_pending_tweets_hashes():
    """Fix empty hashes in pending_tweets.json"""
    print("🔧 Fixing empty hashes in pending_tweets.json...")
    
    tweets = load_json("pending_tweets.json", [])
    if not tweets:
        print("⚠️ No pending tweets found")
        return
    
    fixed_count = 0
    skipped_count = 0
    
    for tweet in tweets:
        article = tweet.get('article', {})
        title = article.get('title', '').strip()
        hash_value = article.get('hash', '').strip()
        
        # Skip if already has hash
        if hash_value:
            skipped_count += 1
            continue
        
        # Skip if no title
        if not title:
            print(f"⚠️ Tweet with no title found: {article.get('url', 'No URL')[:50]}...")
            skipped_count += 1
            continue
        
        # Generate hash
        new_hash = generate_hash(title)
        article['hash'] = new_hash
        tweet['article'] = article
        fixed_count += 1
        
        print(f"✅ Generated hash for: {title[:50]}...")
    
    # Save updated data
    if save_json("pending_tweets.json", tweets):
        print(f"✅ Fixed {fixed_count} tweets, skipped {skipped_count} tweets")
    else:
        print("❌ Failed to save updated pending_tweets.json")

def main():
    """Main function"""
    print("🚀 Starting hash generation process...")
    print("=" * 50)
    
    # Create backup
    print("💾 Creating backup...")
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        shutil.copy2("posted_articles.json", f"posted_articles_hash_backup_{timestamp}.json")
        shutil.copy2("pending_tweets.json", f"pending_tweets_hash_backup_{timestamp}.json")
        print("✅ Backup created successfully")
    except Exception as e:
        print(f"⚠️ Backup creation failed: {e}")
    
    print("=" * 50)
    
    # Fix hashes
    fix_posted_articles_hashes()
    print("-" * 30)
    
    fix_pending_tweets_hashes()
    print("=" * 50)
    
    print("🎉 Hash generation completed!")
    print("\n💡 Next steps:")
    print("- Run test_duplicate_detection.py to verify the fixes")
    print("- Monitor the application for any new duplicate issues")
    print("- The duplicate detection system should now work more effectively")

if __name__ == "__main__":
    main()
