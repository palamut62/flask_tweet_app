#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for check_and_post_articles function
This script directly tests the backend functionality without authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import check_and_post_articles
import time

def test_check_articles():
    """Test the check_and_post_articles function directly"""
    print("🧪 Test başlatılıyor: check_and_post_articles fonksiyonu")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Fonksiyonu çağır
        result = check_and_post_articles()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️  Çalışma süresi: {execution_time:.2f} saniye")
        print(f"📊 Sonuç: {result}")
        
        if result.get('success'):
            print("✅ Test başarılı!")
            print(f"📝 Mesaj: {result.get('message', 'N/A')}")
            print(f"📤 Paylaşılan tweet sayısı: {result.get('posted_count', 0)}")
            print(f"⏳ Bekleyen tweet sayısı: {result.get('pending_count', 0)}")
        else:
            print("❌ Test başarısız!")
            print(f"🚫 Hata: {result.get('message', 'Bilinmeyen hata')}")
            
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"⏱️  Çalışma süresi: {execution_time:.2f} saniye")
        print(f"💥 Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_check_articles()
