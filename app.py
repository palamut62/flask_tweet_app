from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps

# .env dosyasını yükle
load_dotenv()
from utils import (
    fetch_latest_ai_articles, generate_ai_tweet_with_mcp_analysis,
    post_tweet, mark_article_as_posted, load_json, save_json,
    get_posted_articles_summary, reset_all_data, clear_pending_tweets,
    get_data_statistics, load_automation_settings, save_automation_settings,
    get_automation_status, send_telegram_notification, test_telegram_connection,
    check_telegram_configuration, auto_detect_and_save_chat_id
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Global değişkenler
last_check_time = None
automation_running = False

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
        # Otomatik kontrol sistemi
        global last_check_time
        settings = load_automation_settings()
        
        if settings.get('auto_mode', False):
            current_time = datetime.now()
            check_interval_hours = settings.get('check_interval_hours', 2)
            
            # İlk çalışma veya belirlenen süre geçtiyse kontrol et
            if (last_check_time is None or 
                current_time - last_check_time >= timedelta(hours=check_interval_hours)):
                
                print(f"🔄 Otomatik kontrol başlatılıyor... (Son kontrol: {last_check_time})")
                check_and_post_articles()
                last_check_time = current_time
        
        # Sayfa verilerini hazırla
        articles = load_json("posted_articles.json")
        pending_tweets = load_json("pending_tweets.json")
        stats = get_data_statistics()
        automation_status = get_automation_status()
        
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
        print(f"Ana sayfa hatası: {e}")
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
    """MCP Firecrawl araçlarını kullanarak yeni makaleleri çek"""
    try:
        import hashlib
        import re
        
        # Önce mevcut yayınlanan makaleleri yükle
        posted_articles = load_json("posted_articles.json")
        posted_urls = [article.get('url', '') for article in posted_articles]
        posted_hashes = [article.get('hash', '') for article in posted_articles]
        
        print("🔍 TechCrunch AI kategorisinden MCP Firecrawl ile makale çekiliyor...")
        
        # Gerçek MCP Firecrawl ile TechCrunch AI sayfasını çek
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
            else:
                # Fallback: Web search sonuçlarından en yeni makaleleri kullan
                techcrunch_content = """
                [2025 will be a 'pivotal year' for Meta's augmented and virtual reality, says CTO](https://techcrunch.com/2025/06/06/2025-will-be-a-pivotal-year-for-metas-augmented-and-virtual-reality-says-cto/)
                [Why investing in growth-stage AI startups is getting riskier and more complicated](https://techcrunch.com/2025/06/06/why-investing-in-growth-stage-ai-startups-is-getting-riskier-and-more-complicated/)
                [Anthropic appoints a national security expert to its governing trust](https://techcrunch.com/2025/06/06/anthropic-appoints-a-national-security-expert-to-its-governing-trust/)
                [Figure AI CEO skips live demo, sidesteps BMW deal questions onstage at tech conference](https://techcrunch.com/2025/06/06/figure-ai-ceo-skips-live-demo-sidesteps-bmw-deal-questions-on-stage-at-tech-conference/)
                """
                print("⚠️ MCP Firecrawl başarısız, fallback kullanılıyor")
                
        except Exception as mcp_error:
            print(f"❌ MCP Firecrawl hatası: {mcp_error}")
            # Fallback: Web search sonuçlarından en yeni makaleleri kullan
            techcrunch_content = """
            [2025 will be a 'pivotal year' for Meta's augmented and virtual reality, says CTO](https://techcrunch.com/2025/06/06/2025-will-be-a-pivotal-year-for-metas-augmented-and-virtual-reality-says-cto/)
            [Why investing in growth-stage AI startups is getting riskier and more complicated](https://techcrunch.com/2025/06/06/why-investing-in-growth-stage-ai-startups-is-getting-riskier-and-more-complicated/)
            [Anthropic appoints a national security expert to its governing trust](https://techcrunch.com/2025/06/06/anthropic-appoints-a-national-security-expert-to-its-governing-trust/)
            [Figure AI CEO skips live demo, sidesteps BMW deal questions onstage at tech conference](https://techcrunch.com/2025/06/06/figure-ai-ceo-skips-live-demo-sidesteps-bmw-deal-questions-on-stage-at-tech-conference/)
            """
        
        # URL'leri çıkar
        url_pattern = r'https://techcrunch\.com/\d{4}/\d{2}/\d{2}/[^)\s]+'
        found_urls = re.findall(url_pattern, techcrunch_content)
        
        article_urls = []
        for url in found_urls:
            if (url not in posted_urls and 
                "/2025/" in url and 
                len(article_urls) < 4):  # Sadece son 4 makale
                article_urls.append(url)
        
        print(f"🔗 {len(article_urls)} yeni makale URL'si bulundu")
        
        if not article_urls:
            print("⚠️ Yeni makale URL'si bulunamadı, fallback kullanılıyor...")
            return fetch_latest_ai_articles()
        
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
                            "source": "mcp_enhanced"
                        })
                        print(f"🆕 MCP ile yeni makale: {title[:50]}...")
                    else:
                        print(f"✅ Makale zaten paylaşılmış: {title[:50]}...")
                else:
                    print(f"⚠️ İçerik çekilemedi: {url}")
                    
            except Exception as article_error:
                print(f"❌ Makale çekme hatası ({url}): {article_error}")
                continue
        
        print(f"📊 MCP Enhanced ile {len(articles_data)} yeni makale bulundu")
        return articles_data
        
    except Exception as e:
        print(f"MCP Enhanced haber çekme hatası: {e}")
        print("🔄 Fallback yönteme geçiliyor...")
        return fetch_latest_ai_articles()

