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
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    check_gmail_configuration, get_rate_limit_info, terminal_log
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

def send_otp_email(email, otp_code):
    """E-posta ile OTP kodu gönder"""
    try:
        # E-posta ayarlarını kontrol et
        if not EMAIL_SETTINGS['email'] or not EMAIL_SETTINGS['password']:
            return False, "E-posta ayarları yapılandırılmamış"
        
        # E-posta içeriği
        subject = "AI Tweet Bot - Giriş Doğrulama Kodu"
        body = f"""
        Merhaba,
        
        AI Tweet Bot uygulamasına giriş yapmak için doğrulama kodunuz:
        
        {otp_code}
        
        Bu kod 5 dakika geçerlidir.
        
        Eğer bu giriş denemesi size ait değilse, bu e-postayı görmezden gelebilirsiniz.
        
        İyi günler,
        AI Tweet Bot
        """
        
        # E-posta oluştur
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SETTINGS['email']
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # SMTP ile gönder
        server = smtplib.SMTP(EMAIL_SETTINGS['smtp_server'], EMAIL_SETTINGS['smtp_port'])
        server.starttls()
        server.login(EMAIL_SETTINGS['email'], EMAIL_SETTINGS['password'])
        server.send_message(msg)
        server.quit()
        
        return True, "E-posta başarıyla gönderildi"
        
    except Exception as e:
        return False, f"E-posta gönderme hatası: {str(e)}"

