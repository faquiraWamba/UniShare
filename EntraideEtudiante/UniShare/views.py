from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, HttpResponseRedirect
from .utils import verifier_connexion, verifier_etudiant, verifier_proprietaire, verifier_admin
from django.utils import timezone
from .forms import ConnexionForm, UtilisateurForm, RechercheUtilisateurForm,EtudiantForm,AnnonceForm ,ServiceForm,NotificationForm
from .models import Utilisateur,Etudiant,Annonce,Service, Reservation, Notification

def accueil(request):
    return render(request,'UniShare/accueil.html')

"""
    Actions d'authentification
"""

def creerCompte(request):
    if request.method == 'POST':
        user_form = UtilisateurForm(request.POST, request.FILES)
        etu_form = EtudiantForm(request.POST)

        if user_form.is_valid():
            utilisateur = user_form.save(commit=False)
            
            # Si l'utilisateur est étudiant, on ajoute les infos étudiant
            if utilisateur.role == "ETU":
                if etu_form.is_valid():
                    Etudiant.objects.create(
                        id=utilisateur.id,
                        nom=utilisateur.nom,
                        prenom=utilisateur.prenom,
                        email=utilisateur.email,
                        mot_de_passe=utilisateur.mot_de_passe,
                        role=utilisateur.role,
                        photo=utilisateur.photo,
                        ecole=etu_form.cleaned_data['ecole'],
                        niveau=etu_form.cleaned_data['niveau'],
                        formation=etu_form.cleaned_data['formation'],
                        promo=etu_form.cleaned_data['promo'],
                    )

            return HttpResponseRedirect(reverse("connexion"))

    else:
        user_form = UtilisateurForm()
        etu_form = EtudiantForm()

    return render(request, 'UniShare/Authentification/creation_compte.html', {
        'user_form': user_form,
        'etu_form': etu_form
    })

def connexion(request):
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            mot_de_passe = form.cleaned_data['mot_de_passe']

            utilisateurs = Utilisateur.objects.filter(email=email, mot_de_passe=mot_de_passe)

            if len(utilisateurs) != 0:
                user = utilisateurs[0]
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_role'] = getattr(user, 'role', None)

                return HttpResponseRedirect(reverse("accueil")) 
            else:
                return render(request, 'UniShare/Authentification/connexion.html', {
                    'form': form,
                    'erreur': "email ou mot de passe incorrect"
                })
    else:
        form = ConnexionForm()

    return render(request, 'UniShare/Authentification/connexion.html', {'form': form})

def deconnexion(request):
    if 'user_id' in request.session:
        del request.session['user_id']
        del request.session['user_email']
        if 'user_role' in request.session:
            del request.session['user_role']
    return HttpResponseRedirect(reverse("accueil"))


"""
    Actions Annonces
"""

""" Creer une Annonce"""
def creerAnnonce(request):

    redirection = verifier_connexion(request)
    if redirection:
        return redirection

    if request.method == 'POST':
        form = AnnonceForm(request.POST, request.FILES)

        if form.is_valid():
            annonce = form.save(commit=False)

            # auteur = étudiant connecté
            etudiant = Etudiant.objects.get(id=request.session['user_id'])
            annonce.auteur = etudiant

            annonce.save()

            return HttpResponseRedirect(reverse("mesAnnonces"))

    else:
        form = AnnonceForm()

    return render(request, "UniShare/Annonce/creerAnnonce.html", {
        "form": form
    })


""" Liste des annonces sauf annonces de la personne connectée """
def listeAnnonces(request):

    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection
    
    # Vérification du role utilisateur étudiant
    redirection = verifier_etudiant(request)
    if redirection:
        return redirection

     # récupérer l'étudiant connecté
    user_id = request.session['user_id']
    etudiant = Etudiant.objects.get(id=user_id)

    # annonces visibles par l'étudiant : uniquement celles des autres
    annonces = Annonce.objects.exclude(auteur=etudiant)

    return render(request, "UniShare/Annonce/listeAnnonces.html", {
        "lesannonces": annonces,
        "etudiant": etudiant
    })

