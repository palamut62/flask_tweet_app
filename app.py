from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import os
import json
import time
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from werkzeug.utils import secure_filename
import tweepy

# .env dosyasını yükle
load_dotenv()

# Debug mode kontrolü
DEBUG_MODE = os.environ.get('DEBUG', 'False').lower() == 'true'

from utils import (
    fetch_latest_ai_articles, generate_ai_tweet_with_mcp_analysis,
    post_tweet, mark_article_as_posted, load_json, save_json,
    get_posted_articles_summary, reset_all_data, clear_pending_tweets,
    get_data_statistics, load_automation_settings, save_automation_settings,
    get_automation_status, send_telegram_notification, test_telegram_connection,
    check_telegram_configuration, auto_detect_and_save_chat_id,
    setup_twitter_api, send_gmail_notification, test_gmail_connection,
    check_gmail_configuration, get_twitter_rate_limit_status,
    retry_pending_tweets_after_rate_limit, check_and_retry_rate_limited_tweets,
    get_rate_limited_tweets_count
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Global değişkenler
last_check_time = None
automation_running = False
background_scheduler_running = False

# Giriş kontrolü decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş sayfası"""
    if request.method == 'POST':
        password = request.form.get('password')
        correct_password = os.environ.get('SIFRE', 'admin123')
        
        if password == correct_password:
            session['logged_in'] = True
            session['login_time'] = datetime.now().isoformat()
            flash('Başarıyla giriş yaptınız!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Hatalı şifre!', 'error')
            return render_template('login.html', error='Hatalı şifre girdiniz.')
    
    # Eğer zaten giriş yapmışsa ana sayfaya yönlendir
    if 'logged_in' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Çıkış yap"""
    session.clear()
    flash('Başarıyla çıkış yaptınız!', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Ana sayfa"""
    try:
        # Sayfa verilerini hazırla (otomatik kontrol yok)
        articles = load_json("posted_articles.json")
        pending_tweets = load_json("pending_tweets.json")
        stats = get_data_statistics()
        automation_status = get_automation_status()
        
        # Debug için istatistikleri logla (güvenli)
        from utils import safe_log
        safe_log(f"Ana sayfa istatistikleri: {stats}", "DEBUG")
        
        # API durumunu kontrol et (ana sayfa için basit kontrol)
        api_check = {
            "google_api_available": bool(os.environ.get('GOOGLE_API_KEY')),
            "twitter_api_available": bool(os.environ.get('TWITTER_BEARER_TOKEN') and os.environ.get('TWITTER_API_KEY')),
            "telegram_available": bool(os.environ.get('TELEGRAM_BOT_TOKEN'))
        }
        
        return render_template('index.html', 
                             articles=articles[-10:], 
                             pending_tweets=pending_tweets,
                             stats=stats,
                             automation_status=automation_status,
                             api_check=api_check,
                             last_check=last_check_time)
    except Exception as e:
        from utils import safe_log
        safe_log(f"Ana sayfa hatası: {str(e)}", "ERROR")
        return render_template('index.html', 
                             articles=[], 
                             pending_tweets=[],
                             stats={},
                             automation_status={},
                             api_check={},
                             error=str(e))

@app.route('/check_articles')
@login_required
def check_articles():
    """Manuel makale kontrolü"""
    try:
        result = check_and_post_articles()
        flash(f"Kontrol tamamlandı: {result['message']}", 'success')
    except Exception as e:
        flash(f"Hata: {str(e)}", 'error')
    
    return redirect(url_for('index'))

def fetch_latest_ai_articles_with_mcp():
    """Özel haber kaynaklarından ve MCP ile AI makalelerini çek"""
    try:
        import hashlib
        
        # Önce mevcut yayınlanan makaleleri yükle
        posted_articles = load_json("posted_articles.json")
        posted_urls = [article.get('url', '') for article in posted_articles]
        posted_hashes = [article.get('hash', '') for article in posted_articles]
        
        from utils import safe_log
        safe_log("Özel haber kaynaklarından makale çekiliyor...", "INFO")
        
        # Önce özel kaynaklardan makale çek
        try:
            from utils import fetch_articles_from_custom_sources
            custom_articles = fetch_articles_from_custom_sources()
            
            if custom_articles:
                print(f"✅ Özel kaynaklardan {len(custom_articles)} makale bulundu")
                
                # Makale hash'lerini oluştur ve tekrar kontrolü yap
                filtered_articles = []
                for article in custom_articles:
                    title = article.get('title', '')
                    url = article.get('url', '')
                    
                    if title and url:
                        article_hash = hashlib.md5(title.encode()).hexdigest()
                        
                        if url not in posted_urls and article_hash not in posted_hashes:
                            article['hash'] = article_hash
                            filtered_articles.append(article)
                            print(f"🆕 Yeni makale: {title[:50]}...")
                        else:
                            print(f"✅ Makale zaten paylaşılmış: {title[:50]}...")
                
                if filtered_articles:
                    return filtered_articles[:10]  # İlk 10 makaleyi döndür
            
        except Exception as custom_error:
            print(f"❌ Özel kaynaklardan makale çekme hatası: {custom_error}")
        
        # Eğer özel kaynaklardan yeterli makale bulunamadıysa MCP dene
        print("🔄 Özel kaynaklardan yeterli makale bulunamadı, MCP deneniyor...")
        
        try:
            # MCP Firecrawl kullanarak gerçek zamanlı veri çek
            from utils import mcp_firecrawl_scrape
            
            scrape_result = mcp_firecrawl_scrape({
                "url": "https://techcrunch.com/category/artificial-intelligence/",
                "formats": ["markdown"],
                "onlyMainContent": True,
                "waitFor": 2000,
                "removeBase64Images": True
            })
            
            if scrape_result and scrape_result.get("success"):
                techcrunch_content = scrape_result.get("content", "")
                print("✅ MCP Firecrawl ile gerçek zamanlı veri alındı")
                
                # Markdown'dan makale linklerini çıkar
                import re
                url_pattern = r'https://techcrunch\.com/\d{4}/\d{2}/\d{2}/[^)\s]+'
                found_urls = re.findall(url_pattern, techcrunch_content)
                
                article_urls = []
                for url in found_urls:
                    if (url not in posted_urls and 
                        "/2025/" in url and 
                        len(article_urls) < 4):  # Sadece son 4 makale
                        article_urls.append(url)
                
                print(f"🔗 {len(article_urls)} yeni makale URL'si bulundu")
                
                articles_data = []
                for url in article_urls:
                    try:
                        # URL'den başlığı çıkar (basit yöntem)
                        title_part = url.split('/')[-1].replace('-', ' ').title()
                        
                        # Fallback yöntemi ile içeriği çek
                        from utils import fetch_article_content_advanced_fallback
                        article_result = fetch_article_content_advanced_fallback(url)
                        
                        if article_result and article_result.get("content"):
                            title = article_result.get("title", title_part)
                            content = article_result.get("content", "")
                            
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
                                    "source": "TechCrunch AI (MCP)"
                                })
                                print(f"🆕 MCP ile yeni makale: {title[:50]}...")
                            else:
                                print(f"✅ Makale zaten paylaşılmış: {title[:50]}...")
                        else:
                            print(f"⚠️ İçerik çekilemedi: {url}")
                            
                    except Exception as article_error:
                        print(f"❌ Makale çekme hatası ({url}): {article_error}")
                        continue
                
                if articles_data:
                    print(f"📊 MCP ile {len(articles_data)} yeni makale bulundu")
                    return articles_data
                    
        except Exception as mcp_error:
            print(f"❌ MCP Firecrawl hatası: {mcp_error}")
        
        # Son fallback
        print("🔄 Fallback yönteme geçiliyor...")
        return fetch_latest_ai_articles()
        
    except Exception as e:
        print(f"❌ Makale çekme hatası: {e}")
        print("🔄 Fallback yönteme geçiliyor...")
        return fetch_latest_ai_articles()

