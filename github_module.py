import os
import json
import requests
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Diğer modüllerden import
try:
    from utils import (
        terminal_log, load_json, save_json, gemini_call, 
        mcp_firecrawl_scrape
    )
    HISTORY_FILE = "posted_articles.json"
except ImportError as e:
    print(f"Import hatası: {e}")
    # Fallback fonksiyonlar
    def terminal_log(message, level="info"):
        print(f"[{level.upper()}] {message}")
    
    def load_json(filename, default=None):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default or []
    
    def save_json(filename, data):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def gemini_call(prompt, api_key, max_tokens=200):
        return None
    
    def mcp_firecrawl_scrape(params):
        return {"success": False, "error": "MCP not available"}
    
    HISTORY_FILE = "posted_articles.json"

def load_github_settings():
    """GitHub ayarlarını yükle"""
    try:
        return load_json("github_settings.json", {
            "default_language": "python",
            "default_time_period": "weekly", 
            "default_limit": 10,
            "search_topics": ["ai", "machine-learning", "deep-learning"],
            "custom_search_queries": [],
            "languages": ["python", "javascript", "typescript"],
            "time_periods": ["daily", "weekly", "monthly"]
        })
    except Exception as e:
        terminal_log(f"❌ GitHub ayarları yükleme hatası: {e}", "error")
        return {}

def save_github_settings(settings):
    """GitHub ayarlarını kaydet"""
    try:
        settings["last_updated"] = datetime.now().isoformat()
        save_json("github_settings.json", settings)
        terminal_log("✅ GitHub ayarları kaydedildi", "success")
        return True
    except Exception as e:
        terminal_log(f"❌ GitHub ayarları kaydetme hatası: {e}", "error")
        return False

def search_github_repos_by_topics(topics=None, language="python", time_period="weekly", limit=10):
    """Konulara göre GitHub repoları ara"""
    try:
        terminal_log(f"🔍 GitHub repoları konulara göre aranıyor: {topics}", "info")
        
        base_url = "https://api.github.com/search/repositories"
        
        # Tarih hesaplama
        if time_period == "daily":
            since_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        elif time_period == "weekly":
            since_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        else:  # monthly
            since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Arama sorgusu oluştur
        query_parts = [f"language:{language}", f"created:>{since_date}"]
        
        if topics:
            # Konuları arama sorgusuna ekle
            if isinstance(topics, str):
                topics = [topics]
            
            topic_queries = []
            for topic in topics:
                # Hem topic hem de description/name'de ara
                topic_queries.append(f'topic:"{topic}"')
                topic_queries.append(f'"{topic}" in:name,description')
            
            if topic_queries:
                query_parts.append(f"({' OR '.join(topic_queries)})")
        
        query = " ".join(query_parts)
        
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Tweet-Bot/1.0"
        }
        
        # GitHub token varsa ekle
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        repos = []
        
        for repo in data.get("items", []):
            repo_data = {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo.get("description", ""),
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "language": repo.get("language", ""),
                "created_at": repo["created_at"],
                "updated_at": repo["updated_at"],
                "owner": {
                    "login": repo["owner"]["login"],
                    "avatar_url": repo["owner"]["avatar_url"]
                },
                "topics": repo.get("topics", []),
                "license": repo.get("license", {}).get("name", "") if repo.get("license") else "",
                "open_issues": repo.get("open_issues_count", 0),
                "watchers": repo.get("watchers_count", 0),
                "search_topics": topics  # Hangi konularla bulunduğunu kaydet
            }
            repos.append(repo_data)
        
        terminal_log(f"✅ {len(repos)} GitHub repo bulundu (konular: {topics})", "success")
        return repos
        
    except requests.exceptions.RequestException as e:
        terminal_log(f"❌ GitHub API hatası: {e}", "error")
        return []
    except Exception as e:
        terminal_log(f"❌ GitHub konu araması hatası: {e}", "error")
        return []

