from django.db import models
from django.utils import timezone


# UTILISATEUR
class Utilisateur(models.Model):
    class Role(models.TextChoices):
        ETUDIANT = "ETU", "Etudiant"
        ANCIEN = "ANC", "Ancien"
        ADMIN = "ADM", "Administrateur"

    nom = models.fields.CharField(max_length=100)
    prenom = models.fields.CharField(max_length=100)
    email = models.fields.EmailField(unique=True)
    mot_de_passe = models.fields.CharField(max_length=128)  # hashé idéalement
    role = models.fields.CharField(max_length=3, choices=Role.choices, default=Role.ETUDIANT)
    photo = models.ImageField(upload_to="photos/utilisateurs/", blank=True, null=True)
    demande_suppression_en_cours = models.BooleanField(default=False)
    date_demande_suppression = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

#  ETUDIANT
class Etudiant(Utilisateur):
    class StatutCompte(models.TextChoices):
        ACTIF = "ACTIF", "Actif"
        SUSPENDU = "SUSP", "Suspendu"
        
    class Niveau(models.TextChoices):
        L1 = "L1", "Licence 1"
        L2 = "L2", "Licence 2"
        L3 = "L3", "Licence 3"
        M1 = "M1", "Master 1"
        M2 = "M2", "Master 2"
        DOC = "DOC", "Doctorat"

    ecole = models.fields.CharField(max_length=255)
    statut_compte = models.fields.CharField(max_length=5, choices=StatutCompte.choices, default=StatutCompte.ACTIF)
    niveau = models.CharField(max_length=3,choices=Niveau.choices,default=Niveau.L1)     
    formation = models.fields.CharField(max_length=255) 
    promo = models.fields.CharField(max_length=20)      

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.niveau} - {self.formation})"



# ANNONCE
class Annonce(models.Model):
    class Visibilite(models.TextChoices):
        PROMO = "PROMO", "Promo"
        ECOLE = "ECOLE", "Ecole"
        PUBLIC = "PUBLIC", "Public"

    class Categorie(models.TextChoices):
        JOB = "JOB", "Job/Stage/Alternance"
        BONPLAN = "BONPLAN", "Bon plan"
        EVENEMENT = "EVENT", "Evenement"
        AUTRE = "AUTRE", "Autre"

    id_annonce = models.AutoField(primary_key=True)
    titre = models.fields.CharField(max_length=120)
    description = models.fields.TextField()
    categorie = models.fields.CharField(max_length=10, choices=Categorie.choices, default=Categorie.AUTRE)
    visibilite = models.fields.CharField(max_length=6, choices=Visibilite.choices, default=Visibilite.PUBLIC)
    date_creation = models.fields.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField(null=True, blank=True)
    # Auteur (etudiant) de l'annone
    auteur = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name="annonces")
    photo = models.ImageField(upload_to="photos/annonces/", blank=True, null=True)

    def __str__(self):
        return f"{self.titre}"

    @property
    def is_expired(self):
        if not self.date_expiration:
            return False
        return self.date_expiration < timezone.now()

#SERVICE
class Service(Annonce):
    class StatutService(models.TextChoices):
        DISPONIBLE = "DISPO", "Disponible"
        RESERVE = "RES", "Reserve"
        
    class TypeService(models.TextChoices):
        TUTORAT = "TUTORAT", "Tutorat"
        COVOIT = "COVOIT", "Covoiturage"
        DON = "DON", "Don d'objets"
        AUTRE = "AUTRE", "Autre"

    id_service = models.AutoField(primary_key=True)
    type_service = models.CharField(max_length=10,choices=TypeService.choices,default=TypeService.AUTRE)
    statut = models.fields.CharField(max_length=5, choices=StatutService.choices, default=StatutService.DISPONIBLE)
    lieu_rencontre = models.fields.CharField(max_length=120, blank=True, null=True)
    date_rencontre = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Service: {self.titre}"



# RESERVATION
class Reservation(models.Model):
    class StatutReservation(models.TextChoices):
        EN_ATTENTE = "ATT", "En attente"
        ACCEPTEE = "ACC", "Acceptee"
        VALIDEE = "VAL", "Validee"
        REFUSEE = "REF", "Refusee"

    id_reservation = models.AutoField(primary_key=True)
    statut = models.fields.CharField(max_length=3, choices=StatutReservation.choices, default=StatutReservation.EN_ATTENTE)
    date_creation = models.fields.DateTimeField(auto_now_add=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="reservations")
    demandeur = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name="reservations")

    def __str__(self):
        return f"Reservation #{self.id_reservation} - {self.get_statut_display()}"

#NOTIFICATION
class Notification(models.Model):
    class TypeNotification(models.TextChoices):
        RESERVATION = "RESERVATION", "Notification de réservation"
        ANNONCE = "ANNONCE", "Notification d'annonce"
        RESERVATION_AUTEUR = "RESERVATION_AUTEUR", "Notification pour l'auteur du service"
        
    id_notif = models.AutoField(primary_key=True)
    titre = models.fields.CharField(max_length=120)
    message = models.fields.TextField()
    lu = models.fields.BooleanField(default=False)
    date = models.fields.DateTimeField(auto_now_add=True)
    type_notification = models.CharField(max_length=20, choices=TypeNotification.choices, default=TypeNotification.ANNONCE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)

    def __str__(self):
        return f"{self.titre}"

