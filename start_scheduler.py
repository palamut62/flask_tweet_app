#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Otomatik Tweet Zamanlayıcı Başlatıcı
Bu script otomatik tweet paylaşım sistemini başlatır.
"""

import os
import sys
import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import logging

# Logging ayarları
logging.basicConfig(
    level=logging.INFO, 
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

def run_auto_check():
    """Otomatik haber kontrolü ve tweet paylaşımı"""
    try:
        logging.info("🔄 Otomatik haber kontrolü başlatılıyor...")
        
        # app.py'den fonksiyonu import et
        from app import check_and_post_articles, load_automation_settings
        
        # Ayarları kontrol et
        settings = load_automation_settings()
        if not settings.get('auto_post_enabled', False):
            logging.info("⏸️ Otomatik paylaşım devre dışı, atlanıyor...")
            return
        
        # Haber kontrolü yap
        result = check_and_post_articles()
        logging.info(f"✅ Otomatik kontrol tamamlandı: {result.get('message', 'Sonuç yok')}")
        
    except Exception as e:
        logging.error(f"❌ Otomatik kontrol hatası: {e}")

def main():
    """Ana zamanlayıcı fonksiyonu"""
    logging.info("🚀 AI Tweet Bot Otomatik Zamanlayıcı Başlatıldı")
    logging.info("=" * 60)
    
    # Zamanlayıcı oluştur
    scheduler = BlockingScheduler()
    
    # Her 3 saatte bir çalışacak şekilde ayarla
    scheduler.add_job(
        run_auto_check,
        'interval',
        hours=3,
        id='auto_tweet_job',
        name='Otomatik Tweet Paylaşımı'
    )
    
    logging.info("⏰ Zamanlayıcı ayarlandı: Her 3 saatte bir çalışacak")
    logging.info("🛑 Durdurmak için Ctrl+C tuşlayın")
    logging.info("=" * 60)
    
    try:
        # İlk çalışmayı hemen yap
        logging.info("🔄 İlk kontrol başlatılıyor...")
        run_auto_check()
        
        # Zamanlayıcıyı başlat
        scheduler.start()
        
    except KeyboardInterrupt:
        logging.info("🛑 Zamanlayıcı kullanıcı tarafından durduruldu")
        scheduler.shutdown()
    except Exception as e:
        logging.error(f"❌ Zamanlayıcı hatası: {e}")
        scheduler.shutdown()

if __name__ == "__main__":
    main() 