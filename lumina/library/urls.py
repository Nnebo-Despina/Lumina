# library/urls.py
# OWNER: Intermediate developer (member experience)
# Placeholders from lumina/placeholders.py: replace each page(...) with your real view.

from django.urls import path

from lumina.placeholders import page

app_name = "library"

urlpatterns = [
    path("member/account/", page("library/account.html", access="member"), name="account"),
    path("member/read/<int:pk>/", page("library/read.html", access="member"), name="read"),
]
