from django import forms


class StyledPredictionForm(forms.ModelForm):
    """
    Base class that automatically applies Bootstrap classes
    to all prediction forms.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():

            widget = field.widget

            # Don't override hidden inputs
            if isinstance(widget, forms.HiddenInput):
                continue

            # Radio buttons
            if isinstance(widget, forms.RadioSelect):
                widget.attrs["class"] = "form-check-input"

            # Dropdowns
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"

            # Everything else
            else:
                widget.attrs["class"] = "form-control"

            widget.attrs.setdefault("placeholder", field.label)