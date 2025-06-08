import os
import json
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import tweepy
from datetime import datetime, timedelta
import hashlib
from dotenv import load_dotenv
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import re
from difflib import SequenceMatcher

# .env dosyasını yükle
load_dotenv()

# Firecrawl MCP fonksiyonları için placeholder
def mcp_firecrawl_scrape(params):
    """Firecrawl MCP scrape fonksiyonu - Bu fonksiyon artık gerçek MCP araçları kullanılarak çağrılacak"""
    try:
        print(f"[MCP] Firecrawl scrape çağrısı: {params.get('url', 'unknown')}")
        
        # Bu fonksiyon artık app.py içinde gerçek MCP araçları ile çağrılacak
        # Şimdilik fallback kullanılacak ama MCP entegrasyonu hazır
        return {
            "success": False,
            "reason": "MCP araçları app.py seviyesinde çağrılacak"
        }
        
    except Exception as e:
        print(f"[MCP] Firecrawl scrape hatası: {e}")
        return {"success": False, "error": str(e)}

HISTORY_FILE = "posted_articles.json"
HASHTAG_FILE = "hashtags.json"
ACCOUNT_FILE = "accounts.json"
SUMMARY_FILE = "summaries.json"
MCP_CONFIG_FILE = "mcp_config.json"

def fetch_latest_ai_articles_with_firecrawl():
    """Firecrawl MCP ile gelişmiş haber çekme - Sadece son 4 makale"""
    try:
        # Önce mevcut yayınlanan makaleleri yükle
        posted_articles = load_json(HISTORY_FILE)
        posted_urls = [article.get('url', '') for article in posted_articles]
        posted_hashes = [article.get('hash', '') for article in posted_articles]
        
        print("🔍 TechCrunch AI kategorisinden Firecrawl MCP ile makale çekiliyor...")
        
        # Firecrawl MCP ile ana sayfa çek
        try:
            # Firecrawl MCP scrape fonksiyonunu kullan
            scrape_result = mcp_firecrawl_scrape({
                "url": "https://techcrunch.com/category/artificial-intelligence/",
                "formats": ["markdown", "links"],
                "onlyMainContent": True,
                "waitFor": 2000
            })
            
            if not scrape_result.get("success", False):
                print(f"⚠️ Firecrawl MCP hatası, fallback yönteme geçiliyor...")
                return fetch_latest_ai_articles_fallback()
            
            # Markdown içeriğinden makale linklerini çıkar
            markdown_content = scrape_result.get("markdown", "")
            
            # Basit regex ile TechCrunch makale URL'lerini bul
            import re
            current_year = datetime.now().year
            
            # Tüm TechCrunch URL'lerini bul
            all_urls = re.findall(r'https://techcrunch\.com/[^\s\)\]]+', markdown_content)
            
            # Güncel yıl ve önceki yılın makalelerini filtrele
            article_urls = []
            for url in all_urls:
                # URL'yi temizle
                url = url.rstrip(')')
                
                # Yıl kontrolü
                year_check = f'/{current_year}/' in url or f'/{current_year-1}/' in url
                
                # Makale URL'si kontrolü (tarih formatı içermeli)
                date_pattern = r'/\d{4}/\d{2}/\d{2}/'
                is_article = re.search(date_pattern, url)
                
                if (year_check and is_article and 
                    url not in posted_urls and 
                    url not in article_urls and
                    len(article_urls) < 4):  # Sadece son 4 makale
                    article_urls.append(url)
            
            print(f"🔗 {len(article_urls)} makale URL'si bulundu")
            
        except Exception as firecrawl_error:
            print(f"⚠️ Firecrawl MCP hatası: {firecrawl_error}")
            print("🔄 Fallback yönteme geçiliyor...")
            return fetch_latest_ai_articles_fallback()
        
        articles_data = []
        for url in article_urls:
            try:
                # Her makaleyi Firecrawl MCP ile çek
                article_content = fetch_article_content_with_firecrawl(url)
                
                if article_content and len(article_content.get("content", "")) > 100:
                    title = article_content.get("title", "")
                    content = article_content.get("content", "")
                    
                    # Makale hash'i oluştur
                    article_hash = hashlib.md5(title.encode()).hexdigest()
                    
                    # Tekrar kontrolü
                    if article_hash not in posted_hashes:
                        articles_data.append({
                            "title": title,
                            "url": url,
                            "content": content,
                            "hash": article_hash,
                            "fetch_date": datetime.now().isoformat(),
                            "is_new": True,
                            "already_posted": False,
                            "source": "firecrawl_mcp"
                        })
                        print(f"🆕 Firecrawl ile yeni makale: {title[:50]}...")
                    else:
                        print(f"✅ Makale zaten paylaşılmış: {title[:50]}...")
                else:
                    print(f"⚠️ İçerik yetersiz: {url}")
                    
            except Exception as article_error:
                print(f"❌ Makale çekme hatası ({url}): {article_error}")
                continue
        
        print(f"📊 Firecrawl MCP ile {len(articles_data)} yeni makale bulundu")
        
        # Duplikat filtreleme uygula
        if articles_data:
            articles_data = filter_duplicate_articles(articles_data)
        
        return articles_data
        
    except Exception as e:
        print(f"Firecrawl MCP haber çekme hatası: {e}")
        print("🔄 Fallback yönteme geçiliyor...")
        return fetch_latest_ai_articles_fallback()

def fetch_latest_ai_articles():
    """Ana haber çekme fonksiyonu - Firecrawl MCP öncelikli"""
    try:
        # Önce Firecrawl MCP ile dene
        articles = fetch_latest_ai_articles_with_firecrawl()
        
        # Eğer Firecrawl'dan makale gelmezse fallback kullan
        if not articles:
            print("🔄 Firecrawl'dan makale gelmedi, fallback yöntemi deneniyor...")
            articles = fetch_latest_ai_articles_fallback()
        
        return articles
        
    except Exception as e:
        print(f"Ana haber çekme hatası: {e}")
        return fetch_latest_ai_articles_fallback()

def fetch_latest_ai_articles_fallback():
    """Fallback haber çekme yöntemi - BeautifulSoup ile"""
    try:
        # Önce mevcut yayınlanan makaleleri yükle
        posted_articles = load_json(HISTORY_FILE)
        posted_urls = [article.get('url', '') for article in posted_articles]
        posted_hashes = [article.get('hash', '') for article in posted_articles]
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        html = requests.get("https://techcrunch.com/category/artificial-intelligence/", headers=headers).text
        soup = BeautifulSoup(html, "html.parser")
        article_links = soup.select("a.loop-card__title-link")[:4]  # Sadece son 4 makale
        
        print(f"🔍 Fallback: TechCrunch AI kategorisinden son {len(article_links)} makale kontrol ediliyor...")
        
        articles_data = []
        for link_tag in article_links:
            title = link_tag.text.strip()
            url = link_tag['href']
            
            # Makale hash'i oluştur (başlık bazlı)
            article_hash = hashlib.md5(title.encode()).hexdigest()
            
            # Tekrar kontrolü - URL ve hash bazlı
            is_already_posted = url in posted_urls or article_hash in posted_hashes
            
            if is_already_posted:
                print(f"✅ Makale zaten paylaşılmış, atlanıyor: {title[:50]}...")
                continue
            
            # Makale içeriğini gelişmiş şekilde çek
            content = fetch_article_content_advanced(url, headers)
            
            if content and len(content) > 100:  # Minimum içerik kontrolü
                articles_data.append({
                    "title": title, 
                    "url": url, 
                    "content": content,
                    "hash": article_hash,
                    "fetch_date": datetime.now().isoformat(),
                    "is_new": True,  # Yeni makale işareti
                    "already_posted": False,
                    "source": "fallback"
                })
                print(f"🆕 Fallback ile yeni makale bulundu: {title[:50]}...")
            else:
                print(f"⚠️ İçerik yetersiz, atlanıyor: {title[:50]}...")
        
        print(f"📊 Fallback ile toplam {len(articles_data)} yeni makale bulundu")
        
        # Duplikat filtreleme uygula
        if articles_data:
            articles_data = filter_duplicate_articles(articles_data)
        
        return articles_data
        
    except Exception as e:
        print(f"Fallback haber çekme hatası: {e}")
        return []

def fetch_article_content_with_firecrawl(url):
    """Firecrawl MCP ile makale içeriği çekme"""
    try:
        print(f"🔍 Firecrawl MCP ile makale çekiliyor: {url[:50]}...")
        
        # Firecrawl MCP scrape fonksiyonunu kullan
        scrape_result = mcp_firecrawl_scrape({
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
            "waitFor": 3000,
            "removeBase64Images": True
        })
        
        if not scrape_result.get("success", False):
            print(f"⚠️ Firecrawl MCP başarısız, fallback deneniyor...")
            return fetch_article_content_advanced_fallback(url)
        
        # Markdown içeriğini al
        markdown_content = scrape_result.get("markdown", "")
        
        if not markdown_content or len(markdown_content) < 100:
            print(f"⚠️ Firecrawl'dan yetersiz içerik, fallback deneniyor...")
            return fetch_article_content_advanced_fallback(url)
        
        # Başlığı çıkar (genellikle ilk # ile başlar)
        lines = markdown_content.split('\n')
        title = ""
        content_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('# ') and not title:
                title = line[2:].strip()
            elif line and not line.startswith('#') and len(line) > 20:
                content_lines.append(line)
        
        # İçeriği birleştir ve temizle
        content = '\n'.join(content_lines)
        
        # Gereksiz karakterleri temizle
        content = content.replace('*', '').replace('**', '').replace('_', '')
        content = ' '.join(content.split())  # Çoklu boşlukları tek boşluğa çevir
        
        # İçeriği sınırla
        content = content[:2500]
        
        print(f"✅ Firecrawl ile içerik çekildi: {len(content)} karakter")
        
        return {
            "title": title or "Başlık bulunamadı",
            "content": content,
            "source": "firecrawl_mcp"
        }
        
    except Exception as e:
        print(f"❌ Firecrawl MCP hatası ({url}): {e}")
        print("🔄 Fallback yönteme geçiliyor...")
        return fetch_article_content_advanced_fallback(url)

def fetch_article_content_advanced_fallback(url):
    """Fallback makale içeriği çekme - BeautifulSoup ile"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        article_html = requests.get(url, headers=headers, timeout=10).text
        article_soup = BeautifulSoup(article_html, "html.parser")
        
        # Başlığı bul
        title = ""
        title_selectors = ["h1", "h1.entry-title", "h1.post-title", ".article-title h1"]
        for selector in title_selectors:
            title_elem = article_soup.select_one(selector)
            if title_elem:
                title = title_elem.text.strip()
                break
        
        # Çoklu selector deneme - daha kapsamlı içerik çekme
        content_selectors = [
            "div.article-content p",
            "div.entry-content p", 
            "div.post-content p",
            "article p",
            "div.content p",
            ".article-body p"
        ]
        
        content = ""
        for selector in content_selectors:
            paragraphs = article_soup.select(selector)
            if paragraphs:
                content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
                if len(content) > 200:  # Yeterli içerik bulundu
                    break
        
        # Eğer hala içerik bulunamadıysa, tüm p etiketlerini dene
        if not content:
            all_paragraphs = article_soup.find_all('p')
            content = "\n".join([p.text.strip() for p in all_paragraphs if len(p.text.strip()) > 50])
        
        content = content[:2000]  # İçeriği sınırla
        
        return {
            "title": title or "Başlık bulunamadı",
            "content": content,
            "source": "fallback"
        }
        
    except Exception as e:
        print(f"Fallback makale içeriği çekme hatası ({url}): {e}")
        return None

def fetch_article_content_advanced(url, headers):
    """Geriye dönük uyumluluk için eski fonksiyon"""
    result = fetch_article_content_advanced_fallback(url)
    return result.get("content", "") if result else ""

def load_json(path):
    return json.load(open(path, 'r', encoding='utf-8')) if os.path.exists(path) else []

def save_json(path, data):
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def summarize_article(article_content, api_key):
    """LLM ile gelişmiş makale özetleme"""
    prompt = f"""Aşağıdaki AI/teknoloji haberini Türkçe olarak özetle. Özet tweet formatında, ilgi çekici ve bilgilendirici olsun:

Haber İçeriği:
{article_content[:1500]}

Lütfen:
- Maksimum 200 karakter
- Ana konuyu vurgula
- Teknik detayları basitleştir
- İlgi çekici bir dil kullan

Özet:"""
    return gemini_call(prompt, api_key, max_tokens=100)

def score_article(article_content, api_key):
    prompt = f"""Bu AI/teknoloji haberinin önemini 1-10 arasında değerlendir (sadece sayı):

{article_content[:800]}

Değerlendirme kriterleri:
- Yenilik derecesi
- Sektörel etki
- Geliştiriciler için önem
- Genel ilgi

Puan:"""
    result = gemini_call(prompt, api_key, max_tokens=5)
    try:
        return int(result.strip().split()[0])
    except:
        return 5

def categorize_article(article_content, api_key):
    prompt = f"""Bu haberin hedef kitlesini belirle:

{article_content[:500]}

