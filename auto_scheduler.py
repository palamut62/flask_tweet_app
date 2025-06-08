from apscheduler.schedulers.blocking import BlockingScheduler
from app import check_and_post_articles
from utils import check_and_retry_rate_limited_tweets, safe_log
import logging

# Logları göster
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

scheduler = BlockingScheduler()

# Her 2 saatte bir çalışacak şekilde ayarlandı (aralığı değiştirebilirsin)
@scheduler.scheduled_job('interval', hours=2)
def scheduled_job():
    safe_log('Otomatik paylaşım başlatılıyor...', "INFO")
    
    # Önce yeni makaleleri kontrol et
    result = check_and_post_articles()
    safe_log(f'Makale kontrol sonucu: {result}', "INFO")
    
    # Sonra rate limit tweet'lerini kontrol et
    try:
        rate_limit_result = check_and_retry_rate_limited_tweets()
        safe_log(f'Rate limit kontrol sonucu: {rate_limit_result}', "INFO")
    except Exception as e:
        safe_log(f'Rate limit kontrol hatası: {e}', "ERROR")

# Her 30 dakikada bir sadece rate limit tweet'lerini kontrol et
@scheduler.scheduled_job('interval', minutes=30)
def rate_limit_check_job():
    safe_log('Rate limit tweet kontrol başlatılıyor...', "INFO")
    try:
        rate_limit_result = check_and_retry_rate_limited_tweets()
        safe_log(f'Rate limit kontrol sonucu: {rate_limit_result}', "INFO")
    except Exception as e:
        safe_log(f'Rate limit kontrol hatası: {e}', "ERROR")

if __name__ == "__main__":
    logging.info('Otomatik paylaşım zamanlayıcı başlatıldı.')
    scheduler.start() 