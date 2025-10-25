from django.db.models import Q

def filter_jobs(queryset, q=None, location=None):
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) | Q(company__icontains=q) | Q(description__icontains=q)
        )
    if location:
        queryset = queryset.filter(location__icontains=location)
    return queryset