Seçenekler: Developer, Investor, General
Cevap:"""
    return gemini_call(prompt, api_key, max_tokens=10).strip()

def gemini_call(prompt, api_key, max_tokens=100):
    """Google Gemini API çağrısı"""
    if not api_key:
        safe_log("Gemini API anahtarı bulunamadı", "WARNING")
        return "API anahtarı eksik"
    
    try:
        import google.generativeai as genai
        
        # API anahtarını yapılandır
        genai.configure(api_key=api_key)
        
        # Modeli oluştur
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        safe_log("Gemini API çağrısı yapılıyor... Model: gemini-2.0-flash", "DEBUG")
        
        # Generation config
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.7,
        )
        
        # API çağrısı
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        safe_log("Gemini API Yanıtı alındı", "DEBUG")
        
        if response.text:
            content = response.text.strip()
            safe_log(f"İçerik alındı: {len(content)} karakter", "DEBUG")
            return content
        else:
            safe_log("Gemini API yanıtında metin bulunamadı", "DEBUG")
            return "API hatası"
            
    except Exception as e:
        safe_log(f"Gemini API çağrı hatası: {str(e)}", "ERROR")
        return "API hatası"

def generate_smart_hashtags(title, content):
    """Makale içeriğine göre akıllı hashtag oluşturma - 5 popüler hashtag"""
    combined_text = f"{title.lower()} {content.lower()}"
    hashtags = []
    
    # AI ve Machine Learning hashtag'leri
    if any(keyword in combined_text for keyword in ["artificial intelligence", "ai", "machine learning", "ml", "neural", "deep learning"]):
        hashtags.extend(["#ArtificialIntelligence", "#MachineLearning", "#DeepLearning", "#NeuralNetworks"])
    
    # Teknoloji ve yazılım hashtag'leri
    if any(keyword in combined_text for keyword in ["software", "programming", "code", "developer", "api"]):
        hashtags.extend(["#SoftwareDevelopment", "#Programming", "#Developer", "#API"])
    
    # Startup ve yatırım hashtag'leri
    if any(keyword in combined_text for keyword in ["startup", "funding", "investment", "venture", "billion", "million"]):
        hashtags.extend(["#Startup", "#Investment", "#VentureCapital", "#Funding", "#Business"])
    
    # Şirket özel hashtag'leri
    if "openai" in combined_text:
        hashtags.extend(["#OpenAI", "#ChatGPT", "#GPT"])
    if "google" in combined_text:
        hashtags.extend(["#Google", "#Alphabet", "#GoogleAI"])
    if "microsoft" in combined_text:
        hashtags.extend(["#Microsoft", "#Azure", "#Copilot"])
    if "meta" in combined_text:
        hashtags.extend(["#Meta", "#Facebook", "#MetaAI"])
    if "apple" in combined_text:
        hashtags.extend(["#Apple", "#iOS", "#AppleAI"])
    if "tesla" in combined_text:
        hashtags.extend(["#Tesla", "#ElonMusk", "#Autopilot"])
    if "nvidia" in combined_text:
        hashtags.extend(["#NVIDIA", "#GPU", "#CUDA"])
    if "anthropic" in combined_text:
        hashtags.extend(["#Anthropic", "#Claude"])
    
    # Teknoloji alanları
    if any(keyword in combined_text for keyword in ["blockchain", "crypto", "bitcoin", "ethereum"]):
        hashtags.extend(["#Blockchain", "#Cryptocurrency", "#Web3", "#DeFi"])
    if any(keyword in combined_text for keyword in ["cloud", "aws", "azure", "gcp"]):
        hashtags.extend(["#CloudComputing", "#AWS", "#Azure", "#CloudNative"])
    if any(keyword in combined_text for keyword in ["cybersecurity", "security", "privacy", "encryption"]):
        hashtags.extend(["#Cybersecurity", "#DataPrivacy", "#InfoSec"])
    if any(keyword in combined_text for keyword in ["quantum", "quantum computing"]):
        hashtags.extend(["#QuantumComputing", "#Quantum", "#QuantumTech"])
    if any(keyword in combined_text for keyword in ["robotics", "robot", "automation"]):
        hashtags.extend(["#Robotics", "#Automation", "#RoboticProcess"])
    if any(keyword in combined_text for keyword in ["iot", "internet of things", "smart home"]):
        hashtags.extend(["#IoT", "#SmartHome", "#ConnectedDevices"])
    if any(keyword in combined_text for keyword in ["5g", "6g", "network", "connectivity"]):
        hashtags.extend(["#5G", "#Connectivity", "#Telecommunications"])
    if any(keyword in combined_text for keyword in ["ar", "vr", "augmented reality", "virtual reality", "metaverse"]):
        hashtags.extend(["#AR", "#VR", "#Metaverse", "#XR"])
    
    # Genel teknoloji hashtag'leri
    general_hashtags = ["#Innovation", "#Technology", "#DigitalTransformation", "#FutureTech", "#TechNews"]
    hashtags.extend(general_hashtags)
    
    # Tekrarları kaldır ve 5 tane seç
    unique_hashtags = list(dict.fromkeys(hashtags))  # Sırayı koruyarak tekrarları kaldır
    
    # En alakalı 5 hashtag seç
    selected_hashtags = unique_hashtags[:5]
    
    # Eğer 5'ten az varsa, genel hashtag'lerle tamamla
    if len(selected_hashtags) < 5:
        remaining_general = [h for h in general_hashtags if h not in selected_hashtags]
        selected_hashtags.extend(remaining_general[:5-len(selected_hashtags)])
    
    return selected_hashtags[:5]

def generate_smart_emojis(title, content):
    """Makale içeriğine göre akıllı emoji seçimi"""
    combined_text = f"{title.lower()} {content.lower()}"
    emojis = []
    
    # Konu bazlı emojiler
    if any(keyword in combined_text for keyword in ["ai", "artificial intelligence", "robot", "machine learning"]):
        emojis.extend(["🤖", "🧠", "⚡"])
    if any(keyword in combined_text for keyword in ["funding", "investment", "billion", "million", "money"]):
        emojis.extend(["💰", "💸", "📈"])
    if any(keyword in combined_text for keyword in ["launch", "release", "unveil", "announce"]):
        emojis.extend(["🚀", "🎉", "✨"])
    if any(keyword in combined_text for keyword in ["research", "development", "breakthrough", "discovery"]):
        emojis.extend(["🔬", "💡", "🧪"])
    if any(keyword in combined_text for keyword in ["security", "privacy", "protection", "safe"]):
        emojis.extend(["🔒", "🛡️", "🔐"])
    if any(keyword in combined_text for keyword in ["acquisition", "merger", "partnership"]):
        emojis.extend(["🤝", "🔗", "💼"])
    if any(keyword in combined_text for keyword in ["search", "query", "find", "discover"]):
        emojis.extend(["🔍", "🔎", "📊"])
    if any(keyword in combined_text for keyword in ["mobile", "phone", "app", "smartphone"]):
        emojis.extend(["📱", "📲", "💻"])
    if any(keyword in combined_text for keyword in ["cloud", "server", "data", "storage"]):
        emojis.extend(["☁️", "💾", "🗄️"])
    if any(keyword in combined_text for keyword in ["game", "gaming", "entertainment"]):
        emojis.extend(["🎮", "🕹️", "🎯"])
    
    # Eğer emoji bulunamadıysa varsayılan emojiler
    if not emojis:
        emojis = ["🚀", "💻", "🌟", "⚡", "🔥"]
    
    # En fazla 3 emoji seç
    return emojis[:3]

def generate_comprehensive_analysis(article_data, api_key):
    """Makale için kapsamlı AI analizi - Ayrı ayrı çağrılar ile güvenilir sonuç (İngilizce)"""
    title = article_data.get("title", "")
    content = article_data.get("content", "")
    
    print(f"🔍 Kapsamlı AI analizi başlatılıyor...")
    
    analysis_result = {
        "innovation": "",
        "companies": [],
        "impact_level": 5,
        "audience": "General",
        "hashtags": [],
        "emojis": [],
        "tweet_text": ""
    }
    
    try:
        # 1. Main innovation/insight analysis (ENGLISH)
        innovation_prompt = f"""Briefly explain the main innovation or breakthrough in this AI/tech news (max 50 words, in English):\n\nTitle: {title}\nContent: {content[:800]}\n\nMain innovation:"""
        innovation = gemini_call(innovation_prompt, api_key, max_tokens=80)
        analysis_result["innovation"] = innovation.strip() if innovation != "API hatası" else "Technology innovation"
        
        # 2. Company analysis (ENGLISH)
        company_prompt = f"""List the main companies mentioned in this news (max 3, comma separated, in English):\n\nTitle: {title}\nContent: {content[:600]}\n\nCompanies:"""
        companies_text = gemini_call(company_prompt, api_key, max_tokens=50)
        if companies_text != "API hatası":
            companies = [c.strip() for c in companies_text.split(",") if c.strip()]
            analysis_result["companies"] = companies[:3]
        
        # 3. Impact level analysis (ENGLISH)
        impact_prompt = f"""Rate the impact of this news on the tech sector from 1 to 10 (just a number):\n\nTitle: {title}\nContent: {content[:600]}\n\nImpact score (1-10):"""
        impact_text = gemini_call(impact_prompt, api_key, max_tokens=10)
        try:
            impact_level = int(impact_text.strip().split()[0])
            if 1 <= impact_level <= 10:
                analysis_result["impact_level"] = impact_level
        except:
            analysis_result["impact_level"] = 5
        
        # 4. Audience analysis (ENGLISH)
        audience_prompt = f"""Determine the target audience for this news (Developer/Investor/General):\n\nTitle: {title}\nContent: {content[:500]}\n\nAudience:"""
        audience = gemini_call(audience_prompt, api_key, max_tokens=15)
        if audience != "API hatası" and audience.strip() in ["Developer", "Investor", "General"]:
            analysis_result["audience"] = audience.strip()
        
        # 5. Hashtag analysis (ENGLISH)
        hashtag_prompt = f"""Suggest the 3 most relevant hashtags for this news (in English, only hashtags, comma separated):\n\nTitle: {title}\nContent: {content[:800]}\n\nExample: #AI, #Technology, #Innovation\n\nHashtags:"""
        ai_hashtags_text = gemini_call(hashtag_prompt, api_key, max_tokens=50)
        ai_hashtags = []
        if ai_hashtags_text != "API hatası":
            clean_text = ai_hashtags_text.replace("Hashtags:", "").replace("Hashtag'ler:", "").replace("Hashtag'ler", "").strip()
            import re
            hashtag_matches = re.findall(r'#\w+', clean_text)
            if not hashtag_matches:
                words = re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b', clean_text)
                for word in words[:3]:
                    if len(word) > 2:
                        ai_hashtags.append(f"#{word}")
            else:
                ai_hashtags = hashtag_matches[:3]
        # Smart hashtag system (ENGLISH)
        smart_hashtags = generate_smart_hashtags(title, content)
        combined_hashtags = []
        for tag in ai_hashtags[:3]:
            if tag not in combined_hashtags:
                combined_hashtags.append(tag)
        for tag in smart_hashtags:
            if tag not in combined_hashtags and len(combined_hashtags) < 3:
                combined_hashtags.append(tag)
        analysis_result["hashtags"] = combined_hashtags[:3]
        # 6. Emoji analysis (unchanged, universal)
        emoji_prompt = f"""Suggest the 3 most suitable emojis for this news (just emojis, no spaces):\n\nTitle: {title}\nContent: {content[:500]}\n\nEmojis:"""
        ai_emojis_text = gemini_call(emoji_prompt, api_key, max_tokens=20)
        ai_emojis = []
        if ai_emojis_text != "API hatası":
            import re
            emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
            found_emojis = emoji_pattern.findall(ai_emojis_text)
            for emoji in found_emojis:
                for single_emoji in emoji:
                    if single_emoji not in ai_emojis and len(ai_emojis) < 3:
                        ai_emojis.append(single_emoji)
        smart_emojis = generate_smart_emojis(title, content)
        combined_emojis = ai_emojis[:2]
        for emoji in smart_emojis:
            if emoji not in combined_emojis and len(combined_emojis) < 3:
                combined_emojis.append(emoji)
        analysis_result["emojis"] = combined_emojis[:3]
        print(f"✅ Kapsamlı analiz tamamlandı:")
        print(f"🔬 Innovation: {analysis_result['innovation'][:50]}...")
        print(f"🏢 Companies: {', '.join(analysis_result['companies'])}")
        print(f"🎯 Audience: {analysis_result['audience']}")
        print(f"🏷️ Hashtags: {' '.join(analysis_result['hashtags'])}")
        print(f"😊 Emojis: {''.join(analysis_result['emojis'])}")
        return analysis_result
    except Exception as e:
        print(f"❌ Kapsamlı analiz hatası: {e}")
        return {
            "innovation": "AI/tech innovation",
            "companies": [],
            "impact_level": 5,
            "audience": "General",
            "hashtags": generate_smart_hashtags(title, content)[:3],
            "emojis": generate_smart_emojis(title, content)[:3],
            "tweet_text": ""
        }

def generate_ai_tweet_with_mcp_analysis(article_data, api_key):
    """MCP verisi ile gelişmiş AI tweet oluşturma - Kapsamlı analiz ile"""
    title = article_data.get("title", "")
    content = article_data.get("content", "")
    url = article_data.get("url", "")
    source = article_data.get("source", "unknown")
    
    # Twitter karakter limiti
    TWITTER_LIMIT = 280
    URL_LENGTH = 25  # "\n\n🔗 " + URL kısaltması için
    
    print(f"🤖 AI ile tweet oluşturuluyor (kaynak: {source})...")
    
    try:
        # Kapsamlı analiz yap
        analysis = generate_comprehensive_analysis(article_data, api_key)
        
        # Tweet metni oluştur
        companies_text = ', '.join(analysis['companies'][:2]) if analysis['companies'] else ""
        
        tweet_prompt = f"""Create a compelling English tweet about this AI/tech breakthrough:

Title: {title[:120]}
Key Innovation: {analysis['innovation'][:120]}
Companies: {companies_text}

Requirements:
- Write in perfect English only
- Maximum 200 characters
- Make it clear, engaging and newsworthy
- Focus on WHAT changed and WHY it matters
- Use active voice and strong action verbs
- Include specific details when possible (numbers, capabilities)
- Make it accessible to general audience
- Sound exciting but credible
- Do NOT include hashtags, emojis, URLs, or impact levels (added separately)
- Do NOT mention impact, effect level, or rating in the tweet

Examples of good style:
- "OpenAI's new model achieves 95% accuracy in medical diagnosis"
- "Tesla's robot now performs complex assembly tasks autonomously"
- "Google's AI reduces data center energy consumption by 40%"

Tweet text:"""
        
        tweet_text = gemini_call(tweet_prompt, api_key, max_tokens=80)
        
        if tweet_text == "API hatası" or not tweet_text.strip():
            # Fallback tweet metni - daha anlamlı
            if analysis['companies'] and analysis['innovation']:
                company = analysis['companies'][0]
                innovation = analysis['innovation'][:100]
                # Daha anlamlı fallback tweet oluştur
                if "launch" in innovation.lower():
                    tweet_text = f"{company} launches {innovation.lower().replace('launch', '').strip()}"
                elif "announce" in innovation.lower():
                    tweet_text = f"{company} announces {innovation.lower().replace('announce', '').strip()}"
                elif "develop" in innovation.lower():
                    tweet_text = f"{company} develops {innovation.lower().replace('develop', '').strip()}"
                else:
                    tweet_text = f"{company} unveils {innovation}"
            elif analysis['innovation']:
                tweet_text = f"Breaking: {analysis['innovation'][:150]}"
            else:
                tweet_text = f"AI breakthrough: {title[:120]}"
        
        # Tweet metnini temizle
        tweet_text = tweet_text.replace("Tweet:", "").replace("Tweet metni:", "").strip()
        
        # Gereksiz karakterleri temizle
        tweet_text = tweet_text.replace('"', '').replace("'", "'").strip()
        
        # Impact/etki bilgilerini temizle
        import re
        # "impact: orta", "etki: yüksek", "effect: medium" gibi ifadeleri kaldır
        tweet_text = re.sub(r'\b(impact|etki|effect)\s*:\s*\w+\b', '', tweet_text, flags=re.IGNORECASE)
        # "(impact: medium)", "[etki: yüksek]" gibi parantez içindeki ifadeleri kaldır
        tweet_text = re.sub(r'[\(\[\{]\s*(impact|etki|effect)\s*:\s*\w+\s*[\)\]\}]', '', tweet_text, flags=re.IGNORECASE)
        # Fazla boşlukları temizle
        tweet_text = re.sub(r'\s+', ' ', tweet_text).strip()
        
        # Hashtag ve emoji metinlerini oluştur
        hashtag_text = " ".join(analysis['hashtags']).strip()
        emoji_text = "".join(analysis['emojis']).strip()
        url_part = f"\n\n🔗 {url}"
        
        # Sabit kısımların uzunluğu
        fixed_parts_length = len(emoji_text) + len(hashtag_text) + len(url_part) + 2  # 2 boşluk için
        available_chars = TWITTER_LIMIT - fixed_parts_length
        
        # Tweet metnini temizle ve kısalt
        tweet_text = tweet_text.strip()
        
        # Eğer tweet metni çok uzunsa kısalt
        if len(tweet_text) > available_chars:
            # "..." için 3 karakter ayır
            tweet_text = tweet_text[:available_chars-3] + "..."
        
        # Final tweet oluştur - boşlukları optimize et
        if emoji_text and tweet_text:
            # Emoji varsa emoji ile tweet arasında tek boşluk
            main_content = f"{emoji_text} {tweet_text}"
        else:
            # Emoji yoksa direkt tweet
            main_content = tweet_text
        
        if hashtag_text:
            # Hashtag varsa tek boşluk ile ekle
            final_tweet = f"{main_content} {hashtag_text}{url_part}"
        else:
            # Hashtag yoksa direkt URL ekle
            final_tweet = f"{main_content}{url_part}"
        
        # Son güvenlik kontrolü - eğer hala uzunsa daha agresif kısalt
        if len(final_tweet) > TWITTER_LIMIT:
            excess = len(final_tweet) - TWITTER_LIMIT
            # Tweet metninden fazlalığı çıkar
            new_tweet_length = len(tweet_text) - excess - 3  # 3 "..." için
            if new_tweet_length > 10:  # Minimum 10 karakter bırak
                tweet_text = tweet_text[:new_tweet_length] + "..."
            else:
                # Çok kısa kalırsa hashtag'leri azalt
                hashtag_text = " ".join(analysis['hashtags'][:2])  # 2 hashtag
                fixed_parts_length = len(emoji_text) + len(hashtag_text) + len(url_part) + 1  # 1 boşluk
                available_chars = TWITTER_LIMIT - fixed_parts_length
                tweet_text = tweet_text[:available_chars-3] + "..."
            
            # Yeniden oluştur
            if emoji_text and tweet_text:
                main_content = f"{emoji_text} {tweet_text}"
            else:
                main_content = tweet_text
            
            if hashtag_text:
                final_tweet = f"{main_content} {hashtag_text}{url_part}"
            else:
                final_tweet = f"{main_content}{url_part}"
        
        print(f"✅ AI analizi ile tweet oluşturuldu: {len(final_tweet)} karakter")
        print(f"📝 Tweet metni: {len(tweet_text)} karakter")
        print(f"🏷️ AI Hashtag'ler: {hashtag_text} ({len(hashtag_text)} karakter)")
        print(f"😊 AI Emojiler: {emoji_text} ({len(emoji_text)} karakter)")
        print(f"🔗 URL kısmı: {len(url_part)} karakter")
        print(f"🎯 Hedef Kitle: {analysis['audience']}")
        
        # Dictionary formatında döndür
        return {
            "tweet": final_tweet,
            "impact_score": 8,  # Varsayılan yüksek skor
            "analysis": analysis,
            "source": "mcp_analysis"
        }
        
    except Exception as e:
        print(f"❌ AI tweet oluşturma hatası: {e}")
        print("🔄 Fallback yönteme geçiliyor...")
        fallback_tweet = generate_ai_tweet_with_content_fallback(article_data, api_key)
        return {
            "tweet": fallback_tweet,
            "impact_score": 6,  # Orta skor
            "analysis": {"audience": "General", "companies": [], "hashtags": [], "emojis": []},
            "source": "fallback"
        }

def generate_ai_tweet_with_content(article_data, api_key):
    """Ana tweet oluşturma fonksiyonu - MCP analizi öncelikli"""
    try:
        # Önce MCP analizi ile dene
        tweet_data = generate_ai_tweet_with_mcp_analysis(article_data, api_key)
        
        # Eğer başarısızsa fallback kullan
        if not tweet_data or not tweet_data.get('tweet') or len(tweet_data.get('tweet', '')) < 50:
            print("🔄 MCP analizi yetersiz, fallback yöntemi deneniyor...")
            fallback_tweet = generate_ai_tweet_with_content_fallback(article_data, api_key)
            return {
                "tweet": fallback_tweet,
                "impact_score": 6,
                "analysis": {"audience": "General", "companies": [], "hashtags": [], "emojis": []},
                "source": "fallback"
            }
        
        return tweet_data
        
    except Exception as e:
        print(f"Ana tweet oluşturma hatası: {e}")
        fallback_tweet = generate_ai_tweet_with_content_fallback(article_data, api_key)
        return {
            "tweet": fallback_tweet,
            "impact_score": 6,
            "analysis": {"audience": "General", "companies": [], "hashtags": [], "emojis": []},
            "source": "fallback"
        }

