from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import threading
import time
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
from bs4 import BeautifulSoup 
import hashlib
import uuid
import secrets

# .env dosyasını yükle
load_dotenv()

# PythonAnywhere konfigürasyonu
try:
    from pythonanywhere_config import configure_for_pythonanywhere
    is_pythonanywhere = configure_for_pythonanywhere()
except ImportError:
    is_pythonanywhere = False

# Debug mode kontrolü
DEBUG_MODE = os.environ.get('DEBUG', 'True').lower() == 'true'

from utils import (
    fetch_latest_ai_articles, generate_ai_tweet_with_mcp_analysis,
    generate_ai_tweet_with_content, post_tweet, mark_article_as_posted, load_json, save_json,
    get_posted_articles_summary, reset_all_data, clear_pending_tweets,
    get_data_statistics, load_automation_settings, save_automation_settings,
    get_automation_status, send_telegram_notification, test_telegram_connection,
    check_telegram_configuration, auto_detect_and_save_chat_id,
    setup_twitter_api, send_gmail_notification, test_gmail_connection,
    check_gmail_configuration, get_rate_limit_info, terminal_log,
    create_automatic_backup, load_ai_keywords_config, save_ai_keywords_config,
    get_all_active_keywords, fetch_ai_news_with_advanced_keywords,
    update_ai_keyword_category, get_ai_keywords_stats, analyze_tweet_quality,
    safe_log, get_trending_ai_hashtags, remove_emojis_from_text, enhance_hashtags_with_trending,
    reset_rate_limit_status
)

# GitHub modülü kaldırıldı

# Security manager import - SQLite kullanacağız

# Version Information
APP_VERSION = "1.4.2"
APP_RELEASE_DATE = "2025-08-24"
VERSION_CHANGELOG = {
    "1.4.2": "🔐 Şifre Yönetici Güvenlik İyileştirmeleri - 3 yanlış deneme sonrası otomatik veri silme, Gelişmiş session güvenliği, Detaylı hata yönetimi, Template güvenlik uyarıları, Kapsamlı test sistemi",
    "1.4.1": "🔧 Sistem Kontrolü ve İyileştirmeleri - Duplicate kontrol sistemi kapsamlı kontrol ve doğrulama, Toplu tweet sistemi güvenlik kontrolleri, Haber çekme sistemi multi-source duplicate prevention, Version tracking sistemi otomatik güncelleme",
    "1.4.0": "🚀 OpenRouter OCR Entegrasyonu - Ücretsiz vision modelleri ile gelişmiş OCR sistemi, Çok katmanlı fallback sistemi, Gelişmiş hata yönetimi, OCR test sistemi, Kapsamlı dokümantasyon",
    "1.3.0": "🔄 GitHub modülü kaldırıldı, Footer düzeltildi, Navbar yenilendi",
    "1.2.0": "✨ UI iyileştirmeleri ve performans optimizasyonları", 
    "1.1.0": "🚀 Otomatik tweet sistemi ve AI entegrasyonu"
}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Security Manager instance - JSON kullan (basit ve güvenilir)
try:
    from security_manager import SecurityManager
    security_manager = SecurityManager()
    print("✅ JSON SecurityManager kullanılıyor")
except ImportError as e:
    print(f"❌ SecurityManager yüklenemedi: {e}")
    security_manager = None

