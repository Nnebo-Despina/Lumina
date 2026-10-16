# library/urls.py
# OWNER: Intermediate developer (member experience). Connected to the database.

from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("member/account/", views.account, name="account"),
    path("member/read/<int:pk>/", views.read, name="read"),
    path("member/read/<int:pk>/save/", views.save_progress, name="save_progress"),
    path("member/files/<int:pk>/", views.book_file, name="file"),               # the PDF (members only)
    path("member/download/<int:pk>/", views.download, name="download"),
    path("member/watch/<int:pk>/", views.watch, name="watch"),
]
