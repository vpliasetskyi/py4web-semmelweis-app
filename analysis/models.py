from django.db import models

class YearlyRecord(models.Model):
    """
    Stores one row from yearly_deaths_by_clinic.csv.

    Each row represents the total births and deaths at one clinic for one year.
    The CSV contains data for Clinic 1 and Clinic 2 from 1841 to 1846.
    """

    year   = models.IntegerField()           # e.g. 1841, 1842, …
    births = models.IntegerField()           # total births in that year
    deaths = models.IntegerField()           # total deaths in that year
    clinic = models.CharField(max_length=20) # 'clinic 1' or 'clinic 2'

    class Meta:
        # Default sort order: clinic name first, then year ascending.
        # This means all Clinic 1 rows appear before Clinic 2 rows.
        ordering = ["clinic", "year"]

    def __str__(self):
        # Human-readable label used in admin and delete confirmation pages.
        return f"{self.clinic} – {self.year}"

    @property
    def proportion_deaths(self):
        """
        Computed field: deaths ÷ births, rounded to 6 decimal places.
        @property means it is accessed like an attribute (r.proportion_deaths)
        but is never stored in the database — it is always calculated on the fly.
        The guard against zero prevents ZeroDivisionError if births is 0.
        """
        return round(self.deaths / self.births, 6) if self.births else 0


class MonthlyRecord(models.Model):
    """
    Stores one row from monthly_deaths.csv.

    Contains monthly birth and death counts for Clinic 1 from 1841 to 1849.
    The pivotal date — when Semmelweis mandated handwashing — is June 1847.
    """

    date   = models.DateField()   # first day of the reported month, e.g. 1841-01-01
    births = models.IntegerField()
    deaths = models.IntegerField()

    # Class constant: the date handwashing was made mandatory.
    # Stored here so every part of the code can reference MonthlyRecord.HANDWASHING_START
    # instead of hard-coding the string "1847-06-01" in multiple places.
    HANDWASHING_START = "1847-06-01"

    class Meta:
        ordering = ["date"]  # chronological order

    def __str__(self):
        return str(self.date)

    @property
    def proportion_deaths(self):
        """Deaths as a fraction of births for this month."""
        return round(self.deaths / self.births, 6) if self.births else 0

    @property
    def after_handwashing(self):
        """
        Returns True if this record falls on or after June 1847.
        Used in the monthly_list.html template to colour rows and show
        'Before' / 'After' badges.
        The import is inside the function to avoid a circular import at module
        load time (though in practice it would not cause issues here).
        """
        from datetime import date
        pivot = date(1847, 6, 1)
        return self.date >= pivot
# Create your models here.
