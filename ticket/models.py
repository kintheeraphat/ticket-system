from django.db import models

class Ticket(models.Model):
    title = models.CharField(max_length=255)

    # Django สร้างให้เอง (aware → UTC)
    created_at = models.DateTimeField(auto_now_add=True)

    # วันที่ครบกำหนด (ต้องเป็น aware ก่อน save)
    due_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