def fetch_trending_github_repos(language="python", time_period="daily", limit=10):
    """GitHub'dan trend olan repoları çek"""
    try:
        print("🔍 GitHub trending repoları çekiliyor...")
        
        # GitHub API endpoint'i
        base_url = "https://api.github.com/search/repositories"
        
        # Tarih hesaplama
        if time_period == "daily":
            since_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        elif time_period == "weekly":
            since_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        else:  # monthly
            since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Arama parametreleri
        params = {
            "q": f"language:{language} created:>{since_date}",
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Tweet-Bot/1.0"
        }
        
        # GitHub token varsa ekle
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        repos = []
        
        for repo in data.get("items", []):
            repo_data = {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo.get("description", ""),
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "language": repo.get("language", ""),
                "created_at": repo["created_at"],
                "updated_at": repo["updated_at"],
                "owner": {
                    "login": repo["owner"]["login"],
                    "avatar_url": repo["owner"]["avatar_url"]
                },
                "topics": repo.get("topics", []),
                "license": repo.get("license", {}).get("name", "") if repo.get("license") else "",
                "open_issues": repo.get("open_issues_count", 0),
                "watchers": repo.get("watchers_count", 0)
            }
            repos.append(repo_data)
        
        print(f"✅ {len(repos)} GitHub repo çekildi")
        return repos
        
    except requests.exceptions.RequestException as e:
        print(f"❌ GitHub API hatası: {e}")
        return []
    except Exception as e:
        print(f"❌ GitHub repo çekme hatası: {e}")
        return []

def fetch_github_repo_details_with_mcp(repo_url):
    """MCP ile GitHub repo detaylarını çek"""
    try:
        terminal_log(f"🔍 GitHub repo detayları çekiliyor: {repo_url}", "info")
        
        # MCP ile repo sayfasını çek
        scrape_result = mcp_firecrawl_scrape({
            "url": repo_url,
            "formats": ["markdown"],
            "onlyMainContent": True,
            "waitFor": 2000
        })
        
        if not scrape_result.get("success", False):
            terminal_log("⚠️ MCP ile repo çekilemedi, fallback yönteme geçiliyor...", "warning")
            return fetch_github_repo_details_fallback(repo_url)
        
        content = scrape_result.get("markdown", "")
        
        # README içeriğini çıkar
        readme_content = ""
        if "README" in content:
            readme_start = content.find("README")
            if readme_start != -1:
                readme_content = content[readme_start:readme_start+2000]  # İlk 2000 karakter
        
        terminal_log("✅ GitHub repo detayları MCP ile çekildi", "success")
        return {
            "success": True,
            "content": content,
            "readme": readme_content,
            "method": "mcp"
        }
        
    except Exception as e:
        terminal_log(f"❌ MCP GitHub repo detay hatası: {e}", "error")
        return fetch_github_repo_details_fallback(repo_url)

