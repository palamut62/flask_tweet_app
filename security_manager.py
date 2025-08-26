import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class SecurityManager:
    def __init__(self, data_dir=""):
        self.data_dir = data_dir
        self.passwords_file = os.path.join(data_dir, "user_passwords.json")
        self.cards_file = os.path.join(data_dir, "user_cards.json")
        self.access_codes_file = os.path.join(data_dir, "access_codes.json")
        
    def _generate_key_from_password(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _encrypt_data(self, data: str, password: str) -> dict:
        salt = os.urandom(16)
        key = self._generate_key_from_password(password, salt)
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())
        
        return {
            'encrypted_data': base64.b64encode(encrypted_data).decode(),
            'salt': base64.b64encode(salt).decode(),
            'created_at': datetime.now().isoformat()
        }
    
    def _decrypt_data(self, encrypted_dict: dict, password: str) -> str:
        try:
            salt = base64.b64decode(encrypted_dict['salt'])
            key = self._generate_key_from_password(password, salt)
            fernet = Fernet(key)
            encrypted_data = base64.b64decode(encrypted_dict['encrypted_data'])
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError("Şifre çözme hatası: Yanlış anahtar veya bozuk veri")
    
    def generate_one_time_code(self, user_session_id: str) -> str:
        code = secrets.token_hex(16)  # 32 karakter hex kod
        
        access_codes = self._load_json(self.access_codes_file, {})
        
        # Eski kodu varsa iptal et (log için)
        old_code_existed = user_session_id in access_codes
        if old_code_existed:
            old_code_info = access_codes[user_session_id]
            was_used = old_code_info.get('used', False)
            attempts = old_code_info.get('attempts', 0)
            print(f"🔄 Eski kod iptal ediliyor - Kullanıldı: {was_used}, Denemeler: {attempts}")
        
        # Yeni kod oluştur (eski kod tamamen üzerine yazılır)
        access_codes[user_session_id] = {
            'code_hash': hashlib.sha256(code.encode()).hexdigest(),
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'used': False,
            'attempts': 0,
            'previous_code_existed': old_code_existed
        }
        
        self._save_json(self.access_codes_file, access_codes)
        print(f"✅ Yeni kod oluşturuldu: {len(code)} karakter")
        return code
    
    def verify_one_time_code(self, user_session_id: str, code: str) -> dict:
        """Erişim kodunu doğrula ve sonuç döndür"""
        access_codes = self._load_json(self.access_codes_file, {})
        
        if user_session_id not in access_codes:
            return {
                'success': False,
                'error': 'no_code',
                'message': 'Hiç erişim kodunuz yok'
            }
            
        code_info = access_codes[user_session_id]
        
        # Kod kullanıldı mı kontrol et
        if code_info.get('used', False):
            return {
                'success': False,
                'error': 'used_code',
                'message': 'Bu kod zaten kullanılmış'
            }
            
        # Süre doldu mu kontrol et
        expires_at = datetime.fromisoformat(code_info['expires_at'])
        if datetime.now() > expires_at:
            # Süresi dolmuş kodu temizle
            code_info['used'] = True
            self._save_json(self.access_codes_file, access_codes)
            return {
                'success': False,
                'error': 'expired_code',
                'message': 'Kod süresi dolmuş'
            }
        
        # 3 yanlış denemeden sonra kodu geçersiz kıl ve verileri sil
        if code_info.get('attempts', 0) >= 3:
            code_info['used'] = True
            self._save_json(self.access_codes_file, access_codes)
            
            # GÜVENLİK: 3 yanlış deneme sonrası tüm verileri sil
            deleted_data = self.clear_user_data(user_session_id)
            print(f"🚨 GÜVENLİK: 3 yanlış deneme sonrası veriler silindi: {deleted_data}")
            
            return {
                'success': False,
                'error': 'max_attempts',
                'message': 'Çok fazla yanlış deneme. Tüm verileriniz güvenlik için silindi.',
                'data_deleted': True,
                'deleted_data': deleted_data
            }
        
        # Kodu kontrol et
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        if code_hash == code_info['code_hash']:
            # DOĞRU KOD - başarıyla doğrulandı
            code_info['used'] = True
            code_info['verified_at'] = datetime.now().isoformat()
            self._save_json(self.access_codes_file, access_codes)
            return {
                'success': True,
                'message': 'Kod başarıyla doğrulandı'
            }
        else:
            # YANLIŞ KOD - deneme sayısını artır
            code_info['attempts'] = code_info.get('attempts', 0) + 1
            remaining_attempts = 3 - code_info['attempts']
            
            # 3. deneme sonrası verileri sil
            if code_info['attempts'] >= 3:
                deleted_data = self.clear_user_data(user_session_id)
                print(f"🚨 GÜVENLİK: 3. yanlış deneme sonrası veriler silindi: {deleted_data}")
                
                self._save_json(self.access_codes_file, access_codes)
                return {
                    'success': False,
                    'error': 'max_attempts',
                    'message': 'Çok fazla yanlış deneme. Tüm verileriniz güvenlik için silindi.',
                    'data_deleted': True,
                    'deleted_data': deleted_data
                }
            
            self._save_json(self.access_codes_file, access_codes)
            return {
                'success': False,
                'error': 'wrong_code',
                'message': f'Yanlış kod. Kalan deneme: {remaining_attempts}',
                'remaining_attempts': remaining_attempts
            }
    
    def is_code_verified(self, user_session_id: str) -> bool:
        access_codes = self._load_json(self.access_codes_file, {})
        
        if user_session_id not in access_codes:
            return False
            
        code_info = access_codes[user_session_id]
        return code_info.get('used', False) and 'verified_at' in code_info
    
    def has_active_access_code(self, user_session_id: str) -> bool:
        """Kullanıcının aktif (henüz süresi dolmamış ve kullanılabilir) erişim kodu var mı kontrol et"""
        access_codes = self._load_json(self.access_codes_file, {})
        
        if user_session_id not in access_codes:
            return False
            
        code_info = access_codes[user_session_id]
        
        # Süre kontrolü
        try:
            expires_at = datetime.fromisoformat(code_info['expires_at'])
            is_expired = datetime.now() > expires_at
        except:
            return False
        
        # Kod kullanıldı mı kontrol et
        is_used = code_info.get('used', False)
        
        # Deneme limiti aşıldı mı kontrol et
        attempts = code_info.get('attempts', 0)
        is_blocked = attempts >= 3
        
        # Aktif kod: süresi dolmamış VE kullanılmamış VE bloklanmamış
        return not is_expired and not is_used and not is_blocked
    
    def get_remaining_attempts(self, user_session_id: str) -> int:
        """Kullanıcının kalan deneme hakkını döndür"""
        access_codes = self._load_json(self.access_codes_file, {})
        
        if user_session_id not in access_codes:
            return 3
            
        code_info = access_codes[user_session_id]
        attempts = code_info.get('attempts', 0)
        return max(0, 3 - attempts)
    
    def clear_user_data(self, user_session_id: str) -> dict:
        """Kullanıcının tüm verilerini temizle ve istatistik döndür"""
        deleted_data = {
            'passwords_count': 0,
            'cards_count': 0,
            'access_codes_cleared': False
        }
        
        try:
            # Şifreleri sil
            passwords = self._load_json(self.passwords_file, {})
            if user_session_id in passwords:
                deleted_data['passwords_count'] = len(passwords[user_session_id])
                del passwords[user_session_id]
                self._save_json(self.passwords_file, passwords)
            
            # Kartları sil
            cards = self._load_json(self.cards_file, {})
            if user_session_id in cards:
                deleted_data['cards_count'] = len(cards[user_session_id])
                del cards[user_session_id]
                self._save_json(self.cards_file, cards)
            
            # Erişim kodlarını sil
            access_codes = self._load_json(self.access_codes_file, {})
            if user_session_id in access_codes:
                del access_codes[user_session_id]
                self._save_json(self.access_codes_file, access_codes)
                deleted_data['access_codes_cleared'] = True
            
            print(f"🗑️ Kullanıcı verileri temizlendi: {deleted_data}")
            return deleted_data
            
        except Exception as e:
            print(f"❌ Veri temizleme hatası: {e}")
            return deleted_data
    
    def save_password(self, user_session_id: str, site_name: str, username: str, password: str, master_password: str) -> bool:
        try:
            passwords = self._load_json(self.passwords_file, {})
            
            if user_session_id not in passwords:
                passwords[user_session_id] = {}
            
            password_data = {
                'site_name': site_name,
                'username': username,
                'password': self._encrypt_data(password, master_password),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            passwords[user_session_id][site_name] = password_data
            self._save_json(self.passwords_file, passwords)
            return True
            
        except Exception as e:
            print(f"Şifre kaydetme hatası: {e}")
            return False
    
    def get_passwords(self, user_session_id: str, master_password: str = None) -> list:
        passwords = self._load_json(self.passwords_file, {})
        
        if user_session_id not in passwords:
            return []
        
        user_passwords = []
        for site_name, password_data in passwords[user_session_id].items():
            # Şifre çözme kontrolü: master_password varsa çöz, yoksa maskele
            if master_password:
                try:
                    decrypted_password = self._decrypt_data(password_data['password'], master_password)
                    password_display = decrypted_password
                    print(f"🔓 Şifre çözüldü: {site_name}")
                except Exception as e:
                    password_display = "****"
                    print(f"❌ Şifre çözme hatası {site_name}: {e}")
            else:
                password_display = "****"
                print(f"🔒 Şifre maskelendi: {site_name}")
            
            user_passwords.append({
                'site_name': site_name,
                'username': password_data['username'],
                'password': password_display,
                'created_at': password_data['created_at'],
                'updated_at': password_data['updated_at']
            })
        
        return user_passwords
    
    def save_card(self, user_session_id: str, card_name: str, card_number: str, expiry_date: str, cardholder_name: str, cvv: str = None, notes: str = None, master_password: str = None) -> bool:
        try:
            print(f"🔍 SecurityManager.save_card çağrıldı: card_name={card_name}, card_number_length={len(card_number)}, expiry_date={expiry_date}")
            cards = self._load_json(self.cards_file, {})
            
            if user_session_id not in cards:
                cards[user_session_id] = {}
            
            # Kart numarasının son 4 hanesini maskesiz tutuyoruz
            masked_number = "**** **** **** " + card_number[-4:] if len(card_number) >= 4 else card_number
            
            card_data = {
                'card_name': card_name,
                'card_number': self._encrypt_data(card_number, master_password),
                'masked_number': masked_number,
                'expiry_date': expiry_date,
                'cardholder_name': cardholder_name,
                'notes': notes,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            cards[user_session_id][card_name] = card_data
            self._save_json(self.cards_file, cards)
            return True
            
        except Exception as e:
            print(f"Kart kaydetme hatası: {e}")
            return False
    
    def get_cards(self, user_session_id: str, master_password: str = None) -> list:
        cards = self._load_json(self.cards_file, {})
        
        if user_session_id not in cards:
            return []
        
        user_cards = []
        for card_name, card_data in cards[user_session_id].items():
            # Kart numarası çözme kontrolü: master_password varsa çöz, yoksa maskele
            if master_password:
                try:
                    decrypted_number = self._decrypt_data(card_data['card_number'], master_password)
                    display_number = decrypted_number
                    print(f"🔓 Kart çözüldü: {card_name}")
                except Exception as e:
                    display_number = card_data['masked_number']
                    print(f"❌ Kart çözme hatası {card_name}: {e}")
            else:
                display_number = card_data['masked_number']
                print(f"🔒 Kart maskelendi: {card_name}")
            
            user_cards.append({
                'card_name': card_name,
                'card_number': display_number,
                'masked_number': card_data['masked_number'],
                'expiry_date': card_data['expiry_date'],
                'cardholder_name': card_data['cardholder_name'],
                'notes': card_data.get('notes', ''),
                'created_at': card_data['created_at'],
                'updated_at': card_data['updated_at']
            })
        
        return user_cards
    
    def delete_password(self, user_session_id: str, site_name: str) -> bool:
        try:
            passwords = self._load_json(self.passwords_file, {})
            
            if user_session_id in passwords and site_name in passwords[user_session_id]:
                del passwords[user_session_id][site_name]
                self._save_json(self.passwords_file, passwords)
                return True
            return False
            
        except Exception as e:
            print(f"Şifre silme hatası: {e}")
            return False
    
    def delete_card(self, user_session_id: str, card_name: str) -> bool:
        try:
            cards = self._load_json(self.cards_file, {})
            
            if user_session_id in cards and card_name in cards[user_session_id]:
                del cards[user_session_id][card_name]
                self._save_json(self.cards_file, cards)
                return True
            return False
            
        except Exception as e:
            print(f"Kart silme hatası: {e}")
            return False
    
    def generate_password_access_code(self, user_session_id: str, password_id: str) -> str:
        """Belirli bir şifre için erişim kodu oluştur"""
        code = secrets.token_hex(16)  # 32 karakter hex kod
        
        access_codes = self._load_json(self.access_codes_file, {})
        
        # Şifre bazlı kod anahtarı oluştur
        password_code_key = f"{user_session_id}_{password_id}"
        
        # Eski kodu varsa iptal et
        old_code_existed = password_code_key in access_codes
        if old_code_existed:
            old_code_info = access_codes[password_code_key]
            was_used = old_code_info.get('used', False)
            attempts = old_code_info.get('attempts', 0)
            print(f"🔄 Şifre erişim kodu iptal ediliyor - Kullanıldı: {was_used}, Denemeler: {attempts}")
        
        # Yeni kod oluştur
        access_codes[password_code_key] = {
            'code_hash': hashlib.sha256(code.encode()).hexdigest(),
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=30)).isoformat(),  # 30 dakika geçerli
            'used': False,
            'attempts': 0,
            'password_id': password_id,
            'user_session_id': user_session_id,
            'type': 'password_access'
        }
        
        self._save_json(self.access_codes_file, access_codes)
        print(f"✅ Şifre erişim kodu oluşturuldu: {password_id}")
        return code
    
    def verify_password_access_code(self, user_session_id: str, password_id: str, code: str) -> dict:
        """Belirli bir şifre için erişim kodunu doğrula"""
        access_codes = self._load_json(self.access_codes_file, {})
        password_code_key = f"{user_session_id}_{password_id}"
        
        if password_code_key not in access_codes:
            return {
                'success': False,
                'error': 'no_code',
                'message': 'Bu şifre için erişim kodunuz yok'
            }
            
        code_info = access_codes[password_code_key]
        
        # Kod türü kontrolü
        if code_info.get('type') != 'password_access':
            return {
                'success': False,
                'error': 'invalid_code_type',
                'message': 'Geçersiz kod türü'
            }
        
        # Kod kullanıldı mı kontrol et
        if code_info.get('used', False):
            return {
                'success': False,
                'error': 'used_code',
                'message': 'Bu kod zaten kullanılmış'
            }
            
        # Süre doldu mu kontrol et
        expires_at = datetime.fromisoformat(code_info['expires_at'])
        if datetime.now() > expires_at:
            # Süresi dolmuş kodu temizle
            code_info['used'] = True
            self._save_json(self.access_codes_file, access_codes)
            return {
                'success': False,
                'error': 'expired_code',
                'message': 'Kod süresi dolmuş (30 dakika)'
            }
        
        # 3 yanlış denemeden sonra kodu geçersiz kıl
        if code_info.get('attempts', 0) >= 3:
            code_info['used'] = True
            self._save_json(self.access_codes_file, access_codes)
            return {
                'success': False,
                'error': 'max_attempts',
                'message': 'Çok fazla yanlış deneme. Kod iptal edildi.',
                'code_blocked': True
            }
        
        # Kodu kontrol et
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        if code_hash == code_info['code_hash']:
            # DOĞRU KOD - başarıyla doğrulandı
            code_info['used'] = True
            code_info['verified_at'] = datetime.now().isoformat()
            self._save_json(self.access_codes_file, access_codes)
            return {
                'success': True,
                'message': 'Şifre erişim kodu doğrulandı',
                'password_id': password_id
            }
        else:
            # YANLIŞ KOD - deneme sayısını artır
            code_info['attempts'] = code_info.get('attempts', 0) + 1
            remaining_attempts = 3 - code_info['attempts']
            
            # 3. deneme sonrası kodu blokla
            if code_info['attempts'] >= 3:
                code_info['used'] = True
                self._save_json(self.access_codes_file, access_codes)
                return {
                    'success': False,
                    'error': 'max_attempts',
                    'message': 'Çok fazla yanlış deneme. Kod iptal edildi.',
                    'code_blocked': True
                }
            
            self._save_json(self.access_codes_file, access_codes)
            return {
                'success': False,
                'error': 'wrong_code',
                'message': f'Yanlış kod. Kalan deneme: {remaining_attempts}',
                'remaining_attempts': remaining_attempts
            }
    
    def has_active_password_code(self, user_session_id: str, password_id: str) -> bool:
        """Belirli bir şifre için aktif erişim kodu var mı kontrol et"""
        access_codes = self._load_json(self.access_codes_file, {})
        password_code_key = f"{user_session_id}_{password_id}"
        
        if password_code_key not in access_codes:
            return False
            
        code_info = access_codes[password_code_key]
        
        # Süre kontrolü
        try:
            expires_at = datetime.fromisoformat(code_info['expires_at'])
            is_expired = datetime.now() > expires_at
        except:
            return False
        
        # Kod kullanıldı mı kontrol et
        is_used = code_info.get('used', False)
        
        # Deneme limiti aşıldı mı kontrol et
        attempts = code_info.get('attempts', 0)
        is_blocked = attempts >= 3
        
        # Aktif kod: süresi dolmamış VE kullanılmamış VE bloklanmamış
        return not is_expired and not is_used and not is_blocked
    
    def get_password_remaining_attempts(self, user_session_id: str, password_id: str) -> int:
        """Belirli bir şifre için kalan deneme hakkını döndür"""
        access_codes = self._load_json(self.access_codes_file, {})
        password_code_key = f"{user_session_id}_{password_id}"
        
        if password_code_key not in access_codes:
            return 3
            
        code_info = access_codes[password_code_key]
        attempts = code_info.get('attempts', 0)
        return max(0, 3 - attempts)
    
    def _load_json(self, filename: str, default: dict) -> dict:
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default
        except Exception as e:
            print(f"JSON yükleme hatası: {e}")
            return default
    
    def _save_json(self, filename: str, data: dict) -> bool:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"JSON kaydetme hatası: {e}")
            return False