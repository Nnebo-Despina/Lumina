from django.db import models
from django.core.validators import FileExtensionValidator, RegexValidator
from accounts.models import User

# This is used as a fixed enumeration class for checking download status
class DownloadStatus(models.TextChoices):
    INHERIT = 'INHERIT', 'Inherit'
    ALLOW = 'ALLOW', 'Allow'
    DENY = 'DENY', 'Deny'

# This is used as a fixed enumeration class to checking status
class Statuses(models.TextChoices):
    LIVE = 'LIVE', 'Live'
    DRAFT = 'DRAFT', 'Draft'

# This is used as a fixed enumeration class to show levels of the video's difficulty
class Levels(models.TextChoices):
    BEGINNER = 'BEGINNER', 'Beginner'
    INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
    ADVANCED = 'ADVANCED', 'Advanced'
    ALL = 'ALL', 'All'

mmss_validator = RegexValidator(
    regex=r'^\d+:[0-5]\d$',
    message='Enter a valid duration in MM:SS format'
)

# This is the book model that will store all books
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150)
    publisher = models.CharField(max_length=150, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    book_type = models.ForeignKey(BookType, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    pages = models.PositiveIntegerField(blank=True, null=True)

    # This is used to identify the book
    isbn = models.CharField(max_length=13, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    cover = models.ImageField(upload_to="covers/", blank=True, null=True)

    # This is where the pdf of the book will be stored, I used File extension validator to ensure the file will be in pdf format
    file = models.FileField(
        upload_to="books/", 
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf']
            )
        ]
    )

    download_permission = models.CharField(max_length=10, choices=DownloadStatus.choices, default=DownloadStatus.INHERIT)
    status = models.CharField(max_length=10, choices=Statuses.choices, default=Statuses.LIVE)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Video(models.Model):
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    level = models.CharField(max_length=10, choices=Levels.choices)
    duration = models.CharField(max_length=8, blank=True, null=True, validators=[mmss_validator], help_text="Format: MM:SS")
    video_url = models.URLField(blank=True, null=True)
    video_file = models.URLField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to="thumbnail/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=Statuses.choices, default=Statuses.LIVE)

    created_at = models.DateTimeField(auto_now_add=True)






