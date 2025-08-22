#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otomatik Rate Limit Sıfırlama Sistemi
Bu sistem, Twitter API rate limit'ini otomatik olarak sıfırlar.
"""

import json
import time
import os
import schedule
from datetime import datetime, timedelta
import logging

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rate_limit_reset.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Dosya yolları
RATE_LIMIT_FILE = "rate_limit_status.json"
RESET_LOG_FILE = "rate_limit_reset_history.json"

def load_json(filename, default=None):
    """JSON dosyasını yükle"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default if default is not None else {}
    except Exception as e:
        logger.error(f"❌ {filename} yükleme hatası: {e}")
        return default if default is not None else {}

def save_json(filename, data):
    """JSON dosyasını kaydet"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"❌ {filename} kaydetme hatası: {e}")
        return False

def check_rate_limit_status():
    """Rate limit durumunu kontrol et"""
    rate_limit_status = load_json(RATE_LIMIT_FILE, {})
    
    if not rate_limit_status:
        logger.warning("Rate limit dosyası bulunamadı")
        return False
    
    current_time = time.time()
    
    for endpoint, status in rate_limit_status.items():
        requests_made = status.get('requests', 0)
        reset_time = status.get('reset_time', 0)
        
        # Limit bilgileri
        if endpoint == "tweets":
            limit = 25  # Free plan limit
        else:
            limit = 100
        
        # Zaman hesaplamaları
        time_until_reset = reset_time - current_time
        minutes_until_reset = int(time_until_reset / 60) if time_until_reset > 0 else 0
        
        logger.info(f"📊 {endpoint.upper()}: {requests_made}/{limit} kullanım")
        logger.info(f"⏰ Reset'e kalan: {minutes_until_reset} dakika")
        
        # Rate limit aşıldı mı kontrol et
        if requests_made >= limit:
            logger.warning(f"🚨 {endpoint.upper()} rate limit aşıldı!")
            return True
    
    return False

def reset_rate_limit():
    """Rate limit'i sıfırla"""
    try:
        current_time = time.time()
        
        # Mevcut rate limit durumunu yükle
        rate_limit_status = load_json(RATE_LIMIT_FILE, {})
        
        # Her endpoint için sıfırla
        for endpoint in rate_limit_status:
            rate_limit_status[endpoint] = {
                "requests": 0,
                "reset_time": current_time + 900,  # 15 dakika sonra
                "last_request": current_time
            }
        
        # Sıfırlanmış durumu kaydet
        if save_json(RATE_LIMIT_FILE, rate_limit_status):
            logger.info("✅ Rate limit başarıyla sıfırlandı")
            
            # Sıfırlama geçmişini kaydet
            log_reset_event("Otomatik sıfırlama")
            
            return True
        else:
            logger.error("❌ Rate limit sıfırlama başarısız")
            return False
            
    except Exception as e:
        logger.error(f"❌ Rate limit sıfırlama hatası: {e}")
        return False

def log_reset_event(reason):
    """Sıfırlama olayını logla"""
    try:
        reset_history = load_json(RESET_LOG_FILE, [])
        
        reset_event = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "previous_usage": get_current_usage()
        }
        
        reset_history.append(reset_event)
        
        # Son 100 olayı tut
        if len(reset_history) > 100:
            reset_history = reset_history[-100:]
        
        save_json(RESET_LOG_FILE, reset_history)
        
    except Exception as e:
        logger.error(f"❌ Reset log hatası: {e}")

def get_current_usage():
    """Mevcut kullanım durumunu al"""
    try:
        rate_limit_status = load_json(RATE_LIMIT_FILE, {})
        usage = {}
        
        for endpoint, status in rate_limit_status.items():
            usage[endpoint] = {
                "requests": status.get('requests', 0),
                "limit": 25 if endpoint == "tweets" else 100
            }
        
        return usage
    except Exception as e:
        logger.error(f"❌ Kullanım durumu alma hatası: {e}")
        return {}