""" détail d'une annonce """
def annonceDetail(request, id):
    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection
    
    
    annonce = Annonce.objects.get(id_annonce=id)
    return render(request, "UniShare/Annonce/annonceDetail.html", {"annonce": annonce})


""" Liste des annonces de la personne connectée """
def mesAnnonces(request):
    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection

    user_id = request.session['user_id']

    # si étudiant => auteur = Etudiant(id=user_id)
    # si ancien/admin => tu peux aussi filtrer sur Utilisateur si ton FK auteur est Etudiant seulement
    # Ici on suppose auteur = Etudiant (donc seuls étudiants publient des annonces).
    auteur = Etudiant.objects.get(id=user_id)

    annonces = Annonce.objects.filter(auteur=auteur)

    return render(request, "UniShare/Annonce/mesAnnonces.html", {
        "lesannonces": annonces
    })

def modifierAnnonce(request, id):
    
    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection
    
    annonce = Annonce.objects.get(id_annonce=id)
    
    etudiant = Etudiant.objects.get(id=request.session['user_id'])

    # sécurité : si ce n’est pas son annonce => refus
    if annonce.auteur != etudiant:
        return HttpResponseRedirect(reverse("mesAnnonces"))

    if request.method == "POST":
        form = AnnonceForm(request.POST, request.FILES, instance=annonce)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("mesAnnonces"))
    else:
        form = AnnonceForm(instance=annonce)

    return render(request, "UniShare/Annonce/modifierAnnonce.html", {"form": form})

def supprimerAnnonce(request, id):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    annonce = Annonce.objects.get(id_annonce=id)
    etudiant = Etudiant.objects.get(id=request.session['user_id'])

    if annonce.auteur != etudiant:
        return HttpResponseRedirect(reverse("mesAnnonces"))

    if request.method == "POST":
        annonce.delete()
        return HttpResponseRedirect(reverse("mesAnnonces"))

    return render(request, "UniShare/Annonce/supprimerAnnonce.html", {"annonce": annonce})

"""
    Actions Services
"""

""" Creer une Service"""
def creerService(request):

    redirection = verifier_connexion(request)
    if redirection:
        return redirection

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)

        if form.is_valid():
            service = form.save(commit=False)

            # auteur = étudiant connecté
            etudiant = Etudiant.objects.get(id=request.session['user_id'])
            service.auteur = etudiant
            

            service.save()

            return HttpResponseRedirect(reverse("mesServices"))

    else:
        form = ServiceForm()

    return render(request, "UniShare/Service/creerService.html", {
        "form": form
    })


""" Liste des services sauf services de la personne connectée """
def listeServices(request):

    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection
    
    # Vérification du role utilisateur étudiant
    redirection = verifier_etudiant(request)
    if redirection:
        return redirection

     # récupérer l'étudiant connecté
    user_id = request.session['user_id']
    etudiant = Etudiant.objects.get(id=user_id)

    # services visibles par l'étudiant : uniquement celles des autres
    services = Service.objects.exclude(auteur=etudiant)

    return render(request, "UniShare/Service/listeServices.html", {
        "lesservices": services,
        "etudiant": etudiant
    })

""" détail d'une service """
def serviceDetail(request, id):
    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection
    
    
    service = Service.objects.get(id_service=id)
    return render(request, "UniShare/Service/serviceDetail.html", {"service": service})


""" Liste des services de la personne connectée """
def mesServices(request):
    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection

    user_id = request.session['user_id']

    # si étudiant => auteur = Etudiant(id=user_id)
    # si ancien/admin => tu peux aussi filtrer sur Utilisateur si ton FK auteur est Etudiant seulement
    # Ici on suppose auteur = Etudiant (donc seuls étudiants publient des services).
    auteur = Etudiant.objects.get(id=user_id)

    services = Service.objects.filter(auteur=auteur)

    return render(request, "UniShare/Service/mesServices.html", {
        "lesservices": services
    })

