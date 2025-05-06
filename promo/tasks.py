from conf.celery import shared_task
from django.conf import settings
from .models import Promo

@shared_task
def process_promo_file(file_content):
    """
    Fayldagi promo kodlarni o'qib, ma'lumotlar bazasiga saqlash.
    """
    codes = file_content.splitlines()
    promo_objs = [
        Promo(promo_text=code.strip())
        for code in codes
        if code.strip()
    ]

    # Takrorlanishlarni e'tiborsiz qoldirish uchun ignore_conflicts=True
    Promo.objects.bulk_create(promo_objs, ignore_conflicts=True)