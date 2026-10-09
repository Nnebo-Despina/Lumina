# catalogue/admin.py
# Registers Category, BookType, Book and Video in Django's admin site.

from django.contrib import admin

from .models import Book, BookType, Category, Video, BookCopy


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "allow_download", "created_at")
    list_editable = ("allow_download",)            # tick/untick right in the list
    search_fields = ("name", "description")        # also needed by autocomplete below
    prepopulated_fields = {"slug": ("name",)}      # slug fills itself from the name
    readonly_fields = ("created_at",)

class BookCopyInline(admin.TabularInline):
    """Lets you add physical copies while editing a book."""
    model = BookCopy
    extra = 1
    fields = ("inventory_code", "status", "acquired_at", "notes")


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ("inventory_code", "book", "status", "acquired_at")
    list_filter = ("status", "book__category")
    search_fields = ("inventory_code", "book__title")   # needed by autocomplete in loans
    autocomplete_fields = ("book",)

@admin.register(BookType)
class BookTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)                      # also needed by autocomplete below


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title", "author", "publisher", "category", "book_type",
        "download_permission", "status", "created_at",
    )
    list_filter = ("category", "book_type", "download_permission", "status")
    list_editable = ("download_permission", "status")
    search_fields = ("title", "author", "publisher", "isbn")
    autocomplete_fields = ("category", "book_type")   # searchable dropdowns
    readonly_fields = ("created_by", "created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        ("Book details", {"fields": ("title", "author", "publisher", "category", "book_type")}),
        ("More information", {"fields": ("year", "pages", "isbn", "description")}),
        ("Files", {"fields": ("cover", "file")}),
        ("Publishing", {"fields": ("status", "download_permission")}),
        ("Record info", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        # Remember which admin added the book
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    inlines = [BookCopyInline]


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "level", "duration", "status", "created_at")
    list_filter = ("category", "level", "status")
    list_editable = ("status",)
    search_fields = ("title", "description")
    autocomplete_fields = ("category",)
    readonly_fields = ("created_at",)