def check_and_post_articles():
    """Makale kontrol ve paylaşım fonksiyonu - MCP Firecrawl entegrasyonlu"""
    try:
        from utils import safe_log
        safe_log("Yeni makaleler kontrol ediliyor...", "INFO")
        
        # Ayarları yükle
        settings = load_automation_settings()
        api_key = os.environ.get('GOOGLE_API_KEY')
        
        if not api_key:
            return {"success": False, "message": "Google API anahtarı bulunamadı"}
        
        # Yeni makaleleri çek (özel kaynaklardan)
        articles = fetch_latest_ai_articles_with_mcp()
        
        if not articles:
            return {"success": True, "message": "Yeni makale bulunamadı"}
        
        posted_count = 0
        max_articles = settings.get('max_articles_per_run', 3)
        min_score = settings.get('min_score_threshold', 5)
        auto_post = settings.get('auto_post_enabled', False)
        
        for article in articles[:max_articles]:
            try:
                # Tweet oluştur
                tweet_data = generate_ai_tweet_with_mcp_analysis(article, api_key)
                
                if not tweet_data or not tweet_data.get('tweet'):
                    continue
                
                # Skor kontrolü
                impact_score = tweet_data.get('impact_score', 0)
                if impact_score < min_score:
                    print(f"⚠️ Düşük skor ({impact_score}), atlanıyor: {article['title'][:50]}...")
                    continue
                
                # Otomatik paylaşım kontrolü
                if auto_post and not settings.get('manual_approval_required', True):
                    # Direkt paylaş
                    tweet_result = post_tweet(tweet_data['tweet'], article['title'])
                    
                    if tweet_result.get('success'):
                        mark_article_as_posted(article, tweet_result)
                        posted_count += 1
                        
                        # Telegram bildirimi
                        if settings.get('telegram_notifications', False):
                            send_telegram_notification(
                                f"✅ Yeni tweet paylaşıldı!\n\n{tweet_data['tweet'][:100]}...",
                                tweet_result.get('tweet_url', ''),
                                article['title']
                            )
                        
                        print(f"✅ Tweet paylaşıldı: {article['title'][:50]}...")
                    else:
                        # Twitter API hatası - pending listesine ekle
                        error_msg = tweet_result.get('error', 'Bilinmeyen hata')
                        is_rate_limited = tweet_result.get('rate_limited', False)
                        
                        if is_rate_limited:
                            print(f"⏳ Rate limit hatası: {error_msg}")
                            print(f"📝 Tweet rate limit sonrası tekrar denenecek: {article['title'][:50]}...")
                        else:
                            print(f"❌ Tweet paylaşım hatası: {error_msg}")
                            print(f"📝 Tweet pending listesine ekleniyor: {article['title'][:50]}...")
                        
                        pending_tweets = load_json("pending_tweets.json")
                        pending_tweets.append({
                            "article": article,
                            "tweet_data": tweet_data,
                            "created_date": datetime.now().isoformat(),
                            "created_at": datetime.now().isoformat(),
                            "status": "pending" if not is_rate_limited else "rate_limited",
                            "error_reason": error_msg,
                            "rate_limited": is_rate_limited,
                            "retry_count": 0
                        })
                        save_json("pending_tweets.json", pending_tweets)
                else:
                    # Manuel onay gerekli - pending listesine ekle
                    pending_tweets = load_json("pending_tweets.json")
                    pending_tweets.append({
                        "article": article,
                        "tweet_data": tweet_data,
                        "created_date": datetime.now().isoformat(),
                        "created_at": datetime.now().isoformat(),  # Geriye uyumluluk için
                        "status": "pending"
                    })
                    save_json("pending_tweets.json", pending_tweets)
                    print(f"📝 Tweet onay bekliyor: {article['title'][:50]}...")
                
                # Rate limiting
                time.sleep(settings.get('rate_limit_seconds', 2))
                
            except Exception as article_error:
                print(f"❌ Makale işleme hatası: {article_error}")
                continue
        
        message = f"{len(articles)} makale bulundu, {posted_count} tweet paylaşıldı"
        return {"success": True, "message": message}
        
    except Exception as e:
        print(f"❌ Makale kontrol hatası: {e}")
        return {"success": False, "message": str(e)}