def check_daily_limit():
    """Günlük limit kontrolü"""
    try:
        current_time = time.time()
        current_date = datetime.fromtimestamp(current_time).date()
        
        # Günlük kullanım dosyasını kontrol et
        daily_usage_file = f"daily_usage_{current_date}.json"
        daily_usage = load_json(daily_usage_file, {"tweets": 0, "date": current_date.isoformat()})
        
        # Bugünkü tweet sayısını kontrol et
        today_tweets = daily_usage.get("tweets", 0)
        
        logger.info(f"📅 Günlük tweet kullanımı: {today_tweets}/25")
        
        # Günlük limit aşıldı mı?
        if today_tweets >= 25:
            logger.info("🎯 Günlük 25 tweet limiti aşıldı, rate limit sıfırlanıyor...")
            reset_rate_limit()
            
            # Günlük kullanımı sıfırla
            daily_usage["tweets"] = 0
            save_json(daily_usage_file, daily_usage)
            
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Günlük limit kontrolü hatası: {e}")
        return False

def update_daily_usage(tweet_count=1):
    """Günlük kullanımı güncelle"""
    try:
        current_date = datetime.now().date()
        daily_usage_file = f"daily_usage_{current_date}.json"
        
        daily_usage = load_json(daily_usage_file, {"tweets": 0, "date": current_date.isoformat()})
        daily_usage["tweets"] += tweet_count
        
        save_json(daily_usage_file, daily_usage)
        
        logger.info(f"📊 Günlük kullanım güncellendi: {daily_usage['tweets']}/25")
        
    except Exception as e:
        logger.error(f"❌ Günlük kullanım güncelleme hatası: {e}")

def schedule_rate_limit_reset():
    """Rate limit sıfırlama zamanlaması"""
    
    # Her 15 dakikada bir kontrol et
    schedule.every(15).minutes.do(check_rate_limit_status)
    
    # Her gün saat 00:00'da günlük limit kontrolü
    schedule.every().day.at("00:00").do(check_daily_limit)
    
    # Her saat başı kontrol et
    schedule.every().hour.do(check_rate_limit_status)
    
    logger.info("⏰ Rate limit sıfırlama zamanlaması başlatıldı")
    logger.info("   • Her 15 dakikada bir kontrol")
    logger.info("   • Her saat başı kontrol")
    logger.info("   • Her gün 00:00'da günlük limit kontrolü")

def run_scheduler():
    """Zamanlayıcıyı çalıştır"""
    logger.info("🚀 Otomatik Rate Limit Sıfırlama Sistemi Başlatılıyor...")
    
    # İlk kontrol
    check_rate_limit_status()
    check_daily_limit()
    
    # Zamanlamayı ayarla
    schedule_rate_limit_reset()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1 dakika bekle
            
    except KeyboardInterrupt:
        logger.info("⏹️  Sistem durduruldu")
    except Exception as e:
        logger.error(f"❌ Zamanlayıcı hatası: {e}")

def manual_reset():
    """Manuel sıfırlama"""
    logger.info("🔧 Manuel rate limit sıfırlama başlatılıyor...")
    
    if reset_rate_limit():
        logger.info("✅ Manuel sıfırlama başarılı")
        return True
    else:
        logger.error("❌ Manuel sıfırlama başarısız")
        return False

def get_reset_history():
    """Sıfırlama geçmişini al"""
    try:
        reset_history = load_json(RESET_LOG_FILE, [])
        
        print("📋 Rate Limit Sıfırlama Geçmişi")
        print("=" * 50)
        
        for i, event in enumerate(reset_history[-10:], 1):  # Son 10 olay
            timestamp = event.get('timestamp', '')
            reason = event.get('reason', '')
            
            print(f"{i}. {timestamp} - {reason}")
        
        return reset_history
        
    except Exception as e:
        logger.error(f"❌ Geçmiş alma hatası: {e}")
        return []

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "reset":
            manual_reset()
        elif command == "check":
            check_rate_limit_status()
        elif command == "history":
            get_reset_history()
        elif command == "daily":
            check_daily_limit()
        else:
            print("Kullanım:")
            print("  python auto_rate_limit_reset.py reset    - Manuel sıfırlama")
            print("  python auto_rate_limit_reset.py check    - Durum kontrolü")
            print("  python auto_rate_limit_reset.py history  - Geçmiş görüntüleme")
            print("  python auto_rate_limit_reset.py daily    - Günlük limit kontrolü")
            print("  python auto_rate_limit_reset.py          - Otomatik sistem başlat")
    else:
        run_scheduler()
