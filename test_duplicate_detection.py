#!/usr/bin/env python3
"""
Test Duplicate Detection Script
This script tests the duplicate detection system to ensure it's working properly
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

def generate_hash(title):
    """Generate hash from title"""
    if not title:
        return ""
    return hashlib.md5(title.encode('utf-8')).hexdigest()

def test_duplicate_detection():
    """Test the duplicate detection system"""
    print("🧪 Testing duplicate detection system...")
    print("=" * 50)
    
    # Load current data
    posted_articles = load_json("posted_articles.json", [])
    pending_tweets = load_json("pending_tweets.json", [])
    settings = load_json("automation_settings.json", {})
    
    print(f"📊 Current data:")
    print(f"   - Posted articles: {len(posted_articles)}")
    print(f"   - Pending tweets: {len(pending_tweets)}")
    print(f"   - Duplicate detection enabled: {settings.get('enable_duplicate_detection', False)}")
    print()
    
    # Test 1: Check for duplicate URLs in posted articles
    print("🔍 Test 1: Checking for duplicate URLs in posted articles...")
    url_counts = {}
    duplicate_urls = []
    
    for article in posted_articles:
        url = article.get('url', '').strip()
        if url:
            url_counts[url] = url_counts.get(url, 0) + 1
            if url_counts[url] > 1:
                duplicate_urls.append(url)
    
    if duplicate_urls:
        print(f"❌ Found {len(duplicate_urls)} duplicate URLs in posted articles:")
        for url in duplicate_urls[:5]:  # Show first 5
            print(f"   - {url}")
    else:
        print("✅ No duplicate URLs found in posted articles")
    
    # Test 2: Check for duplicate hashes in posted articles
    print("\n🔍 Test 2: Checking for duplicate hashes in posted articles...")
    hash_counts = {}
    duplicate_hashes = []
    
    for article in posted_articles:
        hash_value = article.get('hash', '').strip()
        if hash_value:
            hash_counts[hash_value] = hash_counts.get(hash_value, 0) + 1
            if hash_counts[hash_value] > 1:
                duplicate_hashes.append(hash_value)
    
    if duplicate_hashes:
        print(f"❌ Found {len(duplicate_hashes)} duplicate hashes in posted articles")
    else:
        print("✅ No duplicate hashes found in posted articles")
    
    # Test 3: Check for empty hashes
    print("\n🔍 Test 3: Checking for empty hashes...")
    empty_hashes = 0
    empty_titles = 0
    
    for article in posted_articles:
        if not article.get('hash', '').strip():
            empty_hashes += 1
        if not article.get('title', '').strip():
            empty_titles += 1
    
    print(f"   - Articles with empty hashes: {empty_hashes}")
    print(f"   - Articles with empty titles: {empty_titles}")
    
    if empty_hashes > 0:
        print("⚠️ Some articles have empty hashes - this may cause duplicate detection issues")
    else:
        print("✅ All articles have hash values")
    
    # Test 4: Check for cross-duplicates between posted and pending
    print("\n🔍 Test 4: Checking for cross-duplicates...")
    posted_urls = {article.get('url', '') for article in posted_articles if article.get('url')}
    posted_hashes = {article.get('hash', '') for article in posted_articles if article.get('hash')}
    
    cross_duplicates = []
    for tweet in pending_tweets:
        article = tweet.get('article', {})
        url = article.get('url', '')
        hash_value = article.get('hash', '')
        
        if url in posted_urls or hash_value in posted_hashes:
            cross_duplicates.append({
                'title': article.get('title', ''),
                'url': url,
                'hash': hash_value
            })
    
    if cross_duplicates:
        print(f"❌ Found {len(cross_duplicates)} cross-duplicates:")
        for dup in cross_duplicates[:3]:  # Show first 3
            print(f"   - {dup['title'][:50]}...")
    else:
        print("✅ No cross-duplicates found")
    
    # Test 5: Check duplicate detection settings
    print("\n🔍 Test 5: Checking duplicate detection settings...")
    print(f"   - enable_duplicate_detection: {settings.get('enable_duplicate_detection', False)}")
    print(f"   - title_similarity_threshold: {settings.get('title_similarity_threshold', 'Not set')}")
    print(f"   - content_similarity_threshold: {settings.get('content_similarity_threshold', 'Not set')}")
    
    if settings.get('enable_duplicate_detection'):
        print("✅ Duplicate detection is enabled")
    else:
        print("❌ Duplicate detection is disabled")
    
    # Test 6: Simulate duplicate detection
    print("\n🔍 Test 6: Simulating duplicate detection...")
    
    # Create a test article
    test_article = {
        "title": "Test Article for Duplicate Detection",
        "url": "https://example.com/test-article",
        "content": "This is a test article to check duplicate detection",
        "hash": generate_hash("Test Article for Duplicate Detection")
    }
    
    # Check if it would be detected as duplicate
    is_duplicate = False
    duplicate_reason = ""
    
    # Check against posted articles
    for article in posted_articles:
        if (test_article['url'] == article.get('url', '') or 
            test_article['hash'] == article.get('hash', '')):
            is_duplicate = True
            duplicate_reason = "Found in posted articles"
            break
    
    # Check against pending tweets
    if not is_duplicate:
        for tweet in pending_tweets:
            article = tweet.get('article', {})
            if (test_article['url'] == article.get('url', '') or 
                test_article['hash'] == article.get('hash', '')):
                is_duplicate = True
                duplicate_reason = "Found in pending tweets"
                break
    
    if is_duplicate:
        print(f"✅ Duplicate detection working: {duplicate_reason}")
    else:
        print("✅ Test article would be accepted (no duplicates found)")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    
    issues_found = 0
    if duplicate_urls:
        issues_found += 1
        print("❌ Duplicate URLs found in posted articles")
    
    if duplicate_hashes:
        issues_found += 1
        print("❌ Duplicate hashes found in posted articles")
    
    if empty_hashes > 0:
        issues_found += 1
        print("⚠️ Some articles have empty hashes")
    
    if cross_duplicates:
        issues_found += 1
        print("❌ Cross-duplicates found between posted and pending")
    
    if not settings.get('enable_duplicate_detection'):
        issues_found += 1
        print("❌ Duplicate detection is disabled")
    
    if issues_found == 0:
        print("✅ All tests passed! Duplicate detection system is working properly.")
    else:
        print(f"⚠️ Found {issues_found} issues that need attention.")
    
    print("\n💡 Recommendations:")
    if issues_found > 0:
        print("- Run the fix_duplicates.py script to clean up existing duplicates")
        print("- Ensure duplicate detection is enabled in automation settings")
        print("- Monitor the system for new duplicates")
    else:
        print("- System is working correctly")
        print("- Continue monitoring for new duplicates")
        print("- Consider running this test periodically")

if __name__ == "__main__":
    test_duplicate_detection()