@app.route('/send_otp', methods=['POST'])
def send_otp():
    """OTP kodu gönder"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"success": False, "error": "E-posta adresi gerekli"})
        
        # Admin e-posta kontrolü
        admin_email = EMAIL_SETTINGS['admin_email'].lower()
        if not admin_email:
            return jsonify({"success": False, "error": "Admin e-posta adresi yapılandırılmamış"})
        
        if email != admin_email:
            return jsonify({"success": False, "error": "Yetkisiz e-posta adresi"})
        
        # 6 haneli rastgele kod oluştur
        otp_code = str(random.randint(100000, 999999))
        
        # E-posta gönder
        success, message = send_otp_email(email, otp_code)
        
        if success:
            # OTP kodunu kaydet (5 dakika geçerli)
            email_otp_codes[email] = {
                'code': otp_code,
                'timestamp': datetime.now(),
                'attempts': 0
            }
            
            return jsonify({"success": True, "message": "Doğrulama kodu gönderildi"})
        else:
            return jsonify({"success": False, "error": message})
            
    except Exception as e:
        return jsonify({"success": False, "error": f"Sistem hatası: {str(e)}"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    """E-posta OTP ile güvenli giriş"""
    if request.method == 'POST':
        auth_method = request.form.get('auth_method', 'email_otp')
        
        if auth_method == 'email_otp':
            email = request.form.get('email', '').strip().lower()
            otp_code = request.form.get('otp_code', '').strip()
            
            if not email or not otp_code:
                flash('E-posta ve doğrulama kodu gerekli!', 'error')
                return render_template('login.html', error='Eksik bilgi')
            
            # Admin e-posta kontrolü
            admin_email = EMAIL_SETTINGS['admin_email'].lower()
            if email != admin_email:
                flash('Yetkisiz e-posta adresi!', 'error')
                return render_template('login.html', error='Yetkisiz erişim')
            
            # OTP kontrolü
            if email in email_otp_codes:
                otp_data = email_otp_codes[email]
                
                # Süre kontrolü (5 dakika)
                if (datetime.now() - otp_data['timestamp']).seconds > 300:
                    del email_otp_codes[email]
                    flash('Doğrulama kodunun süresi doldu!', 'error')
                    return render_template('login.html', error='Kod süresi doldu')
                
                # Deneme sayısı kontrolü
                if otp_data['attempts'] >= 3:
                    del email_otp_codes[email]
                    flash('Çok fazla hatalı deneme!', 'error')
                    return render_template('login.html', error='Çok fazla deneme')
                
                # Kod kontrolü
                if otp_code == otp_data['code']:
                    # Başarılı giriş
                    del email_otp_codes[email]
                    session['logged_in'] = True
                    session['login_time'] = datetime.now().isoformat()
                    session['auth_method'] = 'email_otp'
                    session['user_email'] = email
                    flash('E-posta doğrulama ile başarıyla giriş yaptınız!', 'success')
                    return redirect(url_for('index'))
                else:
                    # Hatalı kod
                    otp_data['attempts'] += 1
                    flash(f'Hatalı doğrulama kodu! ({3 - otp_data["attempts"]} deneme hakkınız kaldı)', 'error')
                    return render_template('login.html', error='Hatalı kod')
            else:
                flash('Geçersiz veya süresi dolmuş doğrulama kodu!', 'error')
                return render_template('login.html', error='Geçersiz kod')
    
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

# E-posta OTP sistemi için global değişken
email_otp_codes = {}

# E-posta ayarları
EMAIL_SETTINGS = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': os.environ.get('EMAIL_ADDRESS', ''),
    'password': os.environ.get('EMAIL_PASSWORD', ''),
    'admin_email': os.environ.get('ADMIN_EMAIL', '')
}

# Terminal log sistemi için global değişkenler
import queue
log_queue = queue.Queue(maxsize=100)



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
        
        # Ayarları yükle
        settings = load_automation_settings()
        
        return render_template('index.html', 
                             articles=articles[-10:], 
                             pending_tweets=pending_tweets,
                             stats=stats,
                             automation_status=automation_status,
                             api_check=api_check,
                             settings=settings,
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
                             settings={},
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
            terminal_log("🔍 Özel haber kaynaklarından makale çekiliyor...", "info")
            custom_articles = fetch_articles_from_custom_sources()
            
            if custom_articles:
                terminal_log(f"✅ Özel kaynaklardan {len(custom_articles)} makale bulundu", "success")
                
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
                            terminal_log(f"🆕 Yeni makale: {title[:50]}...", "success")
                        else:
                            terminal_log(f"✅ Makale zaten paylaşılmış: {title[:50]}...", "info")
                
                if filtered_articles:
                    terminal_log(f"📊 {len(filtered_articles)} yeni makale filtrelendi", "info")
                    
                    # Duplikat filtreleme uygula
                    from utils import filter_duplicate_articles
                    final_articles = filter_duplicate_articles(filtered_articles)
                    
                    if final_articles:
                        terminal_log(f"✅ Duplikat filtreleme sonrası {len(final_articles)} benzersiz makale", "success")
                        return final_articles[:10]  # İlk 10 makaleyi döndür
                    else:
                        terminal_log("⚠️ Duplikat filtreleme sonrası hiç makale kalmadı", "warning")
                else:
                    terminal_log("⚠️ Özel kaynaklardan yeni makale bulunamadı", "warning")
            else:
                terminal_log("⚠️ Özel kaynaklardan hiç makale çekilemedi", "warning")
            
        except Exception as custom_error:
            terminal_log(f"❌ Özel kaynaklardan makale çekme hatası: {custom_error}", "error")
            import traceback
            traceback.print_exc()
        
        # Eğer özel kaynaklardan yeterli makale bulunamadıysa MCP dene
        terminal_log("🔄 Özel kaynaklardan yeterli makale bulunamadı, MCP deneniyor...", "info")
        
        try:
            # MCP Firecrawl kullanarak gerçek zamanlı veri çek (PythonAnywhere fallback sistemi)
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
                terminal_log("✅ MCP Firecrawl ile gerçek zamanlı veri alındı", "success")
                
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
                
                terminal_log(f"🔗 {len(article_urls)} yeni makale URL'si bulundu", "info")
                
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
                                terminal_log(f"🆕 MCP ile yeni makale: {title[:50]}...", "success")
                            else:
                                terminal_log(f"✅ Makale zaten paylaşılmış: {title[:50]}...", "info")
                        else:
                            terminal_log(f"⚠️ İçerik çekilemedi: {url}", "warning")
                            
                    except Exception as article_error:
                        terminal_log(f"❌ Makale çekme hatası ({url}): {article_error}", "error")
                        continue
                
                if articles_data:
                    terminal_log(f"📊 MCP ile {len(articles_data)} yeni makale bulundu", "success")
                    return articles_data
                    
        except Exception as mcp_error:
            terminal_log(f"❌ MCP Firecrawl hatası: {mcp_error}", "error")
        
        # Son fallback
        terminal_log("🔄 Fallback yönteme geçiliyor...", "info")
        return fetch_latest_ai_articles()
        
    except Exception as e:
        terminal_log(f"❌ Makale çekme hatası: {e}", "error")
        terminal_log("🔄 Fallback yönteme geçiliyor...", "info")
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
                    terminal_log(f"⚠️ Düşük skor ({impact_score}), atlanıyor: {article['title'][:50]}...", "warning")
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
                        
                        terminal_log(f"✅ Tweet paylaşıldı: {article['title'][:50]}...", "success")
                    else:
                        # Twitter API hatası - pending listesine ekle
                        error_msg = tweet_result.get('error', 'Bilinmeyen hata')
                        
                        terminal_log(f"❌ Tweet paylaşım hatası: {error_msg}", "error")
                        terminal_log(f"📝 Tweet pending listesine ekleniyor: {article['title'][:50]}...", "info")
                        
                        pending_tweets = load_json("pending_tweets.json")
                        
                        # Duplikat kontrolü yap
                        new_tweet = {
                            "article": article,
                            "tweet_data": tweet_data,
                            "created_date": datetime.now().isoformat(),
                            "created_at": datetime.now().isoformat(),
                            "status": "pending",
                            "error_reason": error_msg,
                            "retry_count": 0
                        }
                        
                        # URL ve hash kontrolü
                        article_url = article.get('url', '')
                        article_hash = article.get('hash', '')
                        
                        is_duplicate = False
                        for existing_tweet in pending_tweets:
                            existing_article = existing_tweet.get('article', {})
                            if (article_url and article_url == existing_article.get('url', '')) or \
                               (article_hash and article_hash == existing_article.get('hash', '')):
                                is_duplicate = True
                                terminal_log(f"⚠️ Duplikat tweet atlandı: {article['title'][:50]}...", "warning")
                                break
                        
                        if not is_duplicate:
                            pending_tweets.append(new_tweet)
                            save_json("pending_tweets.json", pending_tweets)
                            terminal_log(f"✅ Tweet pending listesine eklendi: {article['title'][:50]}...", "success")
                        else:
                            terminal_log(f"🔄 Duplikat tweet pending listesine eklenmedi", "info")
                else:
                    # Manuel onay gerekli - pending listesine ekle
                    pending_tweets = load_json("pending_tweets.json")
                    
                    # Duplikat kontrolü yap
                    new_tweet = {
                        "article": article,
                        "tweet_data": tweet_data,
                        "created_date": datetime.now().isoformat(),
                        "created_at": datetime.now().isoformat(),  # Geriye uyumluluk için
                        "status": "pending"
                    }
                    
                    # URL ve hash kontrolü
                    article_url = article.get('url', '')
                    article_hash = article.get('hash', '')
                    
                    is_duplicate = False
                    for existing_tweet in pending_tweets:
                        existing_article = existing_tweet.get('article', {})
                        if (article_url and article_url == existing_article.get('url', '')) or \
                           (article_hash and article_hash == existing_article.get('hash', '')):
                            is_duplicate = True
                            terminal_log(f"⚠️ Duplikat tweet atlandı: {article['title'][:50]}...", "warning")
                            break
                    
                    if not is_duplicate:
                        pending_tweets.append(new_tweet)
                        save_json("pending_tweets.json", pending_tweets)
                        terminal_log(f"📝 Tweet onay bekliyor: {article['title'][:50]}...", "info")
                    else:
                        terminal_log(f"🔄 Duplikat tweet onay listesine eklenmedi", "info")

                
            except Exception as article_error:
                terminal_log(f"❌ Makale işleme hatası: {article_error}", "error")
                continue
        
        message = f"{len(articles)} makale bulundu, {posted_count} tweet paylaşıldı"
        terminal_log(f"✅ Otomatik kontrol tamamlandı: {message}", "success")
        return {"success": True, "message": message}
        
    except Exception as e:
        terminal_log(f"❌ Makale kontrol hatası: {e}", "error")
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
    """Tweet silme endpoint'i - Makaleyi silindi olarak işaretle"""
    try:
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        
        if not tweet_id:
            return jsonify({"success": False, "error": "Tweet ID gerekli"})
        
        # Pending tweet'i bul
        pending_tweets = load_json("pending_tweets.json")
        deleted_tweet = None
        
        for i, pending in enumerate(pending_tweets):
            if str(i) == str(tweet_id):
                deleted_tweet = pending
                break
        
        if deleted_tweet:
            # Makaleyi "silindi" olarak işaretle
            article = deleted_tweet['article']
            article['deleted'] = True
            article['deleted_date'] = datetime.now().isoformat()
            article['tweet_text'] = deleted_tweet['tweet_data']['tweet']
            article['deletion_reason'] = 'Manuel olarak silindi'
            
            # Posted articles'a "silindi" olarak ekle
            posted_articles = load_json("posted_articles.json")
            posted_articles.append(article)
            save_json("posted_articles.json", posted_articles)
            
            terminal_log(f"📝 Makale silindi olarak işaretlendi: {article.get('title', '')[:50]}...", "info")
        
        # Pending listesinden kaldır
        pending_tweets = [p for i, p in enumerate(pending_tweets) if str(i) != str(tweet_id)]
        save_json("pending_tweets.json", pending_tweets)
        
        return jsonify({"success": True, "message": "Tweet silindi ve makale bir daha gösterilmeyecek"})
        
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
            'telegram_notifications': request.form.get('telegram_notifications') == 'on',
            'email_notifications': request.form.get('email_notifications') == 'on',
            'enable_duplicate_detection': request.form.get('enable_duplicate_detection') == 'on',
            'title_similarity_threshold': float(request.form.get('title_similarity_threshold', 80)) / 100.0,
            'content_similarity_threshold': float(request.form.get('content_similarity_threshold', 60)) / 100.0,
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
        

        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({"error": str(e)})



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
                    
                    terminal_log(f"🔄 Otomatik haber kontrolü başlatılıyor... (Son kontrol: {last_check_time})", "info")
                    
                    try:
                        result = check_and_post_articles()
                        terminal_log(f"✅ Otomatik kontrol tamamlandı: {result.get('message', 'Sonuç yok')}", "success")
                        

                        
                        last_check_time = current_time
                    except Exception as check_error:
                        terminal_log(f"❌ Otomatik kontrol hatası: {check_error}", "error")
                        
                else:
                    next_check = last_check_time + timedelta(hours=check_interval_hours)
                    remaining = next_check - current_time
                    terminal_log(f"⏰ Sonraki kontrol: {remaining.total_seconds()/3600:.1f} saat sonra", "info")
            else:
                terminal_log("⏸️ Otomatik paylaşım devre dışı", "warning")
            
            # 30 dakika bekle (kontrol sıklığı)
            time.sleep(1800)  # 30 dakika = 1800 saniye
            
        except Exception as e:
            terminal_log(f"❌ Arka plan zamanlayıcı hatası: {e}", "error")
            time.sleep(1800)  # Hata durumunda da 30 dakika bekle

