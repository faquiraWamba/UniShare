from django import forms
from .models import Utilisateur, Etudiant,Annonce,Service,Notification

# Connexion utilisateur
class ConnexionForm(forms.Form):
    email = forms.EmailField(required=True)
    mot_de_passe = forms.CharField(
        required=True,
        widget=forms.PasswordInput
    )



# Création compte utilisateur
class UtilisateurForm(forms.ModelForm):
    mot_de_passe = forms.CharField(
        widget=forms.PasswordInput
    )

    class Meta:
        model = Utilisateur
        fields = [
            "nom",
            "prenom",
            "email",
            "mot_de_passe",
            "role",
            "photo"
        ]



# Création profil étudiant

class EtudiantForm(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = [
            "ecole",
            "niveau",
            "formation",
            "promo"
        ]



# Recherche utilisateur

class RechercheUtilisateurForm(forms.Form):
    email = forms.CharField(required=True)

# Création d'une annonce
class AnnonceForm(forms.ModelForm):
    class Meta:
        model = Annonce
        fields = ['titre', 'description', 'categorie', 'visibilite','date_expiration', 'photo']
        widgets = {
            "date_expiration": forms.DateInput(attrs={"type": "date", "class": "form-control"})
        }
    
# Création d'un service
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['titre', 'description', 'type_service', 'visibilite','date_expiration','date_rencontre','lieu_rencontre', 'photo']
        widgets = {
            "date_expiration": forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            "date_rencontre": forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            })
        }

# Creer une notification
class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['titre', 'message', 'type_notification']
