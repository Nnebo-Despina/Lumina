# catalogue/templatetags/catalogue_extras.py
# Template helpers.  In a template:  {% load catalogue_extras %}

from django import template
from django.utils.safestring import mark_safe

from catalogue.permissions import book_download_allowed

register = template.Library()

# Book covers without an uploaded image are drawn with a CSS gradient. The two
# colours are picked from this palette (the Lumina purple / gold / earth colours)
# using the book's id, so a book always keeps the same cover.
PALETTE = [
    ("#5C3487", "#241536"), ("#A9792F", "#2E1A47"), ("#9575B8", "#3B2159"),
    ("#8A5A34", "#241536"), ("#3B2159", "#C89B3D"), ("#2E1A47", "#9575B8"),
    ("#C89B3D", "#5C3487"), ("#8A5A34", "#5C3487"),
]
ICONS = ["&#9998;", "&#9881;", "&#9884;", "&#9876;", "&#10047;", "&#9733;"]


@register.filter
def cover_style(obj):
    """{{ book|cover_style }}  ->  '--c1:#5C3487;--c2:#241536'"""
    c1, c2 = PALETTE[(obj.pk or 0) % len(PALETTE)]
    return f"--c1:{c1};--c2:{c2}"


@register.filter
def category_icon(index):
    """{{ forloop.counter0|category_icon }}  ->  a small symbol for the category tile"""
    return mark_safe(ICONS[int(index) % len(ICONS)])


@register.filter
def download_allowed(book):
    """{{ book|download_allowed }}  ->  True when the admin's setting allows downloads."""
    return bool(book.file) and book_download_allowed(book)
