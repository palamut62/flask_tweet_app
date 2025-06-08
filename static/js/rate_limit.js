// Rate limit durumunu kontrol et
function checkRateLimitStatus() {
    fetch('/api/rate_limit_status')
        .then(response => response.json())
        .then(data => {
            const content = document.getElementById('rate-limit-content');
            const retryBtn = document.getElementById('retry-rate-limited-btn');
            
            if (data.success) {
                const rateLimitStatus = data.rate_limit_status;
                const rateLimitedCount = data.rate_limited_tweets_count;
                const canRetry = data.can_retry;
                
                let statusHtml = '';
                
                if (rateLimitedCount > 0) {
                    statusHtml = '<div class="space-y-4">' +
                        '<div class="flex justify-between items-center">' +
                            '<span class="text-gray-600">Rate Limited Tweet\'ler:</span>' +
                            '<span class="font-bold text-red-600">' + rateLimitedCount + ' adet</span>' +
                        '</div>' +
                        '<div class="flex justify-between items-center">' +
                            '<span class="text-gray-600">Twitter API Durumu:</span>' +
                            '<span class="px-3 py-1 rounded-full text-sm font-medium ' + (rateLimitStatus.can_post ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800') + '">' +
                                (rateLimitStatus.can_post ? 'Kullanılabilir' : 'Rate Limited') +
                            '</span>' +
                        '</div>';
                    
                    if (!rateLimitStatus.can_post) {
                        statusHtml += '<div class="flex justify-between items-center">' +
                            '<span class="text-gray-600">Kalan Süre:</span>' +
                            '<span class="font-medium text-orange-600">' + (rateLimitStatus.reset_time_minutes || 'Bilinmiyor') + ' dakika</span>' +
                        '</div>';
                    }
                    
                    statusHtml += '</div>';
                    
                    // Retry butonunu göster/gizle
                    if (canRetry) {
                        retryBtn.classList.remove('hidden');
                    } else {
                        retryBtn.classList.add('hidden');
                    }
                } else {
                    statusHtml = '<div class="text-center py-4">' +
                        '<div class="flex items-center justify-center space-x-2 text-green-600">' +
                            '<i class="fas fa-check-circle"></i>' +
                            '<span class="font-medium">Rate limit sorunu yok</span>' +
                        '</div>' +
                        '<p class="text-gray-500 text-sm mt-2">Tüm tweet\'ler normal şekilde paylaşılabilir</p>' +
                    '</div>';
                    retryBtn.classList.add('hidden');
                }
                
                content.innerHTML = statusHtml;
            } else {
                content.innerHTML = '<div class="text-center py-4">' +
                    '<div class="flex items-center justify-center space-x-2 text-red-600">' +
                        '<i class="fas fa-exclamation-triangle"></i>' +
                        '<span class="font-medium">Durum kontrol edilemedi</span>' +
                    '</div>' +
                    '<p class="text-gray-500 text-sm mt-2">' + (data.error || 'Bilinmeyen hata') + '</p>' +
                '</div>';
                retryBtn.classList.add('hidden');
            }
        })
        .catch(error => {
            console.error('Rate limit status error:', error);
            document.getElementById('rate-limit-content').innerHTML = 
                '<div class="text-center py-4">' +
                    '<div class="flex items-center justify-center space-x-2 text-red-600">' +
                        '<i class="fas fa-exclamation-triangle"></i>' +
                        '<span class="font-medium">Bağlantı hatası</span>' +
                    '</div>' +
                    '<p class="text-gray-500 text-sm mt-2">Rate limit durumu kontrol edilemedi</p>' +
                '</div>';
        });
}

// Rate limited tweet'leri tekrar dene
function retryRateLimitedTweets() {
    const btn = document.getElementById('retry-rate-limited-btn');
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Deneniyor...</span>';
    btn.disabled = true;
    
    fetch('/retry_rate_limited_tweets')
        .then(response => {
            if (response.ok) {
                // Sayfa yenileme ile sonucu göster
                window.location.reload();
            } else {
                throw new Error('İstek başarısız');
            }
        })
        .catch(error => {
            console.error('Retry error:', error);
            alert('Rate limited tweet\'leri tekrar deneme işlemi başarısız oldu.');
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

// Sayfa yüklendiğinde rate limit durumunu kontrol et
document.addEventListener('DOMContentLoaded', function() {
    checkRateLimitStatus();
    
    // Her 2 dakikada bir rate limit durumunu güncelle
    setInterval(checkRateLimitStatus, 120000);
});

// Mevcut tweet işleme fonksiyonları
function postTweet(tweetId) {
    if (confirm('Bu tweet\'i API ile paylaşmak istediğinizden emin misiniz?')) {
        fetch('/post_tweet', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({tweet_id: tweetId})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Tweet başarıyla paylaşıldı!');
                location.reload();
            } else {
                alert('Hata: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Bir hata oluştu!');
        });
    }
}

// Manuel tweet paylaşım fonksiyonu
function manualPostTweet(tweetId) {
    fetch('/manual_post_tweet', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({tweet_id: tweetId})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // X.com'da yeni sekmede aç
            const xWindow = window.open(data.x_share_url, '_blank');
            
            // Kullanıcıya onay sor
            setTimeout(() => {
                if (confirm('Tweet\'i X\'te paylaştınız mı? Paylaştıysanız "Tamam"a basın, paylaşmadıysanız "İptal"e basın.')) {
                    // Paylaşım onaylandı, kayıtlara geçir
                    confirmManualPost(tweetId);
                } else {
                    // Paylaşım iptal edildi
                    console.log('Manuel paylaşım iptal edildi');
                }
            }, 2000); // 2 saniye bekle ki kullanıcı X'i görebilsin
        } else {
            alert('Hata: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Bir hata oluştu!');
    });
}

// Manuel paylaşım onaylama fonksiyonu
function confirmManualPost(tweetId) {
    fetch('/confirm_manual_post', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({tweet_id: tweetId})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Tweet manuel paylaşım olarak kaydedildi!');
            location.reload();
        } else {
            alert('Kayıt hatası: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Kayıt sırasında bir hata oluştu!');
    });
}

function deleteTweet(tweetId) {
    if (confirm('Bu tweet\'i silmek istediğinizden emin misiniz?')) {
        fetch('/delete_tweet', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({tweet_id: tweetId})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Tweet silindi!');
                location.reload();
            } else {
                alert('Hata: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Bir hata oluştu!');
        });
    }
} 