def fetch_github_repo_details_fallback(repo_url):
    """Fallback yöntemi ile GitHub repo detaylarını çek"""
    try:
        terminal_log(f"🔄 Fallback ile GitHub repo detayları çekiliyor: {repo_url}", "info")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        response = requests.get(repo_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # README içeriğini çıkar
        readme_element = soup.find('article', class_='markdown-body')
        readme_content = ""
        if readme_element:
            readme_content = readme_element.get_text(strip=True)[:2000]
        
        # Repo açıklamasını çıkar
        description_element = soup.find('p', class_='f4')
        description = ""
        if description_element:
            description = description_element.get_text(strip=True)
        
        content = f"Repository: {repo_url}\n"
        if description:
            content += f"Description: {description}\n"
        if readme_content:
            content += f"README: {readme_content}\n"
        
        terminal_log("✅ GitHub repo detayları fallback ile çekildi", "success")
        return {
            "success": True,
            "content": content,
            "readme": readme_content,
            "description": description,
            "method": "fallback"
        }
        
    except Exception as e:
        terminal_log(f"❌ Fallback GitHub repo detay hatası: {e}", "error")
        return {
            "success": False,
            "error": str(e),
            "method": "fallback"
        }

def generate_github_tweet(repo_data, api_key):
    """GitHub repo için AI tweet oluştur"""
    try:
        terminal_log(f"🤖 GitHub repo için tweet oluşturuluyor: {repo_data['name']}", "info")
        
        # Repo detaylarını çek
        repo_details = fetch_github_repo_details_with_mcp(repo_data["url"])
        
        # Tweet için prompt hazırla
        prompt = f"""
        Create an English Tweet for GitHub Repository:
        
        Repository Information:
        - Name: {repo_data['name']}
        - Description: {repo_data['description']}
        - Language: {repo_data['language']}
        - Stars: {repo_data['stars']}
        - Forks: {repo_data['forks']}
        - Topics: {', '.join(repo_data['topics'][:5])}
        - Owner: {repo_data['owner']['login']}
        - URL: {repo_data['url']}
        
        README Content:
        {repo_details.get('readme', '')[:1000]}
        
        Please create an English tweet for this GitHub repository:
        1. Write in English (280 character limit)
        2. Highlight the key features of the repository
        3. Explain why it's interesting for developers
        4. Add relevant hashtags (#GitHub #OpenSource #Programming)
        5. Use emojis for visual appeal
        6. Keep it engaging and professional
        7. CRITICAL: You MUST include the exact URL at the end: {repo_data['url']}
        8. The URL must be the last line of your tweet
        9. Never modify, shorten, or omit the URL
        
        Required format:
        [Tweet description with emojis]
        
        [Hashtags like #GitHub #OpenSource #Programming]
        
        {repo_data['url']}
        
        EXAMPLE:
        🚀 Amazing Python project for AI development! ⭐ 500 stars
        
        #GitHub #OpenSource #Programming #Python
        
        https://github.com/example/repo
        """
        
        # Gemini API ile tweet oluştur
        tweet_response = gemini_call(prompt, api_key, max_tokens=200)
        
        if not tweet_response:
            # Fallback tweet
            tweet_text = create_fallback_github_tweet(repo_data)
        else:
            tweet_text = tweet_response.strip()
            
            # URL kontrolü - eğer URL tweet'te yoksa fallback kullan
            if repo_data['url'] not in tweet_text:
                terminal_log(f"⚠️ AI tweet'inde URL eksik, fallback kullanılıyor: {repo_data['name']}", "warning")
                tweet_text = create_fallback_github_tweet(repo_data)
        
        # Tweet'i temizle ve formatla
        if len(tweet_text) > 280:
            # URL'yi koruyarak kısalt
            url = repo_data['url']
            if url in tweet_text:
                # URL'den önceki kısmı kısalt
                url_index = tweet_text.find(url)
                before_url = tweet_text[:url_index]
                after_url = tweet_text[url_index:]
                
                if len(before_url) > 277 - len(after_url):
                    before_url = before_url[:274 - len(after_url)] + "..."
                
                tweet_text = before_url + after_url
            else:
                tweet_text = tweet_text[:277] + "..."
        
        terminal_log("✅ GitHub tweet oluşturuldu", "success")
        
        return {
            "success": True,
            "tweet": tweet_text,
            "repo_data": repo_data,
            "repo_details": repo_details
        }
        
    except Exception as e:
        terminal_log(f"❌ GitHub tweet oluşturma hatası: {e}", "error")
        
        # Fallback tweet
        tweet_text = create_fallback_github_tweet(repo_data)
        
        return {
            "success": False,
            "tweet": tweet_text,
            "repo_data": repo_data,
            "error": str(e)
        }

def create_fallback_github_tweet(repo_data):
    """Simple fallback tweet for GitHub repo in English"""
    try:
        name = repo_data.get('name', 'Unknown')
        description = repo_data.get('description', '')
        language = repo_data.get('language', '')
        stars = repo_data.get('stars', 0)
        url = repo_data.get('url', '')
        
        # URL ve hashtag'ler için sabit alan hesapla
        hashtags = f"\n\n#GitHub #OpenSource #Programming"
        if language:
            hashtags += f" #{language}"
        hashtags += f"\n\n{url}"
        
        # Sabit kısımlar için alan hesapla
        fixed_parts = f"🚀 {name}\n"
        
        # Açıklama varsa ekle
        if description:
            fixed_parts += f"{description}\n"
        
        # Dil ve yıldız bilgisi
        tech_info = ""
        if language:
            tech_info += f"💻 {language} "
        if stars > 0:
            tech_info += f"⭐ {stars} stars"
        
        if tech_info:
            fixed_parts += f"{tech_info}\n"
        
        # Açıklama için kalan alan hesapla ve gerekirse kırp
        total_length = len(fixed_parts) + len(hashtags)
        
        if total_length > 280:
            # Açıklamayı kısalt
            excess = total_length - 280
            if description:
                new_desc_length = len(description) - excess - 3  # "..." için 3 karakter
                if new_desc_length > 10:
                    description = description[:new_desc_length] + "..."
                    fixed_parts = f"🚀 {name}\n{description}\n"
                    if tech_info:
                        fixed_parts += f"{tech_info}\n"
                else:
                    # Açıklamayı tamamen çıkar
                    fixed_parts = f"🚀 {name}\n"
                    if tech_info:
                        fixed_parts += f"{tech_info}\n"
        
        # Final tweet'i oluştur
        tweet = fixed_parts + hashtags
        
        return tweet
        
    except Exception as e:
        return f"🚀 New GitHub project discovered!\n\n#GitHub #OpenSource #Programming\n\n{repo_data.get('url', '')}"

def fetch_github_articles_for_tweets():
    """GitHub repoları için tweet'leri hazırla ve pending_tweets.json'a kaydet"""
    try:
        terminal_log("🔍 GitHub repoları tweet'leri hazırlanıyor...", "info")
        
        # Trend repoları çek
        repos = fetch_trending_github_repos(language="python", time_period="daily", limit=5)
        
        if not repos:
            terminal_log("⚠️ GitHub repoları bulunamadı", "warning")
            return []
        
        # Mevcut pending tweets'leri yükle
        try:
            pending_tweets = load_json('pending_tweets.json')
        except:
            pending_tweets = []
        
        # Mevcut GitHub repo URL'lerini kontrol et (duplikasyon önleme)
        existing_urls = [tweet.get('url', '') for tweet in pending_tweets if tweet.get('source_type') == 'github']
        
        # Mevcut paylaşılan repoları da kontrol et
        try:
            posted_articles = load_json(HISTORY_FILE)
        except:
            posted_articles = []
        posted_urls = [article.get('url', '') for article in posted_articles]
        
        # Tweet'leri oluştur
        new_tweets = []
        api_key = os.environ.get('GOOGLE_API_KEY')
        
        for repo in repos:
            try:
                # Duplikasyon kontrolü
                if repo["url"] in existing_urls or repo["url"] in posted_urls:
                    terminal_log(f"⚠️ GitHub repo zaten mevcut: {repo['name']}", "warning")
                    continue
                
                tweet_result = generate_github_tweet(repo, api_key)
                
                if tweet_result.get("success"):
                    # Benzersiz ID oluştur
                    tweet_id = len(pending_tweets) + len(new_tweets) + 1
                    
                    tweet_data = {
                        "id": tweet_id,
                        "title": f"GitHub: {repo['name']}",
                        "content": tweet_result["tweet"],
                        "url": repo["url"],
                        "source": "GitHub",
                        "source_type": "github",
                        "created_at": datetime.now().isoformat(),
                        "repo_data": repo,
                        "is_posted": False,
                        "language": repo.get("language", ""),
                        "stars": repo.get("stars", 0),
                        "forks": repo.get("forks", 0),
                        "owner": repo.get("owner", {}).get("login", ""),
                        "topics": repo.get("topics", [])[:5],
                        "hash": hashlib.md5(repo["url"].encode()).hexdigest()
                    }
                    new_tweets.append(tweet_data)
                    terminal_log(f"✅ GitHub tweet hazırlandı: {repo['name']}", "success")
                else:
                    terminal_log(f"⚠️ GitHub tweet oluşturulamadı: {repo['name']}", "warning")
                    
            except Exception as e:
                terminal_log(f"❌ GitHub tweet hatası ({repo['name']}): {e}", "error")
                continue
        
        if new_tweets:
            # Yeni tweet'leri pending listesine ekle
            pending_tweets.extend(new_tweets)
            save_json('pending_tweets.json', pending_tweets)
            
            terminal_log(f"📊 {len(new_tweets)} GitHub tweet'i pending listesine eklendi", "success")
            
            # GitHub repo geçmişini kaydet
            for tweet in new_tweets:
                save_github_repo_history(tweet["repo_data"], {"success": True, "tweet": tweet["content"]})
        else:
            terminal_log("⚠️ Yeni GitHub tweet'i eklenmedi", "warning")
        
        return new_tweets
        
    except Exception as e:
        terminal_log(f"❌ GitHub tweet hazırlama hatası: {e}", "error")
        return []

def save_github_repo_history(repo_data, tweet_result):
    """GitHub repo paylaşım geçmişini kaydet"""
    try:
        # Mevcut geçmişi yükle
        try:
            posted_articles = load_json(HISTORY_FILE)
        except:
            posted_articles = []
        
        # Yeni kayıt oluştur
        new_record = {
            "title": f"{repo_data['name']} - GitHub Repository",
            "url": repo_data['url'],
            "content": repo_data.get('description', ''),
            "source": "GitHub",
            "published_date": repo_data.get('created_at', datetime.now().isoformat()),
            "posted_date": datetime.now().isoformat(),
            "hash": hashlib.md5(repo_data['url'].encode()).hexdigest(),
            "tweet_id": tweet_result.get('tweet_id'),
            "tweet_url": tweet_result.get('tweet_url', ''),
            "repo_data": repo_data,
            "type": "github_repo"
        }
        
        # Listeye ekle
        posted_articles.append(new_record)
        
        # Kaydet
        save_json(HISTORY_FILE, posted_articles)
        
        terminal_log(f"✅ GitHub repo geçmişi kaydedildi: {repo_data['name']}", "success")
        
    except Exception as e:
        terminal_log(f"❌ GitHub repo geçmişi kaydetme hatası: {e}", "error")

def get_github_stats():
    """GitHub modülü istatistiklerini getir"""
    try:
        try:
            posted_articles = load_json(HISTORY_FILE)
        except:
            posted_articles = []
        
        # GitHub repolarını filtrele
        github_repos = [article for article in posted_articles if article.get('type') == 'github_repo']
        
        # İstatistikleri hesapla
        total_repos = len(github_repos)
        
        # Dil dağılımı
        languages = {}
        for repo in github_repos:
            repo_data = repo.get('repo_data', {})
            lang = repo_data.get('language', 'Unknown')
            languages[lang] = languages.get(lang, 0) + 1
        
        # Son 7 günde paylaşılan
        week_ago = datetime.now() - timedelta(days=7)
        recent_repos = [
            repo for repo in github_repos 
            if datetime.fromisoformat(repo.get('posted_date', '2020-01-01')) > week_ago
        ]
        
        return {
            "total_repos": total_repos,
            "recent_repos": len(recent_repos),
            "languages": languages,
            "last_repo": github_repos[-1] if github_repos else None
        }
        
    except Exception as e:
        terminal_log(f"❌ GitHub istatistik hatası: {e}", "error")
        return {
            "total_repos": 0,
            "recent_repos": 0,
            "languages": {},
            "last_repo": None
        } 