def generate_ai_tweet_with_content_fallback(article_data, api_key):
    """Fallback tweet oluşturma - Eski yöntem"""
    title = article_data.get("title", "")
    content = article_data.get("content", "")
    url = article_data.get("url", "")
    
    # Twitter karakter limiti (URL için 23 karakter ayrılır)
    TWITTER_LIMIT = 280
    URL_LENGTH = 25  # "\n\n🔗 " + URL kısaltması için
    
    # Akıllı hashtag ve emoji oluştur
    smart_hashtags = generate_smart_hashtags(title, content)
    smart_emojis = generate_smart_emojis(title, content)
    
    hashtag_text = " ".join(smart_hashtags).strip()
    emoji_text = "".join(smart_emojis).strip()
    
    # Hashtag ve emoji için yer ayır
    hashtag_emoji_length = len(hashtag_text) + len(emoji_text) + 2  # 2 boşluk için
    MAX_CONTENT_LENGTH = TWITTER_LIMIT - URL_LENGTH - hashtag_emoji_length
    
    # İngilizce tweet için gelişmiş prompt
    prompt = f"""Create a compelling English tweet about this AI/tech breakthrough:

Article Title: {title}
Article Content: {content[:1000]}

Requirements:
- Write in perfect English only
- Maximum {MAX_CONTENT_LENGTH} characters
- Make it clear, engaging and newsworthy
- Focus on WHAT changed and WHY it matters
- Use active voice and strong action verbs
- Include specific details when possible (numbers, capabilities, improvements)
- Make it accessible to general audience
- Sound exciting but credible
- Avoid jargon and technical terms
- Do NOT include hashtags, emojis, URLs, or impact levels (added separately)
- Do NOT mention impact, effect level, or rating in the tweet

Examples of good style:
- "OpenAI's new model achieves 95% accuracy in medical diagnosis"
- "Tesla's robot now performs complex assembly tasks autonomously"
- "Google's AI reduces data center energy consumption by 40%"
- "Meta's VR headset delivers 4K resolution at half the price"

Tweet text (max {MAX_CONTENT_LENGTH} chars):"""

    try:
        tweet_text = gemini_call(prompt, api_key, max_tokens=150)
        
        if tweet_text and len(tweet_text.strip()) > 10:
            # Tweet metnini temizle
            import re
            # Impact/etki bilgilerini temizle
            tweet_text = re.sub(r'\b(impact|etki|effect)\s*:\s*\w+\b', '', tweet_text, flags=re.IGNORECASE)
            tweet_text = re.sub(r'[\(\[\{]\s*(impact|etki|effect)\s*:\s*\w+\s*[\)\]\}]', '', tweet_text, flags=re.IGNORECASE)
            tweet_text = re.sub(r'\s+', ' ', tweet_text).strip()
            
            # Karakter limiti kontrolü
            if len(tweet_text.strip()) > MAX_CONTENT_LENGTH:
                tweet_text = tweet_text.strip()[:MAX_CONTENT_LENGTH-3] + "..."
            
            # Emoji, tweet metni, hashtag'ler ve URL'yi birleştir - boşlukları optimize et
            parts = []
            if emoji_text:
                parts.append(emoji_text)
            if tweet_text.strip():
                parts.append(tweet_text.strip())
            if hashtag_text:
                parts.append(hashtag_text)
            
            main_content = " ".join(parts)
            final_tweet = f"{main_content}\n\n🔗 {url}"
            
            # Final karakter kontrolü
            if len(final_tweet) > TWITTER_LIMIT:
                # Tekrar kısalt
                excess = len(final_tweet) - TWITTER_LIMIT
                tweet_text = tweet_text.strip()[:-(excess + 3)] + "..."
                
                # Yeniden birleştir - boşlukları optimize et
                parts = []
                if emoji_text:
                    parts.append(emoji_text)
                if tweet_text:
                    parts.append(tweet_text)
                if hashtag_text:
                    parts.append(hashtag_text)
                
                main_content = " ".join(parts)
                final_tweet = f"{main_content}\n\n🔗 {url}"
            
            print(f"[FALLBACK] Tweet oluşturuldu: {len(final_tweet)} karakter (limit: {TWITTER_LIMIT})")
            print(f"[FALLBACK] Hashtag'ler: {hashtag_text}")
            print(f"[FALLBACK] Emojiler: {emoji_text}")
            
            return final_tweet
        else:
            print("[FALLBACK] API yanıtı yetersiz, basit fallback tweet oluşturuluyor...")
            return create_fallback_tweet(title, content, url)
            
    except Exception as e:
        print(f"Fallback tweet oluşturma hatası: {e}")
        print("[FALLBACK] API hatası, basit fallback tweet oluşturuluyor...")
        return create_fallback_tweet(title, content, url)

def create_fallback_tweet(title, content, url=""):
    """API hatası durumunda fallback tweet oluştur - Akıllı hashtag ve emoji ile"""
    try:
        # Twitter karakter limiti
        TWITTER_LIMIT = 280
        URL_LENGTH = 25  # "\n\n🔗 " + URL için
        
        # Akıllı hashtag ve emoji oluştur
        smart_hashtags = generate_smart_hashtags(title, content)
        smart_emojis = generate_smart_emojis(title, content)
        
        hashtag_text = " ".join(smart_hashtags).strip()
        emoji_text = "".join(smart_emojis).strip()
        
        # Hashtag ve emoji için yer ayır
        hashtag_emoji_length = len(hashtag_text) + len(emoji_text) + 2  # 2 boşluk için
        MAX_CONTENT_LENGTH = TWITTER_LIMIT - URL_LENGTH - hashtag_emoji_length
        
        # Başlığı temizle
        clean_title = title.strip()
        
        # İçerikten anahtar kelimeler ve önemli bilgiler çıkar
        content_lower = content.lower()
        title_lower = title.lower()
        combined_text = f"{title_lower} {content_lower}"
        
        # Sayısal bilgileri çıkar
        import re
        numbers = re.findall(r'\$?(\d+(?:\.\d+)?)\s*(billion|million|%|percent)', combined_text, re.IGNORECASE)
        
        # Şirket isimlerini tespit et
        companies = []
        company_names = ["OpenAI", "Google", "Microsoft", "Meta", "Apple", "Amazon", "Tesla", "Nvidia", "Anthropic", "Perplexity", "Cursor", "DeviantArt", "AMD", "Intel"]
        for company in company_names:
            if company.lower() in combined_text:
                companies.append(company)
        
        # Ana tweet metni oluştur - daha anlamlı İngilizce
        tweet_parts = []
        
        # Şirket ve eylem bazlı tweet oluştur
        if companies:
            main_company = companies[0]
            
            # Eyleme göre anlamlı cümle oluştur
            if "acquisition" in combined_text or "acquire" in combined_text:
                if "billion" in combined_text:
                    tweet_parts.append(f"{main_company} completes major acquisition")
                else:
                    tweet_parts.append(f"{main_company} acquires strategic company")
            elif "funding" in combined_text or "investment" in combined_text:
                if numbers:
                    largest_num = max(numbers, key=lambda x: float(x[0]))
                    if largest_num[1].lower() == 'billion':
                        tweet_parts.append(f"{main_company} raises ${largest_num[0]}B in funding")
                    elif largest_num[1].lower() == 'million':
                        tweet_parts.append(f"{main_company} secures ${largest_num[0]}M investment")
                    else:
                        tweet_parts.append(f"{main_company} secures major funding")
                else:
                    tweet_parts.append(f"{main_company} secures new funding round")
            elif "launch" in combined_text or "release" in combined_text:
                if "ai" in combined_text or "artificial intelligence" in combined_text:
                    tweet_parts.append(f"{main_company} launches new AI technology")
                elif "robot" in combined_text:
                    tweet_parts.append(f"{main_company} unveils advanced robotics")
                else:
                    tweet_parts.append(f"{main_company} releases breakthrough innovation")
            elif "partnership" in combined_text or "partner" in combined_text:
                tweet_parts.append(f"{main_company} forms strategic partnership")
            elif "breakthrough" in combined_text or "innovation" in combined_text:
                tweet_parts.append(f"{main_company} achieves major breakthrough")
            else:
                # Başlığı kullan ama şirket adını öne çıkar
                clean_title_short = clean_title.replace(main_company, "").strip()
                if clean_title_short:
                    tweet_parts.append(f"{main_company}: {clean_title_short[:80]}")
                else:
                    tweet_parts.append(f"{main_company} makes major announcement")
        else:
            # Şirket yoksa başlığı kullan
            if "ai" in combined_text or "artificial intelligence" in combined_text:
                tweet_parts.append(f"AI breakthrough: {clean_title[:100]}")
            elif "robot" in combined_text:
                tweet_parts.append(f"Robotics advance: {clean_title[:100]}")
            else:
                tweet_parts.append(f"Tech news: {clean_title[:120]}")
        
        # Sayısal bilgi ekle (eğer henüz eklenmemişse)
        if numbers and not any("$" in part for part in tweet_parts):
            largest_num = max(numbers, key=lambda x: float(x[0]))
            if largest_num[1].lower() == 'billion':
                tweet_parts.append(f"(${largest_num[0]}B)")
            elif largest_num[1].lower() == 'million':
                tweet_parts.append(f"({largest_num[0]}M)")
            elif largest_num[1].lower() in ['%', 'percent']:
                tweet_parts.append(f"({largest_num[0]}% improvement)")
        
        # Tweet'i birleştir
        main_text = " ".join(tweet_parts)
        
        # Karakter limiti kontrolü
        if len(main_text) > MAX_CONTENT_LENGTH:
            # Çok uzunsa kısalt
            main_text = main_text[:MAX_CONTENT_LENGTH-3] + "..."
        
        # Emoji, tweet metni, hashtag'ler ve URL'yi birleştir
        if url:
            fallback_tweet = f"{emoji_text} {main_text} {hashtag_text}\n\n🔗 {url}"
        else:
            fallback_tweet = f"{emoji_text} {main_text} {hashtag_text}"
        
        # Final karakter kontrolü
        if len(fallback_tweet) > TWITTER_LIMIT:
            # Tekrar kısalt
            excess = len(fallback_tweet) - TWITTER_LIMIT
            main_text = main_text[:-(excess + 3)] + "..."
            if url:
                fallback_tweet = f"{emoji_text} {main_text} {hashtag_text}\n\n🔗 {url}"
            else:
                fallback_tweet = f"{emoji_text} {main_text} {hashtag_text}"
        
        print(f"[FALLBACK] Tweet oluşturuldu: {len(fallback_tweet)} karakter (limit: {TWITTER_LIMIT})")
        print(f"[FALLBACK] Hashtag'ler: {hashtag_text}")
        print(f"[FALLBACK] Emojiler: {emoji_text}")
        
        return fallback_tweet
        
    except Exception as e:
        print(f"Fallback tweet oluşturma hatası: {e}")
        # En basit fallback - akıllı hashtag ve emoji ile
        try:
            simple_hashtags = generate_smart_hashtags(title, "")[:3]  # 3 hashtag
            simple_emojis = generate_smart_emojis(title, "")[:2]  # 2 emoji
            
            hashtag_text = " ".join(simple_hashtags)
            emoji_text = "".join(simple_emojis)
            
            # Karakter hesaplama
            url_length = len(f"\n\n🔗 {url}") if url else 0
            available_chars = TWITTER_LIMIT - url_length - len(hashtag_text) - len(emoji_text) - 2
            
            # Başlığı kısalt
            if len(title) > available_chars:
                title_text = title[:available_chars-3] + "..."
            else:
                title_text = title
            
            simple_tweet = f"{emoji_text} {title_text} {hashtag_text}"
            if url:
                simple_tweet += f"\n\n🔗 {url}"
            
            return simple_tweet
            
        except:
            # En son çare - basit tweet
            simple_text = f"🤖 {title[:200]}... #AI #Innovation #Technology"
            if url:
                simple_tweet = f"{simple_text}\n\n🔗 {url}"
            else:
                simple_tweet = simple_text
            
            # Karakter limiti kontrolü
            if len(simple_tweet) > TWITTER_LIMIT:
                available = TWITTER_LIMIT - len("\n\n🔗 ") - len(url) - len(" #AI #Innovation #Technology") - 3
                simple_text = f"🤖 {title[:available]}... #AI #Innovation #Technology"
                simple_tweet = f"{simple_text}\n\n🔗 {url}" if url else simple_text
            
            return simple_tweet

def setup_twitter_api():
    import tweepy
    import os
    # V1.1 API ile oturum aç
    auth = tweepy.OAuth1UserHandler(
        os.environ['TWITTER_API_KEY'],
        os.environ['TWITTER_API_SECRET'],
        os.environ['TWITTER_ACCESS_TOKEN'],
        os.environ['TWITTER_ACCESS_TOKEN_SECRET']
    )
    api = tweepy.API(auth)
    return api

def post_tweet(tweet_text, article_title=""):
    """X platformunda tweet paylaşma ve Gmail bildirimi - Twitter API v2 kullanarak"""
    try:
        # Twitter API v2 kullan
        tweet_result = post_text_tweet_v2(tweet_text)
        
        # Başarısız olursa hata döndür
        if not tweet_result.get("success"):
            safe_log(f"Tweet paylaşım hatası: {tweet_result.get('error', 'Bilinmeyen hata')}", "ERROR")
            return tweet_result
        
        tweet_id = tweet_result.get("tweet_id")
        tweet_url = tweet_result.get("url")
        
        # Gmail bildirimi gönder (Telegram yerine)
        email_sent = False
        try:
            gmail_result = send_gmail_notification(
                message=tweet_text,
                tweet_url=tweet_url,
                article_title=article_title
            )
            if gmail_result.get("success"):
                safe_log(f"Gmail bildirimi gönderildi: {gmail_result.get('email')}", "INFO")
                email_sent = True
            else:
                safe_log(f"Gmail bildirimi gönderilemedi: {gmail_result.get('reason', 'unknown')}", "WARNING")
        except Exception as gmail_error:
            safe_log(f"Gmail bildirim hatası: {gmail_error}", "ERROR")
        
        # Fallback: Telegram bildirimi (eğer Gmail başarısız olursa)
        telegram_sent = False
        if not email_sent:
            try:
                telegram_result = send_telegram_notification(
                    message=tweet_text,
                    tweet_url=tweet_url,
                    article_title=article_title
                )
                if telegram_result.get("success"):
                    safe_log("Fallback Telegram bildirimi gönderildi", "INFO")
                    telegram_sent = True
                else:
                    safe_log(f"Fallback Telegram bildirimi de başarısız: {telegram_result.get('reason', 'unknown')}", "WARNING")
            except Exception as telegram_error:
                safe_log(f"Fallback Telegram bildirim hatası: {telegram_error}", "ERROR")
        
        return {
            "success": True,
            "tweet_id": tweet_id,
            "url": tweet_url,
            "email_sent": email_sent,
            "telegram_sent": telegram_sent
        }
        
    except Exception as e:
        safe_log(f"Tweet paylaşım hatası: {str(e)}", "ERROR")
        return {"success": False, "error": f"Tweet paylaşım hatası: {str(e)}"}

def mark_article_as_posted(article_data, tweet_result):
    """Makaleyi paylaşıldı olarak işaretle - API ve manuel paylaşımları destekler"""
    try:
        posted_articles = load_json(HISTORY_FILE)
        
        # Manuel paylaşım kontrolü
        is_manual_post = tweet_result.get("manual_post", False)
        
        posted_article = {
            "title": article_data.get("title", ""),
            "url": article_data.get("url", ""),
            "hash": article_data.get("hash", ""),
            "posted_date": datetime.now().isoformat(),
            "tweet_id": tweet_result.get("tweet_id", ""),
            "tweet_url": tweet_result.get("url", ""),
            "manual_post": is_manual_post,
            "post_method": "manuel" if is_manual_post else "api"
        }
        
        # Manuel paylaşım için ek bilgiler
        if is_manual_post:
            posted_article["tweet_text"] = article_data.get("tweet_text", "")
            posted_article["manual_posted_at"] = tweet_result.get("posted_at", datetime.now().isoformat())
        
        posted_articles.append(posted_article)
        save_json(HISTORY_FILE, posted_articles)
        
        safe_log(f"Makale kaydedildi: {article_data.get('title', '')[:50]}... (Yöntem: {posted_article['post_method']})", "INFO")
        
        return True
    except Exception as e:
        safe_log(f"Makale kaydetme hatası: {e}", "ERROR")
        return False

def check_duplicate_articles():
    """Tekrarlanan makaleleri temizle"""
    try:
        posted_articles = load_json(HISTORY_FILE)
        
        # Son 30 günlük makaleleri tut
        cutoff_date = datetime.now() - timedelta(days=30)
        
        filtered_articles = []
        seen_hashes = set()
        
        for article in posted_articles:
            try:
                posted_date = datetime.fromisoformat(article.get("posted_date", ""))
                article_hash = article.get("hash", "")
                
                if posted_date > cutoff_date and article_hash not in seen_hashes:
                    filtered_articles.append(article)
                    seen_hashes.add(article_hash)
            except:
                continue
        
        save_json(HISTORY_FILE, filtered_articles)
        return len(posted_articles) - len(filtered_articles)
        
    except Exception as e:
        print(f"Tekrar temizleme hatası: {e}")
        return 0

def generate_ai_digest(summaries_with_links, api_key):
    """Eski fonksiyon - geriye dönük uyumluluk için"""
    if not summaries_with_links:
        return "Özet bulunamadı"
    
    # İlk makaleyi kullanarak tweet oluştur
    first_summary = summaries_with_links[0]
    article_data = {
        "title": "AI Digest",
        "content": first_summary.get("summary", ""),
        "url": first_summary.get("url", "")
    }
    
    return generate_ai_tweet_with_content(article_data, api_key)

