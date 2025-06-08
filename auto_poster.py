from app import check_and_post_articles
from utils import check_and_retry_rate_limited_tweets, safe_log
 
if __name__ == "__main__":
    safe_log("Auto poster başlatıldı", "INFO")
    
    # Önce yeni makaleleri kontrol et
    result = check_and_post_articles()
    safe_log(f"Makale kontrol sonucu: {result}", "INFO")
    
    # Sonra rate limit tweet'lerini kontrol et
    try:
        rate_limit_result = check_and_retry_rate_limited_tweets()
        safe_log(f"Rate limit kontrol sonucu: {rate_limit_result}", "INFO")
    except Exception as e:
        safe_log(f"Rate limit kontrol hatası: {e}", "ERROR")
    
    safe_log("Auto poster tamamlandı", "INFO") 