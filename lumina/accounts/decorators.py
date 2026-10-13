# accounts/decorators.py
# Server-side access control for the whole project.
#
# Hiding a link is NOT security. Every protected view must be wrapped with one of
# these, so a typed-in URL is rejected too.
#
#   Function views                       Class-based views
#   --------------------------------     ----------------------------------------
#   @member_required                     class MyView(MemberRequiredMixin, ...)
#   @admin_required                      class MyView(AdminRequiredMixin, ...)
#
# Three different ideas that must never be mixed up:
#   * member  = any logged-in, active, NOT blocked user
#   * blocked = a member the administrator has blocked (is_blocked=True): logged
#               out and refused everywhere that needs a member
#   * admin   = a user with is_staff=True (the librarian / administrator)

from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, resolve_url
from django.utils.decorators import method_decorator

BLOCKED_MESSAGE = "Your account has been blocked. Please contact the library."


def member_required(view_func):
    """Only logged-in, unblocked users may open the page."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user

        # 1) Guests are sent to the member login page and brought back afterwards
        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path(), resolve_url("accounts:login"))

        # 2) A member blocked while logged in is signed out immediately
        if user.is_blocked:
            logout(request)
            messages.error(request, BLOCKED_MESSAGE)
            return redirect("accounts:login")

        return view_func(request, *args, **kwargs)

    return wrapper


def admin_required(view_func):
    """Only administrators (is_staff) may open the page."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user

        # 1) Guests are sent to the ADMIN login page
        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path(), resolve_url("accounts:admin_login"))

        # 2) Logged in but not an administrator (or blocked): 403 Forbidden.
        #    (Not a redirect: an ordinary member must not be told the page exists.)
        if not user.is_staff or user.is_blocked:
            raise PermissionDenied

        return view_func(request, *args, **kwargs)

    return wrapper


class MemberRequiredMixin:
    """Class-based-view version of @member_required."""

    @method_decorator(member_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin:
    """Class-based-view version of @admin_required."""

    @method_decorator(admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