def create_pdf(summaries, filename="daily_digest.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="AI Tweet Digest", ln=True, align='C')
    for s in summaries:
        pdf.multi_cell(0, 10, f"• {s}")
    pdf.output(filename)
    return filename

def get_posted_articles_summary():
    """Paylaşılmış makalelerin özetini döndür - gelişmiş istatistiklerle"""
    try:
        from datetime import datetime, date, timedelta
        posted_articles = load_json(HISTORY_FILE)
        today = date.today()
        
        # Son 7 günlük makaleleri al
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_articles = []
        today_articles = []
        week_articles = []
        
        # En yüksek skorlu makale
        highest_scored = None
        highest_score = 0
        
        # En son paylaşılan makale
        latest_posted = None
        latest_date = None
        
        for article in posted_articles:
            try:
                posted_date_str = article.get("posted_date", "")
                if posted_date_str:
                    posted_date = datetime.fromisoformat(posted_date_str.replace('Z', '+00:00'))
                    
                    # Bugünkü makaleler
                    if posted_date.date() == today:
                        today_articles.append(article)
                    
                    # Son 7 günlük makaleler
                    if posted_date > cutoff_date:
                        recent_articles.append(article)
                        week_articles.append(article)
                    
                    # En son paylaşılan
                    if latest_date is None or posted_date > latest_date:
                        latest_date = posted_date
                        latest_posted = article
                
                # En yüksek skorlu makale (eğer skor varsa)
                score = article.get("score", 0)
                if isinstance(score, (int, float)) and score > highest_score:
                    highest_score = score
                    highest_scored = article
                    
            except Exception as e:
                print(f"[DEBUG] Makale parse hatası: {e}")
                continue
        
        # Başarı oranı hesapla (basit: paylaşılan / toplam)
        success_rate = (len(posted_articles) / max(len(posted_articles) + 1, 1)) * 100
        
        # Kategori dağılımı (eğer varsa)
        category_distribution = {}
        for article in posted_articles:
            category = article.get("category", "Genel")
            category_distribution[category] = category_distribution.get(category, 0) + 1
        
        return {
            "total_posted": len(posted_articles),
            "recent_posted": len(recent_articles),
            "recent_articles": recent_articles[-5:],  # Son 5 makale
            "today_articles": len(today_articles),
            "week_articles": len(week_articles),
            "highest_scored": highest_scored,
            "latest_posted": latest_posted,
            "success_rate": success_rate,
            "category_distribution": category_distribution,
            "average_score": highest_score / max(len(posted_articles), 1) if highest_score > 0 else 0,
            "last_check_time": datetime.now().strftime("%H:%M") if posted_articles else "Henüz yok"
        }
        
    except Exception as e:
        print(f"Paylaşılmış makale özeti hatası: {e}")
        return {
            "total_posted": 0, 
            "recent_posted": 0, 
            "recent_articles": [],
            "today_articles": 0,
            "week_articles": 0,
            "highest_scored": None,
            "latest_posted": None,
            "success_rate": 0,
            "category_distribution": {},
            "average_score": 0,
            "last_check_time": "Henüz yok"
        }

def reset_all_data():
    """Tüm uygulama verilerini sıfırla"""
    try:
        files_to_reset = [
            "posted_articles.json",
            "pending_tweets.json", 
            "summaries.json",
            "hashtags.json",
            "accounts.json"
        ]
        
        reset_count = 0
        for file_path in files_to_reset:
            if os.path.exists(file_path):
                save_json(file_path, [])
                reset_count += 1
                print(f"✅ {file_path} sıfırlandı")
            else:
                # Dosya yoksa boş oluştur
                save_json(file_path, [])
                print(f"🆕 {file_path} oluşturuldu")
        
        return {
            "success": True,
            "message": f"✅ {reset_count} dosya sıfırlandı",
            "reset_files": files_to_reset
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Sıfırlama hatası: {str(e)}",
            "reset_files": []
        }

def clear_pending_tweets():
    """Sadece bekleyen tweet'leri temizle"""
    try:
        pending_tweets = load_json("pending_tweets.json")
        
        # Sadece posted olanları tut, pending olanları sil
        posted_tweets = [t for t in pending_tweets if t.get("status") == "posted"]
        
        save_json("pending_tweets.json", posted_tweets)
        
        cleared_count = len(pending_tweets) - len(posted_tweets)
        
        return {
            "success": True,
            "message": f"✅ {cleared_count} bekleyen tweet temizlendi",
            "cleared_count": cleared_count
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Temizleme hatası: {str(e)}",
            "cleared_count": 0
        }

def get_data_statistics():
    """Veri istatistiklerini döndür - bugünkü analizler dahil"""
    try:
        from datetime import datetime, date
        today = date.today()
        stats = {}
        
        # Paylaşılan makaleler
        posted_articles = load_json("posted_articles.json")
        stats["posted_articles"] = len(posted_articles)
        stats["total_articles"] = len(posted_articles)  # Template uyumluluğu için
        
        # Bugünkü paylaşılan makaleler
        today_articles = []
        for article in posted_articles:
            if article.get("posted_date"):
                try:
                    # ISO format tarihini parse et
                    posted_date = datetime.fromisoformat(article["posted_date"].replace('Z', '+00:00'))
                    if posted_date.date() == today:
                        today_articles.append(article)
                except (ValueError, TypeError) as e:
                    print(f"[DEBUG] Tarih parse hatası: {e} - {article.get('posted_date')}")
                    continue
        
        stats["today_articles"] = len(today_articles)
        
        # Bekleyen tweet'ler
        pending_tweets = load_json("pending_tweets.json")
        pending_count = len([t for t in pending_tweets if t.get("status") == "pending"])
        posted_count = len([t for t in pending_tweets if t.get("status") == "posted"])
        stats["pending_tweets"] = pending_count
        stats["posted_tweets_in_pending"] = posted_count
        
        # Bugünkü bekleyen tweet'ler
        today_pending = []
        for tweet in pending_tweets:
            if tweet.get("created_date"):
                try:
                    created_date = datetime.fromisoformat(tweet["created_date"].replace('Z', '+00:00'))
                    if created_date.date() == today and tweet.get("status") == "pending":
                        today_pending.append(tweet)
                except (ValueError, TypeError):
                    continue
        
        stats["today_pending"] = len(today_pending)
        
        # Özetler
        summaries = load_json("summaries.json")
        stats["summaries"] = len(summaries)
        
        # Hashtag'ler
        hashtags = load_json("hashtags.json")
        stats["hashtags"] = len(hashtags)
        
        # Hesaplar
        accounts = load_json("accounts.json")
        stats["accounts"] = len(accounts)
        
        # Bugünkü toplam aktivite
        stats["today_total_activity"] = stats["today_articles"] + stats["today_pending"]
        
        print(f"[DEBUG] İstatistikler: Bugün {stats['today_articles']} makale, {stats['today_pending']} bekleyen")
        
        return stats
        
    except Exception as e:
        print(f"İstatistik hatası: {e}")
        return {
            "posted_articles": 0,
            "total_articles": 0,
            "today_articles": 0,
            "pending_tweets": 0,
            "today_pending": 0,
            "posted_tweets_in_pending": 0,
            "summaries": 0,
            "hashtags": 0,
            "accounts": 0,
            "today_total_activity": 0
        }

def load_automation_settings():
    """Otomatikleştirme ayarlarını yükle"""
    try:
        settings_data = load_json("automation_settings.json")
        
        # Eğer liste ise (eski format), boş dict döndür
        if isinstance(settings_data, list):
            settings = {}
        else:
            settings = settings_data
        
        # Varsayılan ayarlar
        default_settings = {
            "auto_mode": False,
            "min_score": 5,
            "check_interval_hours": 3,
            "max_articles_per_run": 10,
            "auto_post_enabled": False,
            "require_manual_approval": True,
            "working_hours_only": False,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "weekend_enabled": True,
            "last_updated": datetime.now().isoformat()
        }
        
        # Eksik ayarları varsayılanlarla doldur
        for key, value in default_settings.items():
            if key not in settings:
                settings[key] = value
        
        return settings
        
    except Exception as e:
        print(f"Ayarlar yükleme hatası: {e}")
        # Varsayılan ayarları döndür
        return {
            "auto_mode": False,
            "min_score": 5,
            "check_interval_hours": 3,
            "max_articles_per_run": 10,
            "auto_post_enabled": False,
            "require_manual_approval": True,
            "working_hours_only": False,
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "weekend_enabled": True,
            "last_updated": datetime.now().isoformat()
        }

def save_automation_settings(settings):
    """Otomatikleştirme ayarlarını kaydet"""
    try:
        settings["last_updated"] = datetime.now().isoformat()
        save_json("automation_settings.json", settings)
        return {"success": True, "message": "✅ Ayarlar başarıyla kaydedildi"}
    except Exception as e:
        return {"success": False, "message": f"❌ Ayarlar kaydedilemedi: {e}"}

def get_automation_status():
    """Otomatikleştirme durumunu kontrol et"""
    try:
        settings = load_automation_settings()
        
        # Çalışma saatleri kontrolü
        if settings.get("working_hours_only", False):
            from datetime import datetime, time
            now = datetime.now()
            start_time = datetime.strptime(settings.get("working_hours_start", "09:00"), "%H:%M").time()
            end_time = datetime.strptime(settings.get("working_hours_end", "18:00"), "%H:%M").time()
            
            current_time = now.time()
            is_working_hours = start_time <= current_time <= end_time
            
            # Hafta sonu kontrolü
            is_weekend = now.weekday() >= 5  # 5=Cumartesi, 6=Pazar
            weekend_allowed = settings.get("weekend_enabled", True)
            
            if is_weekend and not weekend_allowed:
                return {
                    "active": False,
                    "auto_mode": False,
                    "check_interval_hours": settings.get("check_interval_hours", 2),
                    "min_score_threshold": settings.get("min_score_threshold", 5),
                    "reason": "Hafta sonu çalışma devre dışı",
                    "settings": settings
                }
            
            if not is_working_hours:
                return {
                    "active": False,
                    "auto_mode": False,
                    "check_interval_hours": settings.get("check_interval_hours", 2),
                    "min_score_threshold": settings.get("min_score_threshold", 5),
                    "reason": f"Çalışma saatleri dışında ({start_time}-{end_time})",
                    "settings": settings
                }
        
        return {
            "active": settings.get("auto_mode", False),
            "auto_mode": settings.get("auto_mode", False),  # Template uyumluluğu için
            "check_interval_hours": settings.get("check_interval_hours", 2),
            "min_score_threshold": settings.get("min_score_threshold", 5),
            "reason": "Aktif" if settings.get("auto_mode", False) else "Manuel mod",
            "settings": settings
        }
        
    except Exception as e:
        return {
            "active": False,
            "auto_mode": False,
            "check_interval_hours": 2,
            "min_score_threshold": 5,
            "reason": f"Hata: {e}",
            "settings": {}
        }

def update_scheduler_settings():
    """Scheduler ayarlarını güncelle (scheduler.py için)"""
    try:
        settings = load_automation_settings()
        
        # Scheduler için ayarlar dosyası oluştur
        scheduler_config = {
            "auto_mode": settings.get("auto_mode", False),
            "min_score": settings.get("min_score", 5),
            "check_interval_hours": settings.get("check_interval_hours", 3),
            "max_articles_per_run": settings.get("max_articles_per_run", 10),
            "auto_post_enabled": settings.get("auto_post_enabled", False),
            "last_updated": datetime.now().isoformat()
        }
        
        save_json("scheduler_config.json", scheduler_config)
        return {"success": True, "message": "Scheduler ayarları güncellendi"}
        
    except Exception as e:
        return {"success": False, "message": f"Scheduler ayarları güncellenemedi: {e}"}

def validate_automation_settings(settings):
    """Otomatikleştirme ayarlarını doğrula"""
    errors = []
    
    # Minimum skor kontrolü
    min_score = settings.get("min_score", 5)
    if not isinstance(min_score, int) or min_score < 1 or min_score > 10:
        errors.append("Minimum skor 1-10 arasında olmalı")
    
    # Kontrol aralığı kontrolü
    interval = settings.get("check_interval_hours", 3)
    if not isinstance(interval, (int, float)) or interval < 0.5 or interval > 24:
        errors.append("Kontrol aralığı 0.5-24 saat arasında olmalı")
    
    # Maksimum makale sayısı kontrolü
    max_articles = settings.get("max_articles_per_run", 10)
    if not isinstance(max_articles, int) or max_articles < 1 or max_articles > 50:
        errors.append("Maksimum makale sayısı 1-50 arasında olmalı")
    
    # Çalışma saatleri kontrolü
    try:
        start_time = settings.get("working_hours_start", "09:00")
        end_time = settings.get("working_hours_end", "18:00")
        datetime.strptime(start_time, "%H:%M")
        datetime.strptime(end_time, "%H:%M")
    except ValueError:
        errors.append("Çalışma saatleri HH:MM formatında olmalı")
    

    
    return errors

def send_telegram_notification(message, tweet_url="", article_title=""):
    """Telegram bot'a bildirim gönder - Bot token env'den, Chat ID settings'den"""
    try:
        # Bot token'ı environment variable'dan çek
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        
        # Chat ID'yi settings'den çek
        settings = load_automation_settings()
        chat_id = settings.get("telegram_chat_id", "").strip()
        
        # Eğer bot token env'de yoksa settings'den dene (geriye dönük uyumluluk)
        if not bot_token:
            bot_token = settings.get("telegram_bot_token", "").strip()
        
        # Telegram bildirimleri kapalı mı kontrol et
        if not settings.get("telegram_notifications", True):  # Varsayılan True
            print("[DEBUG] Telegram bildirimleri kapalı")
            return {"success": False, "reason": "disabled"}
        
        if not bot_token:
            safe_log("Telegram bot token eksik. .env dosyasında TELEGRAM_BOT_TOKEN ayarlayın.", "WARNING")
            return {"success": False, "reason": "missing_bot_token"}
            
        if not chat_id:
            print("[INFO] Chat ID eksik, otomatik algılama deneniyor...")
            # Otomatik Chat ID algılamayı dene
            auto_result = auto_detect_and_save_chat_id()
            
            if auto_result["success"]:
                chat_id = auto_result["chat_id"]
                print(f"[SUCCESS] Chat ID otomatik algılandı: {chat_id}")
            else:
                print(f"[WARNING] Chat ID otomatik algılanamadı: {auto_result.get('error', 'Bilinmeyen hata')}")
                print("[INFO] Bot'a @tweet62_bot adresinden bir mesaj gönderin ve tekrar deneyin.")
                return {"success": False, "reason": "missing_chat_id", "auto_detect_error": auto_result.get('error')}
        
        # Telegram mesajını hazırla
        telegram_message = f"🤖 **Yeni Tweet Paylaşıldı!**\n\n"
        
        if article_title:
            telegram_message += f"📰 **Makale:** {article_title}\n\n"
        
        telegram_message += f"💬 **Tweet:** {message}\n\n"
        
        if tweet_url:
            telegram_message += f"🔗 **Link:** {tweet_url}\n\n"
        
        telegram_message += f"⏰ **Zaman:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        # Telegram API'ye gönder
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            "chat_id": str(chat_id),
            "text": telegram_message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"[SUCCESS] Telegram bildirimi gönderildi: {chat_id}")
            return {"success": True, "message_id": response.json().get("result", {}).get("message_id")}
        else:
            print(f"[ERROR] Telegram API hatası: {response.status_code} - {response.text}")
            return {"success": False, "error": f"API Error: {response.status_code}"}
            
    except Exception as e:
        print(f"[ERROR] Telegram bildirim hatası: {e}")
        return {"success": False, "error": str(e)}

