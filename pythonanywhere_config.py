# PythonAnywhere Özel Konfigürasyonu
# Bu dosya PythonAnywhere'de çalışırken kullanılacak özel ayarları içerir

import os

# PythonAnywhere'de static dosya yollarını düzelt
def configure_for_pythonanywhere():
    """PythonAnywhere için özel konfigürasyon"""
    
    # Static dosya yolu düzeltmesi
    if 'PYTHONANYWHERE_SITE' in os.environ:
        # PythonAnywhere'de çalışıyor
        os.environ['STATIC_URL'] = '/static/'
        os.environ['MEDIA_URL'] = '/media/'
        
        # CDN erişim sorunları için
        os.environ['USE_LOCAL_ASSETS'] = 'true'
        
        # Debug modunu kapat (production için)
        os.environ['DEBUG'] = 'False'
        
        # SSL/HTTPS ayarları
        os.environ['PREFERRED_URL_SCHEME'] = 'https'
        
        print("✅ PythonAnywhere konfigürasyonu aktif")
        return True
    else:
        # Lokal geliştirme
        print("ℹ️ Lokal geliştirme modu")
        return False

# PythonAnywhere'de CDN sorunları için fallback sistemi
PYTHONANYWHERE_CDN_FALLBACKS = {
    'bootstrap_css': [
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
        'https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css',
        'https://unpkg.com/bootstrap@5.3.0/dist/css/bootstrap.min.css'
    ],
    'bootstrap_js': [
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js',
        'https://unpkg.com/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
    ],
    'fontawesome': [
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
        'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css',
        'https://unpkg.com/@fortawesome/fontawesome-free@6.4.0/css/all.min.css'
    ]
}

# PythonAnywhere'de önerilen ayarlar
PYTHONANYWHERE_RECOMMENDATIONS = {
    'static_files': {
        'use_local_assets': True,
        'cache_control': 'public, max-age=31536000',
        'gzip_compression': True
    },
    'security': {
        'https_only': True,
        'secure_cookies': True,
        'csrf_protection': True
    },
    'performance': {
        'enable_caching': True,
        'compress_responses': True,
        'minify_assets': True
    }
}

if __name__ == "__main__":
    configure_for_pythonanywhere()
