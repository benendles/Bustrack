from django.db import models
from io import BytesIO
from django.core.files.base import ContentFile
import qrcode

class Website(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    receipt_image = models.ImageField(upload_to='receipt_images/', blank=True, null=True)
    picture = models.ImageField(upload_to='user_pictures/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes', blank=True, null=True)

    def __str__(self):
        return f"Extracted Image {self.id} - {self.name}"

    def generate_qr(self, url):
        qr_img = qrcode.make(url)
        qr_img = qr_img.convert('RGB')
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        self.qr_code.save(f'qr_code_{self.name}.png', ContentFile(buffer.getvalue()), save=False)
        buffer.close()