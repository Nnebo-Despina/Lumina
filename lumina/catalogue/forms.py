# catalogue/forms.py
# BookForm, VideoForm, CategoryForm and BookTypeForm are the original plain forms.
# The *Admin* forms below are the ones used by the administration pages
# (/manage/...): they add the CSS classes of the admin stylesheet, auto-fill
# slugs, handle the "physical copies" field, and check uploads.

from django import forms
from django.utils.text import slugify

from lumina.formutils import AdminFormMixin

from .models import Book, BookCopy, BookType, Category, Video


# ----------------------------------------------------------------- original forms
class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        exclude = ["created_by", "created_at", "updated_at"]


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        exclude = ["created_at"]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "description", "allow_download"]


class BookTypeForm(forms.ModelForm):
    class Meta:
        model = BookType
        fields = ["name", "description"]


# ----------------------------------------------------------------- administration forms
class CategoryAdminForm(AdminFormMixin, forms.ModelForm):
    """Add / edit a category. The slug is optional: it is made from the name.

    (allow_download is NOT here on purpose: it is changed on the Download Permissions page,
    and leaving a check box out of a form would silently switch it off.)"""

    slug = forms.SlugField(required=False, help_text="Leave empty to create it from the name.")

    class Meta:
        model = Category
        fields = ["name", "slug", "description"]

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if slug:
            return slug
        base = slugify(self.cleaned_data.get("name", "")) or "category"
        candidate, n = base, 2
        others = Category.objects.exclude(pk=self.instance.pk)
        while others.filter(slug=candidate).exists():       # keep it unique: science, science-2 ...
            candidate = f"{base}-{n}"
            n += 1
        return candidate


class BookTypeAdminForm(AdminFormMixin, forms.ModelForm):
    class Meta:
        model = BookType
        fields = ["name", "description"]


class BookAdminForm(AdminFormMixin, forms.ModelForm):
    """Add / edit a book, including its physical stock."""

    copies = forms.IntegerField(
        label="Physical copies in stock", min_value=0, required=False, initial=0,
        help_text="0 = digital title only. Each copy gets its own inventory code. Copies can only be added here.",
    )

    class Meta:
        model = Book
        fields = [
            "title", "author", "publisher", "category", "book_type", "year", "pages",
            "isbn", "description", "cover", "file", "download_permission", "status",
        ]
        widgets = {
            "cover": forms.FileInput(attrs={"accept": "image/*"}),
            "file": forms.FileInput(attrs={"accept": ".pdf"}),
            "download_permission": forms.RadioSelect,
            "description": forms.Textarea(attrs={"placeholder": "A short summary shown on the book page"}),
            "year": forms.NumberInput(attrs={"min": 1000, "max": 2100, "placeholder": "2024"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].empty_label = "Choose a category"
        self.fields["book_type"].empty_label = "Choose a type"
        self.fields["category"].queryset = Category.objects.order_by("name")
        if self.instance.pk:
            self.fields["copies"].initial = self.instance.copies.count()

    def clean_copies(self):
        wanted = self.cleaned_data.get("copies") or 0
        have = self.instance.copies.count() if self.instance.pk else 0
        if wanted < have:
            raise forms.ValidationError(
                f"This book already has {have} copies. Copies can only be increased here."
            )
        return wanted

    def save_copies(self, book):
        """Create the missing BookCopy rows (LUM-0007-01, LUM-0007-02 ...). Returns how many."""
        wanted = self.cleaned_data.get("copies") or 0
        existing = book.copies.count()
        created, n = 0, existing
        while existing + created < wanted:
            n += 1
            code = f"LUM-{book.pk:04d}-{n:02d}"
            if BookCopy.objects.filter(inventory_code=code).exists():
                continue
            BookCopy.objects.create(book=book, inventory_code=code)
            created += 1
        return created


class VideoAdminForm(AdminFormMixin, forms.ModelForm):
    """Add / edit a video: needs a link OR an uploaded file."""

    class Meta:
        model = Video
        fields = [
            "title", "category", "level", "duration", "video_url",
            "video_file", "thumbnail", "description", "status",
        ]
        widgets = {
            "video_file": forms.FileInput(attrs={"accept": "video/*"}),
            "thumbnail": forms.FileInput(attrs={"accept": "image/*"}),
            "duration": forms.TextInput(attrs={"placeholder": "12:40"}),
            "video_url": forms.URLInput(attrs={"placeholder": "https://..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].empty_label = "Choose a category"
        self.fields["category"].queryset = Category.objects.order_by("name")

    def clean(self):
        data = super().clean()
        has_file = data.get("video_file") or (self.instance.pk and self.instance.video_file)
        if not data.get("video_url") and not has_file:
            raise forms.ValidationError("Give a video link or upload a video file.")
        return data
