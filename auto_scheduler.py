from apscheduler.schedulers.blocking import BlockingScheduler
from app import check_and_post_articles
from utils import safe_log, load_automation_settings
import logging

# Logları göster
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def get_interval_hours():
    """Ayarlardan kontrol aralığını al"""
    try:
        settings = load_automation_settings()
        interval = settings.get('check_interval_hours', 2)
        safe_log(f'Ayarlardan okunan kontrol aralığı: {interval} saat', "INFO")
        return interval
    except Exception as e:
        safe_log(f'Ayar okuma hatası, varsayılan 2 saat kullanılacak: {e}', "WARNING")
        return 2

scheduler = BlockingScheduler()

# Ayarlardan okunan saat aralığı ile çalışır
def scheduled_job():
    safe_log('Otomatik haber kontrolü başlatılıyor...', "INFO")
    
    # Otomatik mod kontrolü
    try:
        settings = load_automation_settings()
        if not settings.get('auto_mode', False):
            safe_log('Otomatik mod devre dışı, atlanıyor...', "INFO")
            return
    except Exception as e:
        safe_log(f'Ayar kontrolü hatası: {e}', "WARNING")
        return
    
    # Yeni makaleleri kontrol et
    result = check_and_post_articles()
    safe_log(f'Makale kontrol sonucu: {result}', "INFO")

if __name__ == "__main__":
    # Dinamik aralık ile job tanımla
    interval_hours = get_interval_hours()
    scheduler.add_job(scheduled_job, 'interval', hours=interval_hours, id='auto_poster')
    
    logging.info(f'Otomatik paylaşım zamanlayıcı başlatıldı. Kontrol aralığı: {interval_hours} saat')
    scheduler.start() 