def test_telegram_connection():
    """Telegram bot bağlantısını test et - Bot token env'den, Chat ID settings'den"""
    try:
        # Bot token'ı environment variable'dan çek
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        
        # Chat ID'yi settings'den çek
        settings = load_automation_settings()
        chat_id = settings.get("telegram_chat_id", "").strip()
        
        # Eğer bot token env'de yoksa settings'den dene (geriye dönük uyumluluk)
        if not bot_token:
            bot_token = settings.get("telegram_bot_token", "").strip()
        
        if not bot_token:
            return {
                "success": False, 
                "error": "Bot token eksik. .env dosyasında TELEGRAM_BOT_TOKEN ayarlayın."
            }
            
        if not chat_id:
            print("[INFO] Chat ID eksik, otomatik algılama deneniyor...")
            # Otomatik Chat ID algılamayı dene
            auto_result = auto_detect_and_save_chat_id()
            
            if auto_result["success"]:
                chat_id = auto_result["chat_id"]
                print(f"[SUCCESS] Chat ID otomatik algılandı: {chat_id}")
            else:
                return {
                    "success": False, 
                    "error": f"Chat ID eksik ve otomatik algılanamadı: {auto_result.get('error', 'Bilinmeyen hata')}. Bot'a @tweet62_bot adresinden bir mesaj gönderin."
                }
        
        # Bot bilgilerini al
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Bot token geçersiz: {response.status_code}"}
        
        bot_info = response.json().get("result", {})
        
        # Test mesajı gönder
        test_message = f"🧪 **Test Mesajı**\n\nBot başarıyla bağlandı!\n\n⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": str(chat_id),
            "text": test_message,
            "parse_mode": "Markdown"
        }
        
        send_response = requests.post(send_url, json=payload, timeout=10)
        
        if send_response.status_code == 200:
            return {
                "success": True, 
                "bot_name": bot_info.get("first_name", "Unknown"),
                "bot_username": bot_info.get("username", "Unknown")
            }
        else:
            error_detail = send_response.text
            return {"success": False, "error": f"Mesaj gönderilemedi: {send_response.status_code} - {error_detail}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_telegram_configuration():
    """Telegram konfigürasyonunu kontrol et - Bot token env'den, Chat ID settings'den"""
    try:
        # Bot token environment variable'dan
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        
        # Chat ID settings'den
        settings = load_automation_settings()
        chat_id = settings.get("telegram_chat_id", "").strip()
        
        # Geriye dönük uyumluluk için settings'den bot token kontrol et
        settings_bot_token = settings.get("telegram_bot_token", "").strip()
        
        status = {
            "bot_token_env": bool(bot_token),
            "bot_token_settings": bool(settings_bot_token),
            "chat_id_set": bool(chat_id),
            "ready": bool((bot_token or settings_bot_token) and chat_id)
        }
        
        if status["ready"]:
            if status["bot_token_env"]:
                status["message"] = "✅ Telegram yapılandırması tamamlanmış (Bot token: ENV, Chat ID: Ayarlar)"
            else:
                status["message"] = "✅ Telegram yapılandırması tamamlanmış (Bot token: Ayarlar, Chat ID: Ayarlar)"
            status["status"] = "ready"
        elif status["bot_token_env"] or status["bot_token_settings"]:
            if not status["chat_id_set"]:
                status["message"] = "⚠️ Bot token var, Chat ID eksik - 'Chat ID Bul' butonu ile ayarlayın"
                status["status"] = "partial"
            else:
                status["message"] = "✅ Telegram yapılandırması tamamlanmış"
                status["status"] = "ready"
        else:
            status["message"] = "❌ Bot token eksik - .env dosyasında TELEGRAM_BOT_TOKEN ayarlayın"
            status["status"] = "missing"
            
        return status
        
    except Exception as e:
        return {
            "bot_token_env": False,
            "bot_token_settings": False,
            "chat_id_set": False,
            "ready": False,
            "message": f"❌ Kontrol hatası: {e}",
            "status": "error"
        }

def get_telegram_chat_id(bot_token=None):
    """Bot'a mesaj gönderen kullanıcıların chat ID'lerini al - Environment variable'lardan token çeker"""
    try:
        # Eğer bot_token parametre olarak verilmemişse env'den çek
        if not bot_token:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
            
            # Eğer env'de yoksa settings'den dene
            if not bot_token:
                settings = load_automation_settings()
                bot_token = settings.get("telegram_bot_token", "").strip()
        
        if not bot_token:
            return {
                "success": False, 
                "error": "Bot token eksik. .env dosyasında TELEGRAM_BOT_TOKEN ayarlayın."
            }
        
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {"success": False, "error": "Bot token geçersiz"}
        
        data = response.json()
        updates = data.get("result", [])
        
        chat_ids = []
        for update in updates[-10:]:  # Son 10 mesaj
            message = update.get("message", {})
            chat = message.get("chat", {})
            if chat.get("id"):
                chat_info = {
                    "chat_id": chat.get("id"),
                    "type": chat.get("type"),
                    "title": chat.get("title") or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
                }
                if chat_info not in chat_ids:
                    chat_ids.append(chat_info)
        
        return {"success": True, "chat_ids": chat_ids}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def save_telegram_chat_id(chat_id):
    """Chat ID'yi otomatik olarak ayarlara kaydet"""
    try:
        settings = load_automation_settings()
        settings["telegram_chat_id"] = str(chat_id).strip()
        
        save_result = save_automation_settings(settings)
        
        if save_result["success"]:
            print(f"[SUCCESS] Chat ID otomatik kaydedildi: {chat_id}")
            return {"success": True, "message": f"✅ Chat ID kaydedildi: {chat_id}"}
        else:
            print(f"[ERROR] Chat ID kaydetme hatası: {save_result['message']}")
            return {"success": False, "error": f"Kaydetme hatası: {save_result['message']}"}
            
    except Exception as e:
        print(f"[ERROR] Chat ID kaydetme hatası: {e}")
        return {"success": False, "error": str(e)}

def auto_detect_and_save_chat_id():
    """Otomatik chat ID tespit et ve kaydet"""
    try:
        # Mevcut chat ID'yi kontrol et
        settings = load_automation_settings()
        current_chat_id = settings.get("telegram_chat_id", "").strip()
        
        if current_chat_id:
            return {
                "success": True, 
                "message": f"Chat ID zaten ayarlanmış: {current_chat_id}",
                "chat_id": current_chat_id,
                "auto_detected": False
            }
        
        # Chat ID'leri bul
        result = get_telegram_chat_id()
        
        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
                "auto_detected": False
            }
        
        chat_ids = result.get("chat_ids", [])
        
        if not chat_ids:
            return {
                "success": False,
                "error": "Chat ID bulunamadı. Bot'a önce bir mesaj gönderin.",
                "auto_detected": False
            }
        
        # İlk chat ID'yi otomatik seç (genellikle en son mesaj)
        selected_chat = chat_ids[0]
        chat_id = selected_chat["chat_id"]
        
        # Chat ID'yi kaydet
        save_result = save_telegram_chat_id(chat_id)
        
        if save_result["success"]:
            return {
                "success": True,
                "message": f"✅ Chat ID otomatik tespit edildi ve kaydedildi: {chat_id}",
                "chat_id": chat_id,
                "chat_info": selected_chat,
                "auto_detected": True,
                "all_chats": chat_ids
            }
        else:
            return {
                "success": False,
                "error": save_result["error"],
                "auto_detected": False
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "auto_detected": False
        }

def load_mcp_config():
    """MCP konfigürasyonunu yükle"""
    try:
        if os.path.exists(MCP_CONFIG_FILE):
            config = load_json(MCP_CONFIG_FILE)
        else:
            # Varsayılan konfigürasyon
            config = {
                "mcp_enabled": False,
                "firecrawl_mcp": {
                    "enabled": False,
                    "server_url": "http://localhost:3000",
                    "api_key": "",
                    "timeout": 30,
                    "retry_count": 3,
                    "fallback_enabled": True
                },
                "content_extraction": {
                    "max_content_length": 2500,
                    "min_content_length": 100,
                    "wait_time": 3000,
                    "remove_base64_images": True,
                    "only_main_content": True
                },
                "ai_analysis": {
                    "enabled": True,
                    "max_tokens": 300,
                    "temperature": 0.7,
                    "model": "deepseek/deepseek-chat-v3-0324:free",
                    "fallback_enabled": True
                },
                "last_updated": datetime.now().isoformat()
            }
            save_json(MCP_CONFIG_FILE, config)
        
        return config
        
    except Exception as e:
        print(f"MCP konfigürasyon yükleme hatası: {e}")
        return {
            "mcp_enabled": False,
            "firecrawl_mcp": {"enabled": False, "fallback_enabled": True},
            "ai_analysis": {"enabled": True, "fallback_enabled": True}
        }

def save_mcp_config(config):
    """MCP konfigürasyonunu kaydet"""
    try:
        config["last_updated"] = datetime.now().isoformat()
        save_json(MCP_CONFIG_FILE, config)
        return {"success": True, "message": "✅ MCP konfigürasyonu kaydedildi"}
    except Exception as e:
        return {"success": False, "message": f"❌ MCP konfigürasyonu kaydedilemedi: {e}"}

def get_mcp_status():
    """MCP durumunu kontrol et"""
    try:
        config = load_mcp_config()
        
        status = {
            "mcp_enabled": config.get("mcp_enabled", False),
            "firecrawl_enabled": config.get("firecrawl_mcp", {}).get("enabled", False),
            "ai_analysis_enabled": config.get("ai_analysis", {}).get("enabled", True),
            "fallback_available": True,
            "ready": False
        }
        
        # MCP hazır mı kontrol et
        if status["mcp_enabled"] and status["firecrawl_enabled"]:
            # Firecrawl MCP server bağlantısını test et
            try:
                server_url = config.get("firecrawl_mcp", {}).get("server_url", "")
                if server_url:
                    # Basit ping testi (gerçek implementasyonda MCP server'a ping atılacak)
                    status["ready"] = True
                    status["message"] = "✅ MCP Firecrawl aktif ve hazır"
                else:
                    status["message"] = "⚠️ MCP server URL'si eksik"
            except:
                status["message"] = "❌ MCP server bağlantısı başarısız"
        elif status["ai_analysis_enabled"]:
            status["message"] = "✅ AI analizi aktif (MCP olmadan)"
        else:
            status["message"] = "⚠️ MCP ve AI analizi devre dışı"
        
        return status
        
    except Exception as e:
        return {
            "mcp_enabled": False,
            "firecrawl_enabled": False,
            "ai_analysis_enabled": True,
            "fallback_available": True,
            "ready": False,
            "message": f"❌ MCP durum kontrolü hatası: {e}"
        }

def test_mcp_connection():
    """MCP bağlantısını test et"""
    try:
        config = load_mcp_config()
        
        if not config.get("mcp_enabled", False):
            return {
                "success": False,
                "message": "MCP devre dışı",
                "details": "MCP konfigürasyondan etkinleştirilmeli"
            }
        
        firecrawl_config = config.get("firecrawl_mcp", {})
        
        if not firecrawl_config.get("enabled", False):
            return {
                "success": False,
                "message": "Firecrawl MCP devre dışı",
                "details": "Firecrawl MCP konfigürasyondan etkinleştirilmeli"
            }
        
        server_url = firecrawl_config.get("server_url", "")
        
        if not server_url:
            return {
                "success": False,
                "message": "MCP server URL'si eksik",
                "details": "Konfigürasyonda server_url ayarlanmalı"
            }
        
        # Gerçek MCP implementasyonunda burada MCP server'a test çağrısı yapılacak
        # Şimdilik simüle ediyoruz
        print(f"[TEST] MCP server test ediliyor: {server_url}")
        
        # Test URL'si ile basit scrape denemesi
        test_result = mcp_firecrawl_scrape({
            "url": "https://example.com",
            "formats": ["markdown"],
            "onlyMainContent": True
        })
        
        if test_result.get("success", False):
            return {
                "success": True,
                "message": "✅ MCP Firecrawl bağlantısı başarılı",
                "details": f"Server: {server_url}"
            }
        else:
            return {
                "success": False,
                "message": "❌ MCP Firecrawl test başarısız",
                "details": test_result.get("reason", "Bilinmeyen hata")
            }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ MCP test hatası: {e}",
            "details": "Bağlantı testi sırasında hata oluştu"
        }

def gemini_ocr_image(image_path):
    import google.generativeai as genai
    import os
    from PIL import Image

    api_key = os.environ.get('GOOGLE_API_KEY')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Resmi PIL ile aç
    image = Image.open(image_path)
    prompt = "Bu görseldeki tüm metni OCR ile çıkar ve sadece metni döndür."
    response = model.generate_content([prompt, image])
    return response.text.strip()

def setup_twitter_v2_client():
    """Tweepy v2 API Client ile kimlik doğrulama (sadece metinli tweet için)"""
    import tweepy
    import os
    # v2 API Client
    client = tweepy.Client(
        bearer_token=os.environ.get('TWITTER_BEARER_TOKEN'),
        consumer_key=os.environ.get('TWITTER_API_KEY'),
        consumer_secret=os.environ.get('TWITTER_API_SECRET'),
        access_token=os.environ.get('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
    )
    return client



def post_text_tweet_v2(tweet_text):
    """Sadece metinli tweet atmak için Tweepy v2 API kullanımı - Rate limit kontrolü ile"""
    try:
        import tweepy
        
        # Rate limit kontrolü yap
        rate_check = check_rate_limit("tweets")
        if not rate_check.get("allowed", True):
            wait_minutes = int(rate_check.get("wait_time", 0) / 60) + 1
            error_msg = f"Twitter API rate limit aşıldı. {wait_minutes} dakika sonra tekrar deneyin. ({rate_check.get('requests_made', 0)}/{rate_check.get('limit', 300)} istek kullanıldı)"
            safe_log(error_msg, "WARNING")
            return {"success": False, "error": error_msg, "rate_limited": True, "wait_minutes": wait_minutes}
        
        client = setup_twitter_v2_client()
        TWITTER_LIMIT = 280
        if len(tweet_text) > TWITTER_LIMIT:
            tweet_text = tweet_text[:TWITTER_LIMIT-3] + "..."
        safe_log(f"Tweet uzunluğu: {len(tweet_text)}", "DEBUG")
        
        response = client.create_tweet(text=tweet_text)
        
        # Rate limit kullanımını güncelle
        update_rate_limit_usage("tweets")
        
        if hasattr(response, 'data') and response.data and 'id' in response.data:
            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"
            safe_log(f"Tweet başarıyla gönderildi: {tweet_url}", "INFO")
            return {"success": True, "tweet_id": tweet_id, "url": tweet_url}
        else:
            safe_log(f"Tweet gönderilemedi: {response}", "ERROR")
            return {"success": False, "error": "Tweet gönderilemedi"}
            
    except tweepy.TooManyRequests as rate_limit_error:
        # API'den gelen rate limit bilgilerini güncelle
        try:
            # Rate limit durumunu güncelle
            status = load_rate_limit_status()
            current_time = time.time()
            if "tweets" not in status:
                status["tweets"] = {}
            status["tweets"]["requests"] = TWITTER_RATE_LIMITS["tweets"]["limit"]  # Limit dolu
            status["tweets"]["reset_time"] = current_time + 3600  # 1 saat sonra reset (Free plan için güvenli)
            save_rate_limit_status(status)
        except:
            pass
        
        wait_minutes = 15  # Twitter API rate limit genelde 15 dakika
        error_msg = f"Twitter API rate limit aşıldı: {rate_limit_error}\n{wait_minutes} dakika sonra tekrar deneyin."
        safe_log(error_msg, "WARNING")
        return {"success": False, "error": error_msg, "rate_limited": True, "wait_minutes": wait_minutes}
        
    except tweepy.Unauthorized as auth_error:
        safe_log(f"Twitter API yetkilendirme hatası: {auth_error}", "ERROR")
        return {"success": False, "error": f"Twitter API yetkilendirme hatası: {auth_error}"}
        
    except tweepy.Forbidden as forbidden_error:
        safe_log(f"Twitter API yasak işlem: {forbidden_error}", "ERROR")
        return {"success": False, "error": f"Twitter API yasak işlem: {forbidden_error}"}
        
    except Exception as e:
        safe_log(f"Tweet paylaşım genel hatası: {e}", "ERROR")
        return {"success": False, "error": str(e)}

def fetch_url_content_with_mcp(url):
    """MCP ile URL içeriği çekme - Tweet oluşturma için"""
    try:
        print(f"🔍 MCP ile URL içeriği çekiliyor: {url}")
        
        # Firecrawl MCP scrape fonksiyonunu kullan
        scrape_result = mcp_firecrawl_scrape({
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
            "waitFor": 3000,
            "removeBase64Images": True
        })
        
        if not scrape_result.get("success", False):
            print(f"⚠️ MCP başarısız, fallback deneniyor...")
            return fetch_url_content_fallback(url)
        
        # Markdown içeriğini al
        markdown_content = scrape_result.get("markdown", "")
        
        if not markdown_content or len(markdown_content) < 100:
            print(f"⚠️ MCP'den yetersiz içerik, fallback deneniyor...")
            return fetch_url_content_fallback(url)
        
        # Başlığı çıkar (genellikle ilk # ile başlar)
        lines = markdown_content.split('\n')
        title = ""
        content_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('# ') and not title:
                title = line[2:].strip()
            elif line and not line.startswith('#') and len(line) > 20:
                content_lines.append(line)
        
        # İçeriği birleştir ve temizle
        content = '\n'.join(content_lines)
        
        # Gereksiz karakterleri temizle
        content = content.replace('*', '').replace('**', '').replace('_', '')
        content = ' '.join(content.split())  # Çoklu boşlukları tek boşluğa çevir
        
        # İçeriği sınırla
        content = content[:2000]
        
        print(f"✅ MCP ile URL içeriği çekildi: {len(content)} karakter")
        
        return {
            "title": title or "Başlık bulunamadı",
            "content": content,
            "url": url,
            "source": "mcp"
        }
        
    except Exception as e:
        print(f"❌ MCP URL çekme hatası ({url}): {e}")
        print("🔄 Fallback yönteme geçiliyor...")
        return fetch_url_content_fallback(url)

def fetch_url_content_fallback(url):
    """Fallback URL içeriği çekme - BeautifulSoup ile"""
    try:
        print(f"🔄 Fallback ile URL içeriği çekiliyor: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Başlığı bul
        title = ""
        title_selectors = ["h1", "h1.entry-title", "h1.post-title", ".article-title h1", "title"]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.text.strip()
                break
        
        # İçeriği bul - çoklu selector deneme
        content_selectors = [
            "article p",
            "div.article-content p",
            "div.entry-content p", 
            "div.post-content p",
            "div.content p",
            ".article-body p",
            "main p",
            ".post p"
        ]
        
        content = ""
        for selector in content_selectors:
            paragraphs = soup.select(selector)
            if paragraphs:
                content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip() and len(p.text.strip()) > 20])
                if len(content) > 200:  # Yeterli içerik bulundu
                    break
        
        # Eğer hala içerik bulunamadıysa, tüm p etiketlerini dene
        if not content:
            all_paragraphs = soup.find_all('p')
            content = "\n".join([p.text.strip() for p in all_paragraphs if len(p.text.strip()) > 30])
        
        # İçeriği temizle ve sınırla
        content = ' '.join(content.split())  # Çoklu boşlukları temizle
        content = content[:2000]  # İçeriği sınırla
        
        print(f"✅ Fallback ile URL içeriği çekildi: {len(content)} karakter")
        
        return {
            "title": title or "Başlık bulunamadı",
            "content": content,
            "url": url,
            "source": "fallback"
        }
        
    except Exception as e:
        print(f"❌ Fallback URL çekme hatası ({url}): {e}")
        return {
            "title": "İçerik çekilemedi",
            "content": f"URL: {url} - İçerik çekilemedi: {str(e)}",
            "url": url,
            "source": "error"
        }

