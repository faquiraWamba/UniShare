from django.contrib import admin
from .models import Utilisateur, Etudiant, Annonce, Service, Reservation, Notification
from django.utils import timezone

# Custom actions for admin
def supprimer_annonces_expirees(modeladmin, request, queryset):
    queryset.filter(date_expiration__lt=timezone.now()).delete()
supprimer_annonces_expirees.short_description = "Supprimer les annonces sélectionnées expirées"

def supprimer_services_expires(modeladmin, request, queryset):
    queryset.filter(date_expiration__lt=timezone.now()).delete()
supprimer_services_expires.short_description = "Supprimer les services sélectionnés expirés"

# Annonce Admin
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'auteur', 'categorie', 'visibilite', 'date_creation', 'date_expiration', 'est_expire')
    list_filter = ('categorie', 'visibilite', 'date_creation', 'date_expiration')
    search_fields = ('titre', 'description', 'auteur__nom', 'auteur__prenom')
    actions = [supprimer_annonces_expirees]
    
    def est_expire(self, obj):
        if obj.date_expiration:
            return obj.date_expiration < timezone.now()
        return False
    est_expire.boolean = True
    est_expire.short_description = "Expiré"

# Service Admin
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'auteur', 'type_service', 'visibilite', 'statut', 'date_creation', 'date_expiration', 'est_expire')
    list_filter = ('type_service', 'visibilite', 'statut', 'date_creation', 'date_expiration')
    search_fields = ('titre', 'description', 'auteur__nom', 'auteur__prenom')
    actions = [supprimer_services_expires]
    
    def est_expire(self, obj):
        if obj.date_expiration:
            return obj.date_expiration < timezone.now()
        return False
    est_expire.boolean = True
    est_expire.short_description = "Expiré"

# Register your models here.
admin.site.register(Utilisateur)
admin.site.register(Etudiant)
admin.site.register(Annonce, AnnonceAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Reservation)
admin.site.register(Notification)