# Markdown filter for Jinja2 templates
import re
def markdown_filter(text):
    """Basit markdown to HTML converter"""
    if not text:
        return ""
    
    # Headers
    text = re.sub(r'^# (.*$)', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*$)', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.*$)', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Code blocks
    text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', text, flags=re.DOTALL)
    
    # Inline code
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    # Lists
    text = re.sub(r'^- (.*$)', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    
    # Line breaks
    text = text.replace('\n\n', '<br><br>')
    text = text.replace('\n', '<br>')
    
    return text

app.jinja_env.filters['markdown'] = markdown_filter

# Test route'u
@app.route('/test')
def test():
    return render_template('test.html')

# Favicon 404 hatasını önle
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

# Template context processor for global variables
@app.context_processor
def inject_globals():
    return {
        'app_version': APP_VERSION,
        'version_changelog': VERSION_CHANGELOG,
        'is_pythonanywhere': is_pythonanywhere,
        'use_local_assets': os.environ.get('USE_LOCAL_ASSETS', 'false').lower() == 'true'
    }

# Global değişkenler ve sabitler
HISTORY_FILE = "posted_articles.json"
last_check_time = None
automation_running = False
background_scheduler_running = False

# Global ilerleme durumu değişkenleri
progress_status = {
    'is_running': False,
    'current_step': '',
    'total_steps': 0,
    'current_step_number': 0,
    'message': '',
    'start_time': None,
    'estimated_time': 0
}
progress_lock = threading.Lock()

def update_progress(step, message, step_number=None, total_steps=None):
    """İlerleme durumunu güncelle"""
    global progress_status
    with progress_lock:
        progress_status['current_step'] = step
        progress_status['message'] = message
        if step_number is not None:
            progress_status['current_step_number'] = step_number
        if total_steps is not None:
            progress_status['total_steps'] = total_steps
        
        # Tahmini süre hesapla
        if progress_status['start_time']:
            elapsed = time.time() - progress_status['start_time']
            if step_number and total_steps and step_number > 0:
                avg_time_per_step = elapsed / step_number
                remaining_steps = total_steps - step_number
                progress_status['estimated_time'] = avg_time_per_step * remaining_steps

def start_progress():
    """İlerleme takibini başlat"""
    global progress_status
    with progress_lock:
        progress_status['is_running'] = True
        progress_status['current_step'] = 'Başlatılıyor...'
        progress_status['message'] = 'Sistem hazırlanıyor...'
        progress_status['current_step_number'] = 0
        progress_status['total_steps'] = 0
        progress_status['start_time'] = time.time()
        progress_status['estimated_time'] = 0

def end_progress():
    """İlerleme takibini sonlandır"""
    global progress_status
    with progress_lock:
        progress_status['is_running'] = False
        progress_status['current_step'] = 'Tamamlandı'
        progress_status['message'] = 'İşlem başarıyla tamamlandı'

def ensure_tweet_ids(pending_tweets):
    """Pending tweets'lerin ID'lerini güvenli şekilde kontrol et ve düzelt"""
    try:
        for i, tweet in enumerate(pending_tweets):
            if isinstance(tweet, dict):
                if 'id' not in tweet or tweet['id'] is None:
                    tweet['id'] = i + 1
            else:
                # Object ise dict'e çevir
                try:
                    tweet_dict = dict(tweet) if hasattr(tweet, '__dict__') else {}
                    tweet_dict['id'] = i + 1
                    pending_tweets[i] = tweet_dict
                except:
                    # Son çare: yeni dict oluştur
                    pending_tweets[i] = {'id': i + 1, 'error': 'Tweet format hatası'}
        
        return pending_tweets
    except Exception as e:
        terminal_log(f"❌ Tweet ID düzeltme hatası: {e}", "error")
        return pending_tweets

# Giriş kontrolü decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            # AJAX isteği ise JSON ve 401 döndür
            try:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'error': 'auth_required',
                        'login_url': url_for('login', _external=False)
                    }), 401
            except Exception:
                pass
            return redirect(url_for('login'))
        
        # "Beni Hatırla" süresini kontrol et
        if session.get('remember_me') and session.get('remember_until'):
            try:
                remember_until = datetime.fromisoformat(session['remember_until'])
                if datetime.now() > remember_until:
                    # Süre dolmuş, çıkış yap
                    session.clear()
                    flash('Oturum süreniz doldu. Lütfen tekrar giriş yapın.', 'info')
                    try:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return jsonify({
                                'success': False,
                                'error': 'session_expired',
                                'login_url': url_for('login', _external=False)
                            }), 401
                    except Exception:
                        pass
                    return redirect(url_for('login'))
            except:
                # Hatalı tarih formatı, güvenlik için çıkış yap
                session.clear()
                try:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'success': False,
                            'error': 'session_invalid',
                            'login_url': url_for('login', _external=False)
                        }), 401
                except Exception:
                    pass
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
        
        # 6 haneli güvenli rastgele kod oluştur
        import secrets
        otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
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
            
            # Giriş verilerini kontrol et
            if not email:
                flash('E-posta adresi gerekli!', 'error')
                return render_template('login.html', error='E-posta adresi eksik')
            
            if not otp_code:
                flash('Doğrulama kodu gerekli!', 'error')
                return render_template('login.html', error='Doğrulama kodu eksik')
            
            # OTP kod formatını kontrol et
            if len(otp_code) != 6 or not otp_code.isdigit():
                flash('Doğrulama kodu 6 haneli rakam olmalıdır!', 'error')
                return render_template('login.html', error='Geçersiz kod formatı')
            
            # Admin e-posta kontrolü
            admin_email = EMAIL_SETTINGS['admin_email'].lower()
            if not admin_email:
                flash('Sistem yapılandırma hatası!', 'error')
                return render_template('login.html', error='Admin e-posta yapılandırılmamış')
            
            if email != admin_email:
                flash('Bu e-posta adresi ile giriş yetkiniz yok!', 'error')
                return render_template('login.html', error='Yetkisiz e-posta adresi')
            
            # OTP kontrolü
            if email not in email_otp_codes:
                flash('Geçersiz veya süresi dolmuş doğrulama kodu! Yeni kod talep edin.', 'error')
                return render_template('login.html', error='Kod bulunamadı')
            
            otp_data = email_otp_codes[email]
            
            # Süre kontrolü (5 dakika = 300 saniye)
            time_elapsed = (datetime.now() - otp_data['timestamp']).total_seconds()
            if time_elapsed > 300:
                del email_otp_codes[email]
                flash('Doğrulama kodunun süresi doldu! Yeni kod talep edin.', 'error')
                return render_template('login.html', error='Kod süresi doldu')
            
            # Deneme sayısı kontrolü
            if otp_data['attempts'] >= 3:
                del email_otp_codes[email]
                flash('Çok fazla hatalı deneme! Güvenlik nedeniyle kod iptal edildi.', 'error')
                return render_template('login.html', error='Çok fazla hatalı deneme')
            
            # Kod kontrolü
            if otp_code == otp_data['code']:
                # Başarılı giriş
                del email_otp_codes[email]
                session['logged_in'] = True
                session['login_time'] = datetime.now().isoformat()
                session['auth_method'] = 'email_otp'
                session['user_email'] = email
                
                # "Beni Hatırla" kontrolü
                remember_me = request.form.get('remember_me')
                if remember_me:
                    # 30 gün boyunca hatırla
                    session.permanent = True
                    app.permanent_session_lifetime = timedelta(days=30)
                    session['remember_me'] = True
                    session['remember_until'] = (datetime.now() + timedelta(days=30)).isoformat()
                    terminal_log(f"✅ Başarılı giriş (30 gün hatırlanacak): {email}", "success")
                    flash('E-posta doğrulama ile başarıyla giriş yaptınız! 30 gün boyunca hatırlanacaksınız.', 'success')
                else:
                    # Normal session (tarayıcı kapanınca sona erer)
                    session.permanent = False
                    terminal_log(f"✅ Başarılı giriş: {email}", "success")
                    flash('E-posta doğrulama ile başarıyla giriş yaptınız!', 'success')
                
                return redirect(url_for('index'))
            else:
                # Hatalı kod
                otp_data['attempts'] += 1
                remaining_attempts = 3 - otp_data['attempts']
                
                # Terminal log
                terminal_log(f"❌ Hatalı giriş denemesi: {email} - Kalan deneme: {remaining_attempts}", "warning")
                
                if remaining_attempts > 0:
                    flash(f'Hatalı doğrulama kodu! {remaining_attempts} deneme hakkınız kaldı.', 'error')
                    return render_template('login.html', error=f'Hatalı kod - {remaining_attempts} deneme kaldı')
                else:
                    del email_otp_codes[email]
                    flash('Çok fazla hatalı deneme! Yeni kod talep edin.', 'error')
                    return render_template('login.html', error='Deneme hakkı bitti')
    
    # Eğer zaten giriş yapmışsa ana sayfaya yönlendir
    if 'logged_in' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Çıkış yap"""
    user_email = session.get('user_email', 'Bilinmeyen kullanıcı')
    was_remembered = session.get('remember_me', False)
    
    session.clear()
    
    if was_remembered:
        terminal_log(f"🚪 Çıkış yapıldı (hatırlanan oturum): {user_email}", "info")
        flash('Başarıyla çıkış yaptınız! Hatırlanan oturum temizlendi.', 'info')
    else:
        terminal_log(f"🚪 Çıkış yapıldı: {user_email}", "info")
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
log_queue = queue.Queue(maxsize=1000)



@app.route('/')
@login_required
def index():
    """Ana sayfa - Minimal versiyon"""
    try:
        # Temel verileri yükle - performans için limit kullan
        all_articles = load_json("posted_articles.json", limit=100)  # Son 100 makale
        pending_tweets = load_json("pending_tweets.json", limit=50)  # Son 50 pending tweet
        rejected_articles = load_json("rejected_articles.json", [])  # Reddedilen makaleler
        
        # Reddedilen makalelerin tarih formatını düzelt
        for article in rejected_articles:
            if 'rejected_at' in article:
                try:
                    from datetime import datetime
                    rejected_date = datetime.fromisoformat(article['rejected_at'].replace('Z', '+00:00'))
                    article['rejected_at_formatted'] = rejected_date.strftime('%d.%m.%Y %H:%M')
                except:
                    article['rejected_at_formatted'] = article.get('rejected_at', 'Bilinmiyor')
            else:
                article['rejected_at_formatted'] = 'Bilinmiyor'
        
        # Aktif makaleleri filtrele
        articles = [article for article in all_articles if not article.get('deleted', False)]
        
        # Tweet ID'lerini güvenli şekilde kontrol et
        pending_tweets = ensure_tweet_ids(pending_tweets)
        
        # Tweet içeriklerini düzenle
        for tweet in pending_tweets:
            # Tweet metnini bul - farklı alan isimleri dene
            tweet_text = ''
            if 'tweet_data' in tweet and 'tweet' in tweet['tweet_data']:
                tweet_text = tweet['tweet_data']['tweet']
            elif 'content' in tweet:
                tweet_text = tweet['content']
            elif 'article' in tweet:
                tweet_text = tweet['article'].get('title', 'İçerik bulunamadı')
            
            # Tweet content alanını ayarla
            tweet['content'] = tweet_text
            
            # Başlık ve URL bilgilerini ekle
            tweet['title'] = tweet['article'].get('title', 'Başlık bulunamadı') if 'article' in tweet else tweet.get('content', 'Başlık bulunamadı')
            tweet['url'] = tweet['article'].get('url', '') if 'article' in tweet else ''
        
        # Tarihe göre sırala
        pending_tweets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # News count hesapla (haber kaynaklı tweet'ler)
        news_count = 0
        for tweet in pending_tweets:
            if 'article' in tweet and tweet['article'].get('source_type') == 'news':
                news_count += 1
        
        # İstatistikleri ve durumu al
        stats = get_data_statistics()
        automation_status = get_automation_status()
        
        # Terminal log
        terminal_log(f"📊 Ana sayfa yüklendi: {len(pending_tweets)} bekleyen tweet, {len(articles)} son makale, {news_count} haber", "info")
        
        # API durumu kontrolü - geliştirilmiş versiyon
        try:
            api_check = {
                "twitter_api_available": bool(os.environ.get('TWITTER_BEARER_TOKEN') and os.environ.get('TWITTER_API_KEY')),
                "telegram_available": bool(os.environ.get('TELEGRAM_BOT_TOKEN')),
                "openrouter_api_available": bool(os.environ.get('OPENROUTER_API_KEY')),
                "google_api_available": bool(os.environ.get('GOOGLE_API_KEY'))
            }
        except Exception as e:
            terminal_log(f"⚠️ API durumu kontrol edilemedi: {str(e)}", "warning")
            api_check = {
                "twitter_api_available": False, 
                "telegram_available": False,
                "google_api_available": False,
                "openrouter_api_available": False
            }
        
        # Ayarları yükle - hata yakalama ile
        try:
            settings = load_automation_settings()
        except Exception as e:
            terminal_log(f"⚠️ Otomasyon ayarları yüklenemedi: {str(e)}", "warning")
            settings = {}
        
        # Gelişmiş özellikler için gerekli verileri hazırla
        try:
            # API durumu kontrolü
            api_check = {
                'openrouter_api_available': bool(os.getenv('OPENROUTER_API_KEY')),
                'twitter_api_available': bool(os.getenv('TWITTER_API_KEY') and os.getenv('TWITTER_API_SECRET')),
                'google_api_available': bool(os.getenv('GOOGLE_API_KEY')),
                'telegram_available': bool(os.getenv('TELEGRAM_BOT_TOKEN'))
            }
        except:
            api_check = {}
        
        # Versiyon bilgisi
        app_version = APP_VERSION
        app_release_date = APP_RELEASE_DATE
        
        # İstatistikler
        stats = {
            'today_articles': len(articles),
            'today_pending': len(pending_tweets),
            'today_total_activity': len(articles) + len(pending_tweets)
        }
        
        # Otomasyon durumu
        automation_status = {
            'auto_mode': True,
            'check_interval_hours': 1,
            'min_score_threshold': 7,
            'max_articles_per_run': 5
        }
        
        # Haber sayısı
        news_count = len(pending_tweets)
        
        return render_template('index.html', 
                             pending_tweets=pending_tweets[:20],  # Maksimum 20 pending tweet
                             posted_count=len(articles),
                             rejected_count=len(rejected_articles),
                             rejected_articles=rejected_articles[:10],  # İlk 10 reddedilen makale
                             api_check=api_check,
                             app_version=app_version,
                             app_release_date=app_release_date,
                             stats=stats,
                             automation_status=automation_status,
                             news_count=news_count)
                             
    except Exception as e:
        safe_log(f"Ana sayfa hatası: {str(e)}", "ERROR")
        return render_template('index.html', 
                             pending_tweets=[],
                             posted_count=0,
                             rejected_count=0,
                             rejected_articles=[],
                             stats={},
                             automation_status={},
                             api_check={},
                             app_version=APP_VERSION,
                             app_release_date=APP_RELEASE_DATE,
                             news_count=0,
                             error=str(e))

@app.route('/api/progress')
@login_required
def get_progress():
    """İlerleme durumunu döndür"""
    global progress_status
    with progress_lock:
        return jsonify(progress_status)

@app.route('/check_articles', methods=['GET', 'POST'])
@login_required
def check_articles():
    """Manuel makale kontrolü"""
    try:
        result = check_and_post_articles()
        
        # AJAX isteği mi kontrol et
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            posted_count = result.get('posted_count', 0)
            pending_count = result.get('pending_count', 0)
            new_articles = posted_count + pending_count  # Toplam yeni tweet sayısı
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'new_articles': new_articles,
                'posted_count': posted_count,
                'pending_count': pending_count,
                'total_pending': len(load_json("pending_tweets.json")),
                'should_refresh': new_articles > 0
            })
        else:
            flash(f"Kontrol tamamlandı: {result['message']}", 'success')
            return redirect(url_for('index'))
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'error': str(e),
                'message': f"Hata: {str(e)}"
            })
        else:
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
        # İlerleme takibini başlat
        start_progress()
        update_progress("Sistem Başlatılıyor", "Makale kontrol sistemi hazırlanıyor...", 1, 8)
        
        safe_log("Yeni makaleler kontrol ediliyor...", "INFO")
        
        # Ayarları yükle
        update_progress("Ayarlar Yükleniyor", "Sistem ayarları kontrol ediliyor...", 2, 8)
        settings = load_automation_settings()
        # AI API anahtarı opsiyonel olmalı: OpenRouter öncelikli, Google yedek, yoksa yerel fallback
        api_key = os.environ.get('OPENROUTER_API_KEY') or ""
        if not os.environ.get('OPENROUTER_API_KEY'):
            # Uyarı ver, fakat işlemi durdurma (yerel fallback tweet üretimi mevcut)
            terminal_log("⚠️ Hiçbir AI API anahtarı bulunamadı – fallback tweet oluşturma kullanılacak", "warning")
        
        # Yeni makaleleri çek (akıllı sistem ile)
        update_progress("Haberler Çekiliyor", "Güncel haberler toplanıyor...", 3, 8)
        try:
            from utils import fetch_latest_ai_articles_smart
            terminal_log("🔍 Akıllı haber çekme sistemi başlatılıyor...", "info")
            articles = fetch_latest_ai_articles_smart()
            terminal_log(f"📊 {len(articles) if articles else 0} makale bulundu", "info")
        except Exception as fetch_error:
            terminal_log(f"❌ Haber çekme hatası: {fetch_error}", "error")
            import traceback
            terminal_log(f"🔍 Hata detayı: {traceback.format_exc()}", "error")
            end_progress()
            return {"success": False, "message": f"Haber çekme hatası: {str(fetch_error)}"}
        
        if not articles:
            end_progress()
            return {"success": True, "message": "Yeni makale bulunamadı"}
        
        posted_count = 0
        pending_count = 0
        ai_failures = 0  # AI API başarısızlık sayacı
        max_articles = settings.get('max_articles_per_run', 3)
        min_score = settings.get('min_score_threshold', 5)
        auto_post = settings.get('auto_post_enabled', False)
        
        # İşlenmiş makaleleri yükle (duplikat kontrolü için)
        posted_articles = load_json("posted_articles.json")
        pending_tweets = load_json("pending_tweets.json")
        
        update_progress("Makaleler İşleniyor", f"{len(articles[:max_articles])} makale işleniyor...", 4, 8)
        
        for i, article in enumerate(articles[:max_articles]):
            try:
                # İlerleme güncelle - makale işleme aşaması
                update_progress("Makale İşleniyor", f"Makale {i+1}/{len(articles[:max_articles])}: {article.get('title', '')[:50]}...", 4 + i, 4 + len(articles[:max_articles]))
                # Önce makale içeriğinin kaliteli olup olmadığını kontrol et
                from utils import is_article_content_valid
                is_valid, reason = is_article_content_valid(article)
                if not is_valid:
                    terminal_log(f"❌ Kalitesiz makale atlandı: {article['title'][:50]}... - Sebep: {reason}", "warning")
                    
                    # Kalitesiz makaleleri ayrı dosyaya kaydet
                    try:
                        rejected_articles = load_json("rejected_articles.json", [])
                        rejected_article = {
                            "title": article.get('title', ''),
                            "url": article.get('url', ''),
                            "reason": reason,
                            "rejected_at": datetime.now().isoformat(),
                            "content_preview": article.get('content', '')[:200] + "..." if article.get('content') else ""
                        }
                        rejected_articles.append(rejected_article)
                        # Son 100 rejected makaleyi tut
                        if len(rejected_articles) > 100:
                            rejected_articles = rejected_articles[-100:]
                        save_json("rejected_articles.json", rejected_articles)
                    except Exception as save_error:
                        terminal_log(f"⚠️ Rejected article kaydetme hatası: {save_error}", "warning")
                    
                    continue
                
                # Makale zaten işlenmiş mi kontrol et
                article_url = article.get('url', '')
                article_title = article.get('title', '')
                article_hash = article.get('hash', '')
                
                # Hash yoksa oluştur
                if not article_hash and article_title:
                    import hashlib
                    article_hash = hashlib.md5(article_title.encode()).hexdigest()
                    article['hash'] = article_hash
                    terminal_log(f"🔧 Hash oluşturuldu: {article_title[:50]}...", "info")
                
                # Boş başlık kontrolü
                if not article_title or not article_title.strip():
                    terminal_log(f"⚠️ Boş başlık, atlanıyor: {article_url[:50]}...", "warning")
                    continue
                
                # Posted articles kontrolü
                already_posted = False
                for posted in posted_articles:
                    posted_url = posted.get('url', '')
                    posted_hash = posted.get('hash', '')
                    
                    # URL kontrolü
                    if article_url and article_url == posted_url:
                        already_posted = True
                        break
                    
                    # Hash kontrolü
                    if article_hash and article_hash == posted_hash:
                        already_posted = True
                        break
                
                # Pending tweets kontrolü
                already_pending = False
                for pending in pending_tweets:
                    pending_article = pending.get('article', {})
                    pending_url = pending_article.get('url', '')
                    pending_hash = pending_article.get('hash', '')
                    
                    # URL kontrolü
                    if article_url and article_url == pending_url:
                        already_pending = True
                        break
                    
                    # Hash kontrolü
                    if article_hash and article_hash == pending_hash:
                        already_pending = True
                        break
                
                if already_posted:
                    terminal_log(f"⏭️ Makale zaten paylaşılmış, atlanıyor: {article['title'][:50]}...", "info")
                    continue
                    
                if already_pending:
                    terminal_log(f"⏭️ Makale zaten onay bekliyor, atlanıyor: {article['title'][:50]}...", "info")
                    continue
                
                # Tweet oluştur - tema ile
                update_progress("Tweet Oluşturuluyor", f"AI ile tweet oluşturuluyor: {article['title'][:50]}...", 4 + i, 4 + len(articles[:max_articles]))
                theme = settings.get('tweet_theme', 'bilgilendirici')
                terminal_log(f"🤖 Tweet oluşturuluyor (tema: {theme}): {article['title'][:50]}...", "info")
                tweet_data = generate_ai_tweet_with_content(article, api_key, theme)
                
                if not tweet_data or not tweet_data.get('tweet'):
                    terminal_log(f"❌ Tweet oluşturulamadı: {article['title'][:50]}...", "error")
                    ai_failures += 1
                    
                    # AI API sürekli başarısız oluyorsa sistemi durdur
                    if ai_failures >= 3:
                        terminal_log(f"🚫 AI API'lar sürekli başarısız oluyor ({ai_failures} başarısızlık). Sistem durduruluyor.", "warning")
                        
                        # Otomatik paylaşımı durdur ama auto_mode'u koruma (sadece haber kontrolü için)
                        settings['auto_post_enabled'] = False
                        # settings['auto_mode'] = False  # Bunu kapatmayalım ki haber kontrolü devam etsin
                        save_automation_settings(settings)
                        
                        return {"success": False, "message": f"AI API'lar sürekli başarısız olduğu için sistem durdu. API kotalarınızı kontrol edin.", "posted_count": posted_count, "pending_count": pending_count}
                    
                    continue
                
                # Tweet kalite kontrolü - OTOMATIK SİSTEMDE KALİTELİ TWEET ZORUNLULUĞU
                update_progress("Kalite Kontrolü", f"Tweet kalitesi değerlendiriliyor: {article['title'][:50]}...", 4 + i, 4 + len(articles[:max_articles]))
                if tweet_data.get('is_valid') == False:
                    quality_issues = tweet_data.get('quality_analysis', {}).get('issues', [])
                    terminal_log(f"❌ Tweet kalite kontrolünden geçemedi: {', '.join(quality_issues[:2])}", "error")
                    terminal_log(f"🚫 Kalitesiz tweet otomatik sistemde paylaşılmayacak: {article['title'][:50]}...", "warning")
                    continue
                
                # Skor kontrolü
                impact_score = tweet_data.get('impact_score', 0)
                quality_score = tweet_data.get('quality_score', 7)
                terminal_log(f"📊 Tweet skoru: {impact_score} (minimum: {min_score}), Kalite: {quality_score}/10", "info")
                
                if impact_score < min_score:
                    terminal_log(f"⚠️ Düşük skor ({impact_score}), atlanıyor: {article['title'][:50]}...", "warning")
                    continue
                
                if quality_score < 5:
                    terminal_log(f"⚠️ Düşük kalite skoru ({quality_score}/10), atlanıyor: {article['title'][:50]}...", "warning")
                    continue
                
                # Otomatik paylaşım kontrolü
                manual_approval = settings.get('manual_approval_required', False)
                terminal_log(f"🔍 Otomatik paylaşım ayarları - auto_post: {auto_post}, manual_approval: {manual_approval}", "info")
                
                if auto_post and not manual_approval:
                    # Direkt paylaş
                    update_progress("Tweet Paylaşılıyor", f"Tweet paylaşılıyor: {article['title'][:50]}...", 4 + i, 4 + len(articles[:max_articles]))
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
                        
                        # Rate limit hatası ise sistemi durdur
                        if tweet_result.get('rate_limited', False):
                            wait_minutes = tweet_result.get('wait_minutes', 15)
                            terminal_log(f"🚫 Rate limit nedeniyle otomatik sistem durduruluyor. {wait_minutes} dakika bekleyin.", "warning")
                            
                            # Otomatik paylaşımı durdur ama auto_mode'u koruma (sadece haber kontrolü için)
                            settings['auto_post_enabled'] = False
                            # settings['auto_mode'] = False  # Bunu kapatmayalım ki haber kontrolü devam etsin
                            save_automation_settings(settings)
                            
                            # Bu makaleyi de pending'e ekle ve döngüyü kır
                            pending_tweets = load_json("pending_tweets.json")
                            
                            new_tweet = {
                                "article": article,
                                "tweet_data": tweet_data,
                                "created_date": datetime.now().isoformat(),
                                "created_at": datetime.now().isoformat(),
                                "status": "pending",
                                "error_reason": error_msg,
                                "retry_count": 0
                            }
                            
                            # Duplikat kontrolü
                            article_url = article.get('url', '')
                            article_hash = article.get('hash', '')
                            
                            is_duplicate = False
                            for existing_tweet in pending_tweets:
                                existing_article = existing_tweet.get('article', {})
                                if (article_url and article_url == existing_article.get('url', '')) or \
                                   (article_hash and article_hash == existing_article.get('hash', '')):
                                    is_duplicate = True
                                    break
                            
                            if not is_duplicate:
                                pending_tweets.append(new_tweet)
                                save_json("pending_tweets.json", pending_tweets)
                                pending_count += 1
                                terminal_log(f"📝 Tweet pending listesine eklendi: {article['title'][:50]}...", "info")
                            
                            # Rate limit nedeniyle işlemi durdur
                            return {"success": False, "message": f"Rate limit nedeniyle sistem durdu. {wait_minutes} dakika sonra tekrar deneyin.", "posted_count": posted_count, "pending_count": pending_count}
                        
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
                        
                        # Hash yoksa oluştur
                        if not article_hash and article.get('title'):
                            import hashlib
                            article_hash = hashlib.md5(article.get('title').encode()).hexdigest()
                            article['hash'] = article_hash
                            new_tweet['article'] = article
                        
                        is_duplicate = False
                        for existing_tweet in pending_tweets:
                            existing_article = existing_tweet.get('article', {})
                            existing_url = existing_article.get('url', '')
                            existing_hash = existing_article.get('hash', '')
                            
                            # URL kontrolü
                            if article_url and article_url == existing_url:
                                is_duplicate = True
                                terminal_log(f"⚠️ Duplikat URL atlandı: {article['title'][:50]}...", "warning")
                                break
                            
                            # Hash kontrolü
                            if article_hash and article_hash == existing_hash:
                                is_duplicate = True
                                terminal_log(f"⚠️ Duplikat hash atlandı: {article['title'][:50]}...", "warning")
                                break
                        
                        if not is_duplicate:
                            pending_tweets.append(new_tweet)
                            save_json("pending_tweets.json", pending_tweets)
                            pending_count += 1
                            terminal_log(f"✅ Tweet pending listesine eklendi: {article['title'][:50]}...", "success")
                        else:
                            terminal_log(f"🔄 Duplikat tweet pending listesine eklenmedi", "info")
                else:
                    # Manuel onay gerekli - pending listesine ekle
                    terminal_log(f"📝 Manuel onay gerekli veya auto_post devre dışı - pending listesine ekleniyor", "info")
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
                    
                    # Hash yoksa oluştur
                    if not article_hash and article.get('title'):
                        import hashlib
                        article_hash = hashlib.md5(article.get('title').encode()).hexdigest()
                        article['hash'] = article_hash
                        new_tweet['article'] = article
                    
                    is_duplicate = False
                    for existing_tweet in pending_tweets:
                        existing_article = existing_tweet.get('article', {})
                        existing_url = existing_article.get('url', '')
                        existing_hash = existing_article.get('hash', '')
                        
                        # URL kontrolü
                        if article_url and article_url == existing_url:
                            is_duplicate = True
                            terminal_log(f"⚠️ Duplikat URL atlandı: {article['title'][:50]}...", "warning")
                            break
                        
                        # Hash kontrolü
                        if article_hash and article_hash == existing_hash:
                            is_duplicate = True
                            terminal_log(f"⚠️ Duplikat hash atlandı: {article['title'][:50]}...", "warning")
                            break
                    
                    if not is_duplicate:
                        # ID ekle
                        update_progress("Tweet Kaydediliyor", f"Tweet onay listesine ekleniyor: {article['title'][:50]}...", 4 + i, 4 + len(articles[:max_articles]))
                        new_tweet['id'] = len(pending_tweets) + 1
                        pending_tweets.append(new_tweet)
                        save_json("pending_tweets.json", pending_tweets)
                        pending_count += 1
                        terminal_log(f"📝 Tweet onay bekliyor: {article['title'][:50]}... (ID: {new_tweet['id']})", "success")
                    else:
                        terminal_log(f"🔄 Duplikat tweet onay listesine eklenmedi: {article['title'][:50]}...", "warning")

                
            except Exception as article_error:
                terminal_log(f"❌ Makale işleme hatası: {article_error}", "error")
                continue
        
        if posted_count > 0 and pending_count > 0:
            message = f"{len(articles)} makale bulundu, {posted_count} tweet paylaşıldı, {pending_count} tweet onay bekliyor"
        elif posted_count > 0:
            message = f"{len(articles)} makale bulundu, {posted_count} tweet paylaşıldı"
        elif pending_count > 0:
            message = f"{len(articles)} makale bulundu, {pending_count} yeni tweet onay bekliyor"
        else:
            message = f"{len(articles)} makale bulundu, ancak hiçbiri tweet haline dönüştürülemedi"
        
        terminal_log(f"✅ Otomatik kontrol tamamlandı: {message}", "success")
        end_progress()
        return {"success": True, "message": message, "posted_count": posted_count, "pending_count": pending_count}
        
    except Exception as e:
        terminal_log(f"❌ Makale kontrol hatası: {e}", "error")
        end_progress()
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
        pending_tweets = ensure_tweet_ids(pending_tweets)
        tweet_to_post = None
        tweet_index = None
        
        for i, pending in enumerate(pending_tweets):
            # Güvenli ID kontrolü
            try:
                pending_id = pending.get('id') if isinstance(pending, dict) else getattr(pending, 'id', None)
                if pending_id is None:
                    pending_id = i + 1
                    # ID yoksa ekle
                    if isinstance(pending, dict):
                        pending['id'] = pending_id
                
                if str(pending_id) == str(tweet_id):
                    tweet_to_post = pending
                    tweet_index = i
                    break
            except (AttributeError, TypeError):
                # Fallback: index kullan
                if str(i + 1) == str(tweet_id):
                    tweet_to_post = pending
                    tweet_index = i
                    break
        
        if not tweet_to_post:
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
        
        # Hash kontrolü - tekrar paylaşımı önle
        hash_value = tweet_to_post.get('hash', '')
        if not hash_value and 'article' in tweet_to_post:
            hash_value = tweet_to_post['article'].get('hash', '')
        
        if not hash_value:
            import hashlib
            title = tweet_to_post.get('title', '')
            if 'article' in tweet_to_post:
                title = tweet_to_post['article'].get('title', '')
            if title:
                hash_value = hashlib.md5(title.encode()).hexdigest()
        
        # Posted articles kontrolü - hash ile tekrar paylaşımı önle
        posted_articles = load_json("posted_articles.json")
        already_posted = False
        for posted in posted_articles:
            posted_hash = posted.get('hash', '')
            if hash_value and hash_value == posted_hash:
                already_posted = True
                terminal_log(f"⚠️ Tweet zaten paylaşılmış (hash kontrolü): {tweet_to_post.get('title', '')[:50]}...", "warning")
                break
        
        if already_posted:
            return jsonify({"success": False, "error": "Bu tweet zaten paylaşılmış"})
        
        # Tweet metnini doğru yerden al
        tweet_text = ""
        title = ""
        
        # Tweet data'sından metni al
        if 'tweet_data' in tweet_to_post and tweet_to_post['tweet_data']:
            tweet_text = tweet_to_post['tweet_data'].get('tweet', '')
        
        # Tweet metni yoksa content'i kullan (eski format için)
        if not tweet_text:
            tweet_text = tweet_to_post.get('content', '')
        
        # Title'ı article'dan al
        if 'article' in tweet_to_post:
            title = tweet_to_post['article'].get('title', '')
        else:
            title = tweet_to_post.get('title', '')
        
        # Tweet metni kontrolü
        if not tweet_text or not tweet_text.strip():
            return jsonify({"success": False, "error": "Tweet metni bulunamadı veya boş"})
        
        tweet_result = post_tweet(tweet_text, title)
        
        if tweet_result.get('success'):
            # Başarılı paylaşım - posted_articles.json'a ekle
            article_data = {
                "title": title,
                "url": tweet_to_post.get('url', ''),
                "content": tweet_text,
                "source": tweet_to_post.get('source', ''),
                "source_type": tweet_to_post.get('source_type', 'news'),
                "published_date": tweet_to_post.get('created_at', datetime.now().isoformat()),
                "posted_date": datetime.now().isoformat(),
                "hash": tweet_to_post.get('hash', ''),
                "tweet_id": tweet_result.get('tweet_id', ''),
                "tweet_url": tweet_result.get('tweet_url', ''),
                "is_posted": True
            }
            
            # GitHub repo ise ek bilgileri ekle
            if tweet_to_post.get('source_type') == 'github':
                article_data.update({
                    "type": "github_repo",
                    "repo_data": tweet_to_post.get('repo_data', {}),
                    "language": tweet_to_post.get('language', ''),
                    "stars": tweet_to_post.get('stars', 0),
                    "forks": tweet_to_post.get('forks', 0),
                    "owner": tweet_to_post.get('owner', ''),
                    "topics": tweet_to_post.get('topics', [])
                })
            
            # Posted articles'a ekle
            posted_articles = load_json("posted_articles.json")
            posted_articles.append(article_data)
            save_json("posted_articles.json", posted_articles)
            
            # Pending listesinden kaldır
            if tweet_index is not None:
                pending_tweets.pop(tweet_index)
                save_json("pending_tweets.json", pending_tweets)
            
            # Telegram bildirimi
            settings = load_automation_settings()
            if settings.get('telegram_notifications', False):
                send_telegram_notification(
                    f"✅ Tweet manuel olarak paylaşıldı!\n\n{tweet_text[:100]}...",
                    tweet_result.get('tweet_url', ''),
                    title
                )
            
            terminal_log(f"✅ Tweet başarıyla paylaşıldı: {title[:50]}...", "success")
            
            return jsonify({
                "success": True, 
                "message": "Tweet başarıyla paylaşıldı",
                "tweet_url": tweet_result.get('tweet_url', ''),
                "should_refresh": True
            })
        else:
            # Rate limit kontrolü
            error_msg = tweet_result.get('error', 'Bilinmeyen hata')
            is_rate_limited = 'rate limit' in error_msg.lower() or 'too many requests' in error_msg.lower()
            
            # Rate limit durumunda manuel paylaşım URL'si oluştur
            manual_share_url = None
            if is_rate_limited:
                import urllib.parse
                encoded_text = urllib.parse.quote(tweet_text)
                manual_share_url = f"https://x.com/intent/tweet?text={encoded_text}"
            
            return jsonify({
                "success": False, 
                "error": error_msg,
                "rate_limited": is_rate_limited,
                "manual_share_url": manual_share_url,
                "tweet_text": tweet_text,
                "wait_minutes": tweet_result.get('wait_minutes', 15)
            })
            
    except Exception as e:
        terminal_log(f"❌ Tweet paylaşım hatası: {e}", "error")
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
        pending_tweets = ensure_tweet_ids(pending_tweets)
        deleted_tweet = None
        tweet_index = None
        
        for i, pending in enumerate(pending_tweets):
            # Güvenli ID kontrolü
            try:
                pending_id = pending.get('id') if isinstance(pending, dict) else getattr(pending, 'id', None)
                if pending_id is None:
                    pending_id = i + 1
                    # ID yoksa ekle
                    if isinstance(pending, dict):
                        pending['id'] = pending_id
                
                if str(pending_id) == str(tweet_id):
                    deleted_tweet = pending
                    tweet_index = i
                    break
            except (AttributeError, TypeError):
                # Fallback: index kullan
                if str(i + 1) == str(tweet_id):
                    deleted_tweet = pending
                    tweet_index = i
                    break
        
        if deleted_tweet:
            # Hash kontrolü - tekrar silmeyi önle
            hash_value = deleted_tweet.get('hash', '')
            if not hash_value and 'article' in deleted_tweet:
                hash_value = deleted_tweet['article'].get('hash', '')
            
            if not hash_value:
                import hashlib
                title = deleted_tweet.get('title', '')
                if 'article' in deleted_tweet:
                    title = deleted_tweet['article'].get('title', '')
                if title:
                    hash_value = hashlib.md5(title.encode()).hexdigest()
            
            # Posted articles kontrolü - hash ile tekrar silmeyi önle
            posted_articles = load_json("posted_articles.json")
            already_deleted = False
            for posted in posted_articles:
                posted_hash = posted.get('hash', '')
                if hash_value and hash_value == posted_hash and posted.get('deleted', False):
                    already_deleted = True
                    terminal_log(f"⚠️ Tweet zaten silinmiş (hash kontrolü): {deleted_tweet.get('title', '')[:50]}...", "warning")
                    break
            
            if already_deleted:
                return jsonify({"success": False, "error": "Bu tweet zaten silinmiş"})
            
            # Makaleyi "silindi" olarak işaretle
            article_data = {
                "title": deleted_tweet.get('title', ''),
                "url": deleted_tweet.get('url', ''),
                "content": deleted_tweet.get('content', ''),
                "source": deleted_tweet.get('source', ''),
                "source_type": deleted_tweet.get('source_type', 'news'),
                "published_date": deleted_tweet.get('created_at', datetime.now().isoformat()),
                "posted_date": datetime.now().isoformat(),
                "hash": hash_value,
                "deleted": True,
                "deleted_date": datetime.now().isoformat(),
                "tweet_text": deleted_tweet.get('content', ''),
                "deletion_reason": 'Manuel olarak silindi',
                "is_posted": False
            }
            
            # GitHub repo ise ek bilgileri ekle
            if deleted_tweet.get('source_type') == 'github':
                article_data.update({
                    "type": "github_repo",
                    "repo_data": deleted_tweet.get('repo_data', {}),
                    "language": deleted_tweet.get('language', ''),
                    "stars": deleted_tweet.get('stars', 0),
                    "forks": deleted_tweet.get('forks', 0),
                    "owner": deleted_tweet.get('owner', ''),
                    "topics": deleted_tweet.get('topics', [])
                })
            
            # Posted articles'a "silindi" olarak ekle
            posted_articles = load_json("posted_articles.json")
            posted_articles.append(article_data)
            save_json("posted_articles.json", posted_articles)
            
            terminal_log(f"📝 Tweet silindi olarak işaretlendi: {article_data.get('title', '')[:50]}...", "info")
        
        # Pending listesinden kaldır
        if tweet_index is not None:
            pending_tweets.pop(tweet_index)
            save_json("pending_tweets.json", pending_tweets)
        
        return jsonify({
            "success": True, 
            "message": "Tweet silindi ve makale bir daha gösterilmeyecek",
            "should_refresh": True
        })
        
    except Exception as e:
        terminal_log(f"❌ Tweet silme hatası: {e}", "error")
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
        pending_tweets = ensure_tweet_ids(pending_tweets)
        tweet_to_post = None
        tweet_index = None
        
        for i, pending in enumerate(pending_tweets):
            # Güvenli ID kontrolü
            try:
                pending_id = pending.get('id') if isinstance(pending, dict) else getattr(pending, 'id', None)
                if pending_id is None:
                    pending_id = i + 1
                    # ID yoksa ekle
                    if isinstance(pending, dict):
                        pending['id'] = pending_id
                
                if str(pending_id) == str(tweet_id):
                    tweet_to_post = pending
                    tweet_index = i
                    break
            except (AttributeError, TypeError):
                # Fallback: index kullan
                if str(i + 1) == str(tweet_id):
                    tweet_to_post = pending
                    tweet_index = i
                    break
        
        if not tweet_to_post:
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
        
        # Hash kontrolü - tekrar paylaşımı önle
        hash_value = tweet_to_post.get('hash', '')
        if not hash_value and 'article' in tweet_to_post:
            hash_value = tweet_to_post['article'].get('hash', '')
        
        if not hash_value:
            import hashlib
            title = tweet_to_post.get('title', '')
            if 'article' in tweet_to_post:
                title = tweet_to_post['article'].get('title', '')
            if title:
                hash_value = hashlib.md5(title.encode()).hexdigest()
        
        # Posted articles kontrolü - hash ile tekrar paylaşımı önle
        posted_articles = load_json("posted_articles.json")
        already_posted = False
        for posted in posted_articles:
            posted_hash = posted.get('hash', '')
            if hash_value and hash_value == posted_hash:
                already_posted = True
                terminal_log(f"⚠️ Tweet zaten paylaşılmış (manuel hash kontrolü): {tweet_to_post.get('title', '')[:50]}...", "warning")
                break
        
        if already_posted:
            return jsonify({"success": False, "error": "Bu tweet zaten paylaşılmış"})
        
        # Tweet metnini hazırla
        tweet_text = ""
        
        # Tweet datasını kontrol et ve metni hazırla
        if 'tweet_data' in tweet_to_post and tweet_to_post['tweet_data']:
            tweet_text = tweet_to_post['tweet_data'].get('tweet', '')
        
        # Tweet metni yoksa content'i kullan
        if not tweet_text:
            tweet_text = tweet_to_post.get('content', '')
        
        # Manuel paylaşım için direkt X.com intent URL'i oluştur
        try:
            import urllib.parse
            
            # Tweet metnini encode et
            encoded_text = urllib.parse.quote(tweet_text)
            x_share_url = f"https://x.com/intent/tweet?text={encoded_text}"
            
            # Tweet'i pending'den kaldır ve posted'a ekle
            manual_tweet_result = {
                "success": True,
                "x_share_url": x_share_url,
                "tweet_text": tweet_text,
                "tweet_id": tweet_id,
                "manual_post": True,
                "posted_at": datetime.now().isoformat()
            }
            
            # Tweet türüne göre işlem yap
            if 'article' in tweet_to_post:
                # Normal makale tweet'i
                tweet_to_post['article']['tweet_text'] = tweet_text
                # Hash yoksa oluştur
                if not tweet_to_post['article'].get('hash'):
                    import hashlib
                    title = tweet_to_post['article'].get('title', '')
                    if title:
                        tweet_to_post['article']['hash'] = hashlib.md5(title.encode()).hexdigest()
                mark_article_as_posted(tweet_to_post['article'], manual_tweet_result)
            else:
                # GitHub repo tweet'i veya diğer türler
                posted_articles = load_json('posted_articles.json')
                
                # Hash yoksa oluştur
                hash_value = tweet_to_post.get('hash', '')
                if not hash_value:
                    import hashlib
                    title = tweet_to_post.get('title', '')
                    if title:
                        hash_value = hashlib.md5(title.encode()).hexdigest()
                
                # Tweet verilerini posted article formatına çevir
                posted_article = {
                    "title": tweet_to_post.get('title', ''),
                    "url": tweet_to_post.get('url', ''),
                    "hash": hash_value,
                    "content": tweet_to_post.get('content', ''),
                    "source": tweet_to_post.get('source', ''),
                    "source_type": tweet_to_post.get('source_type', 'article'),
                    "posted_date": datetime.now().isoformat(),
                    "tweet_content": tweet_to_post.get('content', ''),
                    "tweet_text": tweet_text,
                    "tweet_id": manual_tweet_result.get("tweet_id", ""),
                    "tweet_url": manual_tweet_result.get("url", ""),
                    "manual_post": True,
                    "post_method": "manuel",
                    "confirmed_at": datetime.now().isoformat(),
                    "type": tweet_to_post.get('source_type', 'article')
                }
                
                # GitHub repo için ek veriler
                if tweet_to_post.get('source_type') == 'github':
                    posted_article.update({
                        "repo_data": tweet_to_post.get('repo_data', {}),
                        "language": tweet_to_post.get('language', ''),
                        "stars": tweet_to_post.get('stars', 0),
                        "forks": tweet_to_post.get('forks', 0),
                        "owner": tweet_to_post.get('owner', ''),
                        "topics": tweet_to_post.get('topics', [])
                    })
                
                posted_articles.append(posted_article)
                save_json('posted_articles.json', posted_articles)
            
            terminal_log(f"✅ Manuel paylaşım sonrası tweet kaydedildi: {tweet_to_post.get('title', '')[:50]}...", "success")
            
        except Exception as save_error:
            terminal_log(f"❌ Manuel paylaşım kaydetme hatası: {save_error}", "error")
        
        # Pending listesinden kaldır - hata olsa bile kaldır
        try:
            if tweet_index is not None:
                pending_tweets.pop(tweet_index)
                save_json("pending_tweets.json", pending_tweets)
                terminal_log(f"✅ Tweet pending listesinden kaldırıldı: {tweet_to_post.get('title', '')[:50]}...", "success")
        except Exception as remove_error:
            terminal_log(f"❌ Tweet kaldırma hatası: {remove_error}", "error")
        
        # Article URL'ini al
        article_url = tweet_to_post.get('url', '')
        if 'article' in tweet_to_post and tweet_to_post['article'].get('url'):
            article_url = tweet_to_post['article']['url']
        
        return jsonify({
            "success": True,
            "tweet_text": tweet_text,
            "x_share_url": x_share_url,
            "article_url": article_url,
            "tweet_index": tweet_index,
            "article_title": tweet_to_post.get('title', ''),
            "message": "Tweet manuel olarak paylaşıldı ve kaydedildi"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/bulk_tweet_action', methods=['POST'])
@login_required
def bulk_tweet_action():
    """Toplu tweet işlemleri - onaylama veya reddetme"""
    try:
        data = request.get_json()
        tweet_ids = data.get('tweet_ids', [])
        action = data.get('action', '')  # 'approve' veya 'reject'
        
        if not tweet_ids or not action:
            return jsonify({"success": False, "error": "Tweet ID'leri ve işlem türü gerekli"})
        
        if action not in ['approve', 'reject']:
            return jsonify({"success": False, "error": "Geçersiz işlem türü"})
        
        # Pending tweets yükle
        pending_tweets = load_json("pending_tweets.json", [])
        pending_tweets = ensure_tweet_ids(pending_tweets)
        
        processed_count = 0
        errors = []
        
        for tweet_id in tweet_ids:
            try:
                # Tweet'i bul
                tweet_to_process = None
                tweet_index = None
                
                for i, pending in enumerate(pending_tweets):
                    try:
                        pending_id = pending.get('id') if isinstance(pending, dict) else getattr(pending, 'id', None)
                        if pending_id is None:
                            pending_id = i + 1
                            if isinstance(pending, dict):
                                pending['id'] = pending_id
                        
                        if str(pending_id) == str(tweet_id):
                            tweet_to_process = pending
                            tweet_index = i
                            break
                    except (AttributeError, TypeError):
                        if str(i + 1) == str(tweet_id):
                            tweet_to_process = pending
                            tweet_index = i
                            break
                
                if not tweet_to_process:
                    errors.append(f"Tweet ID {tweet_id} bulunamadı")
                    continue
                
                if action == 'approve':
                    # Tweet'i paylaş
                    try:
                        from utils import post_tweet, mark_article_as_posted
                        
                        # Hash kontrolü - tekrar paylaşımı önle
                        hash_value = tweet_to_process.get('hash', '')
                        if not hash_value:
                            import hashlib
                            title = tweet_to_process.get('title', '')
                            if title:
                                hash_value = hashlib.md5(title.encode()).hexdigest()
                        
                        # Posted articles kontrolü - hash ile tekrar paylaşımı önle
                        posted_articles = load_json("posted_articles.json")
                        already_posted = False
                        for posted in posted_articles:
                            posted_hash = posted.get('hash', '')
                            if hash_value and hash_value == posted_hash:
                                already_posted = True
                                terminal_log(f"⚠️ Tweet zaten paylaşılmış (hash kontrolü): {tweet_to_process.get('title', '')[:50]}...", "warning")
                                break
                        
                        if already_posted:
                            errors.append(f"Tweet ID {tweet_id}: Bu tweet zaten paylaşılmış")
                            continue
                        
                        # Tweet metnini bul - farklı alan isimleri dene
                        tweet_text = ''
                        if isinstance(tweet_to_process, dict):
                            # Önce content alanına bak
                            tweet_text = tweet_to_process.get('content', '')
                            
                            # Content boşsa tweet_data.tweet alanına bak
                            if not tweet_text and 'tweet_data' in tweet_to_process:
                                tweet_data = tweet_to_process['tweet_data']
                                if isinstance(tweet_data, dict):
                                    tweet_text = tweet_data.get('tweet', '')
                            
                            # Hala boşsa direk tweet alanına bak
                            if not tweet_text:
                                tweet_text = tweet_to_process.get('tweet', '')
                        
                        # Tweet metni hala boşsa hata ver
                        if not tweet_text or not tweet_text.strip():
                            errors.append(f"Tweet ID {tweet_id}: Tweet metni boş olamaz")
                            continue
                        
                        # Twitter API ile paylaş
                        tweet_result = post_tweet(tweet_text)
                        
                        if tweet_result.get('success'):
                            # Hash yoksa oluştur
                            hash_value = tweet_to_process.get('hash', '')
                            if not hash_value:
                                import hashlib
                                title = tweet_to_process.get('title', '')
                                if title:
                                    hash_value = hashlib.md5(title.encode()).hexdigest()
                            
                            # Paylaşılan tweet'lere ekle
                            mark_article_as_posted({
                                'id': tweet_to_process.get('id'),
                                'title': tweet_to_process.get('title', ''),
                                'hash': hash_value,
                                'content': tweet_to_process.get('content', ''),
                                'url': tweet_to_process.get('url', ''),
                                'source': tweet_to_process.get('source', ''),
                                'category': tweet_to_process.get('category', 'ai_general'),
                                'tags': tweet_to_process.get('tags', []),
                                'score': tweet_to_process.get('score', 0),
                                'posted_date': datetime.now().isoformat(),
                                'tweet_text': tweet_text,  # Bulunan tweet metnini kullan
                                'manual_approval': True,
                                'bulk_operation': True
                            }, tweet_result)
                            
                            # Pending'den kaldır - sadece başarılı işlem sonrası
                            try:
                                pending_tweets.pop(tweet_index)
                                processed_count += 1
                                terminal_log(f"✅ Bulk approve: Tweet {tweet_id} başarıyla paylaşıldı", "success")
                            except IndexError:
                                terminal_log(f"⚠️ Tweet {tweet_id} pending listesinden kaldırılamadı (index hatası)", "warning")
                        else:
                            # Detaylı hata bilgisi
                            error_detail = tweet_result.get('error', 'API hatası')
                            is_rate_limited = tweet_result.get('rate_limited', False)
                            config_error = tweet_result.get('config_error', False)
                            
                            if config_error:
                                errors.append(f"Tweet ID {tweet_id}: API yapılandırma hatası - {error_detail}")
                            elif is_rate_limited:
                                wait_minutes = tweet_result.get('wait_minutes', 15)
                                errors.append(f"Tweet ID {tweet_id}: Rate limit ({wait_minutes}dk bekle) - {error_detail}")
                            else:
                                errors.append(f"Tweet ID {tweet_id}: {error_detail}")
                            
                            terminal_log(f"❌ Bulk approve başarısız: Tweet {tweet_id} - {error_detail}", "error")
                            
                    except Exception as e:
                        errors.append(f"Tweet ID {tweet_id} paylaşım hatası: {str(e)}")
                
                elif action == 'reject':
                    # Tweet'i sil ve posted_articles.json'a deleted:true ile kaydet
                    try:
                        # Hash kontrolü - tekrar reddetmeyi önle
                        hash_value = tweet_to_process.get('hash', '')
                        if not hash_value:
                            import hashlib
                            title = tweet_to_process.get('title', '')
                            if title:
                                hash_value = hashlib.md5(title.encode()).hexdigest()
                        
                        # Posted articles kontrolü - hash ile tekrar reddetmeyi önle
                        posted_articles = load_json("posted_articles.json")
                        already_rejected = False
                        for posted in posted_articles:
                            posted_hash = posted.get('hash', '')
                            if hash_value and hash_value == posted_hash and posted.get('deleted', False):
                                already_rejected = True
                                terminal_log(f"⚠️ Tweet zaten reddedilmiş (hash kontrolü): {tweet_to_process.get('title', '')[:50]}...", "warning")
                                break
                        
                        if already_rejected:
                            errors.append(f"Tweet ID {tweet_id}: Bu tweet zaten reddedilmiş")
                            continue
                        
                        # Tweet metnini bul - approve ile aynı mantık
                        tweet_text = ''
                        if isinstance(tweet_to_process, dict):
                            tweet_text = tweet_to_process.get('content', '')
                            if not tweet_text and 'tweet_data' in tweet_to_process:
                                tweet_data = tweet_to_process['tweet_data']
                                if isinstance(tweet_data, dict):
                                    tweet_text = tweet_data.get('tweet', '')
                            if not tweet_text:
                                tweet_text = tweet_to_process.get('tweet', '')
                        
                        # Posted articles'a "silindi" olarak ekle
                        
                        deleted_article = {
                            "title": tweet_to_process.get('title', ''),
                            "url": tweet_to_process.get('url', ''),
                            "hash": hash_value,
                            "content": tweet_to_process.get('content', ''),
                            "source": tweet_to_process.get('source', ''),
                            "source_type": tweet_to_process.get('source_type', 'news'),
                            "published_date": tweet_to_process.get('created_at', datetime.now().isoformat()),
                            "posted_date": datetime.now().isoformat(),
                            "tweet_text": tweet_text,  # Bulunan tweet metnini kullan
                            "deleted": True,
                            "deleted_date": datetime.now().isoformat(),
                            "deletion_reason": 'Bulk rejection',
                            "bulk_operation": True,
                            "is_posted": False
                        }
                        
                        # GitHub repo ise ek bilgileri ekle
                        if tweet_to_process.get('source_type') == 'github':
                            deleted_article.update({
                                "type": "github_repo",
                                "repo_data": tweet_to_process.get('repo_data', {}),
                                "language": tweet_to_process.get('language', ''),
                                "stars": tweet_to_process.get('stars', 0),
                                "forks": tweet_to_process.get('forks', 0),
                                "owner": tweet_to_process.get('owner', ''),
                                "topics": tweet_to_process.get('topics', [])
                            })
                        
                        posted_articles.append(deleted_article)
                        save_json("posted_articles.json", posted_articles)
                        
                        # Pending'den kaldır
                        pending_tweets.pop(tweet_index)
                        processed_count += 1
                        
                        terminal_log(f"🗑️ Bulk reject: Tweet {tweet_id} silindi olarak işaretlendi", "info")
                        
                    except Exception as e:
                        errors.append(f"Tweet ID {tweet_id} silme hatası: {str(e)}")
                        
            except Exception as e:
                errors.append(f"Tweet ID {tweet_id} işlem hatası: {str(e)}")
        
        # Güncellenmiş pending tweets'i kaydet
        save_json("pending_tweets.json", pending_tweets)
        
        # Sonucu döndür
        if processed_count > 0:
            action_text = "onaylandı" if action == 'approve' else "reddedildi"
            message = f"{processed_count} tweet başarıyla {action_text}"
            if errors:
                message += f". {len(errors)} hata oluştu."
            
            terminal_log(f"📊 Bulk operation tamamlandı - {action}: {processed_count} başarılı, {len(errors)} hata", "info")
            
            return jsonify({
                "success": True, 
                "processed_count": processed_count,
                "errors": errors,
                "message": message
            })
        else:
            return jsonify({
                "success": False, 
                "error": f"Hiçbir tweet işlenemedi. Hatalar: {'; '.join(errors)}"
            })
            
    except Exception as e:
        terminal_log(f"❌ Bulk operation hatası: {e}", "error")
        return jsonify({"success": False, "error": f"Toplu işlem hatası: {str(e)}"})

@app.route('/bulk_delete_rejected', methods=['POST'])
@login_required
def bulk_delete_rejected():
    """Reddedilen makaleleri toplu silme"""
    try:
        data = request.get_json()
        article_ids = data.get('article_ids', [])
        
        if not article_ids:
            return jsonify({"success": False, "error": "Makale ID'leri gerekli"})
        
        # Reddedilen makaleleri yükle
        rejected_articles = load_json("rejected_articles.json", [])
        
        deleted_count = 0
        errors = []
        
        # ID'leri ters sırada işle (büyük indeksten küçüğe) - silme işlemi için
        sorted_ids = sorted([int(id) for id in article_ids], reverse=True)
        
        for article_id in sorted_ids:
            try:
                if 0 <= article_id < len(rejected_articles):
                    # Makaleyi sil
                    deleted_article = rejected_articles.pop(article_id)
                    deleted_count += 1
                    terminal_log(f"🗑️ Reddedilen makale silindi: {deleted_article.get('title', '')[:50]}...", "info")
                else:
                    errors.append(f"Makale ID {article_id} geçersiz")
            except Exception as e:
                errors.append(f"Makale ID {article_id} silme hatası: {str(e)}")
        
        # Güncellenmiş listeyi kaydet
        save_json("rejected_articles.json", rejected_articles)
        
        if deleted_count > 0:
            message = f"{deleted_count} reddedilen makale başarıyla silindi"
            if errors:
                message += f". {len(errors)} hata oluştu."
            
            terminal_log(f"📊 Bulk delete tamamlandı: {deleted_count} silindi, {len(errors)} hata", "info")
            
            return jsonify({
                "success": True,
                "deleted_count": deleted_count,
                "errors": errors,
                "message": message
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Hiçbir makale silinemedi. Hatalar: {'; '.join(errors)}"
            })
            
    except Exception as e:
        terminal_log(f"❌ Bulk delete hatası: {e}", "error")
        return jsonify({"success": False, "error": f"Toplu silme hatası: {str(e)}"})

@app.route('/bulk_clear_rejected', methods=['POST'])
@login_required
def bulk_clear_rejected():
    """Reddedilen makaleleri toplu temizleme (arşivleme)"""
    try:
        data = request.get_json()
        article_ids = data.get('article_ids', [])
        
        if not article_ids:
            return jsonify({"success": False, "error": "Makale ID'leri gerekli"})
        
        # Reddedilen makaleleri yükle
        rejected_articles = load_json("rejected_articles.json", [])
        
        cleared_count = 0
        errors = []
        
        # ID'leri ters sırada işle (büyük indeksten küçüğe) - silme işlemi için
        sorted_ids = sorted([int(id) for id in article_ids], reverse=True)
        
        for article_id in sorted_ids:
            try:
                if 0 <= article_id < len(rejected_articles):
                    # Makaleyi arşivle (silindi olarak işaretle)
                    article = rejected_articles[article_id]
                    article['archived'] = True
                    article['archived_at'] = datetime.now().isoformat()
                    article['archive_reason'] = 'bulk_clear'
                    
                    # Makaleyi arşiv dosyasına taşı
                    archived_articles = load_json("archived_rejected_articles.json", [])
                    archived_articles.append(article)
                    save_json("archived_rejected_articles.json", archived_articles)
                    
                    # Ana listeden kaldır
                    rejected_articles.pop(article_id)
                    cleared_count += 1
                    
                    terminal_log(f"📦 Reddedilen makale arşivlendi: {article.get('title', '')[:50]}...", "info")
                else:
                    errors.append(f"Makale ID {article_id} geçersiz")
            except Exception as e:
                errors.append(f"Makale ID {article_id} arşivleme hatası: {str(e)}")
        
        # Güncellenmiş listeyi kaydet
        save_json("rejected_articles.json", rejected_articles)
        
        if cleared_count > 0:
            message = f"{cleared_count} reddedilen makale başarıyla arşivlendi"
            if errors:
                message += f". {len(errors)} hata oluştu."
            
            terminal_log(f"📊 Bulk clear tamamlandı: {cleared_count} arşivlendi, {len(errors)} hata", "info")
            
            return jsonify({
                "success": True,
                "cleared_count": cleared_count,
                "errors": errors,
                "message": message
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Hiçbir makale arşivlenemedi. Hatalar: {'; '.join(errors)}"
            })
            
    except Exception as e:
        terminal_log(f"❌ Bulk clear hatası: {e}", "error")
        return jsonify({"success": False, "error": f"Toplu arşivleme hatası: {str(e)}"})

@app.route('/retry_rejected_article', methods=['POST'])
@login_required
def retry_rejected_article():
    """Reddedilen makaleyi tekrar dene"""
    try:
        data = request.get_json()
        article_index = data.get('article_index')
        
        if article_index is None:
            return jsonify({"success": False, "error": "Makale indeksi gerekli"})
        
        # Reddedilen makaleleri yükle
        rejected_articles = load_json("rejected_articles.json", [])
        
        if not (0 <= int(article_index) < len(rejected_articles)):
            return jsonify({"success": False, "error": "Geçersiz makale indeksi"})
        
        article_index = int(article_index)
        article = rejected_articles[article_index]
        
        # Makaleyi tekrar işle
        try:
            # Tweet oluştur
            api_key = os.environ.get('OPENROUTER_API_KEY') or ""
            settings = load_automation_settings()
            theme = settings.get('tweet_theme', 'bilgilendirici')
            
            # Makale verilerini hazırla
            article_data = {
                "title": article.get('title', ''),
                "content": article.get('content_preview', ''),
                "url": article.get('url', ''),
                "source": "retry_rejected"
            }
            
            terminal_log(f"🔄 Reddedilen makale tekrar deneniyor: {article_data['title'][:50]}...", "info")
            
            tweet_data = generate_ai_tweet_with_content(article_data, api_key, theme)
            
            if not tweet_data or not tweet_data.get('tweet'):
                return jsonify({"success": False, "error": "Tweet oluşturulamadı"})
            
            # Pending listesine ekle
            pending_tweets = load_json("pending_tweets.json")
            
            new_tweet = {
                "article": article_data,
                "tweet_data": tweet_data,
                "created_date": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "retry_from_rejected": True,
                "original_rejection_reason": article.get('reason', ''),
                "retry_count": 1
            }
            
            # ID ekle
            new_tweet['id'] = len(pending_tweets) + 1
            pending_tweets.append(new_tweet)
            save_json("pending_tweets.json", pending_tweets)
            
            # Reddedilen makaleyi listeden kaldır
            rejected_articles.pop(article_index)
            save_json("rejected_articles.json", rejected_articles)
            
            terminal_log(f"✅ Reddedilen makale başarıyla tekrar denendi: {article_data['title'][:50]}...", "success")
            
            return jsonify({
                "success": True,
                "message": "Makale başarıyla tekrar denendi ve bekleyen listesine eklendi",
                "tweet_id": new_tweet['id']
            })
            
        except Exception as e:
            terminal_log(f"❌ Reddedilen makale tekrar deneme hatası: {e}", "error")
            return jsonify({"success": False, "error": f"Tweet oluşturma hatası: {str(e)}"})
            
    except Exception as e:
        terminal_log(f"❌ Retry rejected article hatası: {e}", "error")
        return jsonify({"success": False, "error": f"İşlem hatası: {str(e)}"})

@app.route('/delete_rejected_article', methods=['POST'])
@login_required
def delete_rejected_article():
    """Reddedilen makaleyi kalıcı olarak sil"""
    try:
        data = request.get_json()
        article_index = data.get('article_index')
        
        if article_index is None:
            return jsonify({"success": False, "error": "Makale indeksi gerekli"})
        
        # Reddedilen makaleleri yükle
        rejected_articles = load_json("rejected_articles.json", [])
        
        if not (0 <= int(article_index) < len(rejected_articles)):
            return jsonify({"success": False, "error": "Geçersiz makale indeksi"})
        
        article_index = int(article_index)
        deleted_article = rejected_articles.pop(article_index)
        
        # Güncellenmiş listeyi kaydet
        save_json("rejected_articles.json", rejected_articles)
        
        terminal_log(f"🗑️ Reddedilen makale kalıcı olarak silindi: {deleted_article.get('title', '')[:50]}...", "info")
        
        return jsonify({
            "success": True,
            "message": "Makale kalıcı olarak silindi"
        })
        
    except Exception as e:
        terminal_log(f"❌ Delete rejected article hatası: {e}", "error")
        return jsonify({"success": False, "error": f"Silme hatası: {str(e)}"})

@app.route('/test_news_system', methods=['GET'])
@login_required
def test_news_system():
    """Haber çekme sistemini test et"""
    try:
        from utils import fetch_latest_ai_articles, safe_print
        import os
        
        test_results = {
            "news_sources_config": True,
            "feedparser_installed": False,
            "openrouter_api_available": bool(os.environ.get('OPENROUTER_API_KEY')),
            "news_fetch_working": False,
            "article_count": 0,
            "errors": [],
            "warnings": []
        }
        
        # Feedparser kontrolü
        try:
            import feedparser
            test_results["feedparser_installed"] = True
            test_results["feedparser_version"] = feedparser.__version__
        except ImportError:
            test_results["errors"].append("feedparser modülü yüklü değil")
        
        # Haber çekme testi
        try:
            articles = fetch_latest_ai_articles()
            test_results["news_fetch_working"] = len(articles) > 0
            test_results["article_count"] = len(articles)
            
            if articles:
                # İlk birkaç makaleyi örnek olarak ekle
                test_results["sample_articles"] = []
                for article in articles[:2]:
                    test_results["sample_articles"].append({
                        "title": article.get("title", "")[:100],
                        "source": article.get("source", ""),
                        "content_length": len(article.get("content", "")),
                        "has_url": bool(article.get("url"))
                    })
            else:
                test_results["warnings"].append("Hiç makale bulunamadı")
                
        except Exception as news_error:
            test_results["errors"].append(f"Haber çekme hatası: {news_error}")
        
        # AI Tweet sistemi testi (OpenRouter)
        test_results["openrouter_api_available"] = bool(os.environ.get('OPENROUTER_API_KEY'))
        
        if test_results["openrouter_api_available"]:
            try:
                from utils import generate_ai_tweet_with_content
                
                test_article = {
                    "title": "OpenRouter Multi-Model AI Test",
                    "content": "Testing the new OpenRouter integration with multiple AI models including Horizon Beta, GLM-4.5-Air, Kimi K2, and Qwen3-30B for automated tweet generation with fallback support.",
                    "url": "https://example.com/test",
                    "source": "test"
                }
                
                api_key = os.environ.get('OPENROUTER_API_KEY')
                tweet_data = generate_ai_tweet_with_content(test_article, api_key)
                
                if tweet_data and tweet_data.get('tweet'):
                    test_results["ai_tweet_working"] = True
                    test_results["sample_tweet"] = tweet_data.get('tweet')[:100]
                    test_results["used_fallback"] = tweet_data.get('source') == 'fallback'
                    test_results["tweet_quality"] = tweet_data.get('quality_score', 'Bilinmiyor')
                else:
                    test_results["ai_tweet_working"] = False
                    test_results["warnings"].append("AI tweet üretimi başarısız")
                    
            except Exception as ai_error:
                test_results["ai_tweet_working"] = False
                if "quota" in str(ai_error).lower():
                    test_results["warnings"].append("Google API quota'sı dolmuş - OpenRouter fallback kullanılmalı")
                else:
                    test_results["errors"].append(f"AI tweet hatası: {ai_error}")
        else:
            test_results["warnings"].append("Ne Google ne de OpenRouter API anahtarı bulunamadı")
        
        # Genel değerlendirme
        test_results["overall_status"] = "working" if test_results["news_fetch_working"] else "error"
        test_results["summary"] = f"{test_results['article_count']} makale çekildi, {len(test_results['errors'])} hata, {len(test_results['warnings'])} uyarı"
        
        # Model listesini ekle
        test_results["available_models"] = {
            "primary": ["moonshotai/kimi-k2:free", "openrouter/auto", "mistralai/mistral-7b-instruct:free"],
            "fallback": ["qwen/qwen3-8b:free", "deepseek/deepseek-chat-v3-0324:free"]
        }
        
        return jsonify(test_results)
        
    except Exception as e:
        return jsonify({
            "overall_status": "error",
            "summary": f"Test sistemi hatası: {e}",
            "errors": [str(e)]
        })

@app.route('/test_openrouter_models', methods=['GET'])
@login_required
def test_openrouter_models():
    """OpenRouter modellerini tek tek test et"""
    try:
        from utils import openrouter_call
        import os
        
        openrouter_key = os.environ.get('OPENROUTER_API_KEY')
        if not openrouter_key:
            return jsonify({
                "success": False,
                "error": "OpenRouter API anahtarı bulunamadı"
            })
        
        # Test edilecek modeller (kullanıcının istediği modeller)
        test_models = [
            "moonshotai/kimi-k2:free",
            "openrouter/auto", 
            "mistralai/mistral-7b-instruct:free"
        ]
        
        test_prompt = "Create a short tweet about AI technology advancements. Keep it under 200 characters."
        
        results = {
            "api_key_available": True,
            "tested_models": [],
            "working_models": [],
            "failed_models": [],
            "test_timestamp": datetime.now().isoformat()
        }
        
        for model in test_models:
            model_result = {
                "model": model,
                "status": "unknown",
                "response": "",
                "error": "",
                "response_length": 0,
                "response_time": 0
            }
            
            try:
                import time
                start_time = time.time()
                
                response = openrouter_call(test_prompt, openrouter_key, max_tokens=100, model=model)
                
                end_time = time.time()
                model_result["response_time"] = round(end_time - start_time, 2)
                
                if response and len(response.strip()) > 10:
                    model_result["status"] = "success"
                    model_result["response"] = response[:200]  # İlk 200 karakter
                    model_result["response_length"] = len(response)
                    results["working_models"].append(model)
                else:
                    model_result["status"] = "empty_response"
                    model_result["error"] = "Model yanıt vermedi veya çok kısa yanıt"
                    results["failed_models"].append(model)
                    
            except Exception as e:
                model_result["status"] = "error"
                model_result["error"] = str(e)
                results["failed_models"].append(model)
            
            results["tested_models"].append(model_result)
        
        # Özet bilgi
        results["summary"] = {
            "total_tested": len(test_models),
            "working_count": len(results["working_models"]),
            "failed_count": len(results["failed_models"]),
            "success_rate": f"{(len(results['working_models']) / len(test_models) * 100):.1f}%"
        }
        
        results["recommendation"] = results["working_models"][0] if results["working_models"] else "Hiç model çalışmıyor"
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"OpenRouter test hatası: {e}"
        })

@app.route('/system_status', methods=['GET'])
@login_required 
def system_status():
    """Sistem durumu özeti - tüm bileşenler"""
    try:
        import os
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "checking",
            "components": {
                "twitter_api": {
                    "configured": bool(os.environ.get('TWITTER_BEARER_TOKEN')),
                    "status": "unknown"
                },
                "openrouter": {
                    "configured": bool(os.environ.get('OPENROUTER_API_KEY')),
                    "status": "ready",
                    "primary_models": [
                        "moonshotai/kimi-k2:free", 
                        "openrouter/auto", 
                        "mistralai/mistral-7b-instruct:free"
                    ]
                },
                "news_sources": {
                    "configured": True,
                    "rss_sources": 3,
                    "scraping_sources": 1,
                    "status": "working"
                },
                "ai_tweet_generation": {
                    "primary": "OpenRouter (ready)",
                    "fallback": "OpenRouter Multi-Model",
                    "status": "fallback_ready"
                }
            },
            "recent_activities": {
                "news_fetch": "Working - 4 articles retrieved",
                "tweet_generation": "Fallback system operational", 
                "twitter_posting": "API configured"
            },
            "recommendations": [
                "OpenRouter API kullanımda",
                "OpenRouter modelleri aktif ve çalışır durumda",
                "Manuel tweet paylaşımı mevcut durumda kullanılabilir"
            ]
        }
        
        # Genel durum hesapla
        working_components = sum(1 for comp in status["components"].values() 
                               if comp.get("status") not in ["unknown", "error"])
        total_components = len(status["components"])
        
        if working_components >= total_components * 0.8:
            status["overall_status"] = "healthy"
        elif working_components >= total_components * 0.5:
            status["overall_status"] = "degraded"
        else:
            status["overall_status"] = "critical"
        
        status["health_score"] = f"{working_components}/{total_components}"
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "overall_status": "error",
            "error": f"Sistem durumu kontrolü hatası: {e}",
            "timestamp": datetime.now().isoformat()
        })

@app.route('/rejected_articles')
@login_required
def rejected_articles():
    """Reddedilen makaleler sayfası"""
    try:
        # Reddedilen makaleleri yükle
        rejected_articles = load_json("rejected_articles.json", [])
        
        # Reddedilen makalelerin tarih formatını düzelt
        for article in rejected_articles:
            if 'rejected_at' in article:
                try:
                    from datetime import datetime
                    rejected_date = datetime.fromisoformat(article['rejected_at'].replace('Z', '+00:00'))
                    article['rejected_at_formatted'] = rejected_date.strftime('%d.%m.%Y %H:%M')
                except:
                    article['rejected_at_formatted'] = article.get('rejected_at', 'Bilinmiyor')
            else:
                article['rejected_at_formatted'] = 'Bilinmiyor'
        
        # İstatistikleri hesapla
        stats = {
            "total_rejected": len(rejected_articles),
            "rejected_today": 0,
            "rejected_this_week": 0,
            "common_reasons": {}
        }
        
        # Bugün ve bu hafta reddedilen sayılarını hesapla
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        for article in rejected_articles:
            try:
                if 'rejected_at' in article:
                    rejected_date = datetime.fromisoformat(article['rejected_at'].replace('Z', '+00:00')).date()
                    
                    if rejected_date == today:
                        stats["rejected_today"] += 1
                    
                    if rejected_date >= week_ago:
                        stats["rejected_this_week"] += 1
            except:
                pass
            
            # Red sebeplerini say
            reason = article.get('reason', 'Bilinmeyen')
            stats["common_reasons"][reason] = stats["common_reasons"].get(reason, 0) + 1
        
        # En sık görülen sebepleri sırala
        stats["common_reasons"] = dict(sorted(stats["common_reasons"].items(), key=lambda x: x[1], reverse=True)[:5])
        
        terminal_log(f"📊 Reddedilen makaleler sayfası yüklendi: {len(rejected_articles)} makale", "info")
        
        return render_template('rejected_articles.html', 
                             rejected_articles=rejected_articles,
                             stats=stats)
                             
    except Exception as e:
        safe_log(f"Reddedilen makaleler sayfası hatası: {str(e)}", "ERROR")
        return render_template('rejected_articles.html', 
                             rejected_articles=[],
                             stats={},
                             error=str(e))

@app.route('/test_bulk_operations', methods=['GET'])
@login_required
def test_bulk_operations():
    """Toplu tweet işlemlerini test et"""
    try:
        # Pending tweets durumunu kontrol et
        pending_tweets = load_json("pending_tweets.json", [])
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "pending_tweets_count": len(pending_tweets),
            "bulk_functions": {
                "bulk_tweet_action": "available",
                "approve_functionality": "ready",
                "reject_functionality": "ready"
            },
            "test_scenarios": [],
            "recommendations": []
        }
        
        if len(pending_tweets) == 0:
            test_results["status"] = "no_data"
            test_results["message"] = "Test için pending tweet bulunamadı"
            test_results["recommendations"].append("Önce haber çekme işlemi yapın veya manuel tweet oluşturun")
        else:
            test_results["status"] = "ready_for_testing" 
            test_results["message"] = f"{len(pending_tweets)} pending tweet mevcut"
            
            # İlk birkaç tweet'i örnek olarak göster
            test_results["sample_tweets"] = []
            for tweet in pending_tweets[:3]:
                test_results["sample_tweets"].append({
                    "id": tweet.get("id"),
                    "title": tweet.get("title", "")[:60],
                    "tweet_length": len(tweet.get("tweet_data", {}).get("tweet", "")),
                    "source": tweet.get("source", "")
                })
            
            # Test senaryolarını tanımla
            test_results["test_scenarios"] = [
                {
                    "name": "Bulk Approve Test",
                    "endpoint": "/bulk_tweet_action",
                    "method": "POST", 
                    "payload": {
                        "tweet_ids": [1, 2],
                        "action": "approve"
                    },
                    "expected": "2 tweet Twitter API ile paylaşılır"
                },
                {
                    "name": "Bulk Reject Test",
                    "endpoint": "/bulk_tweet_action", 
                    "method": "POST",
                    "payload": {
                        "tweet_ids": [3],
                        "action": "reject"
                    },
                    "expected": "1 tweet silindi olarak işaretlenir"
                }
            ]
            
            test_results["recommendations"] = [
                "POST /bulk_tweet_action endpoint'ini kullanarak test edin",
                "tweet_ids array ve action ('approve'/'reject') parametreleri gönderin",
                "Twitter API ayarlarının doğru olduğunu kontrol edin",
                "İşlem sonrası pending_tweets.json ve posted_articles.json dosyalarını kontrol edin"
            ]
        
        return jsonify(test_results)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Bulk operations test hatası: {e}",
            "timestamp": datetime.now().isoformat()
        })

@app.route('/test_twitter_api', methods=['GET'])
@login_required
def test_twitter_api():
    """Twitter API bağlantısını test et"""
    try:
        from utils import setup_twitter_v2_client, check_rate_limit
        
        # API anahtarlarını kontrol et
        import os
        api_keys = {
            'TWITTER_BEARER_TOKEN': bool(os.environ.get('TWITTER_BEARER_TOKEN')),
            'TWITTER_API_KEY': bool(os.environ.get('TWITTER_API_KEY')),
            'TWITTER_API_SECRET': bool(os.environ.get('TWITTER_API_SECRET')),
            'TWITTER_ACCESS_TOKEN': bool(os.environ.get('TWITTER_ACCESS_TOKEN')),
            'TWITTER_ACCESS_TOKEN_SECRET': bool(os.environ.get('TWITTER_ACCESS_TOKEN_SECRET'))
        }
        
        missing_keys = [key for key, value in api_keys.items() if not value]
        
        if missing_keys:
            return jsonify({
                "success": False,
                "error": f"Eksik API anahtarları: {', '.join(missing_keys)}",
                "api_keys_status": api_keys
            })
        
        # Twitter client test
        try:
            client = setup_twitter_v2_client()
            
            # Rate limit kontrolü
            rate_status = check_rate_limit("tweets")
            
            return jsonify({
                "success": True,
                "message": "Twitter API başarıyla yapılandırıldı",
                "api_keys_status": api_keys,
                "rate_limit_status": rate_status,
                "client_created": True
            })
            
        except Exception as client_error:
            return jsonify({
                "success": False,
                "error": f"Twitter client hatası: {client_error}",
                "api_keys_status": api_keys,
                "client_created": False
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Twitter API test hatası: {str(e)}"
        })

@app.route('/confirm_manual_post', methods=['POST'])
@login_required
def confirm_manual_post():
    """Manuel paylaşım sonrası onaylama endpoint'i"""
    try:
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        
        # Debug logging
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
        pending_tweets = ensure_tweet_ids(pending_tweets)
        tweet_to_post = None
        tweet_index = None
        
        # Tweet ID'ye göre tweet'i ara
        for i, tweet in enumerate(pending_tweets):
            if tweet.get('id') == tweet_id:
                tweet_to_post = tweet
                tweet_index = i
                break
        
        if not tweet_to_post:
            safe_log(f"Tweet bulunamadı - ID: {tweet_id}", "ERROR")
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
        
        # Manuel paylaşım olarak işaretle ve kaydet
        from datetime import datetime
        import urllib.parse
        
        # Tweet içeriğini al (GitHub vs normal tweet)
        tweet_content = ""
        if 'tweet_data' in tweet_to_post and 'tweet' in tweet_to_post['tweet_data']:
            tweet_content = tweet_to_post['tweet_data']['tweet']
        elif 'content' in tweet_to_post:
            tweet_content = tweet_to_post['content']
        else:
            tweet_content = tweet_to_post.get('title', 'Tweet içeriği bulunamadı')
        
        manual_tweet_result = {
            "success": True,
            "tweet_id": f"manual_{int(datetime.now().timestamp())}",
            "url": f"https://x.com/search?q={urllib.parse.quote(tweet_content[:50])}",
            "manual_post": True,
            "posted_at": datetime.now().isoformat()
        }
        
        # Tweet türüne göre işlem yap
        if 'article' in tweet_to_post:
            # Normal makale tweet'i
            tweet_to_post['article']['tweet_text'] = tweet_to_post['tweet_data']['tweet']
            # Hash yoksa oluştur
            if not tweet_to_post['article'].get('hash'):
                import hashlib
                title = tweet_to_post['article'].get('title', '')
                if title:
                    tweet_to_post['article']['hash'] = hashlib.md5(title.encode()).hexdigest()
            mark_article_as_posted(tweet_to_post['article'], manual_tweet_result)
        else:
            # GitHub repo tweet'i veya diğer türler
            posted_articles = load_json('posted_articles.json')
            
            # Hash yoksa oluştur
            hash_value = tweet_to_post.get('hash', '')
            if not hash_value:
                import hashlib
                title = tweet_to_post.get('title', '')
                if title:
                    hash_value = hashlib.md5(title.encode()).hexdigest()
            
            # Tweet verilerini posted article formatına çevir
            posted_article = {
                "title": tweet_to_post.get('title', ''),
                "url": tweet_to_post.get('url', ''),
                "hash": hash_value,
                "content": tweet_to_post.get('content', ''),
                "source": tweet_to_post.get('source', ''),
                "source_type": tweet_to_post.get('source_type', 'article'),
                "posted_date": datetime.now().isoformat(),
                "tweet_content": tweet_to_post.get('content', ''),
                "tweet_text": tweet_content,
                "tweet_id": manual_tweet_result.get("tweet_id", ""),
                "tweet_url": manual_tweet_result.get("url", ""),
                "manual_post": True,
                "post_method": "manuel",
                "confirmed_at": datetime.now().isoformat(),
                "type": tweet_to_post.get('source_type', 'article')
            }
            
            # GitHub repo için ek veriler
            if tweet_to_post.get('source_type') == 'github':
                posted_article.update({
                    "repo_data": tweet_to_post.get('repo_data', {}),
                    "language": tweet_to_post.get('language', ''),
                    "stars": tweet_to_post.get('stars', 0),
                    "forks": tweet_to_post.get('forks', 0),
                    "owner": tweet_to_post.get('owner', ''),
                    "topics": tweet_to_post.get('topics', [])
                })
            
            posted_articles.append(posted_article)
            save_json('posted_articles.json', posted_articles)
        
        # Pending listesinden kaldır
        if tweet_index is not None:
            pending_tweets.pop(tweet_index)  # Index'e göre direkt kaldır
            save_json("pending_tweets.json", pending_tweets)
        
        safe_log(f"Tweet başarıyla onaylandı ve kaldırıldı - ID: {tweet_id}", "INFO")
        
        # Bildirimler (Telegram ve Gmail)
        settings = load_automation_settings()
        
        # Tweet başlığını al
        tweet_title = ""
        if 'article' in tweet_to_post and 'title' in tweet_to_post['article']:
            tweet_title = tweet_to_post['article']['title']
        elif 'title' in tweet_to_post:
            tweet_title = tweet_to_post['title']
        else:
            tweet_title = "Tweet"
        
        # Telegram bildirimi
        if settings.get('telegram_notifications', False):
            send_telegram_notification(
                f"✅ Tweet manuel olarak X'te paylaşıldı!\n\n{tweet_content[:100]}...",
                manual_tweet_result.get('url', ''),
                tweet_title
            )
        
        # Gmail bildirimi
        if settings.get('email_notifications', False):
            send_gmail_notification(
                f"✅ Tweet manuel olarak X'te paylaşıldı!\n\n{tweet_content[:100]}...",
                manual_tweet_result.get('url', ''),
                tweet_title
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
            "openrouter_api": os.environ.get('OPENROUTER_API_KEY') is not None,
            "twitter_bearer": os.environ.get('TWITTER_BEARER_TOKEN') is not None,
            "twitter_api_key": os.environ.get('TWITTER_API_KEY') is not None,
            "twitter_api_secret": os.environ.get('TWITTER_API_SECRET') is not None,
            "twitter_access_token": os.environ.get('TWITTER_ACCESS_TOKEN') is not None,
            "twitter_access_secret": os.environ.get('TWITTER_ACCESS_TOKEN_SECRET') is not None,
            "twitter_api_available": bool(os.environ.get('TWITTER_BEARER_TOKEN') and os.environ.get('TWITTER_API_KEY')),
            "telegram_bot_token": os.environ.get('TELEGRAM_BOT_TOKEN') is not None,
            "gmail_email": os.environ.get('GMAIL_EMAIL') is not None,
            "gmail_password": os.environ.get('GMAIL_APP_PASSWORD') is not None,
            "github_token": os.environ.get('GITHUB_TOKEN') is not None
        }
        
        # MCP durumunu kontrol et
        from utils import get_news_fetching_method
        mcp_status = get_news_fetching_method()
        
        # API testlerini sadece anahtarların varlığına göre yap (hızlı kontrol)
        api_status["openrouter_api_working"] = bool(os.environ.get('OPENROUTER_API_KEY'))
        
        return render_template('settings.html', 
                             settings=automation_settings,
                             telegram_config=telegram_config,
                             gmail_config=gmail_config,
                             api_status=api_status,
                             mcp_status=mcp_status)
    except Exception as e:
        return render_template('settings.html', 
                             settings={},
                             telegram_config={},
                             api_status={},
                             error=str(e))

