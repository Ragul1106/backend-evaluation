from django.contrib import admin
from .models import Job, Application

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "poster", "created_at")
    search_fields = ("title", "company", "location", "description")
    list_filter = ("location", "created_at")

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "status", "created_at")
    search_fields = ("job__title", "applicant__username")
    list_filter = ("status", "created_at")