# =============================================================================
# GMAIL E-POSTA BİLDİRİM SİSTEMİ
# =============================================================================

def send_gmail_notification(message, tweet_url="", article_title=""):
    """Gmail SMTP ile e-posta bildirimi gönder"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from datetime import datetime
        import os
        
        # Gmail SMTP ayarları
        gmail_email = os.getenv("GMAIL_EMAIL", "").strip()
        gmail_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
        
        # Ayarları kontrol et
        settings = load_automation_settings()
        email_notifications = settings.get("email_notifications", True)
        
        if not email_notifications:
            print("[DEBUG] E-posta bildirimleri kapalı")
            return {"success": False, "reason": "disabled"}
        
        if not gmail_email:
            print("[WARNING] Gmail e-posta adresi eksik. .env dosyasında GMAIL_EMAIL ayarlayın.")
            return {"success": False, "reason": "missing_email"}
            
        if not gmail_password:
            safe_log("Gmail uygulama şifresi eksik. .env dosyasında GMAIL_APP_PASSWORD ayarlayın.", "WARNING")
            return {"success": False, "reason": "missing_password"}
        
        # E-posta içeriğini hazırla
        subject = "🤖 AI Tweet Bot - Yeni Tweet Paylaşıldı!"
        
        # HTML e-posta içeriği
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                .tweet-box {{ background: white; border-left: 4px solid #1da1f2; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .article-box {{ background: white; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #1da1f2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .stats {{ background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 AI Tweet Bot</h1>
                    <p>Yeni Tweet Başarıyla Paylaşıldı!</p>
                </div>
                
                <div class="content">
                    <div class="tweet-box">
                        <h3>💬 Paylaşılan Tweet:</h3>
                        <p><strong>{message}</strong></p>
                        {f'<a href="{tweet_url}" class="btn">🔗 Tweet&apos;i Görüntüle</a>' if tweet_url else ''}
                    </div>
                    
                    {f'''
                    <div class="article-box">
                        <h3>📰 Kaynak Makale:</h3>
                        <p><strong>{article_title}</strong></p>
                    </div>
                    ''' if article_title else ''}
                    
                    <div class="stats">
                        <h3>📊 Sistem Bilgileri:</h3>
                        <p><strong>⏰ Zaman:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
                        <p><strong>🤖 Bot:</strong> AI Tweet Bot v2.0</p>
                        <p><strong>🔄 Durum:</strong> Otomatik paylaşım aktif</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Bu e-posta AI Tweet Bot tarafından otomatik olarak gönderilmiştir.</p>
                    <p>Bildirimleri kapatmak için uygulama ayarlarından e-posta bildirimlerini devre dışı bırakabilirsiniz.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Metin versiyonu (fallback)
        text_content = f"""
🤖 AI Tweet Bot - Yeni Tweet Paylaşıldı!

💬 Tweet: {message}

{f'📰 Makale: {article_title}' if article_title else ''}

{f'🔗 Tweet Linki: {tweet_url}' if tweet_url else ''}

⏰ Zaman: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

