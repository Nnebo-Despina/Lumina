from django.db import models
from accounts.models import User
from catalogue.models import Book

# Create your models here.

class DwonloadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    book = models.ForeignKey(Book, on_delete=models.SET_NULL)
    downloaded_at = models.DateTimeField(auto_now_add=True)

