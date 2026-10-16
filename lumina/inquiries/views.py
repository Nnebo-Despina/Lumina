# inquiries/views.py
# Public "Contact us" form + the administrator's inbox.

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView

from accounts.decorators import admin_required

from .forms import ContactForm
from .models import Inquiry


class ContactView(CreateView):
    """Guests and members can send an inquiry."""

    form_class = ContactForm
    template_name = "inquiries/contact.html"
    success_url = reverse_lazy("inquiries:contact")

    def get_initial(self):
        user = self.request.user
        if user.is_authenticated:                       # members do not retype their details
            return {"name": user.get_full_name(), "email": user.email}
        return {}

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user      # remember who sent it
        messages.success(self.request, "Thank you! Your message was sent. We will reply within two working days.")
        return super().form_valid(form)


@admin_required
def manage_inquiries(request):
    """Inbox. GET: status = pending / answered."""
    inquiries = Inquiry.objects.select_related("user").order_by("-created_at")
    status = request.GET.get("status", "")
    if status in {"pending", "answered"}:
        inquiries = inquiries.filter(status=status)
    return render(request, "manage/inquiries.html", {
        "inquiries": inquiries, "current_status": status,
        "pending_total": Inquiry.objects.filter(status=Inquiry.Status.PENDING).count(),
    })


@admin_required
@require_POST
def manage_inquiry_answered(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    inquiry.status = Inquiry.Status.ANSWERED
    inquiry.answered_at = timezone.now()
    inquiry.save(update_fields=["status", "answered_at"])
    messages.success(request, f"The message from {inquiry.name} was marked as answered.")
    return redirect("inquiries:manage_inquiries")
