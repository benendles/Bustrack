from django.db import models
from io import BytesIO
from django.core.files.base import ContentFile
import qrcode
from django.conf import settings
from django.urls import reverse

class Website(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    receipt_image = models.ImageField(upload_to='receipt_images/',blank=True,null=True)  # Receipt image
    picture = models.ImageField(upload_to='user_pictures/',blank=True,null=True)           # User's own picture
    qr_code = models.ImageField(upload_to='qr_codes', blank=True, null=True)

    def __str__(self):
        return f"Extracted Image {self.id} - {self.name}"

   
class Website(models.Model):
    ...

    def generate_qr(self, url):
        import qrcode
        from io import BytesIO
        from django.core.files.base import ContentFile

        qr_img = qrcode.make(url)
        qr_img = qr_img.convert('RGB')
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        self.qr_code.save(f'qr_code_{self.name}.png', ContentFile(buffer.getvalue()), save=False)
        buffer.close()