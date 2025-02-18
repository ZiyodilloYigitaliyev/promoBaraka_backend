from django.core.management.base import BaseCommand
from views import UploadAndNotifyService

class Command(BaseCommand):
    help = "Har kuni xlsx fayldan sanani tekshirib, foydalanuvchilarga yuborish"

    def handle(self, *args, **kwargs):
        UploadAndNotifyService.check_and_notify_users()
        self.stdout.write(self.style.SUCCESS("✅ SMS jo‘natish jarayoni tugadi!"))
