from django.contrib import admin
from .models import Utilisateur, Etudiant, Annonce, Service, Reservation, Notification

# Register your models here.
admin.site.register(Utilisateur)
admin.site.register(Etudiant)
admin.site.register(Annonce)
admin.site.register(Service)
admin.site.register(Reservation)
admin.site.register(Notification)