def start_background_scheduler():
    """Arka plan zamanlayıcısını thread olarak başlat"""
    global background_scheduler_running
    
    if not background_scheduler_running:
        scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
        scheduler_thread.start()
        terminal_log("🚀 Arka plan zamanlayıcısı başlatıldı (Her 3 saatte bir çalışacak)", "success")
        terminal_log("🔄 Arka plan zamanlayıcı thread'i başlatıldı", "info")

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
        from utils import add_news_source_with_validation
        
        name = request.form.get('name', '').strip()
        url = request.form.get('url', '').strip()
        description = request.form.get('description', '').strip()
        
        # Checkbox değerini doğru oku (checkbox işaretliyse 'on', değilse None)
        auto_detect_value = request.form.get('auto_detect')
        auto_detect = auto_detect_value == 'on'
        
        # Debug için log ekle
        terminal_log(f"🔍 Form verileri - auto_detect_value: {auto_detect_value}, auto_detect: {auto_detect}", "debug")
        
        # Manuel selector'ları al
        manual_selectors = None
        
        terminal_log(f"🔍 auto_detect durumu: {auto_detect}", "debug")
        
        if not auto_detect:
            terminal_log("📝 Manuel mod aktif - Selector'ları alıyorum", "info")
            manual_selectors = {
                'article_container': request.form.get('article_container', '').strip(),
                'title_selector': request.form.get('title_selector', '').strip(),
                'link_selector': request.form.get('link_selector', '').strip(),
                'date_selector': request.form.get('date_selector', '').strip(),
                'summary_selector': request.form.get('summary_selector', '').strip(),
                'base_url': request.form.get('base_url', '').strip()
            }
            
            terminal_log(f"🔍 Manuel selector'lar: {manual_selectors}", "debug")
            
            # Manuel selector'lar için zorunlu alanları kontrol et
            if not manual_selectors['article_container'] or not manual_selectors['title_selector'] or not manual_selectors['link_selector']:
                terminal_log("❌ Manuel mod için zorunlu alanlar eksik!", "error")
                flash('Manuel mod için konteyner, başlık ve link selector\'ları zorunludur!', 'error')
                return redirect(url_for('news_sources'))
        else:
            # Otomatik tespit modunda manuel selector'ları temizle
            terminal_log("🤖 Otomatik tespit modu aktif - Manuel selector'lar atlanıyor", "info")
            manual_selectors = None
        
        if not name or not url:
            flash('Kaynak adı ve URL gerekli!', 'error')
            return redirect(url_for('news_sources'))
        
        result = add_news_source_with_validation(name, url, description, auto_detect, manual_selectors)
        
        if result['success']:
            flash(result['message'], 'success')
            
            # Test detaylarını da göster
            if 'test_details' in result:
                test_details = result['test_details']
                if test_details.get('sample_articles'):
                    sample_count = len(test_details['sample_articles'])
                    flash(f'🔍 Test: {test_details["container_count"]} konteyner, {sample_count} örnek makale bulundu', 'info')
                elif test_details.get('article_count'):
                    flash(f'🔍 Manuel test: {test_details["article_count"]} makale bulundu', 'info')
        else:
            flash(result['message'], 'error')
            
            # Test detaylarını hata durumunda da göster
            if 'test_details' in result:
                test_details = result['test_details']
                flash(f'🔍 Test detayı: {test_details.get("message", "Bilinmeyen hata")}', 'warning')
            
    except Exception as e:
        flash(f'Kaynak ekleme hatası: {str(e)}', 'error')
    
    return redirect(url_for('news_sources'))

