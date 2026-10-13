# catalogue/urls.py
# OWNERS: Pro 2 (books, videos, downloads, reports, dashboard)
#         Newbie A (home, about, categories, book types)
#         Intermediate (browse/search, book detail, videos page)
#
# Every route below currently uses a PLACEHOLDER from lumina/placeholders.py.
# Replace each page(...) with your real view and keep the same name=.

from django.urls import path

from lumina.placeholders import book_detail_page, page

app_name = "catalogue"

urlpatterns = [
    # ----------------------- public site -----------------------
    path("", page("catalogue/index.html"), name="home"),                              # Newbie A
    path("about/", page("catalogue/about.html"), name="about"),                       # Newbie A
    path("books/", page("catalogue/books.html"), name="books"),                       # Intermediate (search + filter, ?q= ?category=)
    path("books/<int:pk>/", book_detail_page, name="book_detail"),                    # Intermediate (guest / member versions)
    path("videos/", page("catalogue/videos.html", access="member"), name="videos"),   # Intermediate

    # ----------------------- administration (/manage/...) -----------------------
    path("manage/", page("manage/dashboard.html", access="admin"), name="manage_dashboard"),                    # Pro 2
    path("manage/categories/", page("manage/categories.html", access="admin"), name="manage_categories"),       # Newbie A
    path("manage/book-types/", page("manage/book_types.html", access="admin"), name="manage_book_types"),       # Newbie A
    path("manage/books/", page("manage/books.html", access="admin"), name="manage_books"),                      # Pro 2
    path("manage/books/add/", page("manage/book_form.html", access="admin"), name="manage_book_add"),           # Pro 2
    path("manage/books/<int:pk>/edit/", page("manage/book_form.html", access="admin"), name="manage_book_edit"),  # Pro 2
    path("manage/videos/", page("manage/videos.html", access="admin"), name="manage_videos"),                   # Pro 2
    path("manage/videos/add/", page("manage/video_form.html", access="admin"), name="manage_video_add"),        # Pro 2
    path("manage/videos/<int:pk>/edit/", page("manage/video_form.html", access="admin"), name="manage_video_edit"),  # Pro 2
    path("manage/downloads/", page("manage/downloads.html", access="admin"), name="manage_downloads"),          # Pro 2
    path("manage/reports/", page("manage/reports.html", access="admin"), name="manage_reports"),                # Pro 2
]
