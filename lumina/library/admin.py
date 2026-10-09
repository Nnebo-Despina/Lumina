# library/admin.py
from django.contrib import admin

from .models import DownloadLog, ReadingProgress, VideoView


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "last_page", "updated_at")
    list_filter = ("book__category",)
    search_fields = ("user__email", "book__title")
    readonly_fields = ("updated_at",)


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    """Read-only history: downloads are recorded by the site, never edited by hand."""
    list_display = ("user", "book", "downloaded_at")
    list_filter = ("book__category", "downloaded_at")
    search_fields = ("user__email", "book__title")
    date_hierarchy = "downloaded_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(VideoView)
class VideoViewAdmin(admin.ModelAdmin):
    list_display = ("user", "video", "viewed_at")
    list_filter = ("video__category", "viewed_at")
    search_fields = ("user__email", "video__title")
    date_hierarchy = "viewed_at"