# lumina/formutils.py
# Small helpers shared by the forms of several apps.

from django import forms


class AdminFormMixin:
    """Gives every widget the CSS class the admin stylesheet expects.

    Text boxes, text areas and file pickers get class="field"; drop-downs get
    class="select". Check boxes and radio buttons are left alone (they are styled
    by hand in the templates)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
                continue
            css = "select" if isinstance(widget, forms.Select) else "field"
            widget.attrs["class"] = (widget.attrs.get("class", "") + " " + css).strip()