@app.route('/test_news_source_url', methods=['POST'])
@login_required
def test_news_source_url():
    """Haber kaynağı URL'ini test et"""
    try:
        from utils import test_selectors_for_url
        
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'message': 'URL gerekli'
            })
        
        # URL formatını kontrol et
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        result = test_selectors_for_url(url)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Test hatası: {str(e)}'
        })

@app.route('/test_manual_selectors', methods=['POST'])
@login_required
def test_manual_selectors():
    """Manuel selector'ları test et"""
    try:
        from utils import test_manual_selectors_for_url
        
        data = request.get_json()
        url = data.get('url', '').strip()
        selectors = data.get('selectors', {})
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL gerekli'
            })
        
        # Zorunlu selector'ları kontrol et
        required_selectors = ['article_container', 'title_selector', 'link_selector']
        for selector in required_selectors:
            if not selectors.get(selector, '').strip():
                return jsonify({
                    'success': False,
                    'error': f'{selector} zorunludur'
                })
        
        # URL formatını kontrol et
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        result = test_manual_selectors_for_url(url, selectors)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Test hatası: {str(e)}'
        })

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

# =============================================================================
# CANLI TERMINAL SİSTEMİ
# =============================================================================

import queue
import threading
from flask import Response
import json
import time

# Global log queue
log_queue = queue.Queue(maxsize=1000)

class TerminalLogHandler:
    """Terminal için log handler"""
    
    def __init__(self):
        self.clients = set()
    
    def add_client(self, client_queue):
        """Yeni client ekle"""
        self.clients.add(client_queue)
    
    def remove_client(self, client_queue):
        """Client'ı kaldır"""
        self.clients.discard(client_queue)
    
    def broadcast_log(self, message, level='info'):
        """Tüm client'lara log gönder"""
        timestamp = time.strftime('%H:%M:%S')
        log_data = {
            'message': message,
            'level': level,
            'timestamp': timestamp
        }
        
        # Global queue'ya ekle
        try:
            log_queue.put_nowait(log_data)
        except queue.Full:
            # Queue dolu ise eski mesajları at
            try:
                log_queue.get_nowait()
                log_queue.put_nowait(log_data)
            except queue.Empty:
                pass

# Global terminal log handler
terminal_logger = TerminalLogHandler()

def terminal_log(message, level='info'):
    """Terminal'e log gönder"""
    terminal_logger.broadcast_log(message, level)
    
    # Konsola da yazdır
    level_colors = {
        'info': '\033[92m',      # Yeşil
        'warning': '\033[93m',   # Sarı
        'error': '\033[91m',     # Kırmızı
        'debug': '\033[96m',     # Cyan
        'success': '\033[92m'    # Yeşil
    }
    
    color = level_colors.get(level, '\033[0m')
    reset = '\033[0m'
    timestamp = time.strftime('%H:%M:%S')
    
    print(f"{color}[{timestamp}] [{level.upper()}] {message}{reset}")

