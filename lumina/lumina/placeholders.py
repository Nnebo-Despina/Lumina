# lumina/placeholders.py
# --------------------------------------------------------------------------
# TEMPORARY scaffolding written by the lead so that EVERY page of the site
# already has a URL, renders, and is protected correctly while teammates build
# their real views.
#
#   page("catalogue/books.html")                  -> anyone can open it
#   page("library/account.html", access="member") -> logged-in, unblocked users only
#   page("manage/books.html",   access="admin")   -> administrators only
#
# The page simply shows the template with its SAMPLE data. When you write your
# real view, replace the page(...) line in YOUR app's urls.py with it and keep
# the same url name (other templates link to it with {% url %}).
# Protect your real view with @member_required / @admin_required (or the
# matching mixins) from accounts/decorators.py.
#
# When every page has a real view, this file can be deleted.
# --------------------------------------------------------------------------

from django.views.generic import TemplateView

from accounts.decorators import admin_required, member_required


def page(template_name, access="public"):
    """Return a view that just renders `template_name` with the right access rule."""
    view = TemplateView.as_view(template_name=template_name)
    if access == "member":
        return member_required(view)
    if access == "admin":
        return admin_required(view)
    return view


class BookDetailPlaceholder(TemplateView):
    """Guests see the login prompt version, logged-in users the read/download version."""

    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["catalogue/member_book_detail.html"]
        return ["catalogue/book_detail.html"]


book_detail_page = BookDetailPlaceholder.as_view()
