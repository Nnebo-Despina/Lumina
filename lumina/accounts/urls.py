# accounts/urls.py
# Sign-in related pages for members (/accounts/...) and for the administrator (/manage/...).

from django.urls import path

from lumina.placeholders import page

from . import views

app_name = "accounts"

urlpatterns = [
    # ----------------------- members -----------------------
    path("accounts/register/", views.RegisterView.as_view(), name="register"),
    path("accounts/login/", views.LoginView.as_view(), name="login"),
    path("accounts/logout/", views.LogoutView.as_view(), name="logout"),
    path("accounts/forgot-password/", views.ForgotPasswordView.as_view(), name="forgot_password"),
    path("accounts/reset/<uidb64>/<token>/", views.ResetPasswordView.as_view(), name="reset_password"),
    path("accounts/change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("accounts/profile/", views.ProfileView.as_view(), name="profile"),

    # ----------------------- administrator -----------------------
    path("manage/login/", views.AdminLoginView.as_view(), name="admin_login"),
    path("manage/forgot-password/", views.AdminForgotPasswordView.as_view(), name="admin_forgot_password"),
    path("manage/profile/", views.admin_profile, name="admin_profile"),

    # TODO (Newbie B): member list, block / unblock / delete.
    # Replace the placeholder with a real view (use AdminRequiredMixin / @admin_required).
    path("manage/members/", page("manage/users.html", access="admin"), name="manage_members"),
]
