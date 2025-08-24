#!/usr/bin/env python3
"""
PythonAnywhere için gerekli static dosyaları indiren script
Bu script Bootstrap ve Font Awesome dosyalarını static klasörüne indirir
"""

import os
import requests
import urllib.request
from pathlib import Path

def download_file(url, local_path):
    """Dosyayı indir ve kaydet"""
    try:
        print(f"İndiriliyor: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        # Klasörü oluştur
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Dosyayı kaydet
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Başarıyla indirildi: {local_path}")
        return True
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

def main():
    """Ana fonksiyon"""
    print("🚀 PythonAnywhere için static dosyalar indiriliyor...")
    
    # Static klasör yolu
    static_dir = Path("static")
    
    # İndirilecek dosyalar
    files_to_download = [
        # Bootstrap CSS
        {
            "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
            "local_path": static_dir / "css" / "bootstrap.min.css"
        },
        # Bootstrap JS
        {
            "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
            "local_path": static_dir / "js" / "bootstrap.bundle.min.js"
        },
        # Font Awesome CSS
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
            "local_path": static_dir / "css" / "all.min.css"
        },
        # Font Awesome Webfonts (gerekli dosyalar)
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2",
            "local_path": static_dir / "webfonts" / "fa-solid-900.woff2"
        },
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2",
            "local_path": static_dir / "webfonts" / "fa-regular-400.woff2"
        },
        {
            "url": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.woff2",
            "local_path": static_dir / "webfonts" / "fa-brands-400.woff2"
        }
    ]
    
    success_count = 0
    total_count = len(files_to_download)
    
    for file_info in files_to_download:
        if download_file(file_info["url"], file_info["local_path"]):
            success_count += 1
    
    print(f"\n📊 İndirme tamamlandı: {success_count}/{total_count} dosya başarıyla indirildi")
    
    if success_count == total_count:
        print("✅ Tüm dosyalar başarıyla indirildi!")
        print("🚀 PythonAnywhere'de artık local dosyalar kullanılacak")
    else:
        print("⚠️ Bazı dosyalar indirilemedi. CDN fallback sistemi kullanılacak")

if __name__ == "__main__":
    main()
