from django.urls import path
from . import views

app_name = "analysis"

urlpatterns = [
    # ── Dashboard & upload ────────────────────────────────────────────────────
    path("",        views.DashboardView.as_view(), name="dashboard"),
    path("upload/", views.UploadCSVView.as_view(),  name="upload"),

    # ── Yearly CRUD ───────────────────────────────────────────────────────────
    # List:   GET  /yearly/
    # Create: GET  /yearly/add/           (show form)
    #         POST /yearly/add/           (save record)
    # Update: GET  /yearly/<pk>/edit/     (show pre-filled form)
    #         POST /yearly/<pk>/edit/     (save changes)
    # Delete: GET  /yearly/<pk>/delete/   (show confirmation)
    #         POST /yearly/<pk>/delete/   (perform deletion)
    path("yearly/",                  views.YearlyListView.as_view(),   name="yearly-list"),
    path("yearly/add/",              views.YearlyCreateView.as_view(), name="yearly-create"),
    path("yearly/<int:pk>/edit/",    views.YearlyUpdateView.as_view(), name="yearly-update"),
    path("yearly/<int:pk>/delete/",  views.YearlyDeleteView.as_view(), name="yearly-delete"),

    # ── Monthly CRUD ──────────────────────────────────────────────────────────
    path("monthly/",                 views.MonthlyListView.as_view(),   name="monthly-list"),
    path("monthly/add/",             views.MonthlyCreateView.as_view(), name="monthly-create"),
    path("monthly/<int:pk>/edit/",   views.MonthlyUpdateView.as_view(), name="monthly-update"),
    path("monthly/<int:pk>/delete/", views.MonthlyDeleteView.as_view(), name="monthly-delete"),

    # ── Analysis ──────────────────────────────────────────────────────────────
    path("analysis/", views.AnalysisView.as_view(), name="analysis"),

    # ── Downloads ─────────────────────────────────────────────────────────────
    path("download/yearly-csv/",      views.DownloadYearlyCSVView.as_view(),     name="dl-yearly-csv"),
    path("download/monthly-csv/",     views.DownloadMonthlyCSVView.as_view(),    name="dl-monthly-csv"),
    path("download/clinic-chart/",    views.DownloadClinicChartView.as_view(),   name="dl-clinic-chart"),
    path("download/monthly-chart/",   views.DownloadMonthlyChartView.as_view(),  name="dl-monthly-chart"),
    path("download/bootstrap-chart/", views.DownloadBootstrapChartView.as_view(),name="dl-bootstrap-chart"),
]