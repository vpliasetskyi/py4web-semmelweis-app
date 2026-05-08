"""
URL configuration for semmelweis_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # namespace="analysis" means URL names are referenced as "analysis:dashboard" etc.
    path("", include("analysis.urls", namespace="analysis")),
# In development, Django serves media files (uploaded images) itself.
# static() returns an empty list in production when DEBUG=False.
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# analysis/urls.py
# App-level URLconf. Each path() maps a URL pattern to a view class.
# app_name must match the namespace declared in the root urls.py include().

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