# 🔐 PythonAnywhere Security Manager Sorun Çözümü

PythonAnywhere'de şifre kaydetme hatası alıyorsanız, bu adımları takip edin.

## 🚨 Sorun: "Şifre kaydedilirken bir hata oluştu"

Bu hata genellikle şu sebeplerden kaynaklanır:
1. **Cryptography kütüphanesi yüklü değil**
2. **Dosya yazma izinleri yok**
3. **JSON dosyaları mevcut değil**

## 🔧 Çözüm Adımları

### 1. PythonAnywhere Console'a Giriş

1. PythonAnywhere hesabınıza giriş yapın
2. **Consoles** sekmesine gidin
3. **Bash** console'unu açın

### 2. Proje Dizinine Geçin

```bash
cd /home/umutins62/flask_tweet_app
```

### 3. Otomatik Düzeltme Scriptini Çalıştırın

```bash
# Script'i çalıştırılabilir yapın
chmod +x pythonanywhere_fix_commands.sh

# Düzeltme scriptini çalıştırın
./pythonanywhere_fix_commands.sh
```

### 4. Manuel Test

Eğer otomatik script çalışmazsa, manuel olarak test edin:

```bash
# Cryptography yükle
pip install cryptography==41.0.7

# Test scriptini çalıştır
python3 test_security_manager.py

# Fix scriptini çalıştır
python3 pythonanywhere_security_fix.py
```

### 5. Dosya İzinlerini Kontrol Edin

```bash
# Dosya izinlerini kontrol et
ls -la user_passwords.json user_cards.json access_codes.json

# İzinleri düzelt (gerekirse)
chmod 644 user_passwords.json user_cards.json access_codes.json
```

### 6. Boş JSON Dosyaları Oluşturun

Eğer dosyalar mevcut değilse:

```bash
# Boş JSON dosyaları oluştur
echo "{}" > user_passwords.json
echo "{}" > user_cards.json
echo "{}" > access_codes.json

# İzinleri ayarla
chmod 644 user_passwords.json user_cards.json access_codes.json
```

## 🧪 Test Etme

### 1. Python Console'da Test

```python
# Python console'u açın
python3

# Test kodunu çalıştırın
from security_manager import SecurityManager
sm = SecurityManager()

# Test şifresi kaydet
success = sm.save_password("test_user", "test_site", "test_user", "test_pass", "master_pass")
print(f"Şifre kaydetme: {'Başarılı' if success else 'Başarısız'}")

# Test şifresi oku
passwords = sm.get_passwords("test_user", "master_pass")
print(f"Şifre okuma: {len(passwords)} şifre bulundu")

# Test verilerini temizle
sm.delete_password("test_user", "test_site")
```

### 2. Web Uygulamasında Test

1. PythonAnywhere **Web** sekmesine gidin
2. **Reload** butonuna tıklayın
3. Uygulamanızı açın: `https://umutins62.pythonanywhere.com`
4. Şifre yöneticisine gidin ve test şifresi ekleyin

## 🔍 Hata Ayıklama

### Cryptography Hatası

```
ImportError: No module named 'cryptography'
```

**Çözüm:**
```bash
pip install cryptography==41.0.7
```

### Dosya İzin Hatası

```
PermissionError: [Errno 13] Permission denied
```

**Çözüm:**
```bash
chmod 644 user_passwords.json user_cards.json access_codes.json
```

### JSON Hatası

```
JSONDecodeError: Expecting value: line 1 column 1
```

**Çözüm:**
```bash
# Dosyaları yeniden oluştur
echo "{}" > user_passwords.json
echo "{}" > user_cards.json
echo "{}" > access_codes.json
```

## 📋 Kontrol Listesi

- [ ] Cryptography kütüphanesi yüklü
- [ ] JSON dosyaları mevcut ve yazılabilir
- [ ] Dosya izinleri doğru (644)
- [ ] Test scripti başarılı
- [ ] Web uygulaması yeniden başlatıldı

## 🆘 Hala Sorun Varsa

1. **PythonAnywhere Files** sekmesinden dosya izinlerini kontrol edin
2. **Error logs** sekmesinden hata mesajlarını kontrol edin
3. **Consoles** sekmesinden manuel test yapın
4. PythonAnywhere **Web** sekmesinden uygulamayı yeniden başlatın

## 📞 Destek

Eğer sorun devam ederse:
1. Hata mesajlarını kopyalayın
2. Test scriptinin çıktısını paylaşın
3. PythonAnywhere error loglarını kontrol edin

---

**Not:** Bu düzeltmeler güvenliğinizi etkilemez. Mevcut şifreleriniz korunur ve sadece sistem sorunları düzeltilir.