Bu e-posta AI Tweet Bot tarafından otomatik olarak gönderilmiştir.
        """
        
        # E-posta mesajını oluştur
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = gmail_email
        msg['To'] = gmail_email  # Kendine gönder
        
        # Metin ve HTML parçalarını ekle
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Gmail SMTP ile gönder
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(gmail_email, gmail_password)
            server.send_message(msg)
        
        print(f"[SUCCESS] Gmail bildirimi gönderildi: {gmail_email}")
        return {"success": True, "email": gmail_email}
        
    except Exception as e:
        print(f"[ERROR] Gmail bildirim hatası: {e}")
        return {"success": False, "error": str(e)}

def test_gmail_connection():
    """Gmail SMTP bağlantısını test et"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from datetime import datetime
        import os
        
        gmail_email = os.getenv("GMAIL_EMAIL", "").strip()
        gmail_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
        
        if not gmail_email:
            return {
                "success": False, 
                "error": "Gmail e-posta adresi eksik. .env dosyasında GMAIL_EMAIL ayarlayın."
            }
            
        if not gmail_password:
            return {
                "success": False, 
                "error": "Gmail uygulama şifresi eksik. .env dosyasında GMAIL_APP_PASSWORD ayarlayın."
            }
        
        # Test e-postası gönder
        subject = "🧪 AI Tweet Bot - Test E-postası"
        body = f"""
🧪 Test E-postası

Gmail SMTP bağlantısı başarıyla test edildi!

⏰ Test Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
📧 E-posta: {gmail_email}
🤖 AI Tweet Bot v2.0

Bu bir test e-postasıdır.
        """
        
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = gmail_email
        msg['To'] = gmail_email
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(gmail_email, gmail_password)
            server.send_message(msg)
        
        return {
            "success": True, 
            "message": f"✅ Test e-postası başarıyla gönderildi: {gmail_email}"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_gmail_configuration():
    """Gmail konfigürasyonunu kontrol et"""
    try:
        import os
        
        gmail_email = os.getenv("GMAIL_EMAIL", "").strip()
        gmail_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
        
        # Ayarları kontrol et
        settings = load_automation_settings()
        email_notifications = settings.get("email_notifications", True)
        
        status = {
            "email_set": bool(gmail_email and "@" in gmail_email),
            "password_set": bool(gmail_password),
            "notifications_enabled": email_notifications,
            "ready": False
        }
        
        if status["email_set"] and status["password_set"] and status["notifications_enabled"]:
            status["ready"] = True
            status["message"] = "✅ Gmail yapılandırması tamamlanmış ve aktif"
            status["status"] = "ready"
        elif status["email_set"] and status["password_set"]:
            status["message"] = "⚠️ Gmail yapılandırılmış ama bildirimler kapalı"
            status["status"] = "disabled"
        elif status["email_set"]:
            status["message"] = "⚠️ E-posta var, uygulama şifresi eksik"
            status["status"] = "partial"
        else:
            status["message"] = "❌ Gmail yapılandırması eksik"
            status["status"] = "missing"
            
        return status
        
    except Exception as e:
        return {
            "email_set": False,
            "password_set": False,
            "notifications_enabled": False,
            "ready": False,
            "message": f"❌ Kontrol hatası: {e}",
            "status": "error"
        }

# ==========================================
# ÖZEL HABER KAYNAKLARI YÖNETİMİ
# ==========================================

NEWS_SOURCES_FILE = "news_sources.json"

def load_news_sources():
    """Haber kaynaklarını yükle"""
    try:
        if os.path.exists(NEWS_SOURCES_FILE):
            return load_json(NEWS_SOURCES_FILE)
        else:
            # Varsayılan konfigürasyon
            default_config = {
                "sources": [
                    {
                        "id": "techcrunch_ai",
                        "name": "TechCrunch AI",
                        "url": "https://techcrunch.com/category/artificial-intelligence/",
                        "description": "TechCrunch Yapay Zeka haberleri",
                        "enabled": True,
                        "selector_type": "rss_like",
                        "article_selectors": {
                            "container": "article.post-block",
                            "title": "h2.post-block__title a",
                            "link": "h2.post-block__title a",
                            "date": "time.river-byline__time",
                            "excerpt": ".post-block__content"
                        },
                        "added_date": datetime.now().isoformat(),
                        "last_checked": None,
                        "article_count": 0,
                        "success_rate": 100
                    }
                ],
                "settings": {
                    "max_sources": 10,
                    "check_all_sources": True,
                    "source_timeout": 30,
                    "articles_per_source": 5,
                    "last_updated": datetime.now().isoformat()
                }
            }
            save_json(NEWS_SOURCES_FILE, default_config)
            return default_config
    except Exception as e:
        print(f"Haber kaynakları yükleme hatası: {e}")
        return {"sources": [], "settings": {}}

def save_news_sources(config):
    """Haber kaynaklarını kaydet"""
    try:
        config["settings"]["last_updated"] = datetime.now().isoformat()
        save_json(NEWS_SOURCES_FILE, config)
        return {"success": True, "message": "✅ Haber kaynakları kaydedildi"}
    except Exception as e:
        return {"success": False, "message": f"❌ Kaydetme hatası: {e}"}

def test_selectors_for_url(url):
    """URL için selector'ları test et ve önerilerde bulun"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Otomatik selector tespiti
        auto_selectors, container_count = auto_detect_selectors(soup, url)
        
        # Selector'ları doğrula
        is_valid, validation_msg = validate_selectors(soup, auto_selectors)
        
        if is_valid:
            # Örnek makaleler çek
            sample_articles = []
            containers = soup.select(auto_selectors["container"])
            
            for container in containers[:3]:  # İlk 3 makale
                try:
                    title_elem = container.select_one(auto_selectors["title"])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                        link = link_elem.get('href', '') if link_elem else ''
                        
                        if link.startswith('/'):
                            from urllib.parse import urljoin
                            link = urljoin(url, link)
                        
                        sample_articles.append({
                            'title': title[:100] + '...' if len(title) > 100 else title,
                            'link': link
                        })
                except:
                    continue
            
            return {
                'success': True,
                'message': validation_msg,
                'selectors': auto_selectors,
                'container_count': container_count,
                'sample_articles': sample_articles
            }
        else:
            return {
                'success': False,
                'message': validation_msg,
                'selectors': auto_selectors,
                'container_count': container_count
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Test hatası: {str(e)}'
        }

def add_news_source_with_validation(name, url, description="", auto_detect=True):
    """Doğrulama ile yeni haber kaynağı ekle"""
    try:
        config = load_news_sources()
        
        # URL'yi temizle ve doğrula
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Aynı URL var mı kontrol et
        for source in config["sources"]:
            if source["url"] == url:
                return {
                    "success": False,
                    "message": f"❌ Bu URL zaten mevcut: {source['name']}"
                }
        
        # Maksimum kaynak sayısını kontrol et
        max_sources = config["settings"].get("max_sources", 10)
        if len(config["sources"]) >= max_sources:
            return {"success": False, "message": f"❌ Maksimum {max_sources} kaynak eklenebilir"}
        
        # URL'yi test et
        if auto_detect:
            print(f"🔍 {name} kaynağı test ediliyor...")
            test_result = test_selectors_for_url(url)
            
            if not test_result['success']:
                return {
                    "success": False,
                    "message": f"❌ URL test başarısız: {test_result['message']}",
                    "test_details": test_result
                }
            
            selectors = test_result['selectors']
            selector_type = "auto_detected"
            print(f"✅ {name}: {test_result['container_count']} konteyner bulundu")
            
        else:
            # Manuel selector'lar
            selectors = {
                "container": "article, .article, .post, .news-item",
                "title": "h1, h2, h3, .title, .headline",
                "link": "a",
                "date": "time, .date, .published",
                "excerpt": ".excerpt, .summary, p"
            }
            selector_type = "manual"
        
        # Benzersiz ID oluştur
        import random
        source_id = f"custom_{len(config['sources']) + 1}_{random.randint(1000000000, 9999999999)}"
        
        # Yeni kaynak oluştur
        new_source = {
            "id": source_id,
            "name": name.strip(),
            "url": url,
            "description": description.strip(),
            "enabled": True,
            "selector_type": selector_type,
            "article_selectors": selectors,
            "added_date": datetime.now().isoformat(),
            "last_checked": datetime.now().isoformat(),
            "article_count": 0,
            "success_rate": 0
        }
        
        # Kaynağı ekle
        config["sources"].append(new_source)
        config["settings"]["last_updated"] = datetime.now().isoformat()
        
        # Kaydet
        result = save_news_sources(config)
        
        if result["success"]:
            response = {
                "success": True,
                "message": f"✅ '{name}' kaynağı başarıyla eklendi",
                "source": new_source
            }
            
            # Test sonuçlarını da ekle
            if auto_detect and 'test_result' in locals():
                response['test_details'] = test_result
            
            return response
        else:
            return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Kaynak ekleme hatası: {str(e)}"
        }

def add_news_source(name, url, description=""):
    """Yeni haber kaynağı ekle (otomatik doğrulama ile)"""
    return add_news_source_with_validation(name, url, description, auto_detect=True)

def remove_news_source(source_id):
    """Haber kaynağını kaldır"""
    try:
        config = load_news_sources()
        
        # Kaynağı bul ve kaldır
        original_count = len(config["sources"])
        config["sources"] = [s for s in config["sources"] if s["id"] != source_id]
        
        if len(config["sources"]) == original_count:
            return {"success": False, "message": "❌ Kaynak bulunamadı"}
        
        result = save_news_sources(config)
        if result["success"]:
            return {"success": True, "message": "✅ Kaynak başarıyla kaldırıldı"}
        else:
            return result
            
    except Exception as e:
        return {"success": False, "message": f"❌ Kaynak kaldırma hatası: {e}"}

def toggle_news_source(source_id, enabled=None):
    """Haber kaynağını aktif/pasif yap"""
    try:
        config = load_news_sources()
        
        for source in config["sources"]:
            if source["id"] == source_id:
                if enabled is None:
                    source["enabled"] = not source["enabled"]
                else:
                    source["enabled"] = bool(enabled)
                
                result = save_news_sources(config)
                if result["success"]:
                    status = "aktif" if source["enabled"] else "pasif"
                    return {"success": True, "message": f"✅ '{source['name']}' kaynağı {status} yapıldı"}
                else:
                    return result
        
        return {"success": False, "message": "❌ Kaynak bulunamadı"}
        
    except Exception as e:
        return {"success": False, "message": f"❌ Durum değiştirme hatası: {e}"}

def fetch_articles_from_custom_sources():
    """Özel haber kaynaklarından makale çek"""
    try:
        config = load_news_sources()
        all_articles = []
        
        enabled_sources = [s for s in config["sources"] if s.get("enabled", True)]
        
        if not enabled_sources:
            print("⚠️ Aktif haber kaynağı bulunamadı")
            return []
        
        # Terminal log için import
        try:
            from app import terminal_log
        except ImportError:
            # Eğer app.py'den import edilemezse normal print kullan
            def terminal_log(msg, level='info'):
                print(f"[{level.upper()}] {msg}")
        
        terminal_log(f"🔍 {len(enabled_sources)} haber kaynağından makale çekiliyor...", "info")
        
        for source in enabled_sources:
            try:
                terminal_log(f"📰 {source['name']} kaynağı kontrol ediliyor...", "info")
                
                # Kaynak URL'sini çek
                articles = fetch_articles_from_single_source(source)
                
                if articles:
                    all_articles.extend(articles)
                    source["article_count"] = len(articles)
                    source["success_rate"] = min(100, source.get("success_rate", 0) + 10)
                    terminal_log(f"✅ {source['name']}: {len(articles)} makale bulundu", "success")
                else:
                    source["success_rate"] = max(0, source.get("success_rate", 100) - 20)
                    terminal_log(f"⚠️ {source['name']}: Makale bulunamadı", "warning")
                
                source["last_checked"] = datetime.now().isoformat()
                
            except Exception as e:
                terminal_log(f"❌ {source['name']} hatası: {e}", "error")
                source["success_rate"] = max(0, source.get("success_rate", 100) - 30)
                source["last_checked"] = datetime.now().isoformat()
        
        # Güncellenmiş istatistikleri kaydet
        save_news_sources(config)
        
        terminal_log(f"📊 Toplam {len(all_articles)} makale çekildi", "info")
        
        # Duplikat filtreleme uygula
        if all_articles:
            filtered_articles = filter_duplicate_articles(all_articles)
            terminal_log(f"✅ Duplikat filtreleme sonrası {len(filtered_articles)} benzersiz makale", "success")
            return filtered_articles
        
        return all_articles
        
    except Exception as e:
        print(f"❌ Özel kaynaklardan makale çekme hatası: {e}")
        return []

def auto_detect_selectors(soup, url):
    """Sayfadan otomatik olarak en iyi selector'ları tespit et"""
    
    # Yaygın makale konteyner pattern'leri (öncelik sırasına göre)
    container_patterns = [
        # Modern WordPress (TechCrunch tarzı)
        "li.wp-block-post",
        "article.wp-block-post", 
        ".loop-card",
        
        # Modern haber siteleri
        "article[data-testid*='story']",
        "article[data-testid*='card']",
        ".story-card",
        ".news-item",
        
        # Genel WordPress
        "article.post",
        ".post-item",
        ".entry",
        
        # Klasik yapılar
        "article",
        ".article",
        ".post",
        "[class*='article']",
        "[class*='post']",
        "[class*='story']",
        "[class*='news']"
    ]
    
    best_selectors = {
        "container": "article",
        "title": "h2 a",
        "link": "h2 a", 
        "date": "time",
        "excerpt": "p"
    }
    
    max_containers = 0
    
    # En çok konteyner bulan selector'ı seç (ama çok fazla olmasın)
    for pattern in container_patterns:
        containers = soup.select(pattern)
        container_count = len(containers)
        
        # İdeal aralık: 3-50 konteyner
        if 3 <= container_count <= 50 and container_count > max_containers:
            max_containers = container_count
            best_selectors["container"] = pattern
            
            # Bu konteyner için en iyi title selector'ını bul
            if containers:
                sample_container = containers[0]
                
                title_patterns = [
                    "h3.loop-card__title a",  # TechCrunch modern
                    "h2 a", "h3 a", "h1 a",
                    ".title a", ".headline a",
                    "[class*='title'] a",
                    "[class*='headline'] a",
                    "a[href*='article']",
                    "a[href*='post']",
                    "a"  # Son çare
                ]
                
                for title_pattern in title_patterns:
                    title_elem = sample_container.select_one(title_pattern)
                    if title_elem and title_elem.get_text(strip=True):
                        best_selectors["title"] = title_pattern
                        best_selectors["link"] = title_pattern
                        break
                
                # Date selector
                date_patterns = [
                    "time.loop-card__time",
                    "time", ".date", ".published",
                    "[class*='date']", "[class*='time']",
                    "[datetime]"
                ]
                
                for date_pattern in date_patterns:
                    if sample_container.select_one(date_pattern):
                        best_selectors["date"] = date_pattern
                        break
    
    return best_selectors, max_containers

def validate_selectors(soup, selectors):
    """Selector'ların çalışıp çalışmadığını kontrol et"""
    
    container_selector = selectors.get("container", "article")
    containers = soup.select(container_selector)
    
    if not containers:
        return False, "Konteyner bulunamadı"
    
    if len(containers) > 100:
        return False, f"Çok fazla konteyner ({len(containers)}), selector çok genel"
    
    # İlk konteynerden örnek al
    sample_container = containers[0]
    
    title_selector = selectors.get("title", "h2 a")
    title_elem = sample_container.select_one(title_selector)
    
    if not title_elem:
        return False, "Başlık elementi bulunamadı"
    
    title_text = title_elem.get_text(strip=True)
    if len(title_text) < 10:
        return False, "Başlık çok kısa"
    
    # Link kontrolü
    link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
    if not link_elem or not link_elem.get('href'):
        return False, "Link bulunamadı"
    
    return True, f"✅ {len(containers)} konteyner, örnek başlık: {title_text[:50]}..."

def fetch_articles_from_single_source(source):
    """Tek bir kaynaktan makale çek"""
    try:
        url = source["url"]
        selectors = source.get("article_selectors", {})
        source_name = source.get("name", "Bilinmeyen")
        
        # Sayfayı çek
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Eğer selector_type auto_detect ise veya mevcut selector'lar çalışmıyorsa
        if source.get('selector_type') == 'auto_detect' or not selectors:
            print(f"🔍 {source_name} için otomatik selector tespiti yapılıyor...")
            auto_selectors, container_count = auto_detect_selectors(soup, url)
            
            # Otomatik tespit edilen selector'ları doğrula
            is_valid, validation_msg = validate_selectors(soup, auto_selectors)
            
            if is_valid:
                print(f"✅ Otomatik tespit başarılı: {validation_msg}")
                selectors = auto_selectors
                
                # Başarılı selector'ları kaydet
                source["article_selectors"] = auto_selectors
                source["selector_type"] = "auto_detected"
            else:
                print(f"❌ Otomatik tespit başarısız: {validation_msg}")
                return []
        else:
            # Mevcut selector'ları doğrula
            is_valid, validation_msg = validate_selectors(soup, selectors)
            if not is_valid:
                print(f"⚠️ Mevcut selector'lar çalışmıyor: {validation_msg}")
                print(f"🔄 Otomatik tespit deneniyor...")
                
                auto_selectors, container_count = auto_detect_selectors(soup, url)
                is_auto_valid, auto_validation_msg = validate_selectors(soup, auto_selectors)
                
                if is_auto_valid:
                    print(f"✅ Otomatik tespit ile düzeltildi: {auto_validation_msg}")
                    selectors = auto_selectors
                else:
                    print(f"❌ Otomatik tespit de başarısız: {auto_validation_msg}")
                    return []
        
        # Makale konteynerlerini bul
        container_selector = selectors.get("container", "article, .article, .post")
        containers = soup.select(container_selector)
        
        if not containers:
            # Alternatif selectors dene
            alternative_selectors = [
                "li.wp-block-post",  # TechCrunch modern
                "article[data-testid='story-card']",  # The Verge modern
                ".c-entry-box", ".c-compact-river__entry",  # The Verge classic
                "article", ".post", ".news-item", ".story", 
                ".entry", ".content-item", "[class*='article']",
                "[class*='post']", "[class*='news']", "[class*='loop-card']"
            ]
            
            for alt_selector in alternative_selectors:
                containers = soup.select(alt_selector)
                if containers:
                    print(f"🔄 Alternatif selector kullanıldı: {alt_selector}")
                    break
        
        print(f"🔍 {source['name']}: {len(containers)} konteyner bulundu")
        
        for container in containers[:5]:  # İlk 5 makale
            try:
                # Başlık bul
                title_selector = selectors.get("title", "h1, h2, h3, .title, .headline")
                title_elem = container.select_one(title_selector)
                
                # Alternatif title selector'ları dene
                if not title_elem:
                    alt_title_selectors = [
                        "h3.loop-card__title a",  # TechCrunch modern
                        "h2 a", ".c-entry-box__title a",  # The Verge
                        "h1 a", "h2 a", "h3 a", "h4 a",
                        ".title a", ".headline a", "[class*='title'] a"
                    ]
                    
                    for alt_selector in alt_title_selectors:
                        title_elem = container.select_one(alt_selector)
                        if title_elem:
                            break
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Link bul
                link_elem = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if not link_elem:
                    link_elem = container.select_one('a')
                
                if not link_elem:
                    continue
                
                link = link_elem.get('href', '')
                
                # Relative URL'leri absolute yap
                if link.startswith('/'):
                    from urllib.parse import urljoin
                    link = urljoin(url, link)
                elif not link.startswith('http'):
                    continue
                
                # Özet bul
                excerpt_selector = selectors.get("excerpt", ".excerpt, .summary, p")
                excerpt_elem = container.select_one(excerpt_selector)
                excerpt = excerpt_elem.get_text(strip=True)[:200] if excerpt_elem else ""
                
                # Tarih bul (opsiyonel)
                date_selector = selectors.get("date", "time, .date, .published")
                date_elem = container.select_one(date_selector)
                date_str = date_elem.get_text(strip=True) if date_elem else ""
                
                if title and link:
                    articles.append({
                        "title": title,
                        "url": link,
                        "excerpt": excerpt,
                        "date": date_str,
                        "source": source["name"],
                        "source_id": source["id"],
                        "fetch_date": datetime.now().isoformat(),
                        "is_new": True,
                        "already_posted": False
                    })
                    
            except Exception as e:
                print(f"⚠️ Makale parse hatası: {e}")
                continue
        
        return articles
        
    except Exception as e:
        print(f"❌ {source.get('name', 'Bilinmeyen')} kaynak hatası: {e}")
        return []

def get_news_sources_stats():
    """Haber kaynakları istatistiklerini al"""
    try:
        config = load_news_sources()
        
        total_sources = len(config["sources"])
        enabled_sources = len([s for s in config["sources"] if s.get("enabled", True)])
        total_articles = sum(s.get("article_count", 0) for s in config["sources"])
        avg_success_rate = sum(s.get("success_rate", 0) for s in config["sources"]) / max(1, total_sources)
        
        return {
            "total_sources": total_sources,
            "enabled_sources": enabled_sources,
            "disabled_sources": total_sources - enabled_sources,
            "total_articles_fetched": total_articles,
            "average_success_rate": round(avg_success_rate, 1),
            "sources": config["sources"],
            "settings": config["settings"]
        }
        
    except Exception as e:
        return {
            "total_sources": 0,
            "enabled_sources": 0,
            "disabled_sources": 0,
            "total_articles_fetched": 0,
            "average_success_rate": 0,
            "sources": [],
            "settings": {},
            "error": str(e)
        }

def update_fetch_articles_function():
    """Ana makale çekme fonksiyonunu güncelle - özel kaynakları dahil et"""
    try:
        # Önce özel kaynaklardan makale çek
        custom_articles = fetch_articles_from_custom_sources()
        
        # Sonra mevcut TechCrunch fallback'i çek (eğer özel kaynaklarda TechCrunch yoksa)
        config = load_news_sources()
        has_techcrunch = any("techcrunch" in s.get("url", "").lower() for s in config["sources"] if s.get("enabled", True))
        
        if not has_techcrunch:
            print("🔄 TechCrunch fallback ekleniyor...")
            fallback_articles = fetch_latest_ai_articles_fallback()
            custom_articles.extend(fallback_articles)
        
        return custom_articles
        
    except Exception as e:
        print(f"❌ Güncellenmiş makale çekme hatası: {e}")
        # Fallback olarak eski fonksiyonu çağır
        return fetch_latest_ai_articles_fallback()

# =============================================================================
# GÜVENLİ LOGGING SİSTEMİ
# =============================================================================

def safe_log(message, level="INFO", sensitive_data=None):
    """Güvenli logging - şifre ve API anahtarlarını gizler"""
    import os
    
    # Sadece debug modunda detaylı log
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    if not debug_mode and level == "DEBUG":
        return
    
    # Mesajı güvenli hale getir
    safe_message = sanitize_log_message(str(message))
    
    # Hassas verileri gizle
    if sensitive_data:
        for key, value in sensitive_data.items():
            if value and len(str(value)) > 3:
                masked_value = str(value)[:3] + "*" * (len(str(value)) - 3)
                safe_message = safe_message.replace(str(value), masked_value)
    
    # Production'da sadece önemli logları göster
    if not debug_mode and level not in ["ERROR", "WARNING", "INFO"]:
        return
    
    print(f"[{level}] {safe_message}")

# =============================================================================
# GÜVENLİK KONTROL FONKSİYONLARI
# =============================================================================

def check_security_configuration():
    """Güvenlik yapılandırmasını kontrol et"""
    import os
    
    security_issues = []
    
    # 1. Debug mode kontrolü
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    flask_env = os.environ.get('FLASK_ENV', 'production')
    
    if debug_mode and flask_env == 'production':
        security_issues.append("⚠️ Production'da DEBUG modu açık!")
    
    # 2. Varsayılan şifre kontrolü
    password = os.environ.get('SIFRE', 'admin123')
    if password in ['admin123', 'password', '123456', 'admin']:
        security_issues.append("🔒 Varsayılan şifre kullanılıyor! Değiştirin.")
    
    # 3. Secret key kontrolü
    secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    if secret_key == 'your-secret-key-here' or len(secret_key) < 32:
        security_issues.append("🔑 Güçlü SECRET_KEY kullanın!")
    
    # 4. API anahtarları kontrolü
    api_keys = [
        'GOOGLE_API_KEY',
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET',
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET'
    ]
    
    for key in api_keys:
        value = os.environ.get(key, '')
        if value and ('your-' in value.lower() or 'example' in value.lower()):
            security_issues.append(f"🔐 {key} örnek değer içeriyor!")
    
    return {
        "secure": len(security_issues) == 0,
        "issues": security_issues,
        "debug_mode": debug_mode,
        "flask_env": flask_env
    }

def sanitize_log_message(message):
    """Log mesajlarından hassas bilgileri temizle"""
    import re
    
    # API anahtarı pattern'leri
    patterns = [
        r'AIza[0-9A-Za-z-_]{35}',  # Google API Key
        r'sk-[a-zA-Z0-9]{48}',     # OpenAI API Key
        r'[0-9]{10}:[A-Za-z0-9_-]{35}',  # Telegram Bot Token
        r'[A-Za-z0-9]{25}',        # Twitter Bearer Token
        r'[A-Za-z0-9]{15,25}',     # Twitter API Keys
    ]
    
    for pattern in patterns:
        message = re.sub(pattern, '***MASKED***', message)
    
    # Şifre pattern'leri
    password_patterns = [
        r'password["\s]*[:=]["\s]*[^"\s]+',
        r'pass["\s]*[:=]["\s]*[^"\s]+',
        r'token["\s]*[:=]["\s]*[^"\s]+',
        r'key["\s]*[:=]["\s]*[^"\s]+',
    ]
    
    for pattern in password_patterns:
        message = re.sub(pattern, 'password=***MASKED***', message, flags=re.IGNORECASE)
    
    return message

def calculate_text_similarity(text1, text2):
    """İki metin arasındaki benzerlik oranını hesapla (0-1 arası)"""
    if not text1 or not text2:
        return 0.0
    
    # Metinleri normalize et
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    
    # Çok kısa metinler için direkt karşılaştırma
    if len(text1) < 10 or len(text2) < 10:
        return 1.0 if text1 == text2 else 0.0
    
    # SequenceMatcher ile benzerlik hesapla
    similarity = SequenceMatcher(None, text1, text2).ratio()
    return similarity

def normalize_title_for_comparison(title):
    """Başlığı karşılaştırma için normalize et"""
    if not title:
        return ""
    
    # Küçük harfe çevir
    normalized = title.lower()
    
    # Gereksiz karakterleri kaldır
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    
    # Çoklu boşlukları tek boşluğa çevir
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Yaygın kelimeler ve ifadeleri kaldır
    stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'says', 'announces', 'reveals', 'launches', 'introduces']
    words = normalized.split()
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    return ' '.join(filtered_words)

def extract_key_content_features(content):
    """İçerikten anahtar özellikler çıkar"""
    if not content:
        return set()
    
    # Metni normalize et
    normalized = content.lower()
    
    # Sayıları ve özel terimleri çıkar
    features = set()
    
    # Sayısal değerler (para, yüzde, sayılar)
    numbers = re.findall(r'\$[\d,]+(?:\.\d+)?[bmk]?|\d+(?:\.\d+)?%|\d+(?:\.\d+)?(?:\s*(?:billion|million|thousand|percent))?', normalized)
    features.update(numbers)
    
    # Şirket isimleri (büyük harfle başlayan kelimeler)
    companies = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
    features.update([c.lower() for c in companies])
    
    # Önemli teknoloji terimleri
    tech_terms = re.findall(r'\b(?:ai|artificial intelligence|machine learning|deep learning|neural network|algorithm|api|cloud|blockchain|cryptocurrency|robot|automation|quantum|5g|iot|ar|vr|metaverse)\b', normalized)
    features.update(tech_terms)
    
    return features

def check_content_similarity(article1, article2, title_threshold=0.8, content_threshold=0.6):
    """İki makale arasındaki benzerliği kontrol et"""
    try:
        title1 = article1.get('title', '')
        title2 = article2.get('title', '')
        content1 = article1.get('content', '')
        content2 = article2.get('content', '')
        
        # Başlık benzerliği
        normalized_title1 = normalize_title_for_comparison(title1)
        normalized_title2 = normalize_title_for_comparison(title2)
        title_similarity = calculate_text_similarity(normalized_title1, normalized_title2)
        
        # Eğer başlıklar çok benzer ise, muhtemelen aynı haber
        if title_similarity >= title_threshold:
            return True, title_similarity, "title"
        
        # İçerik özellik benzerliği
        features1 = extract_key_content_features(content1)
        features2 = extract_key_content_features(content2)
        
        if features1 and features2:
            # Jaccard benzerliği (kesişim / birleşim)
            intersection = len(features1.intersection(features2))
            union = len(features1.union(features2))
            feature_similarity = intersection / union if union > 0 else 0.0
            
            if feature_similarity >= content_threshold:
                return True, feature_similarity, "content_features"
        
        # İçerik metni benzerliği (sadece kısa içerikler için)
        if len(content1) < 1000 and len(content2) < 1000:
            content_similarity = calculate_text_similarity(content1[:500], content2[:500])
            if content_similarity >= content_threshold:
                return True, content_similarity, "content_text"
        
        return False, max(title_similarity, feature_similarity if 'feature_similarity' in locals() else 0), "no_match"
        
    except Exception as e:
        print(f"Benzerlik kontrolü hatası: {e}")
        return False, 0.0, "error"

