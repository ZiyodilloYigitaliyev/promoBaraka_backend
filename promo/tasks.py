from celery import shared_task
from django.conf import settings
from .models import Promo
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_promo_file(file_content):
    """
    Fayldagi promo kodlarni o'qib, ma'lumotlar bazasiga saqlash.
    """
    try:
        # Fayldagi promo kodlarni qatorma-qator ajratish
        codes = file_content.splitlines()

        # Batch hajmini sozlanadigan qilamiz
        batch_size = getattr(settings, "PROMO_BATCH_SIZE", 10000)
        batch = []

        for code in codes:
            code = code.strip()
            if code:  # Bo'sh satrlarni o'tkazib yuborish
                batch.append(Promo(promo_text=code))
            
            # Agar batch to'lsa, ma'lumotlar bazasiga yozish
            if len(batch) >= batch_size:
                Promo.objects.bulk_create(batch, ignore_conflicts=True)
                batch = []

        # Oxirgi qoldiq batchni saqlash
        if batch:
            Promo.objects.bulk_create(batch, ignore_conflicts=True)
        
        logger.info("Promo kodlar muvaffaqiyatli import qilindi.")
    except Exception as e:
        # Xatolikni log qilish
        logger.error(f"Promo faylni qayta ishlashda xatolik yuz berdi: {str(e)}")
        raise e  # Xatolikni qayta ko'tarish