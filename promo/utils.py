import requests
from datetime import datetime
from .models import PostbackRequest, PromoEntry
def fetch_and_save_data():
    url = "https://walrus-app-gwabt.ondigitalocean.app/api/promo/"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        for entry in data:
            postback_request = PostbackRequest.objects.create(
                msisdn=entry["msisdn"],
                opi=entry["opi"],
                short_number=entry["short_number"],
                sent_count=entry["sent_count"],
                notification_sent=entry.get("notification_sent", False)
            )

            for promo in entry.get("promos", []):
                PromoEntry.objects.create(
                    postback_request=postback_request,
                    text=promo["text"],
                    created_at=datetime.fromisoformat(promo["created_at"].replace("Z", "+00:00")),
                    used=promo["used"]
                )
    else:
        print("API so'rovi muvaffaqiyatsiz yakunlandi, kod:", response.status_code)
        