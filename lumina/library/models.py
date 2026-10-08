from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class ReadingProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    last_chapter = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.book} (Chapter {self.last_chapter})"

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['user', 'book'], name='unique_user_book_progress')
        ]
    class VideoView(models.Model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        video = models.ForeignKey('Video', on_delete=models.CASCADE)
        viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.video} (Viewed at: {self.viewed_atfffff   })"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'video'], name='unique_user_video_view')
        ]