@app.route('/post_tweet', methods=['POST'])
@login_required
def post_tweet_route():
    """Tweet paylaşım endpoint'i"""
    try:
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        
        if not tweet_id:
            return jsonify({"success": False, "error": "Tweet ID gerekli"})
        
        # Pending tweet'i bul
        pending_tweets = load_json("pending_tweets.json")
        tweet_to_post = None
        
        for i, pending in enumerate(pending_tweets):
            if str(i) == str(tweet_id):
                tweet_to_post = pending
                break
        
        if not tweet_to_post:
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
        
        # Tweet'i paylaş
        tweet_result = post_tweet(
            tweet_to_post['tweet_data']['tweet'], 
            tweet_to_post['article']['title']
        )
        
        if tweet_result.get('success'):
            # Başarılı paylaşım
            mark_article_as_posted(tweet_to_post['article'], tweet_result)
            
            # Pending listesinden kaldır
            pending_tweets = [p for i, p in enumerate(pending_tweets) if str(i) != str(tweet_id)]
            save_json("pending_tweets.json", pending_tweets)
            
            # Telegram bildirimi
            settings = load_automation_settings()
            if settings.get('telegram_notifications', False):
                send_telegram_notification(
                    f"✅ Tweet manuel olarak paylaşıldı!\n\n{tweet_to_post['tweet_data']['tweet'][:100]}...",
                    tweet_result.get('tweet_url', ''),
                    tweet_to_post['article']['title']
                )
            
            return jsonify({
                "success": True, 
                "message": "Tweet başarıyla paylaşıldı",
                "tweet_url": tweet_result.get('tweet_url', '')
            })
        else:
            return jsonify({
                "success": False, 
                "error": tweet_result.get('error', 'Bilinmeyen hata')
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/delete_tweet', methods=['POST'])
@login_required
def delete_tweet_route():
    """Tweet silme endpoint'i"""
    try:
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        
        if not tweet_id:
            return jsonify({"success": False, "error": "Tweet ID gerekli"})
        
        # Pending listesinden kaldır
        pending_tweets = load_json("pending_tweets.json")
        pending_tweets = [p for i, p in enumerate(pending_tweets) if str(i) != str(tweet_id)]
        save_json("pending_tweets.json", pending_tweets)
        
        return jsonify({"success": True, "message": "Tweet silindi"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/manual_post_tweet', methods=['POST'])
@login_required
def manual_post_tweet_route():
    """Manuel tweet paylaşım endpoint'i - API kullanmadan X'te paylaşım için"""
    try:
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        
        if not tweet_id:
            return jsonify({"success": False, "error": "Tweet ID gerekli"})
        
        # Pending tweet'i bul
        pending_tweets = load_json("pending_tweets.json")
        tweet_to_post = None
        tweet_index = None
        
        for i, pending in enumerate(pending_tweets):
            if str(i) == str(tweet_id):
                tweet_to_post = pending
                tweet_index = i
                break
        
        if not tweet_to_post:
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
        
        # Tweet metnini ve URL'yi hazırla
        tweet_text = tweet_to_post['tweet_data']['tweet']
        article_url = tweet_to_post['article'].get('url', '')
        
        # X.com paylaşım URL'si oluştur
        import urllib.parse
        encoded_text = urllib.parse.quote(tweet_text)
        x_share_url = f"https://x.com/intent/tweet?text={encoded_text}"
        
        return jsonify({
            "success": True,
            "tweet_text": tweet_text,
            "x_share_url": x_share_url,
            "article_url": article_url,
            "tweet_index": tweet_index,
            "article_title": tweet_to_post['article'].get('title', '')
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/confirm_manual_post', methods=['POST'])
@login_required
def confirm_manual_post():
    """Manuel paylaşım sonrası onaylama endpoint'i"""
    try:
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        
        # Debug logging
        from utils import safe_log
        safe_log(f"Manuel onay isteği - Tweet ID: {tweet_id}, Data: {data}", "DEBUG")
        
        if tweet_id is None or tweet_id == "":
            safe_log(f"Tweet ID eksik - Data: {data}", "ERROR")
            return jsonify({"success": False, "error": "Tweet ID gerekli"})
        
        # Tweet ID'yi integer'a çevir
        try:
            tweet_id = int(tweet_id)
        except (ValueError, TypeError):
            safe_log(f"Tweet ID integer'a çevrilemedi: {tweet_id}", "ERROR")
            return jsonify({"success": False, "error": "Geçersiz Tweet ID"})
        
        # Pending tweet'i bul
        pending_tweets = load_json("pending_tweets.json")
        tweet_to_post = None
        
        if tweet_id >= len(pending_tweets) or tweet_id < 0:
            safe_log(f"Tweet ID aralık dışı: {tweet_id}, Toplam: {len(pending_tweets)}", "ERROR")
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
        
        tweet_to_post = pending_tweets[tweet_id]
        
        if not tweet_to_post:
            safe_log(f"Tweet bulunamadı - ID: {tweet_id}", "ERROR")
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
        
        # Manuel paylaşım olarak işaretle ve kaydet
        from datetime import datetime
        import urllib.parse
        manual_tweet_result = {
            "success": True,
            "tweet_id": f"manual_{int(datetime.now().timestamp())}",
            "url": f"https://x.com/search?q={urllib.parse.quote(tweet_to_post['tweet_data']['tweet'][:50])}",
            "manual_post": True,
            "posted_at": datetime.now().isoformat()
        }
        
        # Tweet metnini article data'ya ekle (manuel paylaşım için)
        tweet_to_post['article']['tweet_text'] = tweet_to_post['tweet_data']['tweet']
        
        # Makaleyi paylaşıldı olarak işaretle
        mark_article_as_posted(tweet_to_post['article'], manual_tweet_result)
        
        # Pending listesinden kaldır
        pending_tweets.pop(tweet_id)  # Index'e göre direkt kaldır
        save_json("pending_tweets.json", pending_tweets)
        
        safe_log(f"Tweet başarıyla onaylandı ve kaldırıldı - ID: {tweet_id}", "INFO")
        
        # Telegram bildirimi
        settings = load_automation_settings()
        if settings.get('telegram_notifications', False):
            send_telegram_notification(
                f"✅ Tweet manuel olarak X'te paylaşıldı!\n\n{tweet_to_post['tweet_data']['tweet'][:100]}...",
                manual_tweet_result.get('url', ''),
                tweet_to_post['article']['title']
            )
        
        return jsonify({
            "success": True, 
            "message": "Tweet manuel paylaşım olarak kaydedildi",
            "tweet_url": manual_tweet_result.get('url', '')
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/settings')
@login_required
def settings():
    """Ayarlar sayfası"""
    try:
        automation_settings = load_automation_settings()
        telegram_config = check_telegram_configuration()
        gmail_config = check_gmail_configuration()
        
        # API durumunu kontrol et
        api_status = {
            "google_api": os.environ.get('GOOGLE_API_KEY') is not None,
            "twitter_bearer": os.environ.get('TWITTER_BEARER_TOKEN') is not None,
            "twitter_api_key": os.environ.get('TWITTER_API_KEY') is not None,
            "twitter_api_secret": os.environ.get('TWITTER_API_SECRET') is not None,
            "twitter_access_token": os.environ.get('TWITTER_ACCESS_TOKEN') is not None,
            "twitter_access_secret": os.environ.get('TWITTER_ACCESS_TOKEN_SECRET') is not None,
            "telegram_bot_token": os.environ.get('TELEGRAM_BOT_TOKEN') is not None,
            "gmail_email": os.environ.get('GMAIL_EMAIL') is not None,
            "gmail_password": os.environ.get('GMAIL_APP_PASSWORD') is not None
        }
        
        # Gemini API test
        try:
            from utils import gemini_call
            api_key = os.environ.get('GOOGLE_API_KEY')
            if api_key:
                test_result = gemini_call("Test message", api_key)
                api_status["google_api_working"] = bool(test_result)
            else:
                api_status["google_api_working"] = False
        except Exception as e:
            api_status["google_api_working"] = False
            api_status["google_api_error"] = str(e)
        
        return render_template('settings.html', 
                             settings=automation_settings,
                             telegram_config=telegram_config,
                             gmail_config=gmail_config,
                             api_status=api_status)
    except Exception as e:
        return render_template('settings.html', 
                             settings={},
                             telegram_config={},
                             api_status={},
                             error=str(e))

@app.route('/save_settings', methods=['POST'])
@login_required
def save_settings():
    """Ayarları kaydet"""
    try:
        settings = {
            'auto_mode': request.form.get('auto_mode') == 'on',
            'check_interval_hours': int(request.form.get('check_interval_hours', 2)),
            'max_articles_per_run': int(request.form.get('max_articles_per_run', 3)),
            'min_score_threshold': int(request.form.get('min_score_threshold', 5)),
            'auto_post_enabled': request.form.get('auto_post_enabled') == 'on',
            'manual_approval_required': request.form.get('manual_approval_required') == 'on',
            'rate_limit_seconds': float(request.form.get('rate_limit_seconds', 2.0)),
            'telegram_notifications': request.form.get('telegram_notifications') == 'on',
            'email_notifications': request.form.get('email_notifications') == 'on',
            'last_updated': datetime.now().isoformat()
        }
        
        save_automation_settings(settings)
        flash('Ayarlar başarıyla kaydedildi!', 'success')
        
    except Exception as e:
        flash(f'Ayar kaydetme hatası: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/test_telegram')
@login_required
def test_telegram():
    """Telegram bağlantı testi"""
    try:
        result = test_telegram_connection()
        if result.get('success'):
            flash('Telegram bağlantısı başarılı!', 'success')
        else:
            flash(f'Telegram hatası: {result.get("error", "Bilinmeyen hata")}', 'error')
    except Exception as e:
        flash(f'Telegram test hatası: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/auto_detect_chat_id')
@login_required
def auto_detect_chat_id():
    """Telegram Chat ID otomatik algılama"""
    try:
        result = auto_detect_and_save_chat_id()
        if result.get('success'):
            flash(f'Chat ID başarıyla algılandı: {result.get("chat_id")}', 'success')
        else:
            flash(f'Chat ID algılama hatası: {result.get("error", "Bilinmeyen hata")}', 'error')
    except Exception as e:
        flash(f'Chat ID algılama hatası: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/test_gmail')
@login_required
def test_gmail():
    """Gmail SMTP bağlantı testi"""
    try:
        result = test_gmail_connection()
        if result.get('success'):
            flash(f'Gmail bağlantısı başarılı! {result.get("message", "")}', 'success')
        else:
            flash(f'Gmail hatası: {result.get("error", "Bilinmeyen hata")}', 'error')
    except Exception as e:
        flash(f'Gmail test hatası: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/statistics')
@login_required
def statistics():
    """İstatistikler sayfası"""
    try:
        stats = get_data_statistics()
        summary = get_posted_articles_summary()
        
        return render_template('statistics.html', 
                             stats=stats,
                             summary=summary)
    except Exception as e:
        return render_template('statistics.html', 
                             stats={},
                             summary={},
                             error=str(e))

@app.route('/reset_data', methods=['POST'])
@login_required
def reset_data():
    """Tüm verileri sıfırla"""
    try:
        reset_all_data()
        flash('Tüm veriler başarıyla sıfırlandı!', 'success')
    except Exception as e:
        flash(f'Veri sıfırlama hatası: {str(e)}', 'error')
    
    return redirect(url_for('statistics'))

@app.route('/clear_pending')
@login_required
def clear_pending():
    """Bekleyen tweet'leri temizle"""
    try:
        clear_pending_tweets()
        flash('Bekleyen tweet\'ler temizlendi!', 'success')
    except Exception as e:
        flash(f'Temizleme hatası: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/status')
@login_required
def api_status():
    """API durumunu kontrol et"""
    try:
        status = get_safe_env_status()
        
        # Gemini API test
        try:
            from utils import gemini_call
            api_key = os.environ.get('GOOGLE_API_KEY')
            if api_key:
                test_result = gemini_call("Test message", api_key)
                status["google_api_test"] = "ÇALIŞIYOR" if test_result else "HATA"
            else:
                status["google_api_test"] = "API ANAHTARI EKSİK"
        except Exception as e:
            status["google_api_test"] = f"HATA: {str(e)}"
        
        # Twitter rate limit durumu ekle
        try:
            twitter_rate_limit = get_twitter_rate_limit_status()
            status["twitter_rate_limit"] = twitter_rate_limit.get("status", "Bilinmeyen")
        except Exception as e:
            status["twitter_rate_limit"] = f"HATA: {str(e)}"
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/test_twitter_rate_limit')
@login_required
def test_twitter_rate_limit():
    """Twitter rate limit durumunu test et"""
    try:
        rate_limit_status = get_twitter_rate_limit_status()
        
        if rate_limit_status.get("success"):
            flash("✅ Twitter API erişilebilir - Rate limit sorunu yok", "success")
        else:
            status = rate_limit_status.get("status", "Bilinmeyen hata")
            flash(f"⚠️ Twitter API durumu: {status}", "warning")
        
        return redirect(url_for('settings'))
        
    except Exception as e:
        flash(f"❌ Twitter rate limit testi hatası: {str(e)}", "error")
        return redirect(url_for('settings'))

@app.route('/retry_rate_limited_tweets')
@login_required
def retry_rate_limited_tweets():
    """Rate limit nedeniyle bekleyen tweet'leri tekrar dene"""
    try:
        result = retry_pending_tweets_after_rate_limit()
        
        if result.get('success'):
            flash(f"Rate limit retry tamamlandı: {result['message']}", 'success')
        else:
            flash(f"Rate limit retry hatası: {result['message']}", 'error')
            
    except Exception as e:
        flash(f"Rate limit retry hatası: {str(e)}", 'error')
    
    return redirect(url_for('index'))

@app.route('/api/rate_limit_status')
@login_required
def api_rate_limit_status():
    """Rate limit durumu ve bekleyen tweet sayısı API"""
    try:
        rate_limit_status = get_twitter_rate_limit_status()
        rate_limited_count = get_rate_limited_tweets_count()
        
        return jsonify({
            "success": True,
            "rate_limit_status": rate_limit_status,
            "rate_limited_tweets_count": rate_limited_count,
            "can_retry": rate_limit_status.get('can_post', False) and rate_limited_count > 0
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/debug/env')
@login_required
def debug_env():
    """Environment variables debug sayfası (sadece geliştirme için)"""
    try:
        env_vars = get_safe_env_status()
        
        return f"""
        <h2>Environment Variables Debug</h2>
        <ul>
        {"".join([f"<li><strong>{key}:</strong> {value}</li>" for key, value in env_vars.items()])}
        </ul>
        <p><a href="/">Ana Sayfaya Dön</a></p>
        """
        
    except Exception as e:
        return f"Hata: {str(e)}"

@app.route('/debug/stats')
@login_required
def debug_stats():
    """Debug: İstatistikleri kontrol et"""
    try:
        stats = get_data_statistics()
        
        # Bugünkü makaleleri detaylı göster
        from datetime import datetime, date
        today = date.today()
        posted_articles = load_json("posted_articles.json")
        
        today_articles_detail = []
        for article in posted_articles:
            if article.get("posted_date"):
                try:
                    posted_date = datetime.fromisoformat(article["posted_date"].replace('Z', '+00:00'))
                    if posted_date.date() == today:
                        today_articles_detail.append({
                            "title": article.get("title", "")[:50],
                            "posted_date": article.get("posted_date"),
                            "parsed_date": posted_date.strftime("%Y-%m-%d %H:%M")
                        })
                except Exception as e:
                    today_articles_detail.append({
                        "title": article.get("title", "")[:50],
                        "posted_date": article.get("posted_date"),
                        "error": str(e)
                    })
        
        return jsonify({
            "success": True,
            "stats": stats,
            "today_date": today.isoformat(),
            "today_articles_detail": today_articles_detail,
            "total_articles_in_file": len(posted_articles)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/create_tweet', methods=['GET', 'POST'])
@login_required
def create_tweet():
    if request.method == 'POST':
        tweet_mode = request.form.get('tweet_mode', 'text')
        tweet_text = request.form.get('tweet_text')
        image_file = request.files.get('tweet_image')
        tweet_url = request.form.get('tweet_url')
        image_path = None
        api_key = os.environ.get('GOOGLE_API_KEY')

        if tweet_mode == 'image':
            # Sadece resimden tweet
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                image_path = os.path.join('static', 'uploads', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image_file.save(image_path)
                try:
                    from utils import gemini_ocr_image, generate_ai_tweet_with_content
                    ocr_text = gemini_ocr_image(image_path)
                    # AI ile konuya uygun tweet üret
                    article_data = {
                        'title': ocr_text[:100],
                        'content': ocr_text,
                        'url': '',
                        'lang': 'en'
                    }
                    tweet_data = generate_ai_tweet_with_content(article_data, api_key)
                    tweet_text = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
                except Exception as e:
                    flash(f'Resimden tweet oluşturulamadı: {e}', 'error')
                    return redirect(url_for('create_tweet'))
            else:
                flash('Resim yüklenmedi!', 'error')
                return redirect(url_for('create_tweet'))
        elif tweet_mode == 'link':
            # Link'ten tweet
            if not tweet_url or not tweet_url.strip():
                flash('URL boş olamaz!', 'error')
                return redirect(url_for('create_tweet'))
            
            try:
                from utils import fetch_url_content_with_mcp, generate_ai_tweet_with_content
                
                # URL'den içerik çek
                url_content = fetch_url_content_with_mcp(tweet_url.strip())
                
                if not url_content or not url_content.get('content'):
                    flash('URL\'den içerik çekilemedi!', 'error')
                    return redirect(url_for('create_tweet'))
                
                # AI ile tweet oluştur
                article_data = {
                    'title': url_content.get('title', ''),
                    'content': url_content.get('content', ''),
                    'url': url_content.get('url', ''),
                    'lang': 'en'
                }
                tweet_data = generate_ai_tweet_with_content(article_data, api_key)
                tweet_text = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
                
            except Exception as e:
                flash(f'Link\'ten tweet oluşturulamadı: {e}', 'error')
                return redirect(url_for('create_tweet'))
        else:
            # Sadece metinden tweet
            if not tweet_text or not tweet_text.strip():
                flash('Tweet metni boş olamaz!', 'error')
                return redirect(url_for('create_tweet'))
            
            try:
                from utils import generate_ai_tweet_with_content
                article_data = {
                    'title': tweet_text[:100],
                    'content': tweet_text,
                    'url': '',
                    'lang': 'en'
                }
                tweet_data = generate_ai_tweet_with_content(article_data, api_key)
                tweet_text = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
            except Exception as e:
                flash(f'AI ile tweet metni oluşturulamadı: {e}', 'error')
                return redirect(url_for('create_tweet'))

        # Tweet oluşturuldu - sadece önizleme göster, paylaşma
        flash('✅ Tweet başarıyla oluşturuldu! Aşağıdaki metni kopyalayıp Twitter\'da manuel olarak paylaşabilirsiniz.', 'success')
        return render_template('create_tweet.html', generated_tweet=tweet_text)

    return render_template('create_tweet.html')

@app.route('/ocr_image', methods=['POST'])
@login_required
def ocr_image():
    image_file = request.files.get('image')
    if not image_file or not image_file.filename:
        return jsonify({'success': False, 'error': 'Resim bulunamadı.'}), 400

    filename = secure_filename(image_file.filename)
    image_path = os.path.join('static', 'uploads', filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    image_file.save(image_path)

    try:
        from utils import gemini_ocr_image, generate_ai_tweet_with_content
        ocr_text = gemini_ocr_image(image_path)
        # AI ile konuya uygun tweet üret
        api_key = os.environ.get('GOOGLE_API_KEY')
        article_data = {
            'title': ocr_text[:100],
            'content': ocr_text,
            'url': '',
            'lang': 'en'
        }
        tweet_data = generate_ai_tweet_with_content(article_data, api_key)
        tweet_text = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
        return jsonify({'success': True, 'text': tweet_text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def background_scheduler():
    """Arka plan zamanlayıcısı - Her 3 saatte bir çalışır"""
    global background_scheduler_running, last_check_time
    
    print("🚀 Arka plan zamanlayıcısı başlatıldı (Her 3 saatte bir çalışacak)")
    background_scheduler_running = True
    
    while background_scheduler_running:
        try:
            # Ayarları kontrol et
            settings = load_automation_settings()
            
            if settings.get('auto_post_enabled', False):
                current_time = datetime.now()
                check_interval_hours = settings.get('check_interval_hours', 3)
                
                # İlk çalışma veya belirlenen süre geçtiyse kontrol et
                if (last_check_time is None or 
                    current_time - last_check_time >= timedelta(hours=check_interval_hours)):
                    
                    print(f"🔄 Otomatik haber kontrolü başlatılıyor... (Son kontrol: {last_check_time})")
                    
                    try:
                        result = check_and_post_articles()
                        print(f"✅ Otomatik kontrol tamamlandı: {result.get('message', 'Sonuç yok')}")
                        
                        # Rate limit tweet'lerini de kontrol et
                        try:
                            rate_limit_result = check_and_retry_rate_limited_tweets()
                            if rate_limit_result.get('success'):
                                print(f"✅ Rate limit kontrol: {rate_limit_result.get('message', 'Sonuç yok')}")
                            else:
                                print(f"⏳ Rate limit kontrol: {rate_limit_result.get('message', 'Sonuç yok')}")
                        except Exception as rate_limit_error:
                            print(f"❌ Rate limit kontrol hatası: {rate_limit_error}")
                        
                        last_check_time = current_time
                    except Exception as check_error:
                        print(f"❌ Otomatik kontrol hatası: {check_error}")
                        
                else:
                    next_check = last_check_time + timedelta(hours=check_interval_hours)
                    remaining = next_check - current_time
                    print(f"⏰ Sonraki kontrol: {remaining.total_seconds()/3600:.1f} saat sonra")
            else:
                print("⏸️ Otomatik paylaşım devre dışı")
            
            # 30 dakika bekle (kontrol sıklığı)
            time.sleep(1800)  # 30 dakika = 1800 saniye
            
        except Exception as e:
            print(f"❌ Arka plan zamanlayıcı hatası: {e}")
            time.sleep(1800)  # Hata durumunda da 30 dakika bekle

def start_background_scheduler():
    """Arka plan zamanlayıcısını thread olarak başlat"""
    global background_scheduler_running
    
    if not background_scheduler_running:
        scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
        scheduler_thread.start()
        print("🔄 Arka plan zamanlayıcı thread'i başlatıldı")

# ==========================================
# ÖZEL HABER KAYNAKLARI ROUTE'LARI
# ==========================================

@app.route('/news_sources')
@login_required
def news_sources():
    """Haber kaynakları yönetim sayfası"""
    try:
        from utils import get_news_sources_stats
        stats = get_news_sources_stats()
        return render_template('news_sources.html', stats=stats)
    except Exception as e:
        return render_template('news_sources.html', stats={}, error=str(e))

@app.route('/add_news_source', methods=['POST'])
@login_required
def add_news_source_route():
    """Yeni haber kaynağı ekle"""
    try:
        from utils import add_news_source
        
        name = request.form.get('name', '').strip()
        url = request.form.get('url', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name or not url:
            flash('Kaynak adı ve URL gerekli!', 'error')
            return redirect(url_for('news_sources'))
        
        result = add_news_source(name, url, description)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'error')
            
    except Exception as e:
        flash(f'Kaynak ekleme hatası: {str(e)}', 'error')
    
    return redirect(url_for('news_sources'))

@app.route('/remove_news_source', methods=['POST'])
@login_required
def remove_news_source_route():
    """Haber kaynağını kaldır"""
    try:
        from utils import remove_news_source
        
        source_id = request.form.get('source_id')
        if not source_id:
            flash('Kaynak ID gerekli!', 'error')
            return redirect(url_for('news_sources'))
        
        result = remove_news_source(source_id)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'error')
            
    except Exception as e:
        flash(f'Kaynak kaldırma hatası: {str(e)}', 'error')
    
    return redirect(url_for('news_sources'))

@app.route('/toggle_news_source', methods=['POST'])
@login_required
def toggle_news_source_route():
    """Haber kaynağını aktif/pasif yap"""
    try:
        from utils import toggle_news_source
        
        source_id = request.form.get('source_id')
        enabled = request.form.get('enabled') == 'true'
        
        if not source_id:
            flash('Kaynak ID gerekli!', 'error')
            return redirect(url_for('news_sources'))
        
        result = toggle_news_source(source_id, enabled)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'error')
            
    except Exception as e:
        flash(f'Durum değiştirme hatası: {str(e)}', 'error')
    
    return redirect(url_for('news_sources'))

@app.route('/test_news_source', methods=['POST'])
@login_required
def test_news_source_route():
    """Haber kaynağını test et"""
    try:
        from utils import fetch_articles_from_single_source, load_news_sources
        
        source_id = request.form.get('source_id')
        if not source_id:
            return jsonify({'success': False, 'error': 'Kaynak ID gerekli'})
        
        config = load_news_sources()
        source = None
        
        for s in config['sources']:
            if s['id'] == source_id:
                source = s
                break
        
        if not source:
            return jsonify({'success': False, 'error': 'Kaynak bulunamadı'})
        
        articles = fetch_articles_from_single_source(source)
        
        return jsonify({
            'success': True,
            'article_count': len(articles),
            'articles': articles[:3],  # İlk 3 makaleyi göster
            'message': f'{len(articles)} makale bulundu'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# =============================================================================
# GÜVENLİK FONKSİYONLARI
# =============================================================================

def mask_sensitive_data(data):
    """Hassas verileri maskele"""
    if not data or len(str(data)) <= 3:
        return "***"
    return str(data)[:3] + "*" * (len(str(data)) - 3)

def get_safe_env_status():
    """Environment variable'ların durumunu güvenli şekilde döndür"""
    return {
        "google_api": "MEVCUT" if os.environ.get('GOOGLE_API_KEY') else "EKSİK",
        "twitter_bearer": "MEVCUT" if os.environ.get('TWITTER_BEARER_TOKEN') else "EKSİK",
        "twitter_api_key": "MEVCUT" if os.environ.get('TWITTER_API_KEY') else "EKSİK",
        "twitter_api_secret": "MEVCUT" if os.environ.get('TWITTER_API_SECRET') else "EKSİK",
        "twitter_access_token": "MEVCUT" if os.environ.get('TWITTER_ACCESS_TOKEN') else "EKSİK",
        "twitter_access_secret": "MEVCUT" if os.environ.get('TWITTER_ACCESS_TOKEN_SECRET') else "EKSİK",
        "telegram_bot_token": "MEVCUT" if os.environ.get('TELEGRAM_BOT_TOKEN') else "EKSİK",
        "gmail_email": "MEVCUT" if os.environ.get('GMAIL_EMAIL') else "EKSİK",
        "gmail_password": "MEVCUT" if os.environ.get('GMAIL_APP_PASSWORD') else "EKSİK",
        "secret_key": "MEVCUT" if os.environ.get('SECRET_KEY') else "EKSİK"
    }

@app.route('/security_check')
@login_required
def security_check():
    """Güvenlik yapılandırmasını kontrol et"""
    try:
        from utils import check_security_configuration
        security_status = check_security_configuration()
        return render_template('security_check.html', security=security_status)
    except Exception as e:
        from utils import safe_log
        safe_log(f"Güvenlik kontrol hatası: {str(e)}", "ERROR")
        return render_template('security_check.html', security={"secure": False, "issues": [f"Kontrol hatası: {str(e)}"]})

@app.route('/test_twitter_rate_limit_detailed')
@login_required
def test_twitter_rate_limit_detailed():
    """Twitter API rate limit durumunu detaylı test et"""
    try:
        from utils import get_twitter_rate_limit_status
        
        # Rate limit durumunu kontrol et
        rate_limit_status = get_twitter_rate_limit_status()
        
        return jsonify({
            "success": True,
            "rate_limit_status": rate_limit_status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/manual_post_confirmation/<int:tweet_id>')
@login_required
def manual_post_confirmation(tweet_id):
    """Manuel paylaşım onaylama sayfası"""
    try:
        # Pending tweet'i bul
        pending_tweets = load_json("pending_tweets.json")
        
        if tweet_id >= len(pending_tweets):
            return redirect(url_for('index'))
        
        tweet_to_confirm = pending_tweets[tweet_id]
        
        return render_template('manual_confirmation.html', 
                             tweet=tweet_to_confirm, 
                             tweet_id=tweet_id)
        
    except Exception as e:
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Arka plan zamanlayıcısını başlat
    start_background_scheduler()
    
    # Python Anywhere için production ayarları
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    from utils import safe_log
    safe_log(f"Flask uygulaması başlatılıyor - Port: {port}", "INFO")
    app.run(host='0.0.0.0', port=port, debug=debug)