@app.route('/api/logs/stream')
@login_required
def log_stream():
    """Server-Sent Events ile canlı log akışı"""
    
    def event_stream():
        client_queue = queue.Queue()
        terminal_logger.add_client(client_queue)
        
        try:
            # İlk bağlantı mesajı
            yield f"data: {json.dumps({'message': 'Terminal bağlantısı kuruldu', 'level': 'success', 'timestamp': time.strftime('%H:%M:%S')})}\n\n"
            
            while True:
                try:
                    # Global queue'dan mesaj al
                    log_data = log_queue.get(timeout=30)  # 30 saniye timeout
                    yield f"data: {json.dumps(log_data)}\n\n"
                    
                except queue.Empty:
                    # Heartbeat gönder
                    yield f"data: {json.dumps({'message': 'heartbeat', 'level': 'debug', 'timestamp': time.strftime('%H:%M:%S')})}\n\n"
                    
        except GeneratorExit:
            terminal_logger.remove_client(client_queue)
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/terminal')
@login_required
def terminal_page():
    """Terminal sayfası"""
    return render_template('terminal.html')

@app.route('/test_duplicate_detection')
@login_required
def test_duplicate_detection():
    """Duplikat tespit sistemini test et"""
    try:
        from utils import filter_duplicate_articles, load_automation_settings
        
        # Test makaleleri oluştur
        test_articles = [
            {
                "title": "OpenAI Launches New GPT-5 Model",
                "url": "https://example.com/openai-gpt5-1",
                "content": "OpenAI today announced the launch of GPT-5, their most advanced language model yet. The new model features improved reasoning capabilities and better understanding of context.",
                "hash": "test_hash_1",
                "fetch_date": "2025-06-08T15:00:00",
                "source": "Test Source 1"
            },
            {
                "title": "OpenAI Unveils GPT-5: Revolutionary AI Model",
                "url": "https://example.com/openai-gpt5-2", 
                "content": "In a groundbreaking announcement, OpenAI has revealed GPT-5, featuring enhanced reasoning and contextual understanding capabilities.",
                "hash": "test_hash_2",
                "fetch_date": "2025-06-08T15:05:00",
                "source": "Test Source 2"
            },
            {
                "title": "Google Announces New Quantum Computer",
                "url": "https://example.com/google-quantum",
                "content": "Google has unveiled a new quantum computing system that promises to solve complex problems faster than traditional computers.",
                "hash": "test_hash_3",
                "fetch_date": "2025-06-08T15:10:00",
                "source": "Test Source 3"
            }
        ]
        
        # Ayarları kontrol et
        settings = load_automation_settings()
        
        # Duplikat filtreleme test et
        filtered_articles = filter_duplicate_articles(test_articles, [])
        
        result = {
            "success": True,
            "message": "Duplikat tespit sistemi test edildi",
            "settings": {
                "enable_duplicate_detection": settings.get('enable_duplicate_detection', True),
                "title_similarity_threshold": settings.get('title_similarity_threshold', 0.8),
                "content_similarity_threshold": settings.get('content_similarity_threshold', 0.6)
            },
            "test_results": {
                "original_count": len(test_articles),
                "filtered_count": len(filtered_articles),
                "duplicates_found": len(test_articles) - len(filtered_articles)
            },
            "filtered_articles": [
                {
                    "title": article.get("title", ""),
                    "source": article.get("source", ""),
                    "url": article.get("url", "")
                } for article in filtered_articles
            ]
        }
        
        flash(f'Duplikat test tamamlandı: {len(test_articles)} → {len(filtered_articles)} makale', 'success')
        return jsonify(result)
        
    except Exception as e:
        flash(f'Duplikat test hatası: {str(e)}', 'error')
        return jsonify({"success": False, "error": str(e)})

@app.route('/clean_duplicate_pending')
@login_required
def clean_duplicate_pending():
    """Bekleyen tweet'lerdeki duplikatları temizle"""
    try:
        from utils import clean_duplicate_pending_tweets
        
        result = clean_duplicate_pending_tweets()
        
        if result.get('success'):
            flash(f'{result.get("message")} - {result.get("original_count")} → {result.get("cleaned_count")} tweet ({result.get("removed_count")} duplikat kaldırıldı)', 'success')
        else:
            flash(result.get('message', 'Bilinmeyen hata'), 'error')
            
    except Exception as e:
        flash(f'Duplikat temizleme hatası: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/rate_limit_status')
