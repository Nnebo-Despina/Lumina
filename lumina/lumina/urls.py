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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),   # Django's built-in admin (developers only)

    path("", include("accounts.urls")),
    path("", include("catalogue.urls")),
    path("", include("library.urls")),
    path("", include("inquiries.urls")),
    path("", include("loans.urls")),
]

# Serve uploaded files (covers, PDFs, videos) while developing.
# (Friendly 403 / 404 pages are the templates templates/403.html and templates/404.html;
#  Django's default error views pick them up automatically.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

