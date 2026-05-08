from django.shortcuts import render

# Django's generic class-based views handle the boilerplate for list/create/
# update/delete operations. We override only what we need to customise.
from django.views.generic import (
    TemplateView,   # renders a template with a context — no model needed
    ListView,       # renders a list of model instances
    CreateView,     # renders and processes a creation form
    UpdateView,     # renders and processes an edit form
    DeleteView,     # renders and processes a deletion confirmation
)
from django.views import View       # base class for views that need custom GET/POST
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import HttpResponse

from .models import YearlyRecord, MonthlyRecord
from .forms import CSVUploadForm, YearlyRecordForm, MonthlyRecordForm
from . import services


# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD
# Uses the base View class directly because we need explicit GET and POST
# methods with custom logic (calling services functions).
# ─────────────────────────────────────────────────────────────────────────────

class UploadCSVView(View):
    template_name = "analysis/upload.html"

    def get(self, request):
        # Show an empty upload form.
        return render(request, self.template_name, {"form": CSVUploadForm()})

    def post(self, request):
        # request.FILES contains the uploaded file objects.
        form = CSVUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            # Re-render the form with validation errors.
            return render(request, self.template_name, {"form": form})
        # call the appropriate importer only for the files that were provided
        if form.cleaned_data.get("yearly_csv"):
            services.import_yearly_csv(form.cleaned_data["yearly_csv"])
        if form.cleaned_data.get("monthly_csv"):
            services.import_monthly_csv(form.cleaned_data["monthly_csv"])
        # Post-Redirect-Get pattern: redirect after a successful POST to
        # prevent the browser from re-submitting on refresh.
        return redirect("analysis:dashboard")


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD (homepage)
# TemplateView is used because this page does not list a single model — it
# shows summary stats and charts from two different models.
# ─────────────────────────────────────────────────────────────────────────────

class DashboardView(TemplateView):
    template_name = "analysis/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["yearly_count"]       = YearlyRecord.objects.count()
        ctx["monthly_count"]      = MonthlyRecord.objects.count()
        # has_data drives the "no data" warning banner in the template.
        ctx["has_data"]           = ctx["yearly_count"] > 0 or ctx["monthly_count"] > 0
        # JSON strings that Chart.js in the template will deserialise.
        ctx["yearly_chart_data"]  = services.yearly_chart_data()
        ctx["monthly_chart_data"] = services.monthly_chart_data()
        return ctx


# ─────────────────────────────────────────────────────────────────────────────
# YEARLY — CRUD
# All four generic views share the same form template (yearly_form.html) for
# Create and Update, and confirm_delete.html for Delete.
# success_url uses reverse_lazy() instead of reverse() because the URLconf has
# not been loaded yet when the class body is evaluated at import time.
# ─────────────────────────────────────────────────────────────────────────────

class YearlyListView(ListView):
    model               = YearlyRecord
    template_name       = "analysis/yearly_list.html"
    context_object_name = "records"   # name used in the template for the queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Provide pre-filtered querysets so the template can show per-clinic tabs
        # without needing to filter in the template layer.
        ctx["clinic1"]    = YearlyRecord.objects.filter(clinic="clinic 1")
        ctx["clinic2"]    = YearlyRecord.objects.filter(clinic="clinic 2")
        ctx["chart_data"] = services.yearly_chart_data()
        return ctx


