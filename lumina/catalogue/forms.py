from django import forms
from .models import Book, Video, Category, BookType


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
        fields = [
            "name",
            "slug",
            "description",
            "allow_download",
        ]


class BookTypeForm(forms.ModelForm):
    class Meta:
        model = BookType
        fields = ["name", "description"]