#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Otomatik Zamanlayıcı Yardımcı Modülü
Bu modül otomatik tweet paylaşım sisteminin yardımcı fonksiyonlarını içerir.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

def setup_logging():
    """Logging ayarlarını yapılandır"""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler('scheduler.log'),
            logging.StreamHandler()
        ]
    )

def check_scheduler_status():
    """Zamanlayıcı durumunu kontrol et"""
    try:
        # Scheduler log dosyasını kontrol et
        if os.path.exists('scheduler.log'):
            with open('scheduler.log', 'r', encoding='utf-8') as f:
                last_lines = f.readlines()[-10:]  # Son 10 satır
                return {
                    'status': 'running',
                    'last_logs': last_lines,
                    'log_file': 'scheduler.log'
                }
        else:
            return {
                'status': 'not_started',
                'message': 'Scheduler log dosyası bulunamadı'
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def get_scheduler_config():
    """Zamanlayıcı ayarlarını al"""
    try:
        from app import load_automation_settings
        settings = load_automation_settings()
        return {
            'auto_mode': settings.get('auto_mode', False),
            'check_interval_hours': settings.get('check_interval_hours', 3),
            'last_check': settings.get('last_check_time', 'Bilinmiyor')
        }
    except Exception as e:
        return {
            'error': f'Ayar okuma hatası: {e}',
            'auto_mode': False,
            'check_interval_hours': 3
        }

def validate_scheduler_requirements():
    """Zamanlayıcı için gerekli dosyaları kontrol et"""
    required_files = [
        'app.py',
        'utils.py',
        'automation_settings.json',
        'news_sources.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return {
        'valid': len(missing_files) == 0,
        'missing_files': missing_files
    }

if __name__ == "__main__":
    setup_logging()
    logging.info("🔍 Zamanlayıcı durumu kontrol ediliyor...")
    
    # Durum kontrolü
    status = check_scheduler_status()
    print(f"Durum: {status['status']}")
    
    # Konfigürasyon kontrolü
    config = get_scheduler_config()
    print(f"Otomatik Mod: {config.get('auto_mode', False)}")
    print(f"Kontrol Aralığı: {config.get('check_interval_hours', 3)} saat")
    
    # Gereksinim kontrolü
    requirements = validate_scheduler_requirements()
    if requirements['valid']:
        print("✅ Tüm gerekli dosyalar mevcut")
    else:
        print(f"❌ Eksik dosyalar: {requirements['missing_files']}")
