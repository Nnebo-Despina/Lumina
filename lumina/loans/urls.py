# loans/urls.py
# OWNER: Intermediate developer (lending is an EXTRA feature - build it last)
# Placeholders from lumina/placeholders.py: replace each page(...) with your real view.

from django.urls import path

from lumina.placeholders import page

app_name = "loans"

urlpatterns = [
    path("member/loans/", page("loans/my_loans.html", access="member"), name="my_loans"),
    path("manage/issues/", page("manage/issues.html", access="admin"), name="manage_issues"),
    path("manage/issues/new/", page("manage/issue_form.html", access="admin"), name="manage_issue_new"),
]
