from apscheduler.schedulers.blocking import BlockingScheduler
from app import check_and_post_articles
from utils import safe_log
import logging

# Logları göster
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

scheduler = BlockingScheduler()

# Her 2 saatte bir çalışacak şekilde ayarlandı (aralığı değiştirebilirsin)
@scheduler.scheduled_job('interval', hours=2)
def scheduled_job():
    safe_log('Otomatik paylaşım başlatılıyor...', "INFO")
    
    # Yeni makaleleri kontrol et
    result = check_and_post_articles()
    safe_log(f'Makale kontrol sonucu: {result}', "INFO")

if __name__ == "__main__":
    logging.info('Otomatik paylaşım zamanlayıcı başlatıldı.')
    scheduler.start() 