class YearlyCreateView(CreateView):
    model         = YearlyRecord
    form_class    = YearlyRecordForm
    template_name = "analysis/yearly_form.html"
    success_url   = reverse_lazy("analysis:yearly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # 'title' and 'cancel_url' are used by the shared yearly_form.html template.
        ctx["title"]      = "Add Yearly Record"
        ctx["cancel_url"] = reverse_lazy("analysis:yearly-list")
        return ctx


class YearlyUpdateView(UpdateView):
    model         = YearlyRecord
    form_class    = YearlyRecordForm
    template_name = "analysis/yearly_form.html"
    success_url   = reverse_lazy("analysis:yearly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # self.object is the model instance being edited — set by UpdateView.
        ctx["title"]      = f"Edit Yearly Record — {self.object}"
        ctx["cancel_url"] = reverse_lazy("analysis:yearly-list")
        return ctx


class YearlyDeleteView(DeleteView):
    model         = YearlyRecord
    template_name = "analysis/confirm_delete.html"
    success_url   = reverse_lazy("analysis:yearly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse_lazy("analysis:yearly-list")
        return ctx


# ─────────────────────────────────────────────────────────────────────────────
# MONTHLY — CRUD
# Same structure as the Yearly CRUD group above.
# ─────────────────────────────────────────────────────────────────────────────

class MonthlyListView(ListView):
    model               = MonthlyRecord
    template_name       = "analysis/monthly_list.html"
    context_object_name = "records"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["chart_data"]        = services.monthly_chart_data()
        # Pass the pivot date string so the template can display it without
        # hard-coding it in the HTML.
        ctx["handwashing_start"] = MonthlyRecord.HANDWASHING_START
        return ctx


class MonthlyCreateView(CreateView):
    model         = MonthlyRecord
    form_class    = MonthlyRecordForm
    template_name = "analysis/monthly_form.html"
    success_url   = reverse_lazy("analysis:monthly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"]      = "Add Monthly Record"
        ctx["cancel_url"] = reverse_lazy("analysis:monthly-list")
        return ctx


class MonthlyUpdateView(UpdateView):
    model         = MonthlyRecord
    form_class    = MonthlyRecordForm
    template_name = "analysis/monthly_form.html"
    success_url   = reverse_lazy("analysis:monthly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"]      = f"Edit Monthly Record — {self.object}"
        ctx["cancel_url"] = reverse_lazy("analysis:monthly-list")
        return ctx


class MonthlyDeleteView(DeleteView):
    model         = MonthlyRecord
    template_name = "analysis/confirm_delete.html"
    success_url   = reverse_lazy("analysis:monthly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse_lazy("analysis:monthly-list")
        return ctx


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS
# TemplateView again — one call to services.run_full_analysis() populates the
# entire context for the analysis_results.html template.
# ─────────────────────────────────────────────────────────────────────────────

class AnalysisView(TemplateView):
    template_name = "analysis/analysis_results.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # run_full_analysis() returns a dict; update() merges it into ctx.
        ctx.update(services.run_full_analysis())
        return ctx


# ─────────────────────────────────────────────────────────────────────────────
# DOWNLOADS
# Each view calls a services function that returns raw PNG bytes or a pandas
# DataFrame. The response Content-Disposition header triggers a browser download.
# ─────────────────────────────────────────────────────────────────────────────

class DownloadYearlyCSVView(View):
    def get(self, request):
        df = services.yearly_to_dataframe()
        resp = HttpResponse(content_type="text/csv")
        # attachment; filename= tells the browser to download rather than display.
        resp["Content-Disposition"] = 'attachment; filename="yearly_deaths.csv"'
        df.to_csv(resp, index=False)  # write CSV directly into the response object
        return resp


class DownloadMonthlyCSVView(View):
    def get(self, request):
        df = services.monthly_to_dataframe()
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="monthly_deaths.csv"'
        df.to_csv(resp, index=False)
        return resp


class DownloadClinicChartView(View):
    def get(self, request):
        png = services.clinic_comparison_chart_png()  # raw PNG bytes
        resp = HttpResponse(content_type="image/png")
        resp["Content-Disposition"] = 'attachment; filename="clinic_comparison.png"'
        resp.write(png)
        return resp


class DownloadMonthlyChartView(View):
    def get(self, request):
        png = services.monthly_proportion_chart_png()
        resp = HttpResponse(content_type="image/png")
        resp["Content-Disposition"] = 'attachment; filename="monthly_proportion.png"'
        resp.write(png)
        return resp


class DownloadBootstrapChartView(View):
    def get(self, request):
        png = services.bootstrap_histogram_png()
        resp = HttpResponse(content_type="image/png")
        resp["Content-Disposition"] = 'attachment; filename="bootstrap_ci.png"'
        resp.write(png)
        return resp
# Create your views here.