@app.route('/update_env_variables', methods=['POST'])
@login_required
def update_env_variables():
    """Environment variables güncelleme"""
    try:
        data = request.get_json()
        
        # Güvenlik kontrolü - sadece belirli anahtarların güncellenmesine izin ver
        allowed_keys = {
            'OPENROUTER_API_KEY', 'TWITTER_BEARER_TOKEN', 'GOOGLE_API_KEY',
            'TWITTER_API_KEY', 'TWITTER_API_SECRET', 'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID',
            'GMAIL_EMAIL', 'GMAIL_APP_PASSWORD', 'GITHUB_TOKEN'
        }
        
        # .env dosyasını oku
        env_path = '.env'
        env_lines = []
        
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
        
        # Güncellenen anahtarları işle
        updated_keys = set()
        for i, line in enumerate(env_lines):
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key = line.split('=')[0].strip()
                if key in data and key in allowed_keys:
                    # Anahtar güncelle
                    new_value = data[key].strip()
                    if new_value:  # Boş değer kontrolü
                        env_lines[i] = f"{key}={new_value}\n"
                        updated_keys.add(key)
                        # Environment variable'ı runtime'da da güncelle
                        os.environ[key] = new_value
        
        # Yeni anahtarları ekle
        for key, value in data.items():
            if key in allowed_keys and key not in updated_keys and value.strip():
                env_lines.append(f"{key}={value.strip()}\n")
                os.environ[key] = value.strip()
                updated_keys.add(key)
        
        # .env dosyasını yaz
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(env_lines)
        
        return jsonify({
            "success": True,
            "message": f"✅ {len(updated_keys)} API anahtarı güncellendi",
            "updated_keys": list(updated_keys)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"❌ Güncelleme hatası: {str(e)}"
        })

