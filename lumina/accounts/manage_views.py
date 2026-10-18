# accounts/manage_views.py
# Member management for the administrator: list, filter, block, unblock, delete.
# (The administrator accounts themselves are never listed here, so an admin can
#  not block or delete another admin, or themselves.)

from django.contrib import messages
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .models import User


def _member(pk):
    return get_object_or_404(User, pk=pk, is_staff=False)


@admin_required
def manage_members(request):
    """GET: q (name or email), status (active / blocked), role."""
    params = request.GET
    members = User.objects.filter(is_staff=False).annotate(
        on_loan=Count("book_issues", filter=Q(book_issues__status="issued"), distinct=True)
    ).order_by("-date_joined")

    q = (params.get("q") or "").strip()
    if q:
        members = members.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
    if params.get("status") == "blocked":
        members = members.filter(is_blocked=True)
    elif params.get("status") == "active":
        members = members.filter(is_blocked=False)
    if params.get("role") in dict(User.Role.choices):
        members = members.filter(role=params["role"])

    return render(request, "manage/users.html", {
        "members": members, "q": q, "status": params.get("status", ""), "role": params.get("role", ""),
        "roles": User.Role.choices, "total": User.objects.filter(is_staff=False).count(),
    })


@admin_required
@require_POST
def manage_member_block(request, pk):
    member = _member(pk)
    member.is_blocked = True
    member.save(update_fields=["is_blocked"])
    messages.success(request, f"{member.get_full_name() or member.email} was blocked.")
    return redirect("accounts:manage_members")


@admin_required
@require_POST
def manage_member_unblock(request, pk):
    member = _member(pk)
    member.is_blocked = False
    member.save(update_fields=["is_blocked"])
    messages.success(request, f"{member.get_full_name() or member.email} was unblocked.")
    return redirect("accounts:manage_members")


@admin_required
@require_POST
def manage_member_delete(request, pk):
    member = _member(pk)
    name = member.get_full_name() or member.email
    try:
        member.delete()
        messages.success(request, f"{name} was deleted.")
    except ProtectedError:
        messages.error(request, f"{name} has loan records and cannot be deleted. Block the account instead.")
    return redirect("accounts:manage_members")