@login_required
def rate_limit_status():
    """Twitter API rate limit durumunu göster"""
    try:
        rate_info = get_rate_limit_info()
        
        return jsonify({
            "success": True,
            "rate_limits": rate_info
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/retry_rate_limited_tweets')
@login_required
def retry_rate_limited_tweets():
    """Rate limit hatası olan tweet'leri tekrar dene"""
    try:
        from utils import retry_pending_tweets_after_rate_limit
        
        result = retry_pending_tweets_after_rate_limit()
        
        if result.get('success'):
            flash(result.get('message', 'İşlem tamamlandı'), 'success')
        else:
            flash(result.get('message', 'Bilinmeyen hata'), 'warning')
            
    except Exception as e:
        flash(f'Retry işlemi hatası: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/debug/test_article_fetch')
@login_required
def debug_test_article_fetch():
    """PythonAnywhere'de makale çekme işlevini test et"""
    try:
        from utils import (
            fetch_articles_from_custom_sources, 
            fetch_latest_ai_articles_fallback,
            fetch_latest_ai_articles,
            load_news_sources
        )
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "environment": "PythonAnywhere" if not DEBUG_MODE else "Local",
            "tests": {}
        }
        
        # Test 1: Özel haber kaynakları
        try:
            terminal_log("🧪 Test 1: Özel haber kaynaklarını test ediliyor...", "info")
            custom_articles = fetch_articles_from_custom_sources()
            test_results["tests"]["custom_sources"] = {
                "success": True,
                "article_count": len(custom_articles) if custom_articles else 0,
                "articles": [
                    {
                        "title": article.get("title", "")[:50] + "...",
                        "url": article.get("url", ""),
                        "source": article.get("source", "")
                    } for article in (custom_articles[:3] if custom_articles else [])
                ]
            }
            terminal_log(f"✅ Test 1 başarılı: {len(custom_articles) if custom_articles else 0} makale", "success")
        except Exception as e:
            test_results["tests"]["custom_sources"] = {
                "success": False,
                "error": str(e)
            }
            terminal_log(f"❌ Test 1 başarısız: {e}", "error")
        
        # Test 2: Fallback sistemi
        try:
            terminal_log("🧪 Test 2: Fallback sistemini test ediliyor...", "info")
            fallback_articles = fetch_latest_ai_articles_fallback()
            test_results["tests"]["fallback_system"] = {
                "success": True,
                "article_count": len(fallback_articles) if fallback_articles else 0,
                "articles": [
                    {
                        "title": article.get("title", "")[:50] + "...",
                        "url": article.get("url", ""),
                        "source": article.get("source", "")
                    } for article in (fallback_articles[:3] if fallback_articles else [])
                ]
            }
            terminal_log(f"✅ Test 2 başarılı: {len(fallback_articles) if fallback_articles else 0} makale", "success")
        except Exception as e:
            test_results["tests"]["fallback_system"] = {
                "success": False,
                "error": str(e)
            }
            terminal_log(f"❌ Test 2 başarısız: {e}", "error")
        
        # Test 3: Ana makale çekme fonksiyonu
        try:
            terminal_log("🧪 Test 3: Ana makale çekme fonksiyonunu test ediliyor...", "info")
            main_articles = fetch_latest_ai_articles()
            test_results["tests"]["main_function"] = {
                "success": True,
                "article_count": len(main_articles) if main_articles else 0,
                "articles": [
                    {
                        "title": article.get("title", "")[:50] + "...",
                        "url": article.get("url", ""),
                        "source": article.get("source", "")
                    } for article in (main_articles[:3] if main_articles else [])
                ]
            }
            terminal_log(f"✅ Test 3 başarılı: {len(main_articles) if main_articles else 0} makale", "success")
        except Exception as e:
            test_results["tests"]["main_function"] = {
                "success": False,
                "error": str(e)
            }
            terminal_log(f"❌ Test 3 başarısız: {e}", "error")
        
        # Test 4: Haber kaynakları yapılandırması
        try:
            terminal_log("🧪 Test 4: Haber kaynakları yapılandırmasını kontrol ediliyor...", "info")
            news_config = load_news_sources()
            enabled_sources = [s for s in news_config.get("sources", []) if s.get("enabled", True)]
            test_results["tests"]["news_sources_config"] = {
                "success": True,
                "total_sources": len(news_config.get("sources", [])),
                "enabled_sources": len(enabled_sources),
                "sources": [
                    {
                        "name": source.get("name", ""),
                        "url": source.get("url", ""),
                        "enabled": source.get("enabled", True),
                        "last_checked": source.get("last_checked", ""),
                        "success_rate": source.get("success_rate", 0)
                    } for source in enabled_sources
                ]
            }
            terminal_log(f"✅ Test 4 başarılı: {len(enabled_sources)} aktif kaynak", "success")
        except Exception as e:
            test_results["tests"]["news_sources_config"] = {
                "success": False,
                "error": str(e)
            }
            terminal_log(f"❌ Test 4 başarısız: {e}", "error")
        
        # Genel sonuç
        successful_tests = sum(1 for test in test_results["tests"].values() if test.get("success", False))
        total_tests = len(test_results["tests"])
        
        test_results["summary"] = {
            "successful_tests": successful_tests,
            "total_tests": total_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "best_method": None
        }
        
        # En iyi yöntemi belirle
        best_content_length = 0
        best_method = None
        
        for test_name, test_result in test_results["tests"].items():
            if test_result.get("success") and test_result.get("content_length", 0) > best_content_length:
                best_content_length = test_result.get("content_length", 0)
                best_method = test_name
        
        test_results["summary"]["best_method"] = best_method
        
        terminal_log(f"🏁 Test tamamlandı: {successful_tests}/{total_tests} başarılı", "info")
        if best_method:
            terminal_log(f"🏆 En iyi yöntem: {best_method} ({best_content_length} karakter)", "success")
        
        return jsonify({
            "success": True,
            "message": f"Test tamamlandı: {successful_tests}/{total_tests} başarılı",
            "results": test_results
        })
        
    except Exception as e:
        terminal_log(f"❌ Test hatası: {e}", "error")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/test_manual_selector_ui')
@login_required
def test_manual_selector_ui():
    """Manuel selector UI test sayfası"""
    return render_template('test_manual_selectors.html')

@app.route('/selector_guide')
@login_required
def selector_guide():
    """CSS Selector bulma kılavuzu"""
    return render_template('selector_guide_page.html')

@app.route('/debug/test_add_source', methods=['POST'])
@login_required
def debug_test_add_source():
    """Kaynak ekleme işlemini debug et"""
    try:
        # Form verilerini al
        form_data = dict(request.form)
        
        terminal_log("=== KAYNAK EKLEME DEBUG ===", "info")
        terminal_log(f"Form verileri: {form_data}", "debug")
        
        # Checkbox değerini kontrol et
        auto_detect_value = request.form.get('auto_detect')
        auto_detect = auto_detect_value == 'on'
        
        terminal_log(f"auto_detect_value: {auto_detect_value}", "debug")
        terminal_log(f"auto_detect: {auto_detect}", "debug")
        
        # Manuel selector'ları kontrol et
        if not auto_detect:
            manual_selectors = {
                'article_container': request.form.get('article_container', '').strip(),
                'title_selector': request.form.get('title_selector', '').strip(),
                'link_selector': request.form.get('link_selector', '').strip(),
                'date_selector': request.form.get('date_selector', '').strip(),
                'summary_selector': request.form.get('summary_selector', '').strip(),
                'base_url': request.form.get('base_url', '').strip()
            }
            terminal_log(f"Manuel selector'lar: {manual_selectors}", "debug")
        else:
            terminal_log("Otomatik tespit modu - Manuel selector'lar atlanıyor", "info")
        
        terminal_log("=== DEBUG TAMAMLANDI ===", "info")
        
        return jsonify({
            "success": True,
            "message": "Debug tamamlandı - Terminal loglarını kontrol edin",
            "form_data": form_data,
            "auto_detect": auto_detect
        })
        
    except Exception as e:
        terminal_log(f"Debug hatası: {e}", "error")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/test_advanced_scraper', methods=['POST'])
@login_required
def test_advanced_scraper():
    """Gelişmiş scraper'ı test et"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL gerekli'
            })
        
        # URL formatını kontrol et
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        terminal_log(f"🧪 Gelişmiş scraper test ediliyor: {url}", "info")
        
        from utils import advanced_web_scraper, mcp_firecrawl_scrape
        
        # Test sonuçları
        test_results = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Gelişmiş scraper (JavaScript ile)
        try:
            terminal_log("🚀 Test 1: Gelişmiş scraper (JavaScript)", "info")
            result1 = advanced_web_scraper(url, wait_time=3, use_js=True)
            
            test_results["tests"]["advanced_js"] = {
                "success": result1.get("success", False),
                "method": result1.get("method", "unknown"),
                "content_length": len(result1.get("content", "")),
                "error": result1.get("error") if not result1.get("success") else None
            }
            
            if result1.get("success"):
                terminal_log(f"✅ Test 1 başarılı: {result1.get('method')} - {len(result1.get('content', ''))} karakter", "success")
            else:
                terminal_log(f"❌ Test 1 başarısız: {result1.get('error', 'Bilinmeyen hata')}", "error")
                
        except Exception as e:
            test_results["tests"]["advanced_js"] = {
                "success": False,
                "error": str(e)
            }
            terminal_log(f"❌ Test 1 hatası: {e}", "error")
        
        # Test 2: Gelişmiş scraper (JavaScript olmadan)
        try:
            terminal_log("🔄 Test 2: Gelişmiş scraper (JavaScript olmadan)", "info")
            result2 = advanced_web_scraper(url, wait_time=1, use_js=False)
            
            test_results["tests"]["advanced_no_js"] = {
                "success": result2.get("success", False),
                "method": result2.get("method", "unknown"),
                "content_length": len(result2.get("content", "")),
                "error": result2.get("error") if not result2.get("success") else None
            }
            
            if result2.get("success"):
                terminal_log(f"✅ Test 2 başarılı: {result2.get('method')} - {len(result2.get('content', ''))} karakter", "success")
            else:
                terminal_log(f"❌ Test 2 başarısız: {result2.get('error', 'Bilinmeyen hata')}", "error")
                
        except Exception as e:
            test_results["tests"]["advanced_no_js"] = {
                "success": False,
                "error": str(e)
            }
            terminal_log(f"❌ Test 2 hatası: {e}", "error")
        
        # Test 3: MCP Firecrawl (gelişmiş fallback sistemi)
        try:
            terminal_log("🔧 Test 3: MCP Firecrawl (gelişmiş fallback)", "info")
            result3 = mcp_firecrawl_scrape({
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "waitFor": 2000
            })
            
            test_results["tests"]["mcp_firecrawl"] = {
                "success": result3.get("success", False),
                "source": result3.get("source", "unknown"),
                "content_length": len(result3.get("content", "")),
                "error": result3.get("error") if not result3.get("success") else None
            }
            
            if result3.get("success"):
                terminal_log(f"✅ Test 3 başarılı: {result3.get('source')} - {len(result3.get('content', ''))} karakter", "success")
            else:
                terminal_log(f"❌ Test 3 başarısız: {result3.get('error', 'Bilinmeyen hata')}", "error")
                
        except Exception as e:
            test_results["tests"]["mcp_firecrawl"] = {
                "success": False,
                "error": str(e)
            }
            terminal_log(f"❌ Test 3 hatası: {e}", "error")
        
        # Genel sonuç
        successful_tests = sum(1 for test in test_results["tests"].values() if test.get("success", False))
        total_tests = len(test_results["tests"])
        
        test_results["summary"] = {
            "successful_tests": successful_tests,
            "total_tests": total_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "best_method": None
        }
        
        # En iyi yöntemi belirle
        best_content_length = 0
        best_method = None
        
        for test_name, test_result in test_results["tests"].items():
            if test_result.get("success") and test_result.get("content_length", 0) > best_content_length:
                best_content_length = test_result.get("content_length", 0)
                best_method = test_name
        
        test_results["summary"]["best_method"] = best_method
        
        terminal_log(f"🏁 Test tamamlandı: {successful_tests}/{total_tests} başarılı", "info")
        if best_method:
            terminal_log(f"🏆 En iyi yöntem: {best_method} ({best_content_length} karakter)", "success")
        
        return jsonify({
            "success": True,
            "message": f"Test tamamlandı: {successful_tests}/{total_tests} başarılı",
            "results": test_results
        })
        
    except Exception as e:
        terminal_log(f"❌ Test hatası: {e}", "error")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/analyze_page_source', methods=['POST'])
@login_required
def analyze_page_source():
    """Sayfa kaynağını AI ile analiz et ve selector'ları tespit et"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL gerekli'
            })
        
        # URL formatını kontrol et
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        terminal_log(f"🔍 Sayfa kaynağı analiz ediliyor: {url}", "info")
        
        from utils import advanced_web_scraper, gemini_call
        
        # Sayfa kaynağını çek
        scrape_result = advanced_web_scraper(url, wait_time=3, use_js=True, return_html=True)
        
        if not scrape_result.get("success"):
            return jsonify({
                'success': False,
                'error': f'Sayfa kaynağı çekilemedi: {scrape_result.get("error", "Bilinmeyen hata")}'
            })
        
        html_content = scrape_result.get("html", "")
        if not html_content:
            return jsonify({
                'success': False,
                'error': 'HTML içeriği bulunamadı'
            })
        
        # HTML'i temizle ve kısalt (AI analizi için)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Script ve style taglarını kaldır
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Sadece body kısmını al
        body = soup.find('body')
        if body:
            clean_html = str(body)[:15000]  # İlk 15KB
        else:
            clean_html = str(soup)[:15000]
        
        # AI ile analiz et
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'Google API anahtarı bulunamadı'
            })
        
        analysis_prompt = f"""
Bu HTML sayfa kaynağını analiz et ve haber makalelerini çekmek için en uygun CSS selector'ları belirle:

URL: {url}

HTML İçeriği:
{clean_html}

Lütfen şu bilgileri JSON formatında döndür:
{{
    "analysis": "Sayfa yapısı hakkında kısa analiz",
    "selectors": {{
        "article_container": "Her makaleyi içeren ana konteyner selector",
        "title_selector": "Makale başlığı selector",
        "link_selector": "Makale linki selector", 
        "date_selector": "Tarih selector (varsa)",
        "summary_selector": "Özet selector (varsa)"
    }},
    "confidence": "Yüksek/Orta/Düşük",
    "notes": "Ek notlar ve öneriler"
}}

Sadece JSON döndür, başka açıklama ekleme.
"""
        
        terminal_log("🤖 AI analizi başlatılıyor...", "info")
        ai_response = gemini_call(analysis_prompt, api_key)
        
        if not ai_response:
            return jsonify({
                'success': False,
                'error': 'AI analizi başarısız oldu'
            })
        
        # JSON parse et
        try:
            import json
            # AI response'dan JSON kısmını çıkar
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = ai_response[json_start:json_end]
                ai_analysis = json.loads(json_str)
            else:
                raise ValueError("JSON bulunamadı")
                
        except Exception as e:
            terminal_log(f"❌ AI response parse hatası: {e}", "error")
            # Fallback analiz
            ai_analysis = {
                "analysis": "Otomatik analiz yapıldı",
                "selectors": {
                    "article_container": ".article, .post, .entry",
                    "title_selector": "h1, h2, h3",
                    "link_selector": "a",
                    "date_selector": ".date, time, .published",
                    "summary_selector": ".excerpt, .summary, p"
                },
                "confidence": "Düşük",
                "notes": "AI analizi başarısız, genel selector'lar önerildi"
            }
        
        # HTML'i highlight'la (selector'ları işaretle)
        highlighted_html = highlight_selectors_in_html(html_content, ai_analysis.get("selectors", {}))
        
        terminal_log("✅ AI analizi tamamlandı", "success")
        
        return jsonify({
            'success': True,
            'url': url,
            'html_content': highlighted_html[:50000],  # İlk 50KB
            'ai_analysis': ai_analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        terminal_log(f"❌ Sayfa analizi hatası: {e}", "error")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def highlight_selectors_in_html(html_content, selectors):
    """HTML içeriğinde selector'ları renklendir"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Selector renkleri
        selector_colors = {
            'article_container': '#ff6b6b',  # Kırmızı
            'title_selector': '#4ecdc4',    # Turkuaz
            'link_selector': '#45b7d1',     # Mavi
            'date_selector': '#96ceb4',     # Yeşil
            'summary_selector': '#feca57'   # Sarı
        }
        
        # Her selector için elementleri bul ve işaretle
        for selector_name, selector in selectors.items():
            if not selector:
                continue
                
            color = selector_colors.get(selector_name, '#cccccc')
            
            try:
                # CSS selector'ı parse et
                elements = soup.select(selector)
                
                for element in elements[:10]:  # İlk 10 elementi işaretle
                    # Mevcut style'ı koru ve yeni style ekle
                    current_style = element.get('style', '')
                    new_style = f"{current_style}; background-color: {color}; border: 2px solid {color}; opacity: 0.8;"
                    element['style'] = new_style
                    element['data-selector'] = selector_name
                    element['data-selector-value'] = selector
                    element['title'] = f"{selector_name}: {selector}"
                    
            except Exception as e:
                terminal_log(f"⚠️ Selector işaretleme hatası ({selector}): {e}", "warning")
                continue
        
        return str(soup)
        
    except Exception as e:
        terminal_log(f"❌ HTML highlight hatası: {e}", "error")
        return html_content

if __name__ == '__main__':
    # Arka plan zamanlayıcısını başlat
    start_background_scheduler()
    
    # Python Anywhere için production ayarları
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    terminal_log(f"Flask uygulaması başlatılıyor - Port: {port}", "info")
    app.run(host='0.0.0.0', port=port, debug=debug)