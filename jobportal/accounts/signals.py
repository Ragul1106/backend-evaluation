from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, EmployerProfile, ApplicantProfile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.role == User.Roles.EMPLOYER:
        EmployerProfile.objects.create(user=instance)
    else:
        ApplicantProfile.objects.create(user=instance)
