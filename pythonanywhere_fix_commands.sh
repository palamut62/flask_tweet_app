#!/bin/bash
# PythonAnywhere Security Manager Fix Commands
# Bu script PythonAnywhere'de security manager sorunlarını çözer

echo "🚀 PythonAnywhere Security Manager Fix Başlatılıyor..."
echo "============================================================"
echo "📅 Tarih: $(date)"
echo "🌐 Ortam: PythonAnywhere"
echo "============================================================"

# 1. Proje dizinine geç
echo "📁 Proje dizinine geçiliyor..."
cd /home/umutins62/flask_tweet_app
echo "✅ Dizin: $(pwd)"

# 2. Cryptography kütüphanesini yükle
echo "📦 Cryptography kütüphanesi yükleniyor..."
pip install cryptography==41.0.7 --user
if [ $? -eq 0 ]; then
    echo "✅ Cryptography başarıyla yüklendi"
else
    echo "❌ Cryptography yükleme hatası"
    echo "🔧 Alternatif yöntem deneniyor..."
    pip install cryptography --user
fi

# 3. Dosya izinlerini kontrol et ve düzelt
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

# 4. Dizin izinlerini kontrol et
echo "🔍 Dizin izinleri kontrol ediliyor..."
if [ -w "." ]; then
    echo "✅ Proje dizini yazılabilir"
else
    echo "⚠️ Proje dizini yazılamıyor, izinler düzeltiliyor..."
    chmod 755 "."
    echo "✅ Proje dizini izinleri düzeltildi"
fi

# 5. Python test scriptini çalıştır
echo "🧪 SecurityManager test ediliyor..."
python3 test_security_manager.py
if [ $? -eq 0 ]; then
    echo "✅ SecurityManager test başarılı"
else
    echo "❌ SecurityManager test başarısız"
fi

# 6. Fix scriptini çalıştır
echo "🔧 SecurityManager düzeltiliyor..."
python3 pythonanywhere_security_fix.py
if [ $? -eq 0 ]; then
    echo "✅ SecurityManager düzeltme başarılı"
else
    echo "❌ SecurityManager düzeltme başarısız"
fi

# 7. Hızlı düzeltme scriptini çalıştır
echo "⚡ Hızlı düzeltme scripti çalıştırılıyor..."
python3 pythonanywhere_quick_fix.py
if [ $? -eq 0 ]; then
    echo "✅ Hızlı düzeltme başarılı"
else
    echo "❌ Hızlı düzeltme başarısız"
fi

# 8. Dosya durumunu kontrol et
echo "📋 Dosya durumu kontrol ediliyor..."
echo "Dosya listesi:"
ls -la *.json 2>/dev/null || echo "JSON dosyaları bulunamadı"

echo "============================================================"
echo "🏁 İşlem tamamlandı!"
echo ""
echo "💡 Şimdi yapmanız gerekenler:"
echo "1. PythonAnywhere'de 'Web' sekmesine gidin"
echo "2. 'Reload' butonuna tıklayın"
echo "3. Uygulamanızı açın: https://umutins62.pythonanywhere.com"
echo "4. Şifre yöneticisini test edin"
echo ""
echo "🔧 Eğer hala sorun varsa:"
echo "1. PythonAnywhere'de 'Files' sekmesinden dosya izinlerini kontrol edin"
echo "2. 'Consoles' sekmesinden manuel olarak test edin"
echo "3. Error logs sekmesinden hata mesajlarını kontrol edin"
echo "4. Uygulamayı yeniden başlatın"
echo "============================================================"
