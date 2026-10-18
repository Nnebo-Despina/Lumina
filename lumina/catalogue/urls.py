# catalogue/urls.py
# OWNERS: Pro 2 (books, videos, downloads, reports, dashboard)
#         Newbie A (home, about, categories, book types)
#         Intermediate (browse / search, book detail, videos page)
#
# All pages are connected to the database now:
#   views.py         public pages          manage_views.py  /manage/... pages (admin only)

from django.urls import path

from . import manage_views as manage
from . import views

app_name = "catalogue"

urlpatterns = [
    # ----------------------- public site -----------------------
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("books/", views.BookListView.as_view(), name="books"),                 # ?q= &by= &category= &type= &page=
    path("books/<int:pk>/", views.book_detail, name="book_detail"),
    path("videos/", views.VideoListView.as_view(), name="videos"),              # members only

    # ----------------------- administration (/manage/...) -----------------------
    path("manage/", manage.manage_dashboard, name="manage_dashboard"),

    path("manage/categories/", manage.manage_categories, name="manage_categories"),
    path("manage/categories/<int:pk>/edit/", manage.manage_category_edit, name="manage_category_edit"),
    path("manage/categories/<int:pk>/delete/", manage.manage_category_delete, name="manage_category_delete"),

    path("manage/book-types/", manage.manage_book_types, name="manage_book_types"),
    path("manage/book-types/<int:pk>/delete/", manage.manage_book_type_delete, name="manage_book_type_delete"),

    path("manage/books/", manage.manage_books, name="manage_books"),
    path("manage/books/add/", manage.manage_book_add, name="manage_book_add"),
    path("manage/books/<int:pk>/edit/", manage.manage_book_edit, name="manage_book_edit"),
    path("manage/books/<int:pk>/delete/", manage.manage_book_delete, name="manage_book_delete"),

    path("manage/videos/", manage.manage_videos, name="manage_videos"),
    path("manage/videos/add/", manage.manage_video_add, name="manage_video_add"),
    path("manage/videos/<int:pk>/edit/", manage.manage_video_edit, name="manage_video_edit"),
    path("manage/videos/<int:pk>/delete/", manage.manage_video_delete, name="manage_video_delete"),

    path("manage/downloads/", manage.manage_downloads, name="manage_downloads"),
    path("manage/reports/", manage.manage_reports, name="manage_reports"),
]
