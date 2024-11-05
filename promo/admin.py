from django.contrib import admin
from .models import *
from django.db.models import Count
@admin.register(PostbackRequest)
class PostbackRequestAdmin(admin.ModelAdmin):
    list_display = ('msisdn', 'opi', 'short_number', 'sent_count')

class PromoEntryAdmin(admin.ModelAdmin):
    list_display = ('text', 'created_at')
admin.site.register(PromoEntry, PromoEntryAdmin)


@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ['promo_text']  # Admin panelda promo matnini ko'rsatish
    search_fields = ['promo_text']  # Qidiruv uchun promo_text maydoni
    actions = ['delete_selected_promos', 'delete_duplicates']  # Tugmalar ro'yxati

    # Tanlangan promolarni o'chirish funksiyasi
    def delete_selected_promos(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} ta promo muvaffaqiyatli o'chirildi.")

    delete_selected_promos.short_description = 'Tanlangan barcha Promo kodlarni o‘chirish'

    # Takrorlangan promokodlarni o'chirish funksiyasi
    def delete_duplicates(self, request, queryset=None):
        # Takrorlangan promokodlarni aniqlash
        duplicates = Promo.objects.values('promo_text').annotate(Count('id')).filter(id__count__gt=1)
        count = 0

        for duplicate in duplicates:
            promo_text = duplicate['promo_text']
            # Birinchi promokoddan tashqari qolgan hamma takrorlanganlarni o'chirish
            Promo.objects.filter(promo_text=promo_text).exclude(
                id=Promo.objects.filter(promo_text=promo_text).first().id).delete()
            count += (duplicate['id__count'] - 1)

        self.message_user(request, f"{count} ta takrorlangan promo muvaffaqiyatli o'chirildi.")

    delete_duplicates.short_description = 'Takrorlangan Promo kodlarni o‘chirish'

admin.site.register(Notification)
