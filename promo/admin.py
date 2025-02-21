from django.contrib import admin
from django.db.models import Count
from .models import PostbackRequest, PromoEntry, Promo, NotificationDaily, QueryLog

@admin.register(PostbackRequest)
class PostbackRequestAdmin(admin.ModelAdmin):
    list_display = ('msisdn', 'opi', 'short_number', 'sent_count')
    search_fields = ('msisdn',)
    list_filter = ('opi', 'short_number')
    ordering = ('msisdn',)
    list_per_page = 25  # sahifalash uchun

@admin.register(PromoEntry)
class PromoEntryAdmin(admin.ModelAdmin):
    list_display = ('text', 'created_at')
    search_fields = ('text',)
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 25
    actions = ['delete_selected_promos', 'delete_duplicates']
    
    def delete_selected_promos(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} ta Promo Entry muvaffaqiyatli o'chirildi.")
    delete_selected_promos.short_description = 'Tanlangan barcha Promo Entrylarni o‘chirish'
    
    def delete_duplicates(self, request, queryset=None):
        # Promo modelidagi takrorlangan promo_text yozuvlarini aniqlash
        duplicates = Promo.objects.values('promo_text').annotate(total=Count('id')).filter(total__gt=1)
        count = 0
        for duplicate in duplicates:
            promo_text = duplicate['promo_text']
            qs = Promo.objects.filter(promo_text=promo_text)
            first = qs.first()
            qs.exclude(id=first.id).delete()
            count += duplicate['total'] - 1
        self.message_user(request, f"{count} ta takrorlangan promo muvaffaqiyatli o'chirildi.")
    delete_duplicates.short_description = 'Takrorlangan Promo kodlarni o‘chirish'

@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ('promo_text',)
    search_fields = ('promo_text',)
    ordering = ('promo_text',)
    list_per_page = 25
    actions = ['delete_selected_promos', 'delete_duplicates']
    
    def delete_selected_promos(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} ta Promo muvaffaqiyatli o'chirildi.")
    delete_selected_promos.short_description = 'Tanlangan barcha Promo kodlarni o‘chirish'
    
    def delete_duplicates(self, request, queryset=None):
        duplicates = Promo.objects.values('promo_text').annotate(total=Count('id')).filter(total__gt=1)
        count = 0
        for duplicate in duplicates:
            promo_text = duplicate['promo_text']
            qs = Promo.objects.filter(promo_text=promo_text)
            first = qs.first()
            qs.exclude(id=first.id).delete()
            count += duplicate['total'] - 1
        self.message_user(request, f"{count} ta takrorlangan promo muvaffaqiyatli o'chirildi.")
    delete_duplicates.short_description = 'Takrorlangan Promo kodlarni o‘chirish'

@admin.register(NotificationDaily)
class NotificationDailyAdmin(admin.ModelAdmin):
    list_display = ('date', 'text1', 'text2', 'text3')
    list_filter = ('date',)
    date_hierarchy = 'date'
    search_fields = ('text1', 'text2', 'text3')
    ordering = ('-date',)
    list_per_page = 25

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ('msisdn', 'opi', 'short_number', 'reqid', 'created_at', 'notification_sent')
    search_fields = ('msisdn', 'reqid')
    list_filter = ('created_at', 'notification_sent')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 25
