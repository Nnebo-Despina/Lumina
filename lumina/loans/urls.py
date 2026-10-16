# loans/urls.py
# OWNER: Intermediate developer (lending is an EXTRA feature). Connected to the database.

from django.urls import path

from . import views

app_name = "loans"

urlpatterns = [
    path("member/loans/", views.my_loans, name="my_loans"),
    path("manage/issues/", views.manage_issues, name="manage_issues"),
    path("manage/issues/new/", views.manage_issue_new, name="manage_issue_new"),
    path("manage/issues/<int:pk>/return/", views.manage_issue_return, name="manage_issue_return"),
]
