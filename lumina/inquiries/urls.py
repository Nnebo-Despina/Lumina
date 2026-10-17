# inquiries/urls.py
# OWNER: Newbie B (contact form + inquiry inbox). Connected to the database.

from django.urls import path

from . import views

app_name = "inquiries"

urlpatterns = [
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("manage/inquiries/", views.manage_inquiries, name="manage_inquiries"),
    path("manage/inquiries/<int:pk>/answered/", views.manage_inquiry_answered, name="manage_inquiry_answered"),
]