def check_and_post_articles():
    """Makale kontrol ve paylaşım fonksiyonu - MCP Firecrawl entegrasyonlu"""
    try:
        print("🔍 Yeni makaleler kontrol ediliyor...")
        
        # Ayarları yükle
        settings = load_automation_settings()
        api_key = os.environ.get('GOOGLE_API_KEY')
        
        if not api_key:
            return {"success": False, "message": "Google API anahtarı bulunamadı"}
        
        # Yeni makaleleri MCP Firecrawl ile çek
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
                        print(f"❌ Tweet paylaşım hatası: {tweet_result.get('error', 'Bilinmeyen hata')}")
                else:
                    # Pending listesine ekle
                    pending_tweets = load_json("pending_tweets.json")
                    pending_tweets.append({
                        "article": article,
                        "tweet_data": tweet_data,
                        "created_at": datetime.now().isoformat(),
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

@app.route('/settings')
@login_required
def settings():
    """Ayarlar sayfası"""
    try:
        automation_settings = load_automation_settings()
        telegram_config = check_telegram_configuration()
        
        # API durumunu kontrol et
        api_status = {
            "google_api": os.environ.get('GOOGLE_API_KEY') is not None,
            "twitter_bearer": os.environ.get('TWITTER_BEARER_TOKEN') is not None,
            "twitter_api_key": os.environ.get('TWITTER_API_KEY') is not None,
            "twitter_api_secret": os.environ.get('TWITTER_API_SECRET') is not None,
            "twitter_access_token": os.environ.get('TWITTER_ACCESS_TOKEN') is not None,
            "twitter_access_secret": os.environ.get('TWITTER_ACCESS_TOKEN_SECRET') is not None,
            "telegram_bot_token": os.environ.get('TELEGRAM_BOT_TOKEN') is not None
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
        status = {
            "google_api": "MEVCUT" if os.environ.get('GOOGLE_API_KEY') else "EKSİK",
            "twitter_bearer": "MEVCUT" if os.environ.get('TWITTER_BEARER_TOKEN') else "EKSİK",
            "twitter_api_key": "MEVCUT" if os.environ.get('TWITTER_API_KEY') else "EKSİK",
            "twitter_api_secret": "MEVCUT" if os.environ.get('TWITTER_API_SECRET') else "EKSİK",
            "twitter_access_token": "MEVCUT" if os.environ.get('TWITTER_ACCESS_TOKEN') else "EKSİK",
            "twitter_access_secret": "MEVCUT" if os.environ.get('TWITTER_ACCESS_TOKEN_SECRET') else "EKSİK",
            "telegram_bot_token": "MEVCUT" if os.environ.get('TELEGRAM_BOT_TOKEN') else "EKSİK",
            "secret_key": "MEVCUT" if os.environ.get('SECRET_KEY') else "EKSİK"
        }
        
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
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/debug/env')
@login_required
def debug_env():
    """Environment variables debug sayfası (sadece geliştirme için)"""
    try:
        env_vars = {
            "GOOGLE_API_KEY": "MEVCUT" if os.environ.get('GOOGLE_API_KEY') else "EKSİK",
            "TWITTER_BEARER_TOKEN": "MEVCUT" if os.environ.get('TWITTER_BEARER_TOKEN') else "EKSİK",
            "TWITTER_API_KEY": "MEVCUT" if os.environ.get('TWITTER_API_KEY') else "EKSİK",
            "TWITTER_API_SECRET": "MEVCUT" if os.environ.get('TWITTER_API_SECRET') else "EKSİK",
            "TWITTER_ACCESS_TOKEN": "MEVCUT" if os.environ.get('TWITTER_ACCESS_TOKEN') else "EKSİK",
            "TWITTER_ACCESS_TOKEN_SECRET": "MEVCUT" if os.environ.get('TWITTER_ACCESS_TOKEN_SECRET') else "EKSİK",
            "TELEGRAM_BOT_TOKEN": "MEVCUT" if os.environ.get('TELEGRAM_BOT_TOKEN') else "EKSİK",
            "SECRET_KEY": "MEVCUT" if os.environ.get('SECRET_KEY') else "EKSİK"
        }
        
        return f"""
        <h2>Environment Variables Debug</h2>
        <ul>
        {"".join([f"<li><strong>{key}:</strong> {value}</li>" for key, value in env_vars.items()])}
        </ul>
        <p><a href="/">Ana Sayfaya Dön</a></p>
        """
        
    except Exception as e:
        return f"Hata: {str(e)}"

if __name__ == '__main__':
    # Python Anywhere için production ayarları
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)