from apscheduler.schedulers.blocking import BlockingScheduler
from app import check_and_post_articles
import logging

# Logları göster
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

scheduler = BlockingScheduler()

# Her 2 saatte bir çalışacak şekilde ayarlandı (aralığı değiştirebilirsin)
@scheduler.scheduled_job('interval', hours=2)
def scheduled_job():
    logging.info('Otomatik paylaşım başlatılıyor...')
    result = check_and_post_articles()
    logging.info(f'Sonuç: {result}')

if __name__ == "__main__":
    logging.info('Otomatik paylaşım zamanlayıcı başlatıldı.')
    scheduler.start() 