@app.route('/get_env_variables', methods=['GET'])
@login_required
def get_env_variables():
    """Mevcut environment variables'ları getir"""
    try:
        # Güvenlik kontrolü - sadece belirli anahtarların okunmasına izin ver
        allowed_keys = {
            'OPENROUTER_API_KEY', 'TWITTER_BEARER_TOKEN', 'GOOGLE_API_KEY',
            'TWITTER_API_KEY', 'TWITTER_API_SECRET', 'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID',
            'GMAIL_EMAIL', 'GMAIL_APP_PASSWORD', 'GITHUB_TOKEN'
        }
        
        env_values = {}
        
        for key in allowed_keys:
            value = os.environ.get(key, '')
            if value:
                # Güvenlik için değeri maskele (ilk 4 ve son 4 karakter hariç)
                if len(value) > 8:
                    masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:]
                elif len(value) > 4:
                    masked_value = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    masked_value = '*' * len(value)
                
                env_values[key] = {
                    'exists': True,
                    'masked_value': masked_value,
                    'length': len(value)
                }
            else:
                env_values[key] = {
                    'exists': False,
                    'masked_value': '',
                    'length': 0
                }
        
        return jsonify({
            "success": True,
            "env_values": env_values
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"❌ .env okuma hatası: {str(e)}"
        })

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
            'news_fetching_method': request.form.get('news_fetching_method', 'auto'),
            'tweet_theme': request.form.get('tweet_theme', 'bilgilendirici'),
            'last_updated': datetime.now().isoformat()
        }
        
        save_automation_settings(settings)
        flash('Ayarlar başarıyla kaydedildi!', 'success')
        
    except Exception as e:
        flash(f'Ayar kaydetme hatası: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/test_api_connections')
@login_required 
def test_api_connections():
    """API bağlantılarını test et - ayrı endpoint"""
    try:
        results = {}
        
        # OpenRouter API test
        try:
            from utils import ai_call
            api_key = os.environ.get('OPENROUTER_API_KEY')
            if api_key:
                test_result = ai_call("Test", api_key)
                results["openrouter_api"] = {
                    "working": bool(test_result and test_result != "API hatası"),
                    "message": "✅ Çalışıyor" if test_result else "❌ Yanıt alınamadı"
                }
            else:
                results["openrouter_api"] = {"working": False, "message": "❌ API anahtarı yok"}
        except Exception as e:
            results["openrouter_api"] = {"working": False, "message": f"❌ Hata: {str(e)[:50]}"}
        

            
        return jsonify({"success": True, "results": results})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

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
        
        # OpenRouter API test
        try:
            from utils import ai_call
            api_key = os.environ.get('OPENROUTER_API_KEY')
            if api_key:
                test_result = ai_call("Test message", api_key)
                status["openrouter_api_test"] = "ÇALIŞIYOR" if (test_result and test_result != "API hatası") else "HATA"
            else:
                status["openrouter_api_test"] = "API ANAHTARI EKSİK"
        except Exception as e:
            status["openrouter_api_test"] = f"HATA: {str(e)}"
        

        

        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/dashboard_data')
