"""
URL configuration for EntraideEtudiante project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path
from UniShare import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.accueil, name="accueil"), 
    path("accueil/", views.accueil, name="accueil"), 
    
    #Authentification
    path("connexion/", views.connexion, name="connexion"), 
    path("creerCompte/", views.creerCompte,name="creerCompte"),
    path("compte-suspendu/", views.compteSuspendu, name="compteSuspendu"),
    path("deconnexion/", views.deconnexion, name="deconnexion"), 
    path("profil/", views.profil, name="profil"),
    path("profil/modifier/", views.modifierProfil, name="modifierProfil"),
    path("profil/supprimer/", views.supprimerProfil, name="supprimerProfil"),
    path("profil/annuler-suppression/", views.annulerDemandeSuppressionProfil, name="annulerDemandeSuppressionProfil"),
    
    
    # Annonces
    path("annonces/", views.listeAnnonces, name="listeAnnonces"),
    path("annonces/<int:id>/", views.annonceDetail, name="annonceDetail"),
    path("annonces/creer/", views.creerAnnonce, name="creerAnnonce"),
    path("annonces/mes-annonces/", views.mesAnnonces, name="mesAnnonces"),
    path("annonces/modifier/<int:id>/", views.modifierAnnonce, name="modifierAnnonce"),
    path("annonces/supprimer/<int:id>/", views.supprimerAnnonce, name="supprimerAnnonce"),
    
    # Services
    path("services/", views.listeServices, name="listeServices"),
    path("services/<int:id>/", views.serviceDetail, name="serviceDetail"),
    path("services/creer/", views.creerService, name="creerService"),
    path("services/mes-services/", views.mesServices, name="mesServices"),
    path("services/modifier/<int:id>/", views.modifierService, name="modifierService"),
    path("services/supprimer/<int:id>/", views.supprimerService, name="supprimerService"),
    path("services/changer-statut/<int:id>/", views.changerStatutService, name="changerStatutService"),

    # Reservation de service
    path("services/reserver/<int:id>/", views.reserverService, name="reserverService"),
    path("services/mes-reservations/", views.mesReservations, name="mesReservations"),
    path("services/annuler-reservation/<int:id>/", views.annulerReservation, name="annulerReservation"),
    path("services/detail-reservation/<int:id>/", views.detailReservation, name="detailReservation"),
    path("services/reservationsService/<int:id>/", views.reservationsService, name="reservationsService"),
    path("services/accepter-reservation/<int:id_reservation>/", views.accepterReservation, name="accepterReservation"),
    path("services/refuser-reservation/<int:id_reservation>/", views.refuserReservation, name="refuserReservation"),
    path("services/accepter-et-refuser-autres/<int:id_reservation>/", views.accepterEtRefuserAutres, name="accepterEtRefuserAutres"),

    #Notifications
    path("notifications/", views.mesNotifications, name="mesNotifications"),
    path("notifications/mark-as-read/<int:id>/", views.marquerNotificationCommeLue, name="marquerNotificationCommeLue"),
    path("notifications/mark-all-as-read/", views.marquerToutesNotificationsCommeLues, name="marquerToutesNotificationsCommeLues"),
    #path("notifications/services/<int:id>/", views.notificationsService, name="notificationsService"),

    # Admin
    path("Theadmin/utilisateurs/", views.listeUtilisateurs, name="listeUtilisateurs"),
    path("Theadmin/utilisateurs/<int:id>/", views.afficherProfilUtilisateur, name="afficherProfilUtilisateur"),
    path("Theadmin/supprimer-utilisateur/<int:id>/", views.supprimerUtilisateur, name="supprimerUtilisateur"),
    path("Theadmin/dashboard/", views.dashboardAdmin, name="dashboardAdmin"),
    path("Theadmin/annonces/", views.listeAnnoncesAdmin, name="listeAnnoncesAdmin"),
    path("Theadmin/notification-suppression/<int:id>/", views.notificationSuppression, name="notificationSuppression"),
    path("Theadmin/services/", views.listeServicesAdmin, name="listeServicesAdmin"),
    path("Theadmin/annonces-expirees/", views.gererAnnoncesExpirees, name="gererAnnoncesExpirees"),
    path("Theadmin/comptes-suppression/", views.gererComptesEnSuppression, name="gererComptesEnSuppression"),
    
]

urlpatterns += static(settings.MEDIA_URL,
document_root=settings.MEDIA_ROOT)