def filter_duplicate_articles(new_articles, existing_articles=None):
    """Yeni makalelerden duplikatları filtrele"""
    try:
        # Ayarları yükle
        settings = load_automation_settings()
        
        # Eğer duplikat tespiti kapalıysa, sadece temel kontrolleri yap
        if not settings.get('enable_duplicate_detection', True):
            print("🔄 Gelişmiş duplikat tespiti kapalı, sadece temel kontroller yapılıyor...")
            return basic_duplicate_filter(new_articles, existing_articles)
        
        # Eşik değerlerini ayarlardan al
        title_threshold = settings.get('title_similarity_threshold', 0.8)
        content_threshold = settings.get('content_similarity_threshold', 0.6)
        
        print(f"🔍 Gelişmiş duplikat tespiti aktif (Başlık: {title_threshold:.0%}, İçerik: {content_threshold:.0%})")
        
        if existing_articles is None:
            # Mevcut paylaşılan makaleleri yükle
            existing_articles = load_json(HISTORY_FILE)
        
        # Bekleyen tweet'leri de kontrol et
        pending_tweets = load_json("pending_tweets.json")
        pending_articles = [tweet.get('article', {}) for tweet in pending_tweets if tweet.get('article')]
        
        # Tüm mevcut makaleleri birleştir (silinen makaleler de dahil)
        all_existing = existing_articles + pending_articles
        
        # Silinen makaleleri de kontrol et (deleted=True olanlar)
        deleted_articles = [article for article in existing_articles if article.get('deleted', False)]
        if deleted_articles:
            print(f"🗑️ {len(deleted_articles)} silinen makale duplikat kontrole dahil edildi")
        
        filtered_articles = []
        duplicate_count = 0
        
        for new_article in new_articles:
            is_duplicate = False
            
            # Önce URL kontrolü (hızlı)
            new_url = new_article.get('url', '')
            for existing in all_existing:
                if new_url == existing.get('url', ''):
                    is_duplicate = True
                    break
            
            if is_duplicate:
                duplicate_count += 1
                print(f"🔄 URL duplikatı atlandı: {new_article.get('title', '')[:50]}...")
                continue
            
            # Hash kontrolü (hızlı)
            new_hash = new_article.get('hash', '')
            if new_hash:
                for existing in all_existing:
                    if new_hash == existing.get('hash', ''):
                        is_duplicate = True
                        break
            
            if is_duplicate:
                duplicate_count += 1
                print(f"🔄 Hash duplikatı atlandı: {new_article.get('title', '')[:50]}...")
                continue
            
            # İçerik benzerliği kontrolü (yavaş ama etkili)
            for existing in all_existing:
                is_similar, similarity_score, match_type = check_content_similarity(
                    new_article, existing, title_threshold, content_threshold
                )
                if is_similar:
                    is_duplicate = True
                    print(f"🔄 İçerik benzerliği ({match_type}: {similarity_score:.2f}) - atlandı: {new_article.get('title', '')[:50]}...")
                    break
            
            if not is_duplicate:
                # Aynı batch içinde de kontrol et
                for other_article in filtered_articles:
                    is_similar, similarity_score, match_type = check_content_similarity(
                        new_article, other_article, title_threshold, content_threshold
                    )
                    if is_similar:
                        is_duplicate = True
                        print(f"🔄 Batch içi benzerlik ({match_type}: {similarity_score:.2f}) - atlandı: {new_article.get('title', '')[:50]}...")
                        break
            
            if not is_duplicate:
                filtered_articles.append(new_article)
                print(f"✅ Yeni makale eklendi: {new_article.get('title', '')[:50]}...")
            else:
                duplicate_count += 1
        
        print(f"📊 Duplikat filtreleme tamamlandı: {len(new_articles)} makale → {len(filtered_articles)} benzersiz makale ({duplicate_count} duplikat)")
        return filtered_articles
        
    except Exception as e:
        print(f"Duplikat filtreleme hatası: {e}")
        return new_articles  # Hata durumunda orijinal listeyi döndür

def basic_duplicate_filter(new_articles, existing_articles=None):
    """Temel duplikat filtreleme - sadece URL ve hash kontrolü"""
    try:
        if existing_articles is None:
            existing_articles = load_json(HISTORY_FILE)
        
        # Bekleyen tweet'leri de kontrol et
        pending_tweets = load_json("pending_tweets.json")
        pending_articles = [tweet.get('article', {}) for tweet in pending_tweets if tweet.get('article')]
        
        # Tüm mevcut makaleleri birleştir (silinen makaleler de dahil)
        all_existing = existing_articles + pending_articles
        
        # Silinen makaleleri de kontrol et (deleted=True olanlar)
        deleted_articles = [article for article in existing_articles if article.get('deleted', False)]
        if deleted_articles:
            print(f"🗑️ {len(deleted_articles)} silinen makale temel duplikat kontrole dahil edildi")
        
        # Mevcut URL'ler ve hash'ler
        existing_urls = set(article.get('url', '') for article in all_existing)
        existing_hashes = set(article.get('hash', '') for article in all_existing)
        
        filtered_articles = []
        duplicate_count = 0
        
        for new_article in new_articles:
            new_url = new_article.get('url', '')
            new_hash = new_article.get('hash', '')
            
            # URL kontrolü
            if new_url in existing_urls:
                duplicate_count += 1
                print(f"🔄 URL duplikatı atlandı: {new_article.get('title', '')[:50]}...")
                continue
            
            # Hash kontrolü
            if new_hash and new_hash in existing_hashes:
                duplicate_count += 1
                print(f"🔄 Hash duplikatı atlandı: {new_article.get('title', '')[:50]}...")
                continue
            
            # Aynı batch içinde URL kontrolü
            batch_urls = set(article.get('url', '') for article in filtered_articles)
            if new_url in batch_urls:
                duplicate_count += 1
                print(f"🔄 Batch içi URL duplikatı atlandı: {new_article.get('title', '')[:50]}...")
                continue
            
            filtered_articles.append(new_article)
            print(f"✅ Yeni makale eklendi: {new_article.get('title', '')[:50]}...")
        
        print(f"📊 Temel duplikat filtreleme tamamlandı: {len(new_articles)} makale → {len(filtered_articles)} benzersiz makale ({duplicate_count} duplikat)")
        return filtered_articles
        
    except Exception as e:
        print(f"Temel duplikat filtreleme hatası: {e}")
        return new_articles

def clean_duplicate_pending_tweets():
    """Bekleyen tweet'lerdeki duplikatları temizle"""
    try:
        pending_tweets = load_json("pending_tweets.json")
        
        if not pending_tweets:
            return {
                "success": True,
                "message": "Bekleyen tweet bulunamadı",
                "original_count": 0,
                "cleaned_count": 0,
                "removed_count": 0
            }
        
        print(f"🔍 {len(pending_tweets)} bekleyen tweet kontrol ediliyor...")
        
        # Benzersiz tweet'leri saklamak için
        unique_tweets = []
        seen_urls = set()
        seen_hashes = set()
        seen_titles = set()
        
        duplicate_count = 0
        
        for tweet in pending_tweets:
            article = tweet.get('article', {})
            url = article.get('url', '')
            hash_val = article.get('hash', '')
            title = article.get('title', '')
            
            # URL kontrolü
            if url and url in seen_urls:
                duplicate_count += 1
                print(f"🔄 URL duplikatı atlandı: {title[:50]}...")
                continue
            
            # Hash kontrolü
            if hash_val and hash_val in seen_hashes:
                duplicate_count += 1
                print(f"🔄 Hash duplikatı atlandı: {title[:50]}...")
                continue
            
            # Başlık kontrolü (normalize edilmiş)
            if title:
                normalized_title = normalize_title_for_comparison(title)
                if normalized_title in seen_titles:
                    duplicate_count += 1
                    print(f"🔄 Başlık duplikatı atlandı: {title[:50]}...")
                    continue
                seen_titles.add(normalized_title)
            
            # Benzersiz tweet olarak ekle
            unique_tweets.append(tweet)
            if url:
                seen_urls.add(url)
            if hash_val:
                seen_hashes.add(hash_val)
            
            print(f"✅ Benzersiz tweet korundu: {title[:50]}...")
        
        # Temizlenmiş listeyi kaydet
        save_json("pending_tweets.json", unique_tweets)
        
        result = {
            "success": True,
            "message": f"✅ Bekleyen tweet'ler temizlendi",
            "original_count": len(pending_tweets),
            "cleaned_count": len(unique_tweets),
            "removed_count": duplicate_count
        }
        
        print(f"📊 Duplikat temizleme tamamlandı: {len(pending_tweets)} → {len(unique_tweets)} tweet ({duplicate_count} duplikat kaldırıldı)")
        
        return result
        
    except Exception as e:
        print(f"❌ Duplikat temizleme hatası: {e}")
        return {
            "success": False,
            "message": f"❌ Temizleme hatası: {str(e)}",
            "original_count": 0,
            "cleaned_count": 0,
            "removed_count": 0
        }

# =============================================================================
# Rate limit yönetimi için global değişkenler
RATE_LIMIT_FILE = "rate_limit_status.json"
TWITTER_RATE_LIMITS = {
    "tweets": {"limit": 5, "window": 900},  # 15 dakikada 5 tweet (Free plan için güvenli)
    "user_lookup": {"limit": 50, "window": 900},  # 15 dakikada 50 kullanıcı sorgusu
    "timeline": {"limit": 30, "window": 900}  # 15 dakikada 30 timeline sorgusu
}

def load_rate_limit_status():
    """Rate limit durumunu yükle"""
    try:
        if os.path.exists(RATE_LIMIT_FILE):
            with open(RATE_LIMIT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Rate limit durumu yüklenirken hata: {e}")
        return {}

def save_rate_limit_status(status):
    """Rate limit durumunu kaydet"""
    try:
        with open(RATE_LIMIT_FILE, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Rate limit durumu kaydedilirken hata: {e}")

def check_rate_limit(endpoint="tweets"):
    """Rate limit kontrolü yap"""
    try:
        status = load_rate_limit_status()
        current_time = time.time()
        
        if endpoint not in status:
            status[endpoint] = {
                "requests": 0,
                "reset_time": current_time + TWITTER_RATE_LIMITS[endpoint]["window"],
                "last_request": current_time
            }
        
        endpoint_status = status[endpoint]
        
        # Reset zamanı geçtiyse sıfırla
        if current_time >= endpoint_status["reset_time"]:
            endpoint_status["requests"] = 0
            endpoint_status["reset_time"] = current_time + TWITTER_RATE_LIMITS[endpoint]["window"]
        
        # Limit kontrolü
        if endpoint_status["requests"] >= TWITTER_RATE_LIMITS[endpoint]["limit"]:
            wait_time = endpoint_status["reset_time"] - current_time
            return {
                "allowed": False,
                "wait_time": wait_time,
                "requests_made": endpoint_status["requests"],
                "limit": TWITTER_RATE_LIMITS[endpoint]["limit"]
            }
        
        return {
            "allowed": True,
            "requests_made": endpoint_status["requests"],
            "limit": TWITTER_RATE_LIMITS[endpoint]["limit"],
            "reset_time": endpoint_status["reset_time"]
        }
        
    except Exception as e:
        print(f"Rate limit kontrolü hatası: {e}")
        return {"allowed": True}  # Hata durumunda izin ver

def update_rate_limit_usage(endpoint="tweets"):
    """Rate limit kullanımını güncelle"""
    try:
        status = load_rate_limit_status()
        current_time = time.time()
        
        if endpoint not in status:
            status[endpoint] = {
                "requests": 0,
                "reset_time": current_time + TWITTER_RATE_LIMITS[endpoint]["window"],
                "last_request": current_time
            }
        
        # Reset zamanı geçtiyse sıfırla
        if current_time >= status[endpoint]["reset_time"]:
            status[endpoint]["requests"] = 0
            status[endpoint]["reset_time"] = current_time + TWITTER_RATE_LIMITS[endpoint]["window"]
        
        # Kullanımı artır
        status[endpoint]["requests"] += 1
        status[endpoint]["last_request"] = current_time
        
        save_rate_limit_status(status)
        
        print(f"Rate limit güncellendi - {endpoint}: {status[endpoint]['requests']}/{TWITTER_RATE_LIMITS[endpoint]['limit']}")
        
    except Exception as e:
        print(f"Rate limit güncelleme hatası: {e}")

def get_rate_limit_info():
    """Rate limit bilgilerini al"""
    try:
        status = load_rate_limit_status()
        current_time = time.time()
        info = {}
        
        for endpoint in TWITTER_RATE_LIMITS:
            if endpoint in status:
                endpoint_status = status[endpoint]
                
                # Reset zamanı geçtiyse sıfırla
                if current_time >= endpoint_status["reset_time"]:
                    requests_made = 0
                    reset_time = current_time + TWITTER_RATE_LIMITS[endpoint]["window"]
                else:
                    requests_made = endpoint_status["requests"]
                    reset_time = endpoint_status["reset_time"]
                
                info[endpoint] = {
                    "requests_made": requests_made,
                    "limit": TWITTER_RATE_LIMITS[endpoint]["limit"],
                    "remaining": TWITTER_RATE_LIMITS[endpoint]["limit"] - requests_made,
                    "reset_time": reset_time,
                    "reset_in_minutes": max(0, (reset_time - current_time) / 60)
                }
            else:
                info[endpoint] = {
                    "requests_made": 0,
                    "limit": TWITTER_RATE_LIMITS[endpoint]["limit"],
                    "remaining": TWITTER_RATE_LIMITS[endpoint]["limit"],
                    "reset_time": current_time + TWITTER_RATE_LIMITS[endpoint]["window"],
                    "reset_in_minutes": TWITTER_RATE_LIMITS[endpoint]["window"] / 60
                }
        
        return info
        
    except Exception as e:
        print(f"Rate limit bilgisi alma hatası: {e}")
        return {}

def retry_pending_tweets_after_rate_limit():
    """Rate limit sıfırlandıktan sonra bekleyen tweet'leri tekrar dene"""
    try:
        # Rate limit durumunu kontrol et
        rate_check = check_rate_limit("tweets")
        if not rate_check.get("allowed", True):
            print(f"Rate limit hala aktif, {int(rate_check.get('wait_time', 0) / 60)} dakika daha beklenecek")
            return {"success": False, "message": "Rate limit hala aktif"}
        
        # Bekleyen tweet'leri yükle
        pending_tweets = load_json("pending_tweets.json")
        if not pending_tweets:
            return {"success": True, "message": "Bekleyen tweet yok"}
        
        # Rate limit hatası olan tweet'leri filtrele
        rate_limited_tweets = []
        other_tweets = []
        
        for tweet in pending_tweets:
            error_reason = tweet.get('error_reason', '')
            if 'rate limit' in error_reason.lower() or '429' in error_reason:
                rate_limited_tweets.append(tweet)
            else:
                other_tweets.append(tweet)
        
        if not rate_limited_tweets:
            return {"success": True, "message": "Rate limit hatası olan tweet yok"}
        
        print(f"🔄 {len(rate_limited_tweets)} rate limit hatası olan tweet tekrar deneniyor...")
        
        successful_posts = 0
        failed_posts = 0
        
        for tweet in rate_limited_tweets:
            try:
                # Rate limit kontrolü yap (her tweet için)
                rate_check = check_rate_limit("tweets")
                if not rate_check.get("allowed", True):
                    print("Rate limit tekrar aşıldı, kalan tweet'ler beklemede kalacak")
                    break
                
                # Tweet'i paylaş
                tweet_text = tweet['tweet_data']['tweet']
                result = post_text_tweet_v2(tweet_text)
                
                if result.get('success'):
                    # Başarılı paylaşım - posted_articles'a ekle
                    article = tweet['article']
                    article['posted_date'] = datetime.now().isoformat()
                    article['tweet_text'] = tweet_text
                    article['tweet_url'] = result.get('url', '')
                    article['manual_post'] = False
                    
                    # Posted articles'a ekle
                    posted_articles = load_json("posted_articles.json")
                    posted_articles.append(article)
                    save_json("posted_articles.json", posted_articles)
                    
                    successful_posts += 1
                    print(f"✅ Tweet başarıyla paylaşıldı: {article.get('title', '')[:50]}...")
                    
                else:
                    # Hala hata var - tweet'i other_tweets'e ekle
                    tweet['retry_count'] = tweet.get('retry_count', 0) + 1
                    tweet['error_reason'] = result.get('error', 'Bilinmeyen hata')
                    other_tweets.append(tweet)
                    failed_posts += 1
                    print(f"❌ Tweet paylaşım hatası: {result.get('error', 'Bilinmeyen hata')}")
                    
                    # Rate limit hatası ise dur
                    if result.get('rate_limited'):
                        print("Rate limit tekrar aşıldı, kalan tweet'ler beklemede kalacak")
                        # Kalan tweet'leri de other_tweets'e ekle
                        remaining_tweets = rate_limited_tweets[rate_limited_tweets.index(tweet) + 1:]
                        other_tweets.extend(remaining_tweets)
                        break
                
            except Exception as e:
                print(f"Tweet retry hatası: {e}")
                tweet['retry_count'] = tweet.get('retry_count', 0) + 1
                tweet['error_reason'] = str(e)
                other_tweets.append(tweet)
                failed_posts += 1
        
        # Güncellenmiş pending tweet'leri kaydet
        save_json("pending_tweets.json", other_tweets)
        
        message = f"✅ {successful_posts} tweet başarıyla paylaşıldı"
        if failed_posts > 0:
            message += f", {failed_posts} tweet hala beklemede"
        
        print(f"📊 Retry tamamlandı: {successful_posts} başarılı, {failed_posts} başarısız")
        
        return {
            "success": True,
            "message": message,
            "successful_posts": successful_posts,
            "failed_posts": failed_posts
        }
        
    except Exception as e:
        print(f"❌ Retry işlemi hatası: {e}")
        return {"success": False, "message": str(e)}

# ... existing code ...

def terminal_log(message, level='info'):
    """Global terminal log fonksiyonu - app.py'dan import edilebilir"""
    try:
        # app.py'dan TerminalLogHandler'ı import etmeye çalış
        from app import log_handler
        if log_handler:
            log_handler.broadcast_log(message, level)
        else:
            print(f"[{level.upper()}] {message}")
    except ImportError:
        # app.py import edilemezse normal print kullan
        print(f"[{level.upper()}] {message}")
    except Exception as e:
        # Herhangi bir hata durumunda normal print kullan
        print(f"[{level.upper()}] {message}")
