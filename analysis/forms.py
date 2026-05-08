from django import forms
from .models import YearlyRecord, MonthlyRecord


class CSVUploadForm(forms.Form):
    """
    A plain Form (not ModelForm) for uploading one or two CSV files.
    Both fields are optional individually, but the clean() method enforces
    that at least one file must be provided.

    The DaisyUI CSS classes are applied via the widget attrs dict —
    this keeps the template clean (no manual class="" on inputs).
    """

    yearly_csv = forms.FileField(
        required=False,
        label="Yearly deaths CSV  (yearly_deaths_by_clinic.csv)",
        # file-input and file-input-bordered are DaisyUI classes for styled
        # file upload buttons. w-full makes it span its container.
        widget=forms.ClearableFileInput(attrs={"class": "file-input file-input-bordered w-full"}),
    )
    monthly_csv = forms.FileField(
        required=False,
        label="Monthly deaths CSV  (monthly_deaths.csv)",
        widget=forms.ClearableFileInput(attrs={"class": "file-input file-input-bordered w-full"}),
    )

    def clean(self):
        """
        Cross-field validation: raises a non-field error if the user submits
        the form without choosing any file. This runs after each field's own
        validation, so cleaned_data is already populated here.
        """
        cleaned = super().clean()
        if not cleaned.get("yearly_csv") and not cleaned.get("monthly_csv"):
            raise forms.ValidationError("Upload at least one CSV file.")
        return cleaned


class YearlyRecordForm(forms.ModelForm):
    """
    ModelForm for creating/editing a YearlyRecord.
    Declaring widgets in Meta.widgets applies DaisyUI classes without
    needing a custom __init__ — the cleanest way to style ModelForms.
    The clinic field uses a Select widget with explicit choices rather than
    a free-text input to prevent typos like "Clinic 1" vs "clinic 1".
    """
    class Meta:
        model  = YearlyRecord
        fields = ["year", "births", "deaths", "clinic"]
        widgets = {
            "year":   forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "births": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "deaths": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "clinic": forms.Select(
                # Hard-coded choices match the values the CSV importer writes.
                choices=[("clinic 1", "Clinic 1"), ("clinic 2", "Clinic 2")],
                attrs={"class": "select select-bordered w-full"},
            ),
        }


class MonthlyRecordForm(forms.ModelForm):
    """
    ModelForm for creating/editing a MonthlyRecord.
    The date field uses type="date" so browsers render a native date-picker
    instead of a plain text input.
    """
    class Meta:
        model  = MonthlyRecord
        fields = ["date", "births", "deaths"]
        widgets = {
            # type="date" renders a browser date-picker (HTML5).
            "date":   forms.DateInput(attrs={"type": "date", "class": "input input-bordered w-full"}),
            "births": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "deaths": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
        }
