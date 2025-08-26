#!/bin/bash
# PythonAnywhere Security Manager Fix Commands
# Bu script PythonAnywhere'de security manager sorunlarını çözer

echo "🚀 PythonAnywhere Security Manager Fix Başlatılıyor..."
echo "============================================================"

# 1. Cryptography kütüphanesini yükle
echo "📦 Cryptography kütüphanesi yükleniyor..."
pip install cryptography==41.0.7

# 2. Dosya izinlerini kontrol et ve düzelt
echo "🔍 Dosya izinleri kontrol ediliyor..."

# JSON dosyalarını kontrol et
for file in user_passwords.json user_cards.json access_codes.json; do
    if [ -f "$file" ]; then
        echo "📁 $file mevcut"
        # Yazma izni kontrol et
        if [ -w "$file" ]; then
            echo "✅ $file yazılabilir"
        else
            echo "⚠️ $file yazılamıyor, izinler düzeltiliyor..."
            chmod 644 "$file"
            echo "✅ $file izinleri düzeltildi"
        fi
    else
        echo "📄 $file mevcut değil, oluşturuluyor..."
        echo "{}" > "$file"
        chmod 644 "$file"
        echo "✅ $file oluşturuldu"
    fi
done

# 3. Python test scriptini çalıştır
echo "🧪 SecurityManager test ediliyor..."
python3 test_security_manager.py

# 4. Fix scriptini çalıştır
echo "🔧 SecurityManager düzeltiliyor..."
python3 pythonanywhere_security_fix.py

echo "============================================================"
echo "🏁 İşlem tamamlandı!"
echo ""
echo "💡 Eğer hala sorun varsa:"
echo "1. PythonAnywhere'de 'Files' sekmesinden dosya izinlerini kontrol edin"
echo "2. 'Consoles' sekmesinden manuel olarak test edin"
echo "3. Uygulamayı yeniden başlatın"
