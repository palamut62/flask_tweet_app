#!/usr/bin/env python3
"""
PythonAnywhere için özel konfigürasyon
Bu dosya PythonAnywhere ortamında çalışırken gerekli ayarları yapar
"""

import os
import sys

def configure_for_pythonanywhere():
    """
    PythonAnywhere ortamını yapılandırır
    Returns:
        bool: PythonAnywhere'de çalışıyorsa True, değilse False
    """
    
    # PythonAnywhere'de çalışıp çalışmadığını kontrol et
    is_pythonanywhere = (
        'PYTHONANYWHERE_SITE' in os.environ or
        'PYTHONANYWHERE_DOMAIN' in os.environ or
        '/home/' in os.getcwd() or
        'pythonanywhere' in os.getcwd().lower()
    )
    
    if is_pythonanywhere:
        print("🐍 PythonAnywhere ortamı tespit edildi")
        
        # Environment variables'ları manuel olarak ayarla
        setup_environment_variables()
        
        # Python path'ini ayarla
        setup_python_path()
        
        # Static dosya yollarını ayarla
        setup_static_paths()
        
        print("✅ PythonAnywhere konfigürasyonu tamamlandı")
    
    return is_pythonanywhere

def setup_environment_variables():
    """Environment variables'ları ayarla"""
    
    # Temel environment variables
    env_vars = {
        'FLASK_ENV': 'production',
        'DEBUG': 'False',
        'USE_LOCAL_ASSETS': 'True',
        'PYTHONANYWHERE_MODE': 'True'
    }
    
    # .env dosyasından oku (varsa)
    env_file = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_file):
        print(f"📄 .env dosyası bulundu: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Environment variables'ları ayarla
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"🔧 {key} = {value}")

def setup_python_path():
    """Python path'ini ayarla"""
    
    # Proje dizinini Python path'ine ekle
    project_dir = os.getcwd()
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
        print(f"📁 Python path'e eklendi: {project_dir}")

def setup_static_paths():
    """Static dosya yollarını ayarla"""
    
    # Static dosya dizinlerini oluştur
    static_dirs = [
        'static/css',
        'static/js', 
        'static/webfonts',
        'static/images'
    ]
    
    for static_dir in static_dirs:
        if not os.path.exists(static_dir):
            os.makedirs(static_dir, exist_ok=True)
            print(f"📁 Dizin oluşturuldu: {static_dir}")

def check_pythonanywhere_requirements():
    """PythonAnywhere gereksinimlerini kontrol et"""
    
    required_packages = [
        'flask',
        'requests',
        'python-dotenv',
        'tweepy',
        'beautifulsoup4'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️ Eksik paketler: {', '.join(missing_packages)}")
        print("💡 Çözüm: pip install --user " + " ".join(missing_packages))
        return False
    
    print("✅ Tüm gerekli paketler yüklü")
    return True

if __name__ == "__main__":
    # Test amaçlı çalıştırma
    is_pa = configure_for_pythonanywhere()
    print(f"PythonAnywhere: {is_pa}")
    check_pythonanywhere_requirements()
