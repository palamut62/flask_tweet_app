from app import check_and_post_articles
from utils import safe_log
 
if __name__ == "__main__":
    safe_log("Auto poster başlatıldı", "INFO")
    
    # Yeni makaleleri kontrol et
    result = check_and_post_articles()
    safe_log(f"Makale kontrol sonucu: {result}", "INFO")
    
    safe_log("Auto poster tamamlandı", "INFO") 