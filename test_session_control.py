#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Kontrol Testi - PythonAnywhere
"""

import os
import sys
from datetime import datetime

def test_session_flow():
    """Session akışını test et"""
    print("🔐 Session Kontrol Testi")
    print("=" * 40)
    
    try:
        from app import app
        
        with app.test_client() as client:
            # 1. Ana sayfa (login gerektirir)
            print("1️⃣ Ana sayfa testi:")
            response = client.get('/')
            print(f"   Status: {response.status_code}")
            print(f"   Redirect: {response.headers.get('Location', 'Yok')}")
            
            # 2. Login sayfası
            print("\n2️⃣ Login sayfası testi:")
            response = client.get('/login')
            print(f"   Status: {response.status_code}")
            
            # 3. Password manager (login gerektirir)
            print("\n3️⃣ Password manager testi:")
            response = client.get('/password_manager')
            print(f"   Status: {response.status_code}")
            print(f"   Redirect: {response.headers.get('Location', 'Yok')}")
            
            # 4. Session ile test
            print("\n4️⃣ Session ile test:")
            with client.session_transaction() as sess:
                sess['logged_in'] = True
                sess['session_id'] = 'test_session_123'
                sess['master_password'] = 'test_master_123'
            
            response = client.get('/password_manager')
            print(f"   Status (session ile): {response.status_code}")
            
            # 5. Session içeriği kontrol
            print("\n5️⃣ Session içeriği:")
            with client.session_transaction() as sess:
                print(f"   logged_in: {sess.get('logged_in', 'Yok')}")
                print(f"   session_id: {sess.get('session_id', 'Yok')}")
                print(f"   master_password: {sess.get('master_password', 'Yok')}")
            
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

def test_login_required_routes():
    """Login gerektiren route'ları test et"""
    print("\n🔍 Login Gerektiren Route'lar:")
    print("=" * 40)
    
    try:
        from app import app
        
        # Login gerektiren route'lar
        protected_routes = [
            '/password_manager',
            '/save_password',
            '/get_passwords',
            '/delete_password',
            '/save_card',
            '/get_cards',
            '/delete_card'
        ]
        
        with app.test_client() as client:
            for route in protected_routes:
                response = client.get(route)
                print(f"   {route}: {response.status_code}")
                if response.status_code == 302:
                    print(f"     → Redirect: {response.headers.get('Location', 'Bilinmiyor')}")
                    
    except Exception as e:
        print(f"❌ Route kontrol hatası: {e}")

def test_session_with_login():
    """Login ile session testi"""
    print("\n🔐 Login ile Session Testi:")
    print("=" * 40)
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Session'ı login durumuna getir
            with client.session_transaction() as sess:
                sess['logged_in'] = True
                sess['session_id'] = 'test_user_123'
                sess['master_password'] = 'master_pass_123'
            
            # Password manager'a eriş
            response = client.get('/password_manager')
            print(f"   Password Manager: {response.status_code}")
            
            # Save password route'u test et
            response = client.post('/save_password', data={
                'site_name': 'test_site',
                'username': 'test_user',
                'password': 'test_pass',
                'master_password': 'master_pass_123'
            })
            print(f"   Save Password: {response.status_code}")
            
            # Get passwords route'u test et
            response = client.get('/get_passwords')
            print(f"   Get Passwords: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Login test hatası: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

def test_session_decorators():
    """Session decorator'larını test et"""
    print("\n🎭 Session Decorator Testi:")
    print("=" * 40)
    
    try:
        from app import app
        
        # @login_required decorator'ını kontrol et
        from functools import wraps
        from flask import session, redirect, url_for
        
        def login_required(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'logged_in' not in session:
                    return redirect(url_for('login'))
                return f(*args, **kwargs)
            return decorated_function
        
        print("   ✅ @login_required decorator tanımlandı")
        
        # Test fonksiyonu
        @login_required
        def test_protected_function():
            return "Protected content"
        
        with app.test_client() as client:
            # Login olmadan test
            with client.session_transaction() as sess:
                if 'logged_in' in sess:
                    del sess['logged_in']
            
            # Login olmadan erişim
            response = client.get('/password_manager')
            print(f"   Login olmadan: {response.status_code}")
            
            # Login ile erişim
            with client.session_transaction() as sess:
                sess['logged_in'] = True
            
            response = client.get('/password_manager')
            print(f"   Login ile: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Decorator test hatası: {e}")

def main():
    """Ana test fonksiyonu"""
    print("🐍 PythonAnywhere Session Kontrol Testi")
    print("=" * 60)
    
    # Session akış testi
    test_session_flow()
    
    # Login gerektiren route'lar
    test_login_required_routes()
    
    # Login ile session testi
    test_session_with_login()
    
    # Session decorator testi
    test_session_decorators()
    
    print("\n📊 Session Test Sonuçları:")
    print("=" * 30)
    print("💡 302 = Login gerekiyor")
    print("💡 200 = Başarılı erişim")
    print("💡 500 = Sunucu hatası")
    print("\n💡 Web uygulamasında giriş yapın, sonra password manager'ı test edin")

if __name__ == "__main__":
    main()