def modifierService(request, id):
    
    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection
    
    service = Service.objects.get(id_service=id)
    
    etudiant = Etudiant.objects.get(id=request.session['user_id'])

    # sécurité : si ce n’est pas son service => refus
    if service.auteur != etudiant:
        return HttpResponseRedirect(reverse("mesServices"))

    if request.method == "POST":
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("mesServices"))
    else:
        form = ServiceForm(instance=service)

    return render(request, "UniShare/Service/modifierService.html", {"form": form})

def supprimerService(request, id):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    service = Service.objects.get(id_service=id)
    etudiant = Etudiant.objects.get(id=request.session['user_id'])

    if service.auteur != etudiant:
        return HttpResponseRedirect(reverse("mesServices"))

    if request.method == "POST":
        service.delete()
        return HttpResponseRedirect(reverse("mesServices"))

    return render(request, "UniShare/Service/supprimerService.html", {"service": service})

"""
    Actions Reservation
"""

""" Creer une   reservation"""
def reserverService(request, id):
    redirection = verifier_etudiant(request)
    if redirection:
        return redirection
    service=Service.objects.get(id_service=id)
    verifier_proprietaire(request, service)

    
    if request.method == 'POST':
        verifier_reservation_existante = Reservation.objects.filter(service=service, demandeur__id=request.session['user_id'])
        if verifier_reservation_existante.exists():
            return render(request, "UniShare/Reservation/creerReservation.html", {
                "service": service,
                "erreur": "Vous avez déjà une réservation pour ce service."
            })
        else:
            reservation = Reservation.objects.create(
                service=service,
                demandeur=Etudiant.objects.get(id=request.session['user_id']),
                date_creation=timezone.now()
            )
            reservation.save()

        return HttpResponseRedirect(reverse("reservationDetail", args=[reservation.id_reservation]))

    else:
        return render(request, "UniShare/Reservation/creerReservation.html", {"service": service})

    

""" Afficher les détails d'une   reservation"""
def detailReservation(request, id):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))
    
    reservation = Reservation.objects.get(id_reservation=id)
    etudiant = Etudiant.objects.get(id=request.session['user_id'])

    if reservation.demandeur != etudiant:
        return HttpResponseRedirect(reverse("mesReservations"))

    return render(request, "UniShare/Reservation/reservationDetail.html", {"reservation": reservation})

""" Annuler une   reservation"""
def annulerReservation(request, id_reservation):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))
 
    reservation = Reservation.objects.get(id_reservation=id_reservation)
    etudiant = Etudiant.objects.get(id=request.session['user_id'])
    if reservation.demandeur != etudiant:
        return HttpResponseRedirect(reverse("mesReservations"))
    if request.method == "POST":
        reservation.delete()
        notification = Notification.objects.create(
            reservation=reservation,
            message=f"{etudiant.prenom} {etudiant.nom} a annulé sa réservation pour le service '{reservation.service.titre}'.",
            type_notification=Notification.TypeNotification.ANNONCE
        )
        return HttpResponseRedirect(reverse("mesReservations"))
    return render(request, "UniShare/Reservation/annulerReservation.html", {"reservation": reservation})

""" Liste des   reservations de la personne connectée """
def mesReservations(request):           
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    user_id = request.session['user_id']
    etudiant = Etudiant.objects.get(id=user_id)

    reservations = Reservation.objects.filter(demandeur=etudiant)

    return render(request, "UniShare/Reservation/mesReservations.html", {
        "lesreservations": reservations
    })

""" Listes des   reservations d'un service (pour le propriétaire du service) """
def reservationsService(request, id):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    service = Service.objects.get(id_service=id_service)
    etudiant = Etudiant.objects.get(id=request.session['user_id'])

    if service.auteur != etudiant:
        return HttpResponseRedirect(reverse("listeServices"))

    

    reservations = Reservation.objects.filter(service=service)

    return render(request, "UniShare/Reservation/reservationsService.html", {
        "lesreservations": reservations,
        "service": service
    })

