#!/usr/bin/env python3
"""
PythonAnywhere WSGI Güvenli Konfigürasyonu
Bu dosya PythonAnywhere'de Flask uygulamasını çalıştırmak için kullanılır
Hata durumlarını güvenli şekilde yönetir
"""

import sys
import os
import traceback

# Proje dizinini Python path'ine ekle
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Environment değişkenlerini ayarla
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('PYTHONANYWHERE_MODE', 'True')
os.environ.setdefault('DEBUG', 'False')

# Hata yakalama için wrapper fonksiyon
def create_safe_application():
    """Güvenli Flask uygulaması oluştur"""
    
    try:
        # PythonAnywhere konfigürasyonunu yükle
        try:
            from pythonanywhere_config import configure_for_pythonanywhere
            is_pythonanywhere = configure_for_pythonanywhere()
            print(f"🐍 PythonAnywhere tespit edildi: {is_pythonanywhere}")
        except ImportError as e:
            print(f"ℹ️ PythonAnywhere konfigürasyonu bulunamadı: {e}")
            is_pythonanywhere = False
        except Exception as e:
            print(f"⚠️ PythonAnywhere konfigürasyon hatası: {e}")
            is_pythonanywhere = False

        # Flask uygulamasını import et
        try:
            from app import app as flask_app
            print("✅ Flask uygulaması başarıyla yüklendi")
            return flask_app
            
        except ImportError as e:
            print(f"❌ Flask uygulaması import hatası: {e}")
            print(f"📁 Çalışma dizini: {os.getcwd()}")
            print(f"🐍 Python path: {sys.path[:3]}...")
            raise e
            
        except Exception as e:
            print(f"❌ Flask uygulaması yükleme hatası: {e}")
            print(f"🔍 Hata detayı: {traceback.format_exc()}")
            raise e
            
    except Exception as e:
        print(f"❌ Kritik hata: {e}")
        print(f"🔍 Tam hata: {traceback.format_exc()}")
        
        # Hata durumunda basit bir uygulama döndür
        from flask import Flask
        
        error_app = Flask(__name__)
        
        @error_app.route('/')
        def error_page():
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>❌ Uygulama Hatası</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .error-container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .error-title {{ color: #d32f2f; font-size: 24px; margin-bottom: 20px; }}
                    .error-details {{ background: #f8f8f8; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 12px; overflow-x: auto; }}
                    .solution {{ background: #e8f5e8; padding: 15px; border-radius: 4px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <div class="error-title">❌ Uygulama Yüklenemedi</div>
                    <p><strong>Hata:</strong> {str(e)}</p>
                    
                    <div class="error-details">
                        <strong>Hata Detayı:</strong><br>
                        {traceback.format_exc().replace(chr(10), '<br>')}
                    </div>
                    
                    <div class="solution">
                        <strong>💡 Çözüm Adımları:</strong><br>
                        1. PythonAnywhere konsolunda şu komutları çalıştırın:<br>
                        <code>pip install --user -r requirements_pythonanywhere.txt</code><br><br>
                        
                        2. Eğer hala hata alıyorsanız:<br>
                        <code>pip install --user flask python-dotenv requests beautifulsoup4 tweepy cryptography</code><br><br>
                        
                        3. Dosya izinlerini kontrol edin:<br>
                        <code>ls -la</code><br><br>
                        
                        4. Python versiyonunu kontrol edin:<br>
                        <code>python --version</code>
                    </div>
                </div>
            </body>
            </html>
            """
        
        @error_app.route('/health')
        def health_check():
            return {"status": "error", "message": str(e)}
        
        return error_app

# Uygulamayı oluştur
try:
    application = create_safe_application()
    print("🚀 Uygulama başarıyla başlatıldı")
except Exception as e:
    print(f"❌ Uygulama başlatma hatası: {e}")
    # Son çare olarak basit bir uygulama
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def fallback():
        return "❌ Uygulama başlatılamadı. Lütfen PythonAnywhere konsolunda hata loglarını kontrol edin."

# Debug bilgileri
print("🔧 WSGI Konfigürasyonu Tamamlandı")
print(f"📁 Çalışma dizini: {os.getcwd()}")
print(f"🐍 Python versiyonu: {sys.version}")
print(f"📦 Python path uzunluğu: {len(sys.path)}")

if __name__ == "__main__":
    application.run(debug=False, host='0.0.0.0', port=5000) 