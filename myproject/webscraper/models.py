from django.db import models

class CrawledData(models.Model):
    url = models.URLField()
    keyword = models.CharField(max_length=100)
    data = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_new = models.BooleanField(default=True)