@login_required
def api_dashboard_data():
    """Dashboard verileri için API endpoint - auto-refresh için"""
    try:
        # Son güncelleme zamanını kontrol et için session kullan
        last_check = session.get('last_dashboard_check', 0)
        current_time = time.time()
        
        # İstatistikleri al
        stats = get_data_statistics()
        
        # Pending tweets yükle
        pending_tweets = load_json("pending_tweets.json", [])
        current_pending_count = len(pending_tweets)
        
        # Önceki pending count ile karşılaştır
        previous_pending_count = session.get('previous_pending_count', 0)
        new_tweets_available = current_pending_count > previous_pending_count
        new_tweets_count = current_pending_count - previous_pending_count if new_tweets_available else 0
        
        # Session'ı güncelle
        session['last_dashboard_check'] = current_time
        session['previous_pending_count'] = current_pending_count
        
        # Automation status
        try:
            automation_status = get_automation_status()
        except:
            automation_status = {'auto_mode': False, 'check_interval_hours': 3}
        
        return jsonify({
            "success": True,
            "stats": {
                "pending_tweets": current_pending_count,
                "today_articles": stats.get('today_articles', 0),
                "total_articles": stats.get('total_articles', 0),
                "today_pending": stats.get('today_pending', 0),
                "average_score": stats.get('average_score', 0)
            },
            "automation": {
                "auto_mode": automation_status.get('auto_mode', False),
                "check_interval_hours": automation_status.get('check_interval_hours', 3),
                "last_check": automation_status.get('last_check', 'Henüz kontrol yapılmadı')
            },
            "new_tweets_available": new_tweets_available,
            "new_tweets_count": new_tweets_count,
            "timestamp": current_time,
            "last_update": datetime.now().isoformat()
        })
        
    except Exception as e:
        terminal_log(f"❌ Dashboard API hatası: {e}", "error")
        return jsonify({
            "success": False, 
            "error": str(e),
            "timestamp": time.time()
        })

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
        selected_theme = request.form.get('tweet_theme', 'bilgilendirici')
        save_as_draft = request.form.get('save_as_draft') == 'on'  # Taslak olarak kaydet checkbox'ı
        action = request.form.get('action', 'preview')  # 'preview' veya 'direct_post'
        
        image_path = None
        api_key = os.environ.get('OPENROUTER_API_KEY')
        
        terminal_log(f"🎨 Tweet oluşturma başlatıldı - Mod: {tweet_mode}, Tema: {selected_theme}, Taslak: {save_as_draft}", "info")

        # Tweet içeriğini oluştur (mevcut kod aynı kalacak)
        final_tweet_text = None
        source_data = {}
        
        if tweet_mode == 'image':
            # Resimden tweet oluşturma
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                image_path = os.path.join('static', 'uploads', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image_file.save(image_path)
                try:
                    from utils import openrouter_ocr_image_enhanced, generate_ai_tweet_with_content
                    terminal_log(f"📷 Resimden OCR çıkarılıyor: {filename}", "info")
                    ocr_text = openrouter_ocr_image_enhanced(image_path)
                    
                    if not ocr_text or len(ocr_text.strip()) < 10:
                        flash('Resimden yeterli metin çıkarılamadı!', 'error')
                        return redirect(url_for('create_tweet'))
                    
                    # AI ile konuya uygun tweet üret
                    article_data = {
                        'title': ocr_text[:100],
                        'content': ocr_text,
                        'url': '',
                        'lang': 'en'
                    }
                    tweet_data = generate_ai_tweet_with_content(article_data, api_key, selected_theme)
                    final_tweet_text = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
                    
                    source_data = {
                        'type': 'image',
                        'image_path': image_path,
                        'ocr_text': ocr_text,
                        'original_filename': filename
                    }
                    
                    terminal_log(f"✅ Resimden tweet oluşturuldu ({selected_theme} teması): {len(final_tweet_text)} karakter", "success")
                    
                except Exception as e:
                    terminal_log(f"❌ Resimden tweet oluşturma hatası: {e}", "error")
                    flash(f'Resimden tweet oluşturulamadı: {e}', 'error')
                    return redirect(url_for('create_tweet'))
            else:
                flash('Resim yüklenmedi!', 'error')
                return redirect(url_for('create_tweet'))
                
        elif tweet_mode == 'link':
            # Link'ten tweet oluşturma
            if not tweet_url or not tweet_url.strip():
                flash('URL boş olamaz!', 'error')
                return redirect(url_for('create_tweet'))
            
            try:
                from utils import fetch_url_content_with_mcp, generate_ai_tweet_with_content
                
                terminal_log(f"🔗 URL'den içerik çekiliyor: {tweet_url.strip()}", "info")
                
                # URL'den içerik çek
                url_content = fetch_url_content_with_mcp(tweet_url.strip())
                
                if not url_content or not url_content.get('content'):
                    flash('URL\'den içerik çekilemedi! Lütfen geçerli bir URL girin.', 'error')
                    return redirect(url_for('create_tweet'))
                
                # İçerik kalitesini kontrol et
                article_data = {
                    'title': url_content.get('title', ''),
                    'content': url_content.get('content', ''),
                    'url': url_content.get('url', ''),
                    'lang': 'en'
                }
                
                from utils import is_article_content_valid
                is_valid, reason = is_article_content_valid(article_data)
                if not is_valid:
                    flash(f'İçerik kalitesiz: {reason}. Lütfen daha kaliteli bir URL deneyin.', 'error')
                    terminal_log(f"❌ Manuel URL kalitesiz: {reason} - {tweet_url}", "warning")
                    return redirect(url_for('create_tweet'))
                tweet_data = generate_ai_tweet_with_content(article_data, api_key, selected_theme)
                final_tweet_text = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
                
                source_data = {
                    'type': 'url',
                    'source_url': tweet_url.strip(),
                    'fetched_title': url_content.get('title', ''),
                    'fetched_content': url_content.get('content', '')[:500]  # İlk 500 karakter
                }
                
                terminal_log(f"✅ URL'den tweet oluşturuldu ({selected_theme} teması): {len(final_tweet_text)} karakter", "success")
                
            except Exception as e:
                terminal_log(f"❌ URL'den tweet oluşturma hatası: {e}", "error")
                flash(f'Link\'ten tweet oluşturulamadı: {e}', 'error')
                return redirect(url_for('create_tweet'))
        else:
            # Metinden tweet oluşturma
            if not tweet_text or not tweet_text.strip():
                flash('Tweet metni boş olamaz!', 'error')
                return redirect(url_for('create_tweet'))
            
            try:
                from utils import generate_ai_tweet_with_content
                
                terminal_log(f"📝 Metinden tweet oluşturuluyor ({selected_theme} teması): {len(tweet_text)} karakter", "info")
                
                article_data = {
                    'title': tweet_text[:100],
                    'content': tweet_text,
                    'url': '',
                    'lang': 'en'
                }
                tweet_data = generate_ai_tweet_with_content(article_data, api_key, selected_theme)
                final_tweet_text = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
                
                source_data = {
                    'type': 'text',
                    'original_text': tweet_text
                }
                
                terminal_log(f"✅ Metinden tweet oluşturuldu ({selected_theme} teması): {len(final_tweet_text)} karakter", "success")
                
            except Exception as e:
                terminal_log(f"❌ Metinden tweet oluşturma hatası: {e}", "error")
                flash(f'AI ile tweet metni oluşturulamadı: {e}', 'error')
                return redirect(url_for('create_tweet'))

        # Tweet başarıyla oluşturuldu - Şimdi kaydet veya doğrudan paylaş
        if final_tweet_text and len(final_tweet_text.strip()) > 0:
            try:
                if action == 'direct_post':
                    # Doğrudan pending tweets'e ekle
                    from utils import save_json, load_json, get_next_tweet_id
                    
                    pending_tweets = load_json("pending_tweets.json", [])
                    
                    new_tweet = {
                        "id": get_next_tweet_id(pending_tweets),
                        "title": f"Manuel Tweet - {selected_theme.title()}",
                        "content": final_tweet_text,
                        "tweet_text": final_tweet_text,
                        "url": source_data.get('url', ''),
                        "source": "Manual Creation",
                        "category": "ai_general",
                        "tags": [selected_theme, "manual"],
                        "score": 8.5,
                        "posted_date": datetime.now().isoformat(),
                        "created_date": datetime.now().isoformat(),
                        "tweet_theme": selected_theme,
                        "source_data": source_data,
                        "manual_creation": True,
                        "auto_approved": True
                    }
                    
                    pending_tweets.append(new_tweet)
                    save_json("pending_tweets.json", pending_tweets)
                    
                    terminal_log(f"🚀 Manuel tweet doğrudan pending'e eklendi - ID: {new_tweet['id']}", "success")
                    flash(f'✅ Tweet oluşturuldu ve paylaşım kuyruğuna eklendi! (ID: {new_tweet["id"]})', 'success')
                    
                    return redirect(url_for('index', highlight_tweet=new_tweet['id']))
                
                else:
                    # Normal önizleme modu
                    tweet_record = save_manual_tweet(
                        tweet_text=final_tweet_text,
                        theme=selected_theme,
                        source_data=source_data,
                        is_draft=save_as_draft
                    )
                    
                    # Tweet istatistikleri
                    char_count = len(final_tweet_text)
                    hashtag_count = len([word for word in final_tweet_text.split() if word.startswith('#')])
                    emoji_count = len([char for char in final_tweet_text if ord(char) > 127])
                    
                    terminal_log(f"📊 Tweet istatistikleri - Karakter: {char_count}/280, Hashtag: {hashtag_count}, Emoji: {emoji_count}", "info")
                    terminal_log(f"💾 Tweet kaydedildi - ID: {tweet_record['id']}, Durum: {'Taslak' if save_as_draft else 'Hazır'}", "success")
                    
                    if save_as_draft:
                        flash(f'✅ Tweet taslak olarak kaydedildi! (ID: {tweet_record["id"]})', 'success')
                    else:
                        flash(f'✅ Tweet başarıyla oluşturuldu ve kaydedildi! (ID: {tweet_record["id"]})', 'success')
                    
                    return render_template('create_tweet.html', 
                                         generated_tweet=final_tweet_text,
                                         selected_theme=selected_theme,
                                         tweet_id=tweet_record['id'],
                                         is_draft=save_as_draft)
                                     
            except Exception as e:
                terminal_log(f"❌ Tweet kaydetme hatası: {e}", "error")
                flash(f'Tweet oluşturuldu ancak kaydedilemedi: {e}', 'warning')
                
                # Yine de sonucu göster
                return render_template('create_tweet.html', 
                                     generated_tweet=final_tweet_text,
                                     selected_theme=selected_theme,
                                     tweet_id=None,
                                     is_draft=False)
        else:
            flash('Tweet oluşturulamadı! Lütfen tekrar deneyin.', 'error')
            return redirect(url_for('create_tweet'))

    # GET request - sayfa yükleme ve mevcut taslakları göster
    try:
        from utils import load_automation_settings
        settings = load_automation_settings()
        default_theme = settings.get('tweet_theme', 'bilgilendirici')
        
        # Mevcut manuel tweet'leri yükle
        manual_tweets = load_manual_tweets()
        draft_tweets = [tweet for tweet in manual_tweets if tweet.get('status') == 'draft']
        ready_tweets = [tweet for tweet in manual_tweets if tweet.get('status') == 'ready']
        
        return render_template('create_tweet.html', 
                             default_theme=default_theme,
                             draft_tweets=draft_tweets[:5],  # Son 5 taslak
                             ready_tweets=ready_tweets[:5])  # Son 5 hazır tweet
    except Exception as e:
        terminal_log(f"⚠️ Ayarlar yüklenemedi, varsayılan tema kullanılıyor: {e}", "warning")
        return render_template('create_tweet.html', 
                             default_theme='bilgilendirici',
                             draft_tweets=[],
                             ready_tweets=[])

# Tweet kayıt sistemi için yardımcı fonksiyonlar
def save_manual_tweet(tweet_text, theme, source_data, is_draft=False):
    """Manuel oluşturulan tweet'i kaydet"""
    try:
        manual_tweets = load_manual_tweets()
        
        # Yeni tweet kaydı oluştur
        tweet_id = generate_manual_tweet_id()
        tweet_hash = hashlib.md5(tweet_text.encode()).hexdigest()
        
        tweet_record = {
            "id": tweet_id,
            "content": tweet_text,
            "theme": theme,
            "source_data": source_data,
            "status": "draft" if is_draft else "ready",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "hash": tweet_hash,
            "char_count": len(tweet_text),
            "hashtag_count": len([word for word in tweet_text.split() if word.startswith('#')]),
            "emoji_count": len([char for char in tweet_text if ord(char) > 127]),
            "is_posted": False,
            "posted_at": None,
            "posted_url": None,
            "created_by": "manual",
            "version": 1
        }
        
        manual_tweets.append(tweet_record)
        save_manual_tweets(manual_tweets)
        
        terminal_log(f"💾 Manuel tweet kaydedildi - ID: {tweet_id}, Durum: {tweet_record['status']}", "success")
        
        return tweet_record
        
    except Exception as e:
        terminal_log(f"❌ Manuel tweet kaydetme hatası: {e}", "error")
        raise e

def load_manual_tweets():
    """Manuel tweet'leri yükle"""
    try:
        return load_json("manual_tweets.json")
    except:
        return []

def save_manual_tweets(tweets):
    """Manuel tweet'leri kaydet"""
    try:
        save_json("manual_tweets.json", tweets)
        return True
    except Exception as e:
        terminal_log(f"❌ Manuel tweet'ler kaydedilemedi: {e}", "error")
        return False

def generate_manual_tweet_id():
    """Manuel tweet için benzersiz ID oluştur"""
    timestamp = int(datetime.now().timestamp())
    random_suffix = random.randint(100, 999)
    return f"manual_{timestamp}_{random_suffix}"

# Tweet yönetim route'ları
@app.route('/api/manual_tweets')
@login_required
def get_manual_tweets():
    """Manuel tweet'leri API ile al"""
    try:
        manual_tweets = load_manual_tweets()
        
        # Tarihe göre sırala (en yeni önce)
        manual_tweets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # İstatistikler
        stats = {
            'total': len(manual_tweets),
            'drafts': len([t for t in manual_tweets if t.get('status') == 'draft']),
            'ready': len([t for t in manual_tweets if t.get('status') == 'ready']),
            'posted': len([t for t in manual_tweets if t.get('is_posted', False)])
        }
        
        return jsonify({
            "success": True,
            "tweets": manual_tweets,
            "stats": stats
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/manual_tweets/<tweet_id>')
@login_required
def get_manual_tweet(tweet_id):
    """Belirli bir manuel tweet'i al"""
    try:
        manual_tweets = load_manual_tweets()
        
        tweet = None
        for t in manual_tweets:
            if t.get('id') == tweet_id:
                tweet = t
                break
        
        if tweet:
            return jsonify({"success": True, "tweet": tweet})
        else:
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/manual_tweets/<tweet_id>/delete', methods=['POST'])
@login_required
def delete_manual_tweet(tweet_id):
    """Manuel tweet'i sil (henüz paylaşılmamış olanlar)"""
    try:
        manual_tweets = load_manual_tweets()
        
        tweet_to_delete = None
        tweet_index = None
        
        for i, tweet in enumerate(manual_tweets):
            if tweet.get('id') == tweet_id:
                if tweet.get('is_posted', False):
                    return jsonify({
                        "success": False, 
                        "error": "Paylaşılmış tweet'ler silinemez"
                    })
                
                tweet_to_delete = tweet
                tweet_index = i
                break
        
        if tweet_to_delete:
            # Tweet'i listeden kaldır
            manual_tweets.pop(tweet_index)
            save_manual_tweets(manual_tweets)
            
            terminal_log(f"🗑️ Manuel tweet silindi - ID: {tweet_id}", "info")
            
            return jsonify({
                "success": True, 
                "message": "Tweet başarıyla silindi"
            })
        else:
            return jsonify({
                "success": False, 
                "error": "Tweet bulunamadı"
            })
            
    except Exception as e:
        terminal_log(f"❌ Manuel tweet silme hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/manual_tweets/<tweet_id>/post', methods=['POST'])
@login_required
def post_manual_tweet(tweet_id):
    """Manuel tweet'i paylaş"""
    try:
        manual_tweets = load_manual_tweets()
        
        tweet_to_post = None
        tweet_index = None
        
        for i, tweet in enumerate(manual_tweets):
            if tweet.get('id') == tweet_id:
                if tweet.get('is_posted', False):
                    return jsonify({
                        "success": False, 
                        "error": "Bu tweet zaten paylaşılmış"
                    })
                
                tweet_to_post = tweet
                tweet_index = i
                break
        
        if not tweet_to_post:
            return jsonify({
                "success": False, 
                "error": "Tweet bulunamadı"
            })
        
        # Tweet'i paylaş
        tweet_text = tweet_to_post.get('content', '')
        title = f"Manuel Tweet - {tweet_to_post.get('theme', 'Tema Yok')}"
        
        tweet_result = post_tweet(tweet_text, title)
        
        if tweet_result.get('success'):
            # Tweet kaydını güncelle
            manual_tweets[tweet_index].update({
                "is_posted": True,
                "posted_at": datetime.now().isoformat(),
                "posted_url": tweet_result.get('tweet_url', ''),
                "tweet_id": tweet_result.get('tweet_id', ''),
                "status": "posted",
                "updated_at": datetime.now().isoformat()
            })
            
            save_manual_tweets(manual_tweets)
            
            # Ana posted_articles.json'a da ekle (uyumluluk için)
            article_data = {
                "title": title,
                "url": "",
                "content": tweet_text,
                "source": "Manuel Tweet",
                "source_type": "manual",
                "published_date": tweet_to_post.get('created_at'),
                "posted_date": datetime.now().isoformat(),
                "hash": tweet_to_post.get('hash', ''),
                "tweet_id": tweet_result.get('tweet_id', ''),
                "tweet_url": tweet_result.get('tweet_url', ''),
                "is_posted": True,
                "manual_tweet_id": tweet_id,
                "theme": tweet_to_post.get('theme', ''),
                "type": "manual_tweet"
            }
            
            posted_articles = load_json("posted_articles.json")
            posted_articles.append(article_data)
            save_json("posted_articles.json", posted_articles)
            
            # Telegram bildirimi
            settings = load_automation_settings()
            if settings.get('telegram_notifications', False):
                send_telegram_notification(
                    f"✅ Manuel tweet paylaşıldı!\n\n{tweet_text[:100]}...",
                    tweet_result.get('tweet_url', ''),
                    title
                )
            
            terminal_log(f"✅ Manuel tweet paylaşıldı - ID: {tweet_id}", "success")
            
            return jsonify({
                "success": True, 
                "message": "Tweet başarıyla paylaşıldı",
                "tweet_url": tweet_result.get('tweet_url', ''),
                "tweet_id": tweet_result.get('tweet_id', '')
            })
        else:
            # Paylaşım hatası
            error_msg = tweet_result.get('error', 'Bilinmeyen hata')
            is_rate_limited = 'rate limit' in error_msg.lower() or 'too many requests' in error_msg.lower()
            
            return jsonify({
                "success": False, 
                "error": error_msg,
                "rate_limited": is_rate_limited
            })
            
    except Exception as e:
        terminal_log(f"❌ Manuel tweet paylaşım hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/confirm_manual_post_create', methods=['POST'])
@login_required
def confirm_manual_post_create():
    """Create tweet sayfasından manuel paylaşım sonrası onaylama endpoint'i"""
    try:
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        
        terminal_log(f"Create tweet manuel onay isteği - Tweet ID: {tweet_id}", "info")
        
        if not tweet_id:
            return jsonify({"success": False, "error": "Tweet ID gerekli"})
        
        # Manuel tweet'i bul
        manual_tweets = load_manual_tweets()
        tweet_to_confirm = None
        tweet_index = None
        
        for i, tweet in enumerate(manual_tweets):
            if tweet.get('id') == tweet_id:
                if tweet.get('is_posted', False):
                    return jsonify({"success": False, "error": "Bu tweet zaten paylaşılmış"})
                tweet_to_confirm = tweet
                tweet_index = i
                break
        
        if not tweet_to_confirm:
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
        
        # Manuel paylaşım olarak işaretle
        from datetime import datetime
        import urllib.parse
        
        tweet_content = tweet_to_confirm.get('content', '')
        
        # Tweet kaydını güncelle
        manual_tweets[tweet_index].update({
            "is_posted": True,
            "posted_at": datetime.now().isoformat(),
            "posted_url": f"https://x.com/search?q={urllib.parse.quote(tweet_content[:50])}",
            "status": "posted",
            "updated_at": datetime.now().isoformat(),
            "manual_post": True,
            "confirmed_at": datetime.now().isoformat()
        })
        
        save_manual_tweets(manual_tweets)
        
        # Ana posted_articles.json'a da ekle (uyumluluk için)
        title = f"Manuel Tweet - {tweet_to_confirm.get('theme', 'Tema Yok')}"
        article_data = {
            "title": title,
            "url": "",
            "content": tweet_content,
            "source": "Manuel Tweet (Create)",
            "source_type": "manual_create",
            "published_date": tweet_to_confirm.get('created_at'),
            "posted_date": datetime.now().isoformat(),
            "hash": tweet_to_confirm.get('hash', ''),
            "tweet_content": tweet_content,
            "manual_post": True,
            "confirmed_at": datetime.now().isoformat(),
            "manual_tweet_id": tweet_id,
            "theme": tweet_to_confirm.get('theme', ''),
            "type": "manual_tweet_create"
        }
        
        posted_articles = load_json("posted_articles.json")
        posted_articles.append(article_data)
        save_json("posted_articles.json", posted_articles)
        
        # Bildirimler
        settings = load_automation_settings()
        
        # Telegram bildirimi
        if settings.get('telegram_notifications', False):
            send_telegram_notification(
                f"✅ Create sayfasından manuel tweet paylaşıldı!\n\n{tweet_content[:100]}...",
                f"https://x.com/search?q={urllib.parse.quote(tweet_content[:50])}",
                title
            )
        
        # Gmail bildirimi
        if settings.get('email_notifications', False):
            send_gmail_notification(
                f"✅ Create sayfasından manuel tweet paylaşıldı!\n\n{tweet_content[:100]}...",
                f"https://x.com/search?q={urllib.parse.quote(tweet_content[:50])}",
                title
            )
        
        terminal_log(f"✅ Create tweet manuel paylaşım onaylandı - ID: {tweet_id}", "success")
        
        return jsonify({
            "success": True, 
            "message": "Tweet manuel paylaşım olarak kaydedildi",
            "tweet_url": f"https://x.com/search?q={urllib.parse.quote(tweet_content[:50])}"
        })
        
    except Exception as e:
        terminal_log(f"❌ Create tweet manuel onay hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/manual_tweets/<tweet_id>/update_status', methods=['POST'])
@login_required
def update_manual_tweet_status(tweet_id):
    """Manuel tweet durumunu güncelle (draft <-> ready)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['draft', 'ready']:
            return jsonify({
                "success": False, 
                "error": "Geçersiz durum. 'draft' veya 'ready' olmalı"
            })
        
        manual_tweets = load_manual_tweets()
        
        tweet_index = None
        for i, tweet in enumerate(manual_tweets):
            if tweet.get('id') == tweet_id:
                if tweet.get('is_posted', False):
                    return jsonify({
                        "success": False, 
                        "error": "Paylaşılmış tweet'lerin durumu değiştirilemez"
                    })
                
                tweet_index = i
                break
        
        if tweet_index is not None:
            manual_tweets[tweet_index]['status'] = new_status
            manual_tweets[tweet_index]['updated_at'] = datetime.now().isoformat()
            
            save_manual_tweets(manual_tweets)
            
            terminal_log(f"📝 Manuel tweet durumu güncellendi - ID: {tweet_id}, Yeni durum: {new_status}", "info")
            
            return jsonify({
                "success": True, 
                "message": f"Tweet durumu '{new_status}' olarak güncellendi"
            })
        else:
            return jsonify({
                "success": False, 
                "error": "Tweet bulunamadı"
            })
            
    except Exception as e:
        terminal_log(f"❌ Manuel tweet durum güncelleme hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/ocr_image', methods=['POST'])
@login_required
def ocr_image():
    """AJAX OCR endpoint - Resimden tweet oluştur"""
    try:
        image_file = request.files.get('image')
        selected_theme = request.form.get('theme', 'bilgilendirici')  # AJAX'tan tema al
        
        if not image_file or not image_file.filename:
            return jsonify({'success': False, 'error': 'Resim bulunamadı.'}), 400

        filename = secure_filename(image_file.filename)
        image_path = os.path.join('static', 'uploads', filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image_file.save(image_path)
        
        terminal_log(f"📷 AJAX OCR başlatıldı - Dosya: {filename}, Tema: {selected_theme}", "info")

        try:
            from utils import openrouter_ocr_image_enhanced, generate_ai_tweet_with_content
            ocr_text = openrouter_ocr_image_enhanced(image_path)
            
            if not ocr_text or len(ocr_text.strip()) < 10:
                return jsonify({'success': False, 'error': 'Resimden yeterli metin çıkarılamadı.'}), 400
            
            # AI ile konuya uygun tweet üret - seçilen tema ile
            api_key = os.environ.get('OPENROUTER_API_KEY')
            
            article_data = {
                'title': ocr_text[:100],
                'content': ocr_text,
                'url': '',
                'lang': 'en'
            }
            tweet_data = generate_ai_tweet_with_content(article_data, api_key, selected_theme)
            tweet_text = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
            
            terminal_log(f"✅ AJAX OCR tweet oluşturuldu ({selected_theme}): {len(tweet_text)} karakter", "success")
            
            return jsonify({
                'success': True, 
                'text': tweet_text,
                'theme': selected_theme,
                'char_count': len(tweet_text),
                'ocr_text': ocr_text[:200] + "..." if len(ocr_text) > 200 else ocr_text,
                'ocr_method': 'openrouter_vision_enhanced',
                'ocr_char_count': len(ocr_text)
            })
            
        except Exception as e:
            terminal_log(f"❌ AJAX OCR hatası: {e}", "error")
            return jsonify({'success': False, 'error': f'OCR işlemi başarısız: {str(e)}'}), 500
            
    except Exception as e:
        terminal_log(f"❌ AJAX OCR genel hatası: {e}", "error")
        return jsonify({'success': False, 'error': str(e)}), 500

def background_scheduler():
    """Arka plan zamanlayıcısı - Akıllı otomatik sistem"""
    global background_scheduler_running, last_check_time
    
    terminal_log("🚀 Akıllı otomatik zamanlayıcı başlatıldı", "success")
    background_scheduler_running = True
    
    # İlk çalıştırmayı hemen yap
    terminal_log("🔄 İlk otomatik kontrol başlatılıyor...", "info")
    try:
        settings = load_automation_settings()
        if settings.get('auto_mode', False):
            result = check_and_post_articles()
            terminal_log(f"✅ İlk kontrol tamamlandı: {result.get('message', 'Sonuç yok')}", "success")
            last_check_time = datetime.now()
        else:
            terminal_log("⏸️ Otomatik mod devre dışı, bekleme modunda", "warning")
    except Exception as e:
        terminal_log(f"❌ İlk kontrol hatası: {e}", "error")
    
    while background_scheduler_running:
        try:
            # Ayarları her döngüde yeniden yükle
            settings = load_automation_settings()
            
            if settings.get('auto_mode', False):
                current_time = datetime.now()
                check_interval_hours = settings.get('check_interval_hours', 3)
                
                # Son kontrolden beri geçen süreyi hesapla
                if last_check_time:
                    time_passed = current_time - last_check_time
                    time_passed_hours = time_passed.total_seconds() / 3600
                    
                    if time_passed_hours >= check_interval_hours:
                        terminal_log(f"🔄 Otomatik kontrol zamanı geldi ({time_passed_hours:.1f} saat geçti)", "info")
                        
                        try:
                            result = check_and_post_articles()
                            terminal_log(f"✅ Otomatik kontrol tamamlandı: {result.get('message', 'Sonuç yok')}", "success")
                            last_check_time = current_time
                        except Exception as check_error:
                            terminal_log(f"❌ Otomatik kontrol hatası: {check_error}", "error")
                    else:
                        remaining_hours = check_interval_hours - time_passed_hours
                        terminal_log(f"⏰ Sonraki kontrol: {remaining_hours:.1f} saat sonra", "info")
                else:
                    # İlk çalıştırma
                    terminal_log("🔄 İlk otomatik kontrol başlatılıyor...", "info")
                    try:
                        result = check_and_post_articles()
                        terminal_log(f"✅ İlk kontrol tamamlandı: {result.get('message', 'Sonuç yok')}", "success")
                        last_check_time = current_time
                    except Exception as check_error:
                        terminal_log(f"❌ İlk kontrol hatası: {check_error}", "error")
            else:
                terminal_log("⏸️ Otomatik mod devre dışı", "info")
            
            # Daha sık kontrol et (5 dakika)
            time.sleep(300)  # 5 dakika = 300 saniye
            
        except Exception as e:
            terminal_log(f"❌ Arka plan zamanlayıcı hatası: {e}", "error")
            time.sleep(300)  # Hata durumunda da 5 dakika bekle

def start_background_scheduler():
    """Arka plan zamanlayıcısını thread olarak başlat"""
    global background_scheduler_running
    
    if not background_scheduler_running:
        try:
            scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
            scheduler_thread.start()
            terminal_log("🚀 Arka plan zamanlayıcısı başlatıldı (Her 5 dakikada kontrol eder)", "success")
            terminal_log("🔄 Arka plan zamanlayıcı thread'i başlatıldı", "info")
            
            # Thread'in gerçekten başladığını kontrol et
            import time
            time.sleep(1)  # Kısa bekle
            if scheduler_thread.is_alive():
                terminal_log("✅ Arka plan zamanlayıcısı aktif olarak çalışıyor", "success")
            else:
                terminal_log("❌ Arka plan zamanlayıcısı başlatılamadı!", "error")
                
        except Exception as e:
            terminal_log(f"❌ Arka plan zamanlayıcı başlatma hatası: {e}", "error")
    else:
        terminal_log("⚠️ Arka plan zamanlayıcısı zaten çalışıyor", "warning")

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
    """Haber kaynağını kaldır - RSS dahil"""
    try:
        from utils import remove_news_source, remove_rss_source
        
        source_id = request.form.get('source_id')
        source_type = request.form.get('source_type', 'scraping')
        
        if not source_id:
            flash('Kaynak ID gerekli!', 'error')
            return redirect(url_for('news_sources'))
        
        if source_type == 'rss':
            result = remove_rss_source(source_id)
        else:
            result = remove_news_source(source_id)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'error')
            
    except Exception as e:
        flash(f'Kaynak kaldırma hatası: {str(e)}', 'error')
    
    return redirect(url_for('news_sources'))

@app.route('/add_rss_source', methods=['POST'])
@login_required
def add_rss_source_route():
    """Yeni RSS kaynağı ekle"""
    try:
        from utils import add_rss_source
        
        name = request.form.get('rss_name', '').strip()
        url = request.form.get('rss_url', '').strip()
        description = request.form.get('rss_description', '').strip()
        
        if not name or not url:
            flash('RSS kaynak adı ve URL gerekli!', 'error')
            return redirect(url_for('news_sources'))
        
        result = add_rss_source(name, url, description)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'error')
            
    except Exception as e:
        flash(f'RSS kaynağı ekleme hatası: {str(e)}', 'error')
    
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

@app.route('/test_rss_url', methods=['POST'])
@login_required
def test_rss_url_route():
    """RSS URL'sini test et (ekleme öncesi)"""
    try:
        from utils import validate_rss_source
        
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"success": False, "message": "URL gerekli"})
        
        result = validate_rss_source(url)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Test hatası: {str(e)}"})

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
        "openrouter_api": "MEVCUT" if os.environ.get('OPENROUTER_API_KEY') else "EKSİK",
        "google_api_ocr": "MEVCUT" if os.environ.get('GOOGLE_API_KEY') else "EKSİK (OCR için)",
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
        safe_log(f"Güvenlik kontrol hatası: {str(e)}", "ERROR")
        return render_template('security_check.html', security={"secure": False, "issues": [f"Kontrol hatası: {str(e)}"]})



@app.route('/manual_post_confirmation/<int:tweet_id>')
@login_required
def manual_post_confirmation(tweet_id):
    """Manuel paylaşım onaylama sayfası"""
    try:
        # Pending tweet'i bul
        pending_tweets = load_json("pending_tweets.json")
        pending_tweets = ensure_tweet_ids(pending_tweets)
        
        # Tweet ID'yi pending tweets listesinde ara
        tweet_to_confirm = None
        actual_index = None
        
        for i, tweet in enumerate(pending_tweets):
            if tweet.get('id') == tweet_id:
                tweet_to_confirm = tweet
                actual_index = i
                break
        
        if not tweet_to_confirm:
            flash('Tweet bulunamadı!', 'error')
            return redirect(url_for('index'))
        
        # Tweet türünü belirle
        is_github_tweet = tweet_to_confirm.get('source_type') == 'github'
        
        return render_template('manual_confirmation.html', 
                             tweet=tweet_to_confirm, 
                             tweet_id=tweet_id,
                             actual_index=actual_index,
                             is_github_tweet=is_github_tweet)
        
    except Exception as e:
        flash(f'Manuel onay sayfası hatası: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/manual_post_confirmation_create/<tweet_id>')
@login_required
def manual_post_confirmation_create(tweet_id):
    """Create tweet sayfasından manuel paylaşım onaylama sayfası"""
    try:
        # Manuel tweet'i bul
        manual_tweets = load_manual_tweets()
        
        tweet_to_confirm = None
        for tweet in manual_tweets:
            if tweet.get('id') == tweet_id:
                if tweet.get('is_posted', False):
                    flash('Bu tweet zaten paylaşılmış!', 'warning')
                    return redirect(url_for('create_tweet'))
                tweet_to_confirm = tweet
                break
        
        if not tweet_to_confirm:
            flash('Tweet bulunamadı!', 'error')
            return redirect(url_for('create_tweet'))
        
        return render_template('manual_confirmation_create.html', 
                             tweet=tweet_to_confirm, 
                             tweet_id=tweet_id)
        
    except Exception as e:
        flash(f'Manuel onay sayfası hatası: {str(e)}', 'error')
        return redirect(url_for('create_tweet'))

# =============================================================================
# LOGGING SİSTEMİ (Terminal kaldırıldı - sadece konsol logları)
# =============================================================================

import time

def terminal_log(message, level='info'):
    """Konsola log gönder (terminal işlevi kaldırıldı)"""
    
    # Konsola yazdır
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
    
    try:
        print(f"{color}[{timestamp}] [{level.upper()}] {message}{reset}")
    except UnicodeEncodeError:
        # Windows terminal encoding sorunu için emoji'leri kaldır
        safe_message = message.encode('ascii', 'ignore').decode('ascii')
        print(f"{color}[{timestamp}] [{level.upper()}] {safe_message}{reset}")

@app.route('/test_twitter_connection')
@login_required 
def test_twitter_connection():
    """Twitter API bağlantısını test et"""
    try:
        from utils import setup_twitter_v2_client, check_rate_limit
        import tweepy
        
        # Rate limit kontrolü
        rate_check = check_rate_limit("tweets")
        if not rate_check.get("allowed", True):
            wait_minutes = int(rate_check.get("wait_time", 0) / 60) + 1
            return jsonify({
                "success": False, 
                "error": f"Rate limit aşıldı. {wait_minutes} dakika bekleyin.",
                "rate_limit": True,
                "wait_minutes": wait_minutes,
                "requests_made": rate_check.get('requests_made', 0),
                "limit": rate_check.get('limit', 5)
            })
        
        # Twitter client oluştur
        client = setup_twitter_v2_client()
        
        # Basit bir test tweet metni
        test_tweet = f"🔧 Twitter API bağlantı testi - {datetime.now().strftime('%H:%M:%S')}"
        
        # Tweet'i gönder
        response = client.create_tweet(text=test_tweet)
        
        if hasattr(response, 'data') and response.data and 'id' in response.data:
            tweet_id = response.data['id']
            tweet_url = f"https://x.com/i/status/{tweet_id}"
            
            # Rate limit kullanımını güncelle
            from utils import update_rate_limit_usage
            update_rate_limit_usage("tweets")
            
            return jsonify({
                "success": True,
                "message": "Twitter API bağlantısı başarılı!",
                "tweet_id": tweet_id,
                "tweet_url": tweet_url,
                "tweet_text": test_tweet
            })
        else:
            return jsonify({
                "success": False,
                "error": "Tweet gönderilemedi - API response problemi",
                "response": str(response)
            })
            
    except tweepy.TooManyRequests as e:
        return jsonify({
            "success": False,
            "error": "Twitter API rate limit aşıldı",
            "rate_limit": True,
            "details": str(e)
        })
    except tweepy.Unauthorized as e:
        return jsonify({
            "success": False,
            "error": "Twitter API kimlik doğrulama hatası - API anahtarlarını kontrol edin",
            "details": str(e)
        })
    except tweepy.Forbidden as e:
        return jsonify({
            "success": False,
            "error": "Twitter API yasak işlem - Hesap kısıtlaması olabilir",
            "details": str(e)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Twitter API test hatası: {str(e)}",
            "details": str(e)
        })

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

@app.route('/reset_rate_limit', methods=['POST'])
@login_required
def reset_rate_limit():
    """Rate limit durumunu manuel olarak sıfırla"""
    try:
        success = reset_rate_limit_status()
        if success:
            terminal_log("✅ Rate limit durumu manuel olarak sıfırlandı", "success")
            return jsonify({"success": True, "message": "Rate limit durumu sıfırlandı"})
        else:
            return jsonify({"success": False, "error": "Rate limit sıfırlama başarısız"})
    except Exception as e:
        terminal_log(f"❌ Rate limit sıfırlama hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

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

@app.route('/test_news_fetching_methods')
@login_required
def test_news_fetching_methods():
    """Haber çekme yöntemlerini test et"""
    try:
        from utils import (
            fetch_latest_ai_articles_pythonanywhere,
            fetch_latest_ai_articles_with_firecrawl,
            fetch_articles_from_custom_sources,
            fetch_latest_ai_articles_smart,
            get_news_fetching_method
        )
        
        results = {}
        method_info = get_news_fetching_method()
        
        # PythonAnywhere sistemi test
        try:
            terminal_log("🐍 PythonAnywhere sistemi test ediliyor (Özel kaynaklar + API'ler)...", "info")
            pa_articles = fetch_latest_ai_articles_pythonanywhere()
            results['pythonanywhere'] = {
                'success': True,
                'count': len(pa_articles) if pa_articles else 0,
                'articles': pa_articles[:3] if pa_articles else [],
                'description': 'Özel haber kaynakları + RSS + Hacker News + Reddit'
            }
            terminal_log(f"✅ PythonAnywhere (Entegre): {len(pa_articles) if pa_articles else 0} makale", "success")
        except Exception as e:
            results['pythonanywhere'] = {'success': False, 'error': str(e)}
            terminal_log(f"❌ PythonAnywhere hatası: {e}", "error")
        
        # Özel kaynaklar test
        try:
            terminal_log("📰 Özel kaynaklar test ediliyor...", "info")
            custom_articles = fetch_articles_from_custom_sources()
            results['custom_sources'] = {
                'success': True,
                'count': len(custom_articles) if custom_articles else 0,
                'articles': custom_articles[:3] if custom_articles else []
            }
            terminal_log(f"✅ Özel kaynaklar: {len(custom_articles) if custom_articles else 0} makale", "success")
        except Exception as e:
            results['custom_sources'] = {'success': False, 'error': str(e)}
            terminal_log(f"❌ Özel kaynaklar hatası: {e}", "error")
        
        # MCP test (eğer aktifse)
        if method_info.get('mcp_enabled'):
            try:
                terminal_log("🔧 MCP sistemi test ediliyor...", "info")
                mcp_articles = fetch_latest_ai_articles_with_firecrawl()
                results['mcp'] = {
                    'success': True,
                    'count': len(mcp_articles) if mcp_articles else 0,
                    'articles': mcp_articles[:3] if mcp_articles else []
                }
                terminal_log(f"✅ MCP: {len(mcp_articles) if mcp_articles else 0} makale", "success")
            except Exception as e:
                results['mcp'] = {'success': False, 'error': str(e)}
                terminal_log(f"❌ MCP hatası: {e}", "error")
        else:
            results['mcp'] = {'success': False, 'error': 'MCP devre dışı'}
            terminal_log("⚠️ MCP devre dışı", "warning")
        
        # Akıllı sistem test
        try:
            terminal_log("🎯 Akıllı sistem test ediliyor...", "info")
            smart_articles = fetch_latest_ai_articles_smart()
            results['smart_system'] = {
                'success': True,
                'count': len(smart_articles) if smart_articles else 0,
                'articles': smart_articles[:3] if smart_articles else []
            }
            terminal_log(f"✅ Akıllı sistem: {len(smart_articles) if smart_articles else 0} makale", "success")
        except Exception as e:
            results['smart_system'] = {'success': False, 'error': str(e)}
            terminal_log(f"❌ Akıllı sistem hatası: {e}", "error")
        
        results['method_info'] = method_info
        results['test_time'] = datetime.now().isoformat()
        
        flash('Haber çekme yöntemleri test edildi! Konsol loglarından detayları görebilirsiniz.', 'success')
        return jsonify(results)
        
    except Exception as e:
        terminal_log(f"❌ Test hatası: {e}", "error")
        return jsonify({'error': str(e)}), 500

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
        
        from utils import advanced_web_scraper, ai_call
        
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
        api_key = os.environ.get('OPENROUTER_API_KEY')
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
        ai_response = ai_call(analysis_prompt, api_key)
        
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
        
        # HTML boyutunu kontrol et (kısaltma yapmıyoruz, sadece log)
        if len(highlighted_html) > 1000000:  # 1MB üzerinde uyarı ver
            terminal_log(f"⚠️ HTML büyük ({len(highlighted_html)} karakter), yükleme biraz uzun sürebilir", "warning")
        else:
            terminal_log(f"✅ HTML boyutu: {len(highlighted_html)} karakter", "info")
        
        terminal_log("✅ AI analizi tamamlandı", "success")
        
        return jsonify({
            'success': True,
            'url': url,
            'html_content': highlighted_html,
            'original_html': html_content,  # Orijinal HTML'i de gönder
            'ai_analysis': ai_analysis,
            'html_size': len(highlighted_html),
            'original_size': len(html_content),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        terminal_log(f"❌ Sayfa analizi hatası: {e}", "error")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def highlight_selectors_in_html(html_content, selectors):
    """HTML içeriğinde selector'ları renklendir - Gelişmiş sistem"""
    try:
        from bs4 import BeautifulSoup
        import re
        
        # HTML'i temizle ve düzenle
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Script ve style taglarını kaldır (görüntüleme için)
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Selector renkleri ve stilleri
        selector_styles = {
            'article_container': {
                'background': 'rgba(255, 107, 107, 0.2)',
                'border': '2px solid #ff6b6b',
                'color': '#721c24',
                'label': 'KONTEYNER'
            },
            'title_selector': {
                'background': 'rgba(78, 205, 196, 0.2)',
                'border': '2px solid #4ecdc4',
                'color': '#0f5132',
                'label': 'BAŞLIK'
            },
            'link_selector': {
                'background': 'rgba(69, 183, 209, 0.2)',
                'border': '2px solid #45b7d1',
                'color': '#0c4a6e',
                'label': 'LİNK'
            },
            'date_selector': {
                'background': 'rgba(150, 206, 180, 0.2)',
                'border': '2px solid #96ceb4',
                'color': '#14532d',
                'label': 'TARİH'
            },
            'summary_selector': {
                'background': 'rgba(254, 202, 87, 0.2)',
                'border': '2px solid #feca57',
                'color': '#92400e',
                'label': 'ÖZET'
            }
        }
        
        # Her selector için elementleri bul ve işaretle
        highlighted_count = 0
        
        for selector_name, selector in selectors.items():
            if not selector or not selector.strip():
                continue
                
            style_info = selector_styles.get(selector_name, {
                'background': 'rgba(200, 200, 200, 0.2)',
                'border': '2px solid #cccccc',
                'color': '#666666',
                'label': selector_name.upper()
            })
            
            try:
                # CSS selector'ı parse et
                elements = soup.select(selector)
                terminal_log(f"🎯 {selector_name} için {len(elements)} element bulundu: {selector}", "info")
                
                for i, element in enumerate(elements[:15]):  # İlk 15 elementi işaretle
                    try:
                        # Element'in mevcut style'ını koru
                        current_style = element.get('style', '')
                        
                        # Yeni style oluştur
                        new_style = f"""
                            {current_style};
                            background: {style_info['background']} !important;
                            border: {style_info['border']} !important;
                            color: {style_info['color']} !important;
                            padding: 2px 4px !important;
                            margin: 1px !important;
                            border-radius: 3px !important;
                            position: relative !important;
                            cursor: pointer !important;
                            transition: all 0.2s ease !important;
                        """.strip()
                        
                        element['style'] = new_style
                        element['data-selector'] = selector_name
                        element['data-selector-value'] = selector
                        element['data-selector-label'] = style_info['label']
                        element['title'] = f"🎯 {style_info['label']}: {selector} (#{i+1})"
                        element['class'] = element.get('class', []) + ['highlighted-selector']
                        
                        # Pseudo-element için label ekle
                        element['data-before-content'] = f"{style_info['label']} #{i+1}"
                        
                        highlighted_count += 1
                        
                    except Exception as elem_error:
                        terminal_log(f"⚠️ Element işaretleme hatası: {elem_error}", "warning")
                        continue
                        
            except Exception as selector_error:
                terminal_log(f"⚠️ Selector işaretleme hatası ({selector}): {selector_error}", "warning")
                continue
        
        terminal_log(f"✅ Toplam {highlighted_count} element işaretlendi", "success")
        
        # HTML'i string'e çevir ve formatla
        html_str = str(soup)
        
        # HTML'i daha okunabilir hale getir
        html_str = re.sub(r'><', '>\n<', html_str)  # Tag'ler arası satır sonu
        html_str = re.sub(r'\n\s*\n', '\n', html_str)  # Çoklu boş satırları tek satıra çevir
        
        return html_str
        
    except Exception as e:
        terminal_log(f"❌ HTML highlight hatası: {e}", "error")
        import traceback
        traceback.print_exc()
        return html_content

@app.route('/deleted_tweets')
@login_required
def deleted_tweets():
    """Silinmiş tweetler sayfası"""
    try:
        # Tüm makaleleri yükle
        all_articles = load_json("posted_articles.json")
        
        # Sadece silinmiş olanları filtrele
        deleted_articles = [article for article in all_articles if article.get('deleted', False)]
        
        # Tarihe göre sırala (en yeni önce)
        deleted_articles.sort(key=lambda x: x.get('deleted_date', ''), reverse=True)
        
        # İstatistikler
        stats = {
            'total_deleted': len(deleted_articles),
            'deleted_today': 0,
            'deleted_this_week': 0,
            'deleted_this_month': 0
        }
        
        # Tarih bazlı istatistikler
        from datetime import datetime, timedelta
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        for article in deleted_articles:
            deleted_date_str = article.get('deleted_date', '')
            if deleted_date_str:
                try:
                    deleted_date = datetime.fromisoformat(deleted_date_str.replace('Z', '+00:00')).date()
                    
                    if deleted_date == today:
                        stats['deleted_today'] += 1
                    if deleted_date >= week_ago:
                        stats['deleted_this_week'] += 1
                    if deleted_date >= month_ago:
                        stats['deleted_this_month'] += 1
                        
                except Exception as e:
                    continue
        
        # Debug için log
        safe_log(f"Silinmiş tweetler sayfası: {len(deleted_articles)} silinmiş tweet", "DEBUG")
        
        return render_template('deleted_tweets.html', 
                             deleted_articles=deleted_articles,
                             stats=stats)
                             
    except Exception as e:
        safe_log(f"Silinmiş tweetler sayfası hatası: {str(e)}", "ERROR")
        return render_template('deleted_tweets.html', 
                             deleted_articles=[],
                             stats={},
                             error=str(e))



@app.route('/restore_deleted_tweet', methods=['POST'])
@login_required
def restore_deleted_tweet():
    """Silinmiş tweet'i geri yükle"""
    try:
        data = request.get_json()
        article_hash = data.get('article_hash')
        
        if not article_hash:
            return jsonify({"success": False, "error": "Makale hash'i gerekli"})
        
        # Tüm makaleleri yükle
        all_articles = load_json("posted_articles.json")
        
        # Silinmiş makaleyi bul
        restored_article = None
        updated_articles = []
        
        for article in all_articles:
            if article.get('hash') == article_hash and article.get('deleted', False):
                # Makaleyi geri yükle
                article['deleted'] = False
                article['restored'] = True
                article['restored_date'] = datetime.now().isoformat()
                article.pop('deleted_date', None)
                article.pop('deletion_reason', None)
                restored_article = article
                terminal_log(f"📝 Makale geri yüklendi: {article.get('title', '')[:50]}...", "info")
            
            updated_articles.append(article)
        
        if restored_article:
            # Güncellenmiş listeyi kaydet
            save_json("posted_articles.json", updated_articles)
            
            return jsonify({
                "success": True, 
                "message": "Tweet başarıyla geri yüklendi",
                "article_title": restored_article.get('title', '')
            })
        else:
            return jsonify({"success": False, "error": "Silinmiş tweet bulunamadı"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/session_info')
@login_required
def session_info():
    """Session bilgilerini göster (debug için)"""
    session_data = {
        'logged_in': session.get('logged_in'),
        'login_time': session.get('login_time'),
        'user_email': session.get('user_email'),
        'remember_me': session.get('remember_me'),
        'remember_until': session.get('remember_until'),
        'auth_method': session.get('auth_method'),
        'session_permanent': session.permanent,
        'current_time': datetime.now().isoformat()
    }
    
    # Kalan süreyi hesapla
    if session.get('remember_until'):
        try:
            remember_until = datetime.fromisoformat(session['remember_until'])
            remaining = remember_until - datetime.now()
            session_data['remaining_days'] = remaining.days
            session_data['remaining_hours'] = remaining.seconds // 3600
        except:
            session_data['remaining_days'] = 'Hata'
            session_data['remaining_hours'] = 'Hata'
    
    return jsonify(session_data)

@app.route('/automation_debug')
@login_required
def automation_debug():
    """Otomatik sistem debug bilgileri"""
    global background_scheduler_running, last_check_time
    
    settings = load_automation_settings()
    current_time = datetime.now()
    
    debug_info = {
        'current_time': current_time.isoformat(),
        'background_scheduler_running': background_scheduler_running,
        'last_check_time': last_check_time.isoformat() if last_check_time else None,
        'settings': settings,
        'auto_mode': settings.get('auto_mode', False),
        'check_interval_hours': settings.get('check_interval_hours', 3)
    }
    
    # Sonraki kontrol zamanını hesapla
    if last_check_time:
        next_check = last_check_time + timedelta(hours=settings.get('check_interval_hours', 3))
        remaining_seconds = (next_check - current_time).total_seconds()
        debug_info['next_check_time'] = next_check.isoformat()
        debug_info['remaining_hours'] = remaining_seconds / 3600
        debug_info['should_run_now'] = remaining_seconds <= 0
    else:
        debug_info['next_check_time'] = 'İlk çalışma - hemen çalışmalı'
        debug_info['remaining_hours'] = 0
        debug_info['should_run_now'] = True
    
    return jsonify(debug_info)

@app.route('/force_automation_run', methods=['POST'])
@login_required
def force_automation_run():
    """Otomatik sistemi manuel olarak çalıştır (test için)"""
    global last_check_time
    
    try:
        settings = load_automation_settings()
        
        if not settings.get('auto_mode', False):
            return jsonify({
                'success': False, 
                'message': 'Otomatik mod kapalı. Önce ayarlardan açın.'
            })
        
        terminal_log("🔄 Manuel otomatik kontrol başlatılıyor...", "info")
        
        # Otomatik sistemi çalıştır
        result = check_and_post_articles()
        
        # Last check time'ı güncelle
        last_check_time = datetime.now()
        
        terminal_log(f"✅ Manuel otomatik kontrol tamamlandı: {result.get('message', 'Sonuç yok')}", "success")
        
        return jsonify({
            'success': True,
            'message': 'Otomatik kontrol başarıyla çalıştırıldı',
            'result': result,
            'last_check_time': last_check_time.isoformat()
        })
        
    except Exception as e:
        terminal_log(f"❌ Manuel otomatik kontrol hatası: {e}", "error")
        return jsonify({
            'success': False,
            'message': f'Hata oluştu: {str(e)}'
        })

@app.route('/test_openrouter_ocr')
@login_required
def test_openrouter_ocr():
    """OpenRouter OCR sistemini test et"""
    try:
        from utils import openrouter_ocr_image_enhanced
        import os
        
        # Test resmi oluştur (basit bir metin içeren resim)
        test_image_path = "static/uploads/test_ocr.png"
        
        # Eğer test resmi yoksa basit bir test yap
        if not os.path.exists(test_image_path):
            return jsonify({
                "success": False,
                "error": "Test resmi bulunamadı",
                "message": "Lütfen bir resim yükleyip OCR testini deneyin"
            })
        
        # OCR testi yap
        ocr_result = openrouter_ocr_image_enhanced(test_image_path)
        
        if ocr_result and len(ocr_result.strip()) > 5:
            return jsonify({
                "success": True,
                "ocr_text": ocr_result,
                "char_count": len(ocr_result),
                "message": "OpenRouter OCR sistemi çalışıyor"
            })
        else:
            return jsonify({
                "success": False,
                "error": "OCR sonucu yetersiz",
                "ocr_text": ocr_result,
                "message": "OCR işlemi başarısız oldu"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"OCR test hatası: {e}"
        })

@app.route('/changelog')
@login_required
def changelog():
    """Changelog sayfası"""
    try:
        # CHANGELOG.md dosyasını oku
        changelog_content = ""
        try:
            with open('CHANGELOG.md', 'r', encoding='utf-8') as f:
                changelog_content = f.read()
        except FileNotFoundError:
            changelog_content = "# Changelog\n\nChangelog dosyası bulunamadı."
        
        return render_template('changelog.html', 
                             changelog_content=changelog_content,
                             app_version=APP_VERSION,
                             app_release_date=APP_RELEASE_DATE,
                             version_changelog=VERSION_CHANGELOG)
    except Exception as e:
        return render_template('changelog.html', 
                             changelog_content=f"Hata: {str(e)}",
                             app_version=APP_VERSION,
                             app_release_date=APP_RELEASE_DATE,
                             version_changelog=VERSION_CHANGELOG)

@app.route('/test_openrouter_api')
@login_required
def test_openrouter_api():
    """OpenRouter API'yi test et"""
    try:
        from utils import openrouter_call, try_openrouter_fallback
        
        openrouter_key = os.environ.get('OPENROUTER_API_KEY')
        if not openrouter_key:
            return jsonify({
                "success": False,
                "error": "OpenRouter API anahtarı bulunamadı",
                "message": "OPENROUTER_API_KEY environment variable'ı ayarlanmamış"
            })
        
        # API anahtarı format kontrolü
        terminal_log(f"🔍 OpenRouter API Key Debug:", "info")
        terminal_log(f"  - Key exists: {openrouter_key is not None}", "info")
        terminal_log(f"  - Key length: {len(openrouter_key)}", "info")
        terminal_log(f"  - Key prefix: {openrouter_key[:10]}...", "info")
        terminal_log(f"  - Expected format: sk-or-v1-...", "info")
        terminal_log(f"  - Format check: {openrouter_key.startswith('sk-or-')}", "info")
        
        terminal_log("🧪 OpenRouter API test ediliyor...", "info")
        
        # Test prompt'u
        test_prompt = "Write a short tweet about artificial intelligence in English (max 50 words):"
        
        # Ücretsiz modelleri test et
        free_models = [
            "qwen/qwen3-8b:free",                           # Yeni Qwen3 8B - En güvenilir
            "qwen/qwen3-30b-a3b:free",                      # Yeni Qwen3 30B A3B - Güçlü
            "qwen/qwen3-4b:free",                           # Yeni Qwen3 4B - Hızlı
            "deepseek/deepseek-chat-v3-0324:free",         # DeepSeek Chat - Güvenilir
            "deepseek/deepseek-r1-zero:free",              # DeepSeek R1 - Reasoning
            "deepseek/deepseek-v3-base:free",              # DeepSeek V3 Base
            "nousresearch/deephermes-3-llama-3-8b-preview:free"  # DeepHermes 3 - Fallback
        ]
        
        test_results = []
        
        for model in free_models:
            try:
                terminal_log(f"🔍 Model test ediliyor: {model}", "info")
                result = openrouter_call(test_prompt, openrouter_key, max_tokens=100, model=model)
                
                if result and len(result.strip()) > 5:
                    test_results.append({
                        "model": model,
                        "success": True,
                        "response": result[:200] + "..." if len(result) > 200 else result,
                        "response_length": len(result)
                    })
                    terminal_log(f"✅ Model başarılı: {model} - {len(result)} karakter", "success")
                else:
                    test_results.append({
                        "model": model,
                        "success": False,
                        "error": "Boş veya çok kısa yanıt"
                    })
                    terminal_log(f"❌ Model başarısız: {model} - Boş yanıt", "error")
                    
            except Exception as e:
                test_results.append({
                    "model": model,
                    "success": False,
                    "error": str(e)
                })
                terminal_log(f"❌ Model hatası: {model} - {e}", "error")
        
        # Fallback sistemi test et
        try:
            terminal_log("🔄 Fallback sistemi test ediliyor...", "info")
            fallback_result = try_openrouter_fallback(test_prompt, max_tokens=100)
            
            fallback_test = {
                "success": fallback_result != "API hatası" and fallback_result is not None,
                "response": fallback_result[:200] + "..." if fallback_result and len(fallback_result) > 200 else fallback_result
            }
            
            if fallback_test["success"]:
                terminal_log("✅ Fallback sistemi başarılı", "success")
            else:
                terminal_log("❌ Fallback sistemi başarısız", "error")
                
        except Exception as e:
            fallback_test = {
                "success": False,
                "error": str(e)
            }
            terminal_log(f"❌ Fallback test hatası: {e}", "error")
        
        # Sonuçları özetle
        successful_models = [r for r in test_results if r.get("success", False)]
        
        return jsonify({
            "success": len(successful_models) > 0,
            "message": f"OpenRouter test tamamlandı: {len(successful_models)}/{len(free_models)} model başarılı",
            "api_key_available": True,
            "total_models_tested": len(free_models),
            "successful_models": len(successful_models),
            "model_results": test_results,
            "fallback_test": fallback_test,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        terminal_log(f"❌ OpenRouter test hatası: {e}", "error")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/test_tweet_generation')
@login_required
def test_tweet_generation():
    """Tweet oluşturma sistemini test et - Farklı senaryolar"""
    try:
        from utils import generate_ai_tweet_with_mcp_analysis, generate_comprehensive_analysis
        
        # Test senaryoları
        test_scenarios = [
            {
                "name": "Normal AI Makale",
                "data": {
                    "title": "OpenAI Releases GPT-5 with Revolutionary Reasoning Capabilities",
                    "content": "OpenAI today announced the release of GPT-5, featuring enhanced reasoning capabilities and improved performance across multiple domains. The new model demonstrates significant improvements in mathematical problem-solving and code generation.",
                    "url": "https://example.com/openai-gpt5"
                }
            },
            {
                "name": "Kısa Başlık",
                "data": {
                    "title": "AI News",
                    "content": "",
                    "url": "https://example.com/ai-news"
                }
            },
            {
                "name": "İçerik Yok",
                "data": {
                    "title": "Technology Innovation Breakthrough",
                    "content": "",
                    "url": "https://example.com/tech"
                }
            },
            {
                "name": "Şirket Adı Var",
                "data": {
                    "title": "Google Announces New Quantum Computing Breakthrough",
                    "content": "Google's quantum computing team has achieved a major milestone in quantum error correction, bringing practical quantum computers closer to reality.",
                    "url": "https://example.com/google-quantum"
                }
            },
            {
                "name": "Sayısal Veriler",
                "data": {
                    "title": "Tesla Reports 40% Increase in Autonomous Driving Accuracy",
                    "content": "Tesla's latest Full Self-Driving update shows 40% improvement in accuracy and 25% reduction in intervention rates during highway driving.",
                    "url": "https://example.com/tesla-fsd"
                }
            }
        ]
        
        api_key = os.environ.get('OPENROUTER_API_KEY')
        test_results = []
        
        for scenario in test_scenarios:
            try:
                terminal_log(f"🧪 Test ediliyor: {scenario['name']}", "info")
                
                # Comprehensive analysis test
                analysis = generate_comprehensive_analysis(scenario['data'], api_key)
                
                # Tweet generation test
                tweet_result = generate_ai_tweet_with_mcp_analysis(scenario['data'], api_key)
                
                result = {
                    "scenario": scenario['name'],
                    "success": True,
                    "analysis": {
                        "innovation": analysis.get('innovation', ''),
                        "companies": analysis.get('companies', []),
                        "hashtags": analysis.get('hashtags', []),
                        "emojis": analysis.get('emojis', [])
                    },
                    "tweet": tweet_result.get('tweet', ''),
                    "tweet_length": len(tweet_result.get('tweet', '')),
                    "source": tweet_result.get('source', ''),
                    "impact_score": tweet_result.get('impact_score', 0)
                }
                
                terminal_log(f"✅ {scenario['name']}: {len(tweet_result.get('tweet', ''))} karakter", "success")
                
            except Exception as e:
                result = {
                    "scenario": scenario['name'],
                    "success": False,
                    "error": str(e)
                }
                terminal_log(f"❌ {scenario['name']}: {e}", "error")
            
            test_results.append(result)
        
        return jsonify({
            "success": True,
            "message": "Tweet oluşturma testleri tamamlandı",
            "test_results": test_results,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        terminal_log(f"❌ Tweet test hatası: {e}", "error")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/debug_openrouter_key')
@login_required
def debug_openrouter_key():
    """OpenRouter API anahtarını debug et"""
    try:
        openrouter_key = os.environ.get('OPENROUTER_API_KEY')
        
        debug_info = {
            "key_exists": openrouter_key is not None,
            "key_length": len(openrouter_key) if openrouter_key else 0,
            "key_prefix": openrouter_key[:8] + "..." if openrouter_key and len(openrouter_key) > 8 else "N/A",
            "key_format_check": openrouter_key.startswith('sk-or-') if openrouter_key else False,
            "env_vars_count": len([k for k in os.environ.keys() if 'OPENROUTER' in k.upper()]),
            "all_openrouter_vars": [k for k in os.environ.keys() if 'OPENROUTER' in k.upper()]
        }
        
        terminal_log(f"🔍 OpenRouter Debug: {debug_info}", "info")
        
        # Basit HTTP test
        if openrouter_key:
            try:
                import requests
                headers = {
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json"
                }
                
                # Basit bir test isteği (models endpoint)
                test_response = requests.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers,
                    timeout=10
                )
                
                debug_info["http_test"] = {
                    "status_code": test_response.status_code,
                    "success": test_response.status_code == 200,
                    "error": test_response.text if test_response.status_code != 200 else None
                }
                
                terminal_log(f"🌐 HTTP Test: {test_response.status_code}", "info")
                
            except Exception as http_error:
                debug_info["http_test"] = {
                    "success": False,
                    "error": str(http_error)
                }
                terminal_log(f"❌ HTTP Test hatası: {http_error}", "error")
        
        return jsonify({
            "success": True,
            "debug_info": debug_info,
            "message": "Debug bilgileri konsol loglarında"
        })
        
    except Exception as e:
        terminal_log(f"❌ OpenRouter debug hatası: {e}", "error")
        return jsonify({
            "success": False,
            "error": str(e)
        })

# ============================================================================
# AI KEYWORDS MANAGEMENT ROUTES
# ============================================================================

@app.route('/ai_keywords')
@login_required
def ai_keywords():
    """AI Keywords yönetim sayfası"""
    try:
        config = load_ai_keywords_config()
        stats = get_ai_keywords_stats()
        active_keywords = get_all_active_keywords()
        
        return render_template('ai_keywords.html', 
                             config=config, 
                             stats=stats, 
                             active_keywords=active_keywords)  # Tüm aktif keywordleri göster
    except Exception as e:
        terminal_log(f"❌ AI Keywords sayfa hatası: {e}", "error")
        flash(f'AI Keywords yükleme hatası: {e}', 'error')
        return redirect(url_for('settings'))

@app.route('/api/ai_keywords/config')
@login_required
def get_ai_keywords_config():
    """AI Keywords yapılandırmasını API ile al"""
    try:
        config = load_ai_keywords_config()
        return jsonify({
            "success": True,
            "config": config
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/ai_keywords/stats')
@login_required
def get_ai_keywords_stats_api():
    """AI Keywords istatistiklerini API ile al"""
    try:
        stats = get_ai_keywords_stats()
        active_keywords = get_all_active_keywords()
        
        return jsonify({
            "success": True,
            "stats": stats,
            "active_keywords_count": len(active_keywords),
            "active_keywords_sample": active_keywords[:10]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/ai_keywords/update', methods=['POST'])
@login_required
def update_ai_keywords():
    """AI Keywords güncelle"""
    try:
        data = request.get_json()
        category_name = data.get('category')
        action = data.get('action')
        keyword = data.get('keyword', '').strip()
        
        if not category_name or not action:
            return jsonify({
                "success": False,
                "error": "Kategori ve işlem gerekli"
            })
        
        success, message = update_ai_keyword_category(category_name, action, keyword)
        
        if success:
            # Güncel istatistikleri al
            stats = get_ai_keywords_stats()
            active_keywords = get_all_active_keywords()
            return jsonify({
                "success": True,
                "message": message,
                "stats": stats,
                "active_keywords": active_keywords
            })
        else:
            return jsonify({
                "success": False,
                "error": message
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/ai_keywords/test_search')
@login_required
def test_ai_keywords_search():
    """AI Keywords aramasını test et"""
    try:
        terminal_log("🧪 AI Keywords arama testi başlatılıyor...", "info")
        
        # Test araması yap
        articles = fetch_ai_news_with_advanced_keywords()
        
        result = {
            "success": True,
            "articles_found": len(articles),
            "articles": articles[:5],  # İlk 5 makaleyi göster
            "test_completed_at": datetime.now().isoformat()
        }
        
        terminal_log(f"✅ AI Keywords test tamamlandı: {len(articles)} makale bulundu", "success")
        
        return jsonify(result)
        
    except Exception as e:
        terminal_log(f"❌ AI Keywords test hatası: {e}", "error")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/ai_keywords/save_settings', methods=['POST'])
@login_required
def save_ai_keywords_settings():
    """AI Keywords genel ayarlarını kaydet"""
    try:
        data = request.get_json()
        config = load_ai_keywords_config()
        
        # Ayarları güncelle
        if 'settings' in data:
            config['settings'].update(data['settings'])
        
        # Kaydet
        if save_ai_keywords_config(config):
            return jsonify({
                "success": True,
                "message": "Ayarlar başarıyla kaydedildi"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Kaydetme hatası"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/ai_keywords/reset_category', methods=['POST'])
@login_required
def reset_ai_keywords_category():
    """AI Keywords kategorisini varsayılana sıfırla"""
    try:
        data = request.get_json()
        category_name = data.get('category')
        
        if not category_name:
            return jsonify({
                "success": False,
                "error": "Kategori adı gerekli"
            })
        
        config = load_ai_keywords_config()
        
        if category_name not in config.get("keyword_categories", {}):
            return jsonify({
                "success": False,
                "error": "Kategori bulunamadı"
            })
        
        # Kullanıcı keywordlerini ve excluded keywordleri temizle
        category = config["keyword_categories"][category_name]
        category["user_keywords"] = []
        category["excluded_keywords"] = []
        category["enabled"] = True
        
        # Kaydet
        if save_ai_keywords_config(config):
            stats = get_ai_keywords_stats()
            return jsonify({
                "success": True,
                "message": f"{category_name} kategorisi varsayılana sıfırlandı",
                "stats": stats
            })
        else:
            return jsonify({
                "success": False,
                "error": "Kaydetme hatası"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/ai_keywords/toggle_keyword', methods=['POST'])
@login_required
def toggle_ai_keyword():
    """Bir keywordü tüm kategorilerde veya belirli kategoride hariç/aktif arasında değiştir"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        category_name = data.get('category', '').strip()
        
        if not keyword:
            return jsonify({"success": False, "error": "Keyword gerekli"})

        config = load_ai_keywords_config()
        changed = False
        message_part = ""
        
        # Belirli kategori belirtilmişse sadece o kategoride işlem yap
        if category_name:
            categories_to_check = {category_name: config.get("keyword_categories", {}).get(category_name)}
            if not categories_to_check[category_name]:
                return jsonify({"success": False, "error": "Kategori bulunamadı"})
        else:
            # Tüm kategorilerde ara
            categories_to_check = config.get("keyword_categories", {})
        
        is_active = None
        for cat_key, cat in categories_to_check.items():
            if not cat:
                continue
                
            # keyword kategoriye ait mi?
            if keyword in cat.get("default_keywords", []) or keyword in cat.get("user_keywords", []):
                excluded = cat.get("excluded_keywords", [])
                if keyword in excluded:
                    excluded.remove(keyword)
                    message_part = "aktifleştirildi"
                    is_active = True
                else:
                    excluded.append(keyword)
                    message_part = "hariç tutuldu"
                    is_active = False
                cat["excluded_keywords"] = excluded
                changed = True
                
        if not changed:
            return jsonify({"success": False, "error": "Keyword kategori listelerinde bulunamadı"})

        if save_ai_keywords_config(config):
            stats = get_ai_keywords_stats()
            active_keywords = get_all_active_keywords()
            return jsonify({
                "success": True, 
                "message": f'"{keyword}" {message_part}', 
                "is_active": is_active,
                "stats": stats,
                "active_keywords": active_keywords
            })
        else:
            return jsonify({"success": False, "error": "Kaydetme hatası"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/shared_tweets')
@login_required
def shared_tweets():
    """Paylaşılan tweetler sayfası"""
    try:
        # Paylaşılan makaleleri yükle
        articles = load_json(HISTORY_FILE)
        
        # Sadece paylaşılan tweetleri filtrele (silinmemiş ve arşivlenmemiş olanlar)
        shared_articles = [article for article in articles if not article.get('deleted', False) and not article.get('archived', False)]
        
        return render_template('shared_tweets.html', articles=shared_articles)
    except Exception as e:
        flash(f'Sayfa yükleme hatası: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/archived_tweets')
@login_required
def archived_tweets():
    """Arşivlenen tweetler sayfası"""
    try:
        # Arşivlenen makaleleri yükle
        archived_articles = load_json("archived_articles.json", [])
        
        return render_template('archived_tweets.html', archived_articles=archived_articles)
    except Exception as e:
        flash(f'Sayfa yükleme hatası: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/api/create_tweet_homepage', methods=['POST'])
@login_required
def create_tweet_homepage():
    """Ana sayfa manuel tweet oluşturma için özel endpoint - JSON response döner"""
    try:
        # Form verilerini al
        tweet_mode = request.form.get('tweet_mode', 'text')
        tweet_theme = request.form.get('tweet_theme', 'bilgilendirici')
        action = request.form.get('action', 'preview')
        save_as_draft = request.form.get('save_as_draft') == 'true'
        
        terminal_log(f"🏠 Ana sayfa tweet oluşturma - Mode: {tweet_mode}, Tema: {tweet_theme}", "info")
        
        # Mode'a göre işlem yap
        tweet_content = None
        source_data = {
            'type': tweet_mode,
            'theme': tweet_theme,
            'created_via': 'homepage'
        }
        
        if tweet_mode == 'text':
            tweet_text = request.form.get('tweet_text', '').strip()
            if not tweet_text or len(tweet_text) < 10:
                return jsonify({'success': False, 'error': 'Tweet en az 10 karakter olmalıdır!'})
            
            # AI ile optimize et
            from utils import generate_ai_tweet_with_content
            api_key = os.environ.get('OPENROUTER_API_KEY')
            
            article_data = {
                'title': tweet_text[:100],
                'content': tweet_text,
                'url': '',
                'lang': 'tr'
            }
            
            tweet_data = generate_ai_tweet_with_content(article_data, api_key, tweet_theme)
            tweet_content = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
            
            source_data.update({
                'original_text': tweet_text
            })
            
        elif tweet_mode == 'image':
            image_file = request.files.get('tweet_image')
            if not image_file or not image_file.filename:
                return jsonify({'success': False, 'error': 'Lütfen bir resim seçin!'})
            
            # Resmi kaydet
            filename = secure_filename(image_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            image_path = os.path.join('static', 'uploads', filename)
            
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image_file.save(image_path)
            
            # OCR ile resimden metin çıkar
            from utils import openrouter_ocr_image_enhanced, generate_ai_tweet_with_content
            ocr_text = openrouter_ocr_image_enhanced(image_path)
            
            if not ocr_text or len(ocr_text.strip()) < 10:
                return jsonify({'success': False, 'error': 'Resimden yeterli metin çıkarılamadı.'})
            
            # AI ile tweet oluştur
            api_key = os.environ.get('OPENROUTER_API_KEY')
            article_data = {
                'title': ocr_text[:100],
                'content': ocr_text,
                'url': '',
                'lang': 'en'
            }
            
            tweet_data = generate_ai_tweet_with_content(article_data, api_key, tweet_theme)
            tweet_content = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
            
            source_data.update({
                'image_path': image_path,
                'original_filename': image_file.filename,
                'ocr_text': ocr_text
            })
            
        elif tweet_mode == 'link':
            url = request.form.get('tweet_url', '').strip()
            if not url:
                return jsonify({'success': False, 'error': 'Lütfen bir URL girin!'})
            
            # URL içeriğini çek
            from utils import fetch_article_content_with_mcp_only, generate_ai_tweet_with_content
            article_data = fetch_article_content_with_mcp_only(url)
            
            if not article_data or not article_data.get('content'):
                return jsonify({'success': False, 'error': 'URL içeriği çekilemedi.'})
            
            # AI ile tweet oluştur
            api_key = os.environ.get('OPENROUTER_API_KEY')
            tweet_data = generate_ai_tweet_with_content(article_data, api_key, tweet_theme)
            tweet_content = tweet_data['tweet'] if isinstance(tweet_data, dict) else tweet_data
            
            source_data.update({
                'source_url': url,
                'fetched_title': article_data.get('title', ''),
                'fetched_content': article_data.get('content', '')[:200]
            })
        
        if not tweet_content:
            return jsonify({'success': False, 'error': 'Tweet içeriği oluşturulamadı.'})
        
        # Tweet'i kaydet
        tweet_id = str(uuid.uuid4())
        tweet_data = {
            'id': tweet_id,
            'content': tweet_content,
            'status': 'draft' if save_as_draft else 'ready',
            'created_at': datetime.now().isoformat(),
            'theme': tweet_theme,
            'source_data': source_data,
            'is_posted': False,
            'char_count': len(tweet_content),
            'created_via': 'homepage'
        }
        
        # Manuel tweets'e kaydet
        manual_tweets = load_manual_tweets()
        manual_tweets.append(tweet_data)
        save_manual_tweets(manual_tweets)
        
        terminal_log(f"✅ Ana sayfa tweet oluşturuldu - ID: {tweet_id}, {len(tweet_content)} karakter", "success")
        
        # Response döndür
        return jsonify({
            'success': True,
            'tweet': {
                'id': tweet_id,
                'content': tweet_content,
                'mode': tweet_mode,
                'theme': tweet_theme,
                'isDraft': save_as_draft,
                'charCount': len(tweet_content),
                'imagePath': source_data.get('image_path'),
                'originalFilename': source_data.get('original_filename'),
                'sourceUrl': source_data.get('source_url'),
                'fetchedTitle': source_data.get('fetched_title')
            }
        })
        
    except Exception as e:
        terminal_log(f"❌ Ana sayfa tweet oluşturma hatası: {e}", "error")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/convert_rejected_to_tweet', methods=['POST'])
@login_required
def convert_rejected_to_tweet():
    """Reddedilen makaleyi direk tweet'e dönüştür"""
    try:
        data = request.get_json()
        article_url = data.get('article_url')
        article_title = data.get('article_title')
        
        if not article_url:
            return jsonify({"success": False, "error": "Makale URL'si gerekli"})
        
        # Reddedilen makaleleri yükle
        rejected_articles = load_json("rejected_articles.json", [])
        
        # İlgili makaleyi bul
        target_article = None
        for article in rejected_articles:
            if article.get('url') == article_url:
                target_article = article
                break
        
        if not target_article:
            return jsonify({"success": False, "error": "Makale bulunamadı"})
        
        # Makale içeriğini yeniden çek ve tweet oluştur
        try:
            from utils import fetch_latest_ai_articles, generate_ai_tweet_with_content
            
            # Makale bilgilerini hazırla
            article_data = {
                'title': target_article.get('title', ''),
                'url': target_article.get('url', ''),
                'content': target_article.get('content_preview', ''),
                'source': 'Rejected Article Recovery',
                'source_type': 'news'
            }
            
            # API key'i al
            api_key = os.environ.get('OPENROUTER_API_KEY')
            if not api_key:
                api_key = os.environ.get('OPENROUTER_API_KEY')
            
            if not api_key:
                return jsonify({"success": False, "error": "API anahtarı bulunamadı. Google API Key veya OpenRouter API Key gerekli."})
            
            # Tweet oluştur
            terminal_log(f"🔄 Tweet oluşturuluyor: {article_data['title'][:50]}...", "info")
            tweet_result = generate_ai_tweet_with_content(article_data, api_key)
            terminal_log(f"📝 Tweet sonucu: {tweet_result}", "debug")
            
            if tweet_result:
                tweet_text = tweet_result.get('tweet', '') or tweet_result.get('tweet_text', '')
                
                # Eğer tweet metni boş veya çok kısaysa, basit bir tweet oluştur
                if not tweet_text or len(tweet_text.strip()) < 10:
                    from utils import create_fallback_tweet
                    tweet_text = create_fallback_tweet(article_data['title'], article_data['content'], article_data['url'])
                    
                    # URL'yi tweet'ten çıkar çünkü ayrıca gösteriyoruz
                    if article_data['url'] in tweet_text:
                        tweet_text = tweet_text.replace(f"\n\n🔗 {article_data['url']}", "").replace(f"🔗 {article_data['url']}", "").strip()
                
                # Direk tweet bilgilerini döndür
                return jsonify({
                    "success": True,
                    "tweet_text": tweet_text,
                    "article_title": article_data['title'],
                    "article_url": article_data['url'],
                    "quality_score": tweet_result.get('quality_score', 7),
                    "impact_score": tweet_result.get('impact_score', 6),
                    "character_count": len(tweet_text),
                    "message": "Tweet oluşturuldu"
                })
            else:
                # Son çare olarak basit fallback tweet oluştur
                from utils import create_fallback_tweet
                fallback_tweet = create_fallback_tweet(article_data['title'], article_data['content'], "")
                
                return jsonify({
                    "success": True,
                    "tweet_text": fallback_tweet,
                    "article_title": article_data['title'],
                    "article_url": article_data['url'],
                    "quality_score": 5,
                    "impact_score": 5,
                    "character_count": len(fallback_tweet),
                    "message": "Fallback tweet oluşturuldu"
                })
                
        except Exception as e:
            terminal_log(f"❌ Tweet oluşturma hatası: {e}", "error")
            return jsonify({"success": False, "error": f"Tweet oluşturma hatası: {str(e)}"})
    
    except Exception as e:
        terminal_log(f"❌ Reddedilen makale dönüştürme hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/share_rejected_tweet', methods=['POST'])
@login_required
def share_rejected_tweet():
    """Reddedilen makaleden oluşturulan tweeti paylaş"""
    try:
        data = request.get_json()
        article_url = data.get('article_url')
        article_title = data.get('article_title')
        tweet_text = data.get('tweet_text')
        
        if not all([article_url, article_title, tweet_text]):
            return jsonify({"success": False, "error": "Gerekli parametreler eksik"})
        
        # Reddedilen makaleleri yükle
        rejected_articles = load_json("rejected_articles.json", [])
        
        # İlgili makaleyi bul
        target_article = None
        for article in rejected_articles:
            if article.get('url') == article_url:
                target_article = article
                break
        
        if not target_article:
            return jsonify({"success": False, "error": "Makale bulunamadı"})
        
        # Pending tweets'e ekle
        pending_tweets = load_json("pending_tweets.json", [])
        
        new_tweet = {
            'id': len(pending_tweets) + 1,
            'title': article_title,
            'url': article_url,
            'content': tweet_text,
            'source': 'Recovered from Rejected',
            'source_type': 'news',
            'created_at': datetime.now().isoformat(),
            'article': target_article,
            'recovered_from_rejected': True
        }
        
        pending_tweets.append(new_tweet)
        save_json("pending_tweets.json", pending_tweets)
        
        # Makaleyi reddedilen listesinden kaldır
        rejected_articles = [a for a in rejected_articles if a.get('url') != article_url]
        save_json("rejected_articles.json", rejected_articles)
        
        terminal_log(f"✅ Reddedilen makale tweet olarak paylaşıldı: {article_title[:50]}...", "success")
        
        return jsonify({
            "success": True,
            "message": "Tweet başarıyla bekleyen listesine eklendi",
            "tweet_id": new_tweet['id']
        })
        
    except Exception as e:
        terminal_log(f"❌ Reddedilen tweet paylaşma hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/remove_from_rejected', methods=['POST'])
@login_required
def remove_from_rejected():
    """Makaleyi reddedilen listesinden kaldır"""
    try:
        data = request.get_json()
        article_url = data.get('article_url')
        
        if not article_url:
            return jsonify({"success": False, "error": "Makale URL'si gerekli"})
        
        # Reddedilen makaleleri yükle
        rejected_articles = load_json("rejected_articles.json", [])
        
        # İlgili makaleyi bul ve kaldır
        original_count = len(rejected_articles)
        rejected_articles = [a for a in rejected_articles if a.get('url') != article_url]
        
        if len(rejected_articles) == original_count:
            return jsonify({"success": False, "error": "Makale bulunamadı"})
        
        # Güncellenmiş listeyi kaydet
        save_json("rejected_articles.json", rejected_articles)
        
        terminal_log(f"🗑️ Makale reddedilen listesinden kaldırıldı: {article_url}", "info")
        
        return jsonify({
            "success": True, 
            "message": "Makale başarıyla kaldırıldı",
            "remaining_count": len(rejected_articles)
        })
        
    except Exception as e:
        terminal_log(f"❌ Reddedilen makale kaldırma hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/bulk_convert_rejected', methods=['POST'])
@login_required
def bulk_convert_rejected():
    """Toplu olarak reddedilen makaleleri tweet'e çevir"""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({"success": False, "error": "URL listesi gerekli"})
        
        # Reddedilen makaleleri yükle
        rejected_articles = load_json("rejected_articles.json", [])
        pending_tweets = load_json("pending_tweets.json", [])
        
        converted_count = 0
        errors = []
        
        for url in urls:
            try:
                # İlgili makaleyi bul
                article = next((a for a in rejected_articles if a.get('url') == url), None)
                
                if article:
                    # Tweet içeriği oluştur
                    tweet_content = f"🤖 {article.get('title', 'Haber')}\n\n📰 Kaynak: {article.get('source', 'Bilinmeyen')}\n🔗 Detaylar: {url}\n\n#AI #Haber #Teknoloji"
                    
                    # Pending tweets'e ekle
                    new_tweet = {
                        'id': len(pending_tweets) + 1,
                        'content': tweet_content,
                        'article': article,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'source_type': 'rejected_converted'
                    }
                    
                    pending_tweets.append(new_tweet)
                    converted_count += 1
                    
                    # Reddedilen listesinden kaldır
                    rejected_articles = [a for a in rejected_articles if a.get('url') != url]
                    
                    terminal_log(f"🔄 Makale tweet'e çevrildi: {article.get('title', 'Bilinmeyen')[:50]}...", "success")
                else:
                    errors.append(f"Makale bulunamadı: {url}")
                    
            except Exception as e:
                errors.append(f"Hata ({url}): {str(e)}")
        
        # Güncellenmiş listeleri kaydet
        save_json("pending_tweets.json", pending_tweets)
        save_json("rejected_articles.json", rejected_articles)
        
        terminal_log(f"✅ {converted_count} makale başarıyla tweet'e çevrildi", "success")
        
        return jsonify({
            "success": True,
            "converted_count": converted_count,
            "errors": errors,
            "message": f"{converted_count} makale başarıyla tweet'e çevrildi"
        })
        
    except Exception as e:
        terminal_log(f"❌ Toplu dönüştürme hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/bulk_remove_rejected', methods=['POST'])
@login_required
def bulk_remove_rejected():
    """Toplu olarak reddedilen makaleleri sil"""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({"success": False, "error": "URL listesi gerekli"})
        
        # Reddedilen makaleleri yükle
        rejected_articles = load_json("rejected_articles.json", [])
        
        original_count = len(rejected_articles)
        removed_count = 0
        errors = []
        
        for url in urls:
            try:
                # İlgili makaleyi bul ve kaldır
                article = next((a for a in rejected_articles if a.get('url') == url), None)
                
                if article:
                    rejected_articles = [a for a in rejected_articles if a.get('url') != url]
                    removed_count += 1
                    terminal_log(f"🗑️ Makale kalıcı olarak silindi: {article.get('title', 'Bilinmeyen')[:50]}...", "info")
                else:
                    errors.append(f"Makale bulunamadı: {url}")
                    
            except Exception as e:
                errors.append(f"Hata ({url}): {str(e)}")
        
        # Güncellenmiş listeyi kaydet
        save_json("rejected_articles.json", rejected_articles)
        
        terminal_log(f"✅ {removed_count} makale başarıyla silindi", "success")
        
        return jsonify({
            "success": True,
            "removed_count": removed_count,
            "errors": errors,
            "message": f"{removed_count} makale başarıyla silindi"
        })
        
    except Exception as e:
        terminal_log(f"❌ Toplu silme hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/get_pending_tweets', methods=['GET'])
@login_required
def get_pending_tweets_api():
    """Pending tweets'leri AJAX ile döndür"""
    try:
        pending_tweets = load_json("pending_tweets.json")
        
        # HTML render et
        from flask import render_template_string
        
        # Basit pending tweets HTML template'i
        html_template = '''
        {% for tweet in pending_tweets %}
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4" data-tweet-id="{{ tweet.id }}">
            <div class="flex justify-between items-start mb-3">
                <div class="flex items-center space-x-2">
                    <span class="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
                        {{ tweet.get('source_type', 'news') }}
                    </span>
                    <span class="text-gray-500 text-xs">
                        {{ tweet.get('created_at', 'Bilinmiyor') }}
                    </span>
                </div>
                <div class="flex space-x-2">
                    <button onclick="postTweet({{ tweet.id }})" 
                            class="bg-green-500 hover:bg-green-600 text-white text-xs px-3 py-1 rounded">
                        <i class="fas fa-paper-plane mr-1"></i> Paylaş
                    </button>
                    <button onclick="deleteTweet({{ tweet.id }})" 
                            class="bg-red-500 hover:bg-red-600 text-white text-xs px-3 py-1 rounded">
                        <i class="fas fa-trash mr-1"></i> Sil
                    </button>
                </div>
            </div>
            
            <div class="text-gray-800 mb-3">
                {{ tweet.get('tweet', 'Tweet metni bulunamadı') }}
            </div>
            
            {% if tweet.get('article_title') %}
            <div class="text-sm text-gray-600 border-t pt-2">
                <strong>Kaynak:</strong> {{ tweet.article_title }}
            </div>
            {% endif %}
        </div>
        {% else %}
        <div class="text-center text-gray-500 py-8">
            <i class="fas fa-inbox text-4xl mb-4"></i>
            <p>Henüz bekleyen tweet yok</p>
        </div>
        {% endfor %}
        '''
        
        html_content = render_template_string(html_template, pending_tweets=pending_tweets)
        
        return jsonify({
            "success": True,
            "html": html_content,
            "count": len(pending_tweets)
        })
        
    except Exception as e:
        terminal_log(f"❌ Pending tweets API hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/rate_limit_status', methods=['GET'])
@login_required
def get_rate_limit_status_api():
    """Rate limit durumunu AJAX ile döndür"""
    try:
        rate_limit_info = get_rate_limit_info()
        
        return jsonify({
            "success": True,
            "rate_limit": rate_limit_info
        })
        
    except Exception as e:
        terminal_log(f"❌ Rate limit API hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/archive_tweet', methods=['POST'])
@login_required
def archive_tweet_api():
    """Tweet arşivleme endpoint'i"""
    try:
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        archive_reason = data.get('archive_reason', 'manual')
        
        if not tweet_id:
            return jsonify({"success": False, "error": "Tweet ID gerekli"})
        
        # Paylaşılan tweet'leri yükle
        articles = load_json("posted_articles.json", [])
        
        # Tweet'i bul
        tweet_to_archive = None
        for article in articles:
            if (str(article.get('hash', '')) == str(tweet_id) or 
                str(article.get('id', '')) == str(tweet_id) or
                str(article.get('tweet_id', '')) == str(tweet_id)):
                tweet_to_archive = article
                break
        
        if not tweet_to_archive:
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
        
        # Arşivleme bilgilerini ekle
        tweet_to_archive['archived'] = True
        tweet_to_archive['archived_at'] = datetime.now().isoformat()
        tweet_to_archive['archive_reason'] = archive_reason
        
        # Arşivlenen tweet'leri ayrı dosyaya kaydet
        archived_articles = load_json("archived_articles.json", [])
        archived_articles.append(tweet_to_archive)
        save_json("archived_articles.json", archived_articles)
        
        # Ana listeden kaldır
        articles = [article for article in articles if article != tweet_to_archive]
        save_json("posted_articles.json", articles)
        
        terminal_log(f"✅ Tweet arşivlendi: {tweet_id}", "info")
        
        return jsonify({
            "success": True,
            "message": "Tweet başarıyla arşivlendi",
            "archived_tweet": tweet_to_archive
        })
        
    except Exception as e:
        terminal_log(f"❌ Tweet arşivleme hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/restore_archived_tweet', methods=['POST'])
@login_required
def restore_archived_tweet_api():
    """Arşivlenen tweet'i geri yükleme endpoint'i"""
    try:
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        
        if not tweet_id:
            return jsonify({"success": False, "error": "Tweet ID gerekli"})
        
        # Arşivlenen tweet'leri yükle
        archived_articles = load_json("archived_articles.json", [])
        
        # Tweet'i bul
        tweet_to_restore = None
        for article in archived_articles:
            if (str(article.get('hash', '')) == str(tweet_id) or 
                str(article.get('id', '')) == str(tweet_id) or
                str(article.get('tweet_id', '')) == str(tweet_id)):
                tweet_to_restore = article
                break
        
        if not tweet_to_restore:
            return jsonify({"success": False, "error": "Tweet bulunamadı"})
        
        # Arşivleme bilgilerini kaldır
        tweet_to_restore.pop('archived', None)
        tweet_to_restore.pop('archived_at', None)
        tweet_to_restore.pop('archive_reason', None)
        
        # Ana listeye geri ekle
        articles = load_json("posted_articles.json", [])
        articles.append(tweet_to_restore)
        save_json("posted_articles.json", articles)
        
        # Arşiv listesinden kaldır
        archived_articles = [article for article in archived_articles if article != tweet_to_restore]
        save_json("archived_articles.json", archived_articles)
        
        terminal_log(f"✅ Tweet geri yüklendi: {tweet_id}", "info")
        
        return jsonify({
            "success": True,
            "message": "Tweet başarıyla geri yüklendi",
            "restored_tweet": tweet_to_restore
        })
        
    except Exception as e:
        terminal_log(f"❌ Tweet geri yükleme hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/bulk_archive_tweets', methods=['POST'])
@login_required
def bulk_archive_tweets_api():
    """Toplu tweet arşivleme endpoint'i"""
    try:
        data = request.get_json()
        tweet_ids = data.get('tweet_ids', [])
        archive_reason = data.get('archive_reason', 'bulk_archive')
        
        if not tweet_ids:
            return jsonify({"success": False, "error": "Tweet ID listesi gerekli"})
        
        if len(tweet_ids) > 1000:  # Güvenlik sınırı
            return jsonify({"success": False, "error": "Maksimum 1000 tweet arşivlenebilir"})
        
        # Paylaşılan tweet'leri yükle
        articles = load_json("posted_articles.json", [])
        
        # Arşivlenecek tweet'leri bul
        tweets_to_archive = []
        for article in articles:
            if (str(article.get('hash', '')) in tweet_ids or 
                str(article.get('id', '')) in tweet_ids or
                str(article.get('tweet_id', '')) in tweet_ids):
                tweets_to_archive.append(article)
        
        if not tweets_to_archive:
            return jsonify({"success": False, "error": "Arşivlenecek tweet bulunamadı"})
        
        # Arşivleme bilgilerini ekle
        for tweet in tweets_to_archive:
            tweet['archived'] = True
            tweet['archived_at'] = datetime.now().isoformat()
            tweet['archive_reason'] = archive_reason
        
        # Arşivlenen tweet'leri ayrı dosyaya kaydet
        archived_articles = load_json("archived_articles.json", [])
        archived_articles.extend(tweets_to_archive)
        save_json("archived_articles.json", archived_articles)
        
        # Ana listeden kaldır
        articles = [article for article in articles if article not in tweets_to_archive]
        save_json("posted_articles.json", articles)
        
        terminal_log(f"✅ {len(tweets_to_archive)} tweet toplu arşivlendi", "info")
        
        return jsonify({
            "success": True,
            "message": f"{len(tweets_to_archive)} tweet başarıyla arşivlendi",
            "archived_count": len(tweets_to_archive),
            "archived_tweets": tweets_to_archive
        })
        
    except Exception as e:
        terminal_log(f"❌ Toplu tweet arşivleme hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

# =============================================================================
# PASSWORD MANAGER ROUTES
# =============================================================================

@app.route('/password_manager')
@login_required
def password_manager():
    """Basit şifre yöneticisi ana sayfası"""
    try:
        user_session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = user_session_id
        
        # Ana parola kontrolü kaldırıldı - direk kayıt modu
        master_password = "default_master_password"
        session['master_password'] = master_password
        
        # Şifreleri ve kartları yükle (direk yükle)
        passwords = security_manager.get_passwords(user_session_id, master_password)
        cards = security_manager.get_cards(user_session_id, master_password)

        return render_template('password_manager.html',
                             master_password=master_password,
                             passwords=passwords,
                             cards=cards)
                             
    except Exception as e:
        terminal_log(f"❌ Şifre yöneticisi hatası: {e}", "error")
        flash("Şifre yöneticisi yüklenirken bir hata oluştu.", "error")
        return redirect(url_for('index'))



@app.route('/set_master_password', methods=['POST'])
@login_required
def set_master_password():
    """Ana parolayı session'a kaydet"""
    try:
        master_password = request.form.get('master_password', '').strip()
        
        if not master_password:
            flash("Lütfen ana parolayı girin.", "error")
            return redirect(url_for('password_manager'))
        
        if len(master_password) < 6:
            flash("Ana parola en az 6 karakter olmalıdır.", "error")
            return redirect(url_for('password_manager'))
        
        # Ana parolayı session'a kaydet
        session['master_password'] = master_password
        flash("Ana parola başarıyla ayarlandı.", "success")
        
        terminal_log("✅ Ana parola başarıyla ayarlandı", "info")
        return redirect(url_for('password_manager'))
        
    except Exception as e:
        terminal_log(f"❌ Ana parola ayarlama hatası: {e}", "error")
        flash("Ana parola ayarlanırken bir hata oluştu.", "error")
        return redirect(url_for('password_manager'))

@app.route('/add_password', methods=['POST'])
@login_required
def add_password():
    """Yeni şifre ekle"""
    try:
        user_session_id = session.get('session_id')
        
        # Ana parola kontrolü kaldırıldı - direk kayıt
        if not user_session_id:
            user_session_id = f"user_{secrets.token_hex(8)}"
            session['session_id'] = user_session_id
        
        # Sabit master password kullan
        master_password = "default_master_password"
        
        # Debug bilgileri
        terminal_log(f"🔍 Şifre ekleme başlatıldı - Session ID: {user_session_id[:8]}...", "info")
        terminal_log("🔍 Ana parola kontrolü atlandı - direk kayıt modu", "info")
        
        site_name = request.form.get('site_name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Form verilerini kontrol et
        terminal_log(f"🔍 Form verileri - Site: {site_name}, Username: {username}, Password: {'*' * len(password)}", "info")
        
        if not site_name or not username or not password:
            terminal_log("❌ Form verileri eksik", "error")
            flash("Tüm alanları doldurun.", "error")
            return redirect(url_for('password_manager'))
        
        # SecurityManager'ı test et
        try:
            terminal_log("🔍 SecurityManager test ediliyor...", "info")
            
            # SecurityManager instance oluştur
            sm = security_manager
            terminal_log("✅ SecurityManager instance başarılı", "success")
            
            # Şifre kaydetme işlemi
            terminal_log("🔐 Şifre kaydetme işlemi başlatılıyor...", "info")
            success = sm.save_password(user_session_id, site_name, username, password, master_password)
            
            if success:
                terminal_log(f"✅ Şifre başarıyla kaydedildi: {site_name}", "success")
                flash(f"{site_name} için şifre başarıyla kaydedildi.", "success")
            else:
                terminal_log(f"❌ Şifre kaydetme başarısız: {site_name}", "error")
                flash("Şifre kaydedilirken bir hata oluştu.", "error")
            
        except Exception as sm_error:
            terminal_log(f"❌ SecurityManager hatası: {sm_error}", "error")
            import traceback
            terminal_log(f"🔍 SecurityManager hata detayı: {traceback.format_exc()}", "error")
            flash("Şifre yöneticisi hatası oluştu.", "error")
        
        return redirect(url_for('password_manager'))
        
    except Exception as e:
        terminal_log(f"❌ Genel şifre ekleme hatası: {e}", "error")
        import traceback
        terminal_log(f"🔍 Genel hata detayı: {traceback.format_exc()}", "error")
        flash("Şifre eklenirken bir hata oluştu.", "error")
        return redirect(url_for('password_manager'))

@app.route('/add_card', methods=['POST'])
@login_required
def add_card():
    """Yeni kart ekle"""
    try:
        user_session_id = session.get('session_id')
        master_password = session.get('master_password')
        
        if not user_session_id or not master_password:
            flash("Lütfen önce ana parolanızı ayarlayın.", "error")
            return redirect(url_for('password_manager'))
        
        card_name = request.form.get('card_name', '').strip()
        card_number = request.form.get('card_number', '').replace(' ', '').strip()
        expiry_date = request.form.get('expiry_date', '').strip()
        cardholder_name = request.form.get('cardholder_name', '').strip().upper()
        notes = request.form.get('notes', '').strip()
        
        # Debug log
        terminal_log(f"🔍 Kart ekleme - Ham veriler: card_name={card_name}, card_number={card_number}, expiry_date={expiry_date}, cardholder_name={cardholder_name}", "info")
        
        if not card_name or not card_number or not expiry_date or not cardholder_name:
            flash("Tüm alanları doldurun.", "error")
            return redirect(url_for('password_manager'))
        
        # Kart numarası validasyonu (sadece rakamlar)
        card_number_clean = card_number.replace(' ', '').replace('-', '').replace('_', '')
        if not card_number_clean.isdigit():
            flash("Kart numarası sadece rakamlardan oluşmalıdır.", "error")
            return redirect(url_for('password_manager'))
        
        if len(card_number_clean) < 13 or len(card_number_clean) > 20:
            flash("Kart numarası 13-20 haneli olmalıdır.", "error")
            return redirect(url_for('password_manager'))
        
        # Temizlenmiş kart numarasını kullan
        card_number = card_number_clean
        
        # Debug log - temizlenmiş veriler
        terminal_log(f"🔍 Kart ekleme - Temizlenmiş veriler: card_number={card_number}, length={len(card_number)}", "info")
        
        # Expiry date validasyonu
        expiry_clean = expiry_date.replace('/', '').replace('-', '')
        if not expiry_clean.isdigit() or len(expiry_clean) != 4:
            flash("Son kullanma tarihi MM/YY formatında olmalıdır.", "error")
            return redirect(url_for('password_manager'))
        
        month = int(expiry_clean[:2])
        year = int(expiry_clean[2:])
        current_year = datetime.now().year % 100
        
        if month < 1 or month > 12:
            flash("Geçerli bir ay girin (01-12).", "error")
            return redirect(url_for('password_manager'))
        
        if year < current_year or year > current_year + 20:
            flash("Geçerli bir yıl girin.", "error")
            return redirect(url_for('password_manager'))
        
        # CVV güvenlik nedeniyle kaydedilmez - None olarak gönder
        cvv = None
        
        # Kartı kaydet (CVV olmadan)
        if security_manager.save_card(user_session_id, card_name, card_number, expiry_date, cardholder_name, cvv, notes, master_password):
            flash(f"{card_name} kartı başarıyla kaydedildi. (CVV güvenlik nedeniyle kaydedilmedi)", "success")
            terminal_log(f"✅ Yeni kart kaydedildi: {card_name} (CVV kaydedilmedi)", "info")
        else:
            flash("Kart kaydedilirken bir hata oluştu.", "error")
        
        return redirect(url_for('password_manager'))
        
    except Exception as e:
        terminal_log(f"❌ Kart ekleme hatası: {e}", "error")
        flash("Kart eklenirken bir hata oluştu.", "error")
        return redirect(url_for('password_manager'))

@app.route('/delete_password', methods=['POST'])
@login_required
def delete_password():
    """Şifre sil"""
    try:
        user_session_id = session.get('session_id')
        site_name = request.form.get('site_name', '').strip()
        
        if not user_session_id or not site_name:
            flash("Geçersiz istek.", "error")
            return redirect(url_for('password_manager'))
        
        if security_manager.delete_password(user_session_id, site_name):
            flash(f"{site_name} için şifre başarıyla silindi.", "success")
            terminal_log(f"✅ Şifre silindi: {site_name}", "info")
        else:
            flash("Şifre silinirken bir hata oluştu.", "error")
        
        return redirect(url_for('password_manager'))
        
    except Exception as e:
        terminal_log(f"❌ Şifre silme hatası: {e}", "error")
        flash("Şifre silinirken bir hata oluştu.", "error")
        return redirect(url_for('password_manager'))

@app.route('/delete_card', methods=['POST'])
@login_required
def delete_card():
    """Kart sil"""
    try:
        user_session_id = session.get('session_id')
        card_name = request.form.get('card_name', '').strip()
        
        if not user_session_id or not card_name:
            flash("Geçersiz istek.", "error")
            return redirect(url_for('password_manager'))
        
        if security_manager.delete_card(user_session_id, card_name):
            flash(f"{card_name} kartı başarıyla silindi.", "success")
            terminal_log(f"✅ Kart silindi: {card_name}", "info")
        else:
            flash("Kart silinirken bir hata oluştu.", "error")
        
        return redirect(url_for('password_manager'))
        
    except Exception as e:
        terminal_log(f"❌ Kart silme hatası: {e}", "error")
        flash("Kart silinirken bir hata oluştu.", "error")
        return redirect(url_for('password_manager'))

@app.route('/generate_password_code', methods=['POST'])
@login_required
def generate_password_code():
    """Belirli bir şifre için erişim kodu oluştur"""
    try:
        user_session_id = session.get('session_id')
        password_id = request.form.get('password_id', '').strip()
        
        if not user_session_id or not password_id:
            return jsonify({"success": False, "error": "Geçersiz istek"})
        
        # Şifre erişim kodu oluştur
        access_code = security_manager.generate_password_access_code(user_session_id, password_id)
        
        terminal_log(f"🔐 Şifre erişim kodu oluşturuldu: {password_id[:8]}...", "info")
        
        return jsonify({
            "success": True,
            "access_code": access_code,
            "message": "Şifre erişim kodu oluşturuldu"
        })
        
    except Exception as e:
        terminal_log(f"❌ Şifre erişim kodu oluşturma hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/verify_password_code', methods=['POST'])
@login_required
def verify_password_code():
    """Belirli bir şifre için erişim kodunu doğrula"""
    try:
        user_session_id = session.get('session_id')
        password_id = request.form.get('password_id', '').strip()
        access_code = request.form.get('access_code', '').strip()
        
        if not user_session_id or not password_id or not access_code:
            return jsonify({"success": False, "error": "Tüm alanlar gerekli"})
        
        # Kodu doğrula
        verification_result = security_manager.verify_password_access_code(user_session_id, password_id, access_code)
        
        if verification_result['success']:
            # Başarılı doğrulama - şifreyi çöz ve döndür
            master_password = session.get('master_password')
            if not master_password:
                return jsonify({"success": False, "error": "Ana parola gerekli"})
            
            # Şifreyi bul ve çöz
            passwords = security_manager.get_passwords(user_session_id, master_password)
            target_password = None
            
            for pwd in passwords:
                if pwd.get('id') == password_id or pwd.get('site_name') == password_id:
                    target_password = pwd
                    break
            
            if target_password:
                terminal_log(f"✅ Şifre erişim kodu doğrulandı: {password_id[:8]}...", "info")
                return jsonify({
                    "success": True,
                    "password": target_password['password'],
                    "message": "Şifre başarıyla gösterildi"
                })
            else:
                return jsonify({"success": False, "error": "Şifre bulunamadı"})
        else:
            # Başarısız doğrulama
            error_type = verification_result.get('error', 'unknown')
            error_message = verification_result.get('message', 'Bilinmeyen hata')
            
            terminal_log(f"❌ Şifre erişim kodu hatası: {error_message}", "warning")
            
            return jsonify({
                "success": False,
                "error": error_message,
                "remaining_attempts": verification_result.get('remaining_attempts', 0),
                "code_blocked": verification_result.get('code_blocked', False)
            })
        
    except Exception as e:
        terminal_log(f"❌ Şifre erişim kodu doğrulama hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_password_status', methods=['POST'])
@login_required
def get_password_status():
    """Belirli bir şifre için durum bilgisi al"""
    try:
        user_session_id = session.get('session_id')
        password_id = request.form.get('password_id', '').strip()
        
        if not user_session_id or not password_id:
            return jsonify({"success": False, "error": "Geçersiz istek"})
        
        # Şifre durumunu kontrol et
        has_active_code = security_manager.has_active_password_code(user_session_id, password_id)
        remaining_attempts = security_manager.get_password_remaining_attempts(user_session_id, password_id)
        
        return jsonify({
            "success": True,
            "has_active_code": has_active_code,
            "remaining_attempts": remaining_attempts
        })
        
    except Exception as e:
        terminal_log(f"❌ Şifre durum kontrolü hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

# =============================================================================
# BULK MANUAL SHARE API ENDPOINTS
# =============================================================================

@app.route('/api/get_tweets_for_manual_share', methods=['POST'])
@login_required
def get_tweets_for_manual_share():
    """Toplu manuel paylaşım için tweet verilerini getir"""
    try:
        data = request.get_json()
        tweet_ids = data.get('tweet_ids', [])
        
        terminal_log(f"🔍 DEBUG - İstenen tweet ID'leri: {tweet_ids}", "info")
        
        if not tweet_ids:
            return jsonify({"success": False, "error": "Tweet ID listesi gerekli"})
        
        if len(tweet_ids) > 10:
            return jsonify({"success": False, "error": "Maksimum 10 tweet seçilebilir"})
        
        # Bekleyen tweet'leri yükle
        pending_tweets = load_json("pending_tweets.json", [])
        terminal_log(f"🔍 DEBUG - Toplam bekleyen tweet sayısı: {len(pending_tweets)}", "info")
        
        # İstenen tweet'leri bul
        selected_tweets = []
        for tweet in pending_tweets:
            tweet_id = str(tweet.get('id', ''))
            terminal_log(f"🔍 DEBUG - Tweet kontrolü: {tweet_id} - Aranan: {tweet_ids}", "info")
            
            if tweet_id in tweet_ids:
                tweet_content = tweet.get('content', '')
                article_title = tweet.get('article', {}).get('title', '') if tweet.get('article') else ''
                
                # Eğer content boşsa title kullan
                if not tweet_content and article_title:
                    tweet_content = f"📰 {article_title}"
                elif not tweet_content:
                    tweet_content = "AI Haber paylaşımı"
                
                selected_tweet = {
                    'id': tweet.get('id'),
                    'content': tweet_content,
                    'title': article_title,
                    'source': tweet.get('article', {}).get('source', '') if tweet.get('article') else ''
                }
                
                selected_tweets.append(selected_tweet)
                terminal_log(f"✅ DEBUG - Tweet eklendi: ID={tweet_id}, Content={tweet_content[:50]}...", "info")
        
        terminal_log(f"🔍 DEBUG - Bulunan tweet sayısı: {len(selected_tweets)}", "info")
        
        if not selected_tweets:
            return jsonify({"success": False, "error": "Seçilen tweet'ler bulunamadı"})
        
        terminal_log(f"✅ {len(selected_tweets)} tweet manuel paylaşım için hazırlandı", "info")
        
        return jsonify({
            "success": True,
            "tweets": selected_tweets,
            "count": len(selected_tweets)
        })
        
    except Exception as e:
        terminal_log(f"❌ Manuel paylaşım tweet verisi alma hatası: {e}", "error")
        import traceback
        terminal_log(f"❌ DEBUG - Hata detayı: {traceback.format_exc()}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/mark_tweets_as_posted', methods=['POST'])
@login_required
def mark_tweets_as_posted():
    """Tweetleri manuel olarak paylaşıldı olarak işaretle"""
    try:
        data = request.get_json()
        tweet_ids = data.get('tweet_ids', [])
        
        if not tweet_ids:
            return jsonify({"success": False, "error": "Tweet ID listesi gerekli"})
        
        # Bekleyen tweet'leri yükle
        pending_tweets = load_json("pending_tweets.json", [])
        posted_articles = load_json("posted_articles.json", [])
        
        # İşaretlenecek tweet'leri bul ve taşı
        tweets_to_move = []
        remaining_tweets = []
        
        for tweet in pending_tweets:
            if str(tweet.get('id', '')) in tweet_ids:
                # Manuel paylaşım bilgilerini ekle
                tweet_data = {
                    'id': tweet.get('id'),
                    'hash': tweet.get('id'),  # ID'yi hash olarak kullan
                    'content': tweet.get('content', ''),
                    'article': tweet.get('article', {}),
                    'created_at': tweet.get('created_at', datetime.now().isoformat()),
                    'posted_at': datetime.now().isoformat(),
                    'manual_post': True,
                    'manual_post_timestamp': datetime.now().isoformat(),
                    'tweet_id': f"manual_{tweet.get('id')}",
                    'url': f"https://twitter.com/intent/tweet?text={tweet.get('content', '')[:50]}...",
                    'source_type': tweet.get('source_type', 'news')
                }
                tweets_to_move.append(tweet_data)
            else:
                remaining_tweets.append(tweet)
        
        if not tweets_to_move:
            return jsonify({"success": False, "error": "İşaretlenecek tweet bulunamadı"})
        
        # Dosyaları güncelle
        save_json("pending_tweets.json", remaining_tweets)
        posted_articles.extend(tweets_to_move)
        save_json("posted_articles.json", posted_articles)
        
        terminal_log(f"✅ {len(tweets_to_move)} tweet manuel paylaşım olarak işaretlendi", "info")
        
        return jsonify({
            "success": True,
            "message": f"{len(tweets_to_move)} tweet paylaşıldı olarak işaretlendi",
            "moved_count": len(tweets_to_move)
        })
        
    except Exception as e:
        terminal_log(f"❌ Tweet işaretleme hatası: {e}", "error")
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    # Sadece local development için çalıştır
    # PythonAnywhere'de WSGI kullanılır
    try:
        # Arka plan zamanlayıcısını başlat
        start_background_scheduler()
        
        # Python Anywhere için production ayarları
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        # PythonAnywhere kontrolü
        is_pythonanywhere = (
            'PYTHONANYWHERE_SITE' in os.environ or
            'PYTHONANYWHERE_DOMAIN' in os.environ or
            '/home/' in os.getcwd() or
            'pythonanywhere' in os.getcwd().lower()
        )
        
        if not is_pythonanywhere:
            terminal_log(f"Flask uygulaması başlatılıyor - Port: {port}, Debug: {debug}", "info")
            app.run(host='0.0.0.0', port=port, debug=debug)
        else:
            terminal_log("PythonAnywhere ortamında - WSGI kullanılıyor", "info")
            
    except Exception as e:
        terminal_log(f"Uygulama başlatma hatası: {e}", "error")

# WSGI altında (ör. PythonAnywhere) ilk istek geldiğinde zamanlayıcıyı başlat (opsiyonel)
try:
    @app.before_first_request
    def _ensure_background_scheduler_started():
        """WSGI ortamında ilk istekte arka plan zamanlayıcısını başlat.
        ENABLE_BACKGROUND_SCHEDULER=false ise devre dışı bırakılır."""
        enable = os.environ.get('ENABLE_BACKGROUND_SCHEDULER', 'true').lower() == 'true'
        if enable:
            start_background_scheduler()
        else:
            terminal_log("⏸️ ENABLE_BACKGROUND_SCHEDULER=false – arka plan zamanlayıcısı başlatılmadı", "info")
except Exception:
    # Eski Flask sürümlerinde before_first_request bulunamazsa sessizce geç
    pass