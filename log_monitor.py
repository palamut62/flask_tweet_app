#!/usr/bin/env python3
"""
PythonAnywhere Log İzleyici
Bu script sürekli olarak log dosyalarını izler
"""

import os
import time
import subprocess
from datetime import datetime

def monitor_logs():
    """Log dosyalarını sürekli izle"""
    print("👀 Log İzleme Başlatıldı...")
    print("Ctrl+C ile durdurun")
    
    # İzlenecek dosyalar
    log_files = [
        'scheduler.log',
        'app.log',
        'error.log'
    ]
    
    # Dosya pozisyonları
    positions = {}
    
    while True:
        try:
            for log_file in log_files:
                if os.path.exists(log_file):
                    current_size = os.path.getsize(log_file)
                    
                    if log_file not in positions:
                        positions[log_file] = current_size
                        print(f"📄 {log_file} izleniyor...")
                    elif current_size > positions[log_file]:
                        # Yeni içerik var
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(positions[log_file])
                            new_content = f.read()
                            if new_content.strip():
                                print(f"\n🆕 {log_file} - {datetime.now()}:")
                                print(new_content)
                        
                        positions[log_file] = current_size
            
            time.sleep(2)  # 2 saniye bekle
            
        except KeyboardInterrupt:
            print("\n⏹️ Log izleme durduruldu")
            break
        except Exception as e:
            print(f"❌ Log izleme hatası: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_logs()
