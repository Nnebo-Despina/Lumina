"""
URL configuration for the Lumina E-Library project.

Every app owns its own urls.py (with an app_name) and declares its FULL paths,
so they are all included at the site root here.

    accounts   -> /accounts/...   member sign-in pages     + /manage/login/ ... admin sign-in pages
    catalogue  -> /  /about/ /books/ /videos/              + /manage/ (dashboard, books, categories ...)
    library    -> /member/account/  /member/read/<id>/
    inquiries  -> /contact/                                + /manage/inquiries/
    loans      -> /member/loans/                           + /manage/issues/

The library's own administration area lives under /manage/.
Django's built-in admin site was moved to /django-admin/ so the two are never confused.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("django-admin/", admin.site.urls),   # Django's built-in admin (developers only)

    path("", include("accounts.urls")),
    path("", include("catalogue.urls")),
    path("", include("library.urls")),
    path("", include("inquiries.urls")),
    path("", include("loans.urls")),
]

# Serve uploaded IMAGES while developing (book covers and video thumbnails only).
# Book PDFs and video files are deliberately NOT public: members reach them through
# the protected views library:file / library:download / library:watch.
# (In production the web server must do the same: never expose /media/books/.)
# (Friendly 403 / 404 pages are the templates templates/403.html and templates/404.html;
#  Django's default error views pick them up automatically.)
if settings.DEBUG:
    urlpatterns += [
        re_path(r"^media/(?P<path>(?:covers|thumbnails)/.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