""" Accepter une   reservation (pour le propriétaire du service)"""
def accepterReservation(request, id_reservation):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    reservation = Reservation.objects.get(id_reservation=id_reservation)
    service = reservation.service
    etudiant = Etudiant.objects.get(id=request.session['user_id'])

    if service.auteur != etudiant:
        return HttpResponseRedirect(reverse("listeServices"))

    reservation.statut = "ACCEPTEE"
    reservation.save()

    notification = Notification.objects.create(
        reservation=reservation,
        message=f"Votre réservation pour le service '{service.titre}' a été acceptée.",
        type_notification=Notification.TypeNotification.RESERVATION
    )

    return HttpResponseRedirect(reverse("reservationsService", args=[service.id_service]))

""" Refuser une   reservation (pour le propriétaire du service)"""
def refuserReservation(request, id_reservation):    
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    reservation = Reservation.objects.get(id_reservation=id_reservation)
    service = reservation.service
    etudiant = Etudiant.objects.get(id=request.session['user_id'])

    if service.auteur != etudiant:
        return HttpResponseRedirect(reverse("listeServices"))

    reservation.statut = "REFUSEE"
    reservation.save()

    notification = Notification.objects.create(
        reservation=reservation,    
        message=f"Votre réservation pour le service '{service.titre}' a été refusée.",
        type_notification=Notification.TypeNotification.RESERVATION
    )

    return HttpResponseRedirect(reverse("reservationsService", args=[service.id_service]))

"""Actions Admin"""
""" Liste des utilisateurs (admin)"""
def listeUtilisateurs(request):
    if 'user_id' not in request.session or request.session.get('user_role') != "ADMIN":
        return HttpResponseRedirect(reverse("connexion"))

    utilisateurs = Utilisateur.objects.all()

    return render(request, "UniShare/Admin/listeUtilisateurs.html", {
        "lesutilisateurs": utilisateurs
    })

""" Supprimer un utilisateur (admin)"""
def supprimerUtilisateur(request, id):
    if 'user_id' not in request.session or request.session.get('user_role') != "ADMIN":
        return HttpResponseRedirect(reverse("connexion"))

    utilisateur = Utilisateur.objects.get(id=id)

    if request.method == "POST":
        utilisateur.delete()
        return HttpResponseRedirect(reverse("listeUtilisateurs"))

    return render(request, "UniShare/Admin/supprimerUtilisateur.html", {"utilisateur": utilisateur})

""" Dashboard admin"""
def dashboardAdmin(request):
    if 'user_id' not in request.session or request.session.get('user_role') != "ADMIN":
        return HttpResponseRedirect(reverse("connexion"))

    nb_utilisateurs = Utilisateur.objects.count()
    nb_etudiants = Etudiant.objects.count()
    nb_annonces = Annonce.objects.count()
    nb_services = Service.objects.count()

    return render(request, "UniShare/Admin/dashboardAdmin.html", {
        "nb_utilisateurs": nb_utilisateurs,
        "nb_etudiants": nb_etudiants,
        "nb_annonces": nb_annonces,
        "nb_services": nb_services
    })

""" Actions Notifications"""
""" Lister les notifications de l'utilisateur connecté"""
def mesNotifications(request):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    user_id = request.session['user_id']
    etudiant = Etudiant.objects.get(id=user_id)

    notifications = Notification.objects.filter(reservation__demandeur=etudiant).order_by('-date')

    return render(request, "UniShare/Notification/mesNotifications.html", {
        "lesnotifications": notifications
    })


""" Créer une notification (lors de la suppression d'une réservation par admin)"""
def creerNotification(request,titre,message, type_notification):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    if request.method == 'POST':

        notification = Notification.objects.create(
            titre=titre,
            message=message,
            type_notification=type_notification
        )
        notification.save()
        return HttpResponseRedirect(reverse("listerNotifications"))
    else:
        form = NotificationForm()
    return render(request, "UniShare/Admin/creerNotification.html", {
        "form": form

    })
