from django.contrib import admin
from .models import YearlyRecord, MonthlyRecord


@admin.register(YearlyRecord)
class YearlyRecordAdmin(admin.ModelAdmin):
    # proportion_deaths is a @property, not a DB column — admin displays it
    # read-only automatically since it has no corresponding form field.
    list_display = ("year", "clinic", "births", "deaths", "proportion_deaths")
    list_filter  = ("clinic",)   # sidebar filter: click Clinic 1 / Clinic 2
    ordering     = ("clinic", "year")


@admin.register(MonthlyRecord)
class MonthlyRecordAdmin(admin.ModelAdmin):
    # after_handwashing is a @property; displayed as a boolean tick/cross icon.
    list_display = ("date", "births", "deaths", "proportion_deaths", "after_handwashing")
    ordering     = ("date",)
# Register your models here.
