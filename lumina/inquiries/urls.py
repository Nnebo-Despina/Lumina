# inquiries/urls.py
# OWNER: Newbie B (contact form + inquiry inbox)
# Placeholders from lumina/placeholders.py: replace each page(...) with your real view.

from django.urls import path

from lumina.placeholders import page

app_name = "inquiries"

urlpatterns = [
    path("contact/", page("inquiries/contact.html"), name="contact"),
    path("manage/inquiries/", page("manage/inquiries.html", access="admin"), name="manage_inquiries"),
]
