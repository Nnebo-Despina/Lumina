# loans/views.py
# Physical lending (an EXTRA feature, not in the original specification).
#   members : see their OWN loans (my_loans)
#   admin   : issue a copy, see every loan, mark returned

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required, member_required

from .forms import BookIssueForm
from .models import BookIssue


# ------------------------------------------------------------------ member
@member_required
def my_loans(request):
    """A member sees ONLY their own loans (never filter by anything the visitor sends)."""
    today = timezone.localdate()
    loans = list(BookIssue.objects.filter(user=request.user).select_related("copy__book"))
    return render(request, "loans/my_loans.html", {
        "loans": loans,
        "current_count": sum(1 for l in loans if l.status == BookIssue.Status.ISSUED),
        "overdue_count": sum(1 for l in loans if l.status == BookIssue.Status.ISSUED and l.due_date < today),
        "returned_count": sum(1 for l in loans if l.status == BookIssue.Status.RETURNED),
    })


# ------------------------------------------------------------------ administrator
@admin_required
def manage_issues(request):
    """Loan register. GET: status (issued / overdue / returned), q (member, book or copy code)."""
    today = timezone.localdate()
    issues = BookIssue.objects.select_related("user", "copy__book")
    on_loan = issues.filter(status=BookIssue.Status.ISSUED)
    stats = {
        "on_loan": on_loan.count(),
        "overdue": on_loan.filter(due_date__lt=today).count(),
        "returned_month": issues.filter(status=BookIssue.Status.RETURNED,
                                        returned_at__year=today.year, returned_at__month=today.month).count(),
    }
    return render(request, "manage/issues.html", {"issues": issues, "stats": stats})


@admin_required
def manage_issue_new(request):
    form = BookIssueForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        issue = form.save(commit=False)
        issue.issued_by = request.user
        issue.save()                                   # also marks the copy as 'on loan'
        messages.success(request, f"'{issue.copy.book.title}' ({issue.copy.inventory_code}) was issued to {issue.user.get_full_name() or issue.user.email}.")
        return redirect("loans:manage_issues")
    return render(request, "manage/issue_form.html", {"form": form})


@admin_required
@require_POST
def manage_issue_return(request, pk):
    issue = get_object_or_404(BookIssue, pk=pk)
    if issue.status == BookIssue.Status.ISSUED:
        issue.mark_returned()                          # also puts the copy back on the shelf
        messages.success(request, f"'{issue.copy.book.title}' was marked as returned.")
    return redirect("loans:manage_issues")
