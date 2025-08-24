#!/bin/bash
# PythonAnywhere Düzeltme Komutları
# Bu script PythonAnywhere'deki tasarım sorunlarını çözer

echo "🚀 PythonAnywhere Tasarım Sorunları Düzeltiliyor..."
echo "=================================================="

# 1. Mevcut durumu kontrol et
echo "📋 1. Mevcut durum kontrol ediliyor..."
python check_pythonanywhere_status.py

echo ""
echo "📋 2. Static dosyalar yeniden indiriliyor..."
python download_static_files.py

echo ""
echo "📋 3. Environment variables kontrol ediliyor..."
if [ -f ".env" ]; then
    echo "✅ .env dosyası mevcut"
    echo "📄 .env içeriği:"
    cat .env | grep -E "(FLASK_ENV|SECRET_KEY|USE_LOCAL_ASSETS|PYTHONANYWHERE_MODE|DEBUG)"
else
    echo "❌ .env dosyası bulunamadı!"
    echo "📝 Örnek .env dosyası oluşturuluyor..."
    cat > .env << EOF
# Flask Configuration
SECRET_KEY=your_secret_key_for_flask_sessions
FLASK_ENV=production
DEBUG=False
USE_LOCAL_ASSETS=True
PYTHONANYWHERE_MODE=True

# API Keys (Bu değerleri kendi API anahtarlarınızla değiştirin)
OPENROUTER_API_KEY=your-openrouter-api-key
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
GOOGLE_API_KEY=your-google-api-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
EOF
    echo "✅ .env dosyası oluşturuldu"
fi

echo ""
echo "📋 4. Test scripti çalıştırılıyor..."
python test_pythonanywhere.py

echo ""
echo "📋 5. Web erişim testi..."
python -c "
import requests
try:
    response = requests.get('https://umutins62.pythonanywhere.com/static/css/bootstrap.min.css')
    print(f'✅ Bootstrap CSS erişimi: {response.status_code}')
except Exception as e:
    print(f'❌ Bootstrap CSS erişim hatası: {e}')
"

echo ""
echo "📋 6. Final durum kontrolü..."
python check_pythonanywhere_status.py

echo ""
echo "🎯 SONUÇ:"
echo "=================================================="
echo "✅ Tüm düzeltmeler tamamlandı!"
echo ""
echo "📋 YAPILMASI GEREKENLER:"
echo "1. PythonAnywhere Web sekmesine gidin"
echo "2. Reload butonuna tıklayın"
echo "3. Browser'da Ctrl+F5 ile hard refresh yapın"
echo "4. Uygulamanızı test edin: https://umutins62.pythonanywhere.com"
echo ""
echo "🔧 Eğer hala sorun varsa:"
echo "- Browser cache'ini temizleyin"
echo "- Developer Tools → Network → Disable cache işaretleyin"
echo "- Farklı bir browser'da test edin"
