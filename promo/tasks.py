# tasks.py
from celery import shared_task
from .models import Promo

@shared_task
def import_promos(codes: list[str]):
    """
    Berilgan kodlar ro'yxatini bazaga bulk_create orqali yozadi.
    Takrorlanuvchi (unique) xatolarni e'tiborsiz qoldiradi.
    """
    promo_objs = [
        Promo(promo_text=code.strip())
        for code in codes
        if code and code.strip()
    ]
    # ignore_conflicts=True takrorlanuvchi unique errorlarni o‘tkazib yuboradi
    Promo.objects.bulk_create(promo_objs, ignore_conflicts=True)
