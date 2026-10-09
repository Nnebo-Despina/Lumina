from django.contrib.auth.models import User
from django.db import models
from accounts.models import User
from catalogue.models import Book, Video, BookCopy


# Create your models here.

class DownloadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="download_logs")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="download_logs")
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} downloaded {self.book}"

class ReadingProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reading_progress")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reading_progress")
    last_page = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.book} (Page {self.last_page})"

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['user', 'book'], name='unique_user_book_progress')
        ]

class VideoView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="video_views")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="video_views")
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.video} (Viewed at: {self.viewed_at})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'video'], name='unique_user_video_view')
        ]


