from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, HttpResponseRedirect
from .utils import verifier_connexion, verifier_etudiant, verifier_proprietaire, verifier_admin
from django.utils import timezone
from .forms import ConnexionForm, UtilisateurForm, RechercheUtilisateurForm,EtudiantForm,AnnonceForm ,ServiceForm,NotificationForm
from .models import Utilisateur,Etudiant,Annonce,Service, Reservation, Notification

def accueil(request):
    # Si l'utilisateur est connecté, le rediriger selon son rôle
    if 'user_id' in request.session:
        user_role = request.session.get('user_role')
        
        if user_role == "ADM":
            return HttpResponseRedirect(reverse("dashboardAdmin"))
        elif user_role == "ANC":
            return HttpResponseRedirect(reverse("mesAnnonces"))
        elif user_role == "ETU":
            return HttpResponseRedirect(reverse("listeAnnonces"))
    
    return render(request, 'UniShare/accueil.html')

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
                if user.role == "ETU" or user.role == "ANC":
                    etudiant = Etudiant.objects.get(id=user.id)
                    if etudiant.statut_compte == "SUSP":
                        return HttpResponseRedirect(reverse("compteSuspendu"))
                
                
                request.session['user_id'] = user.id
                request.session['user_role'] = getattr(user, 'role', None)
                request.session['user_photo'] = user.photo.url if user.photo else None
                # stocker le prénom pour l'affichage rapide
                request.session['user_prenom'] = getattr(user, 'prenom', '')
                request.session['user_email'] = user.email

                return HttpResponseRedirect(reverse("accueil")) 
            else:
                return render(request, 'UniShare/Authentification/connexion.html', {
                    'form': form,
                    'erreur': "email ou mot de passe incorrect"
                })
    else:
        form = ConnexionForm()

    return render(request, 'UniShare/Authentification/connexion.html', {'form': form})

def compteSuspendu(request):
    return render(request, 'UniShare/Authentification/compteSuspendu.html', {})

def deconnexion(request):
    if 'user_id' in request.session:
        del request.session['user_id']
        del request.session['user_email']
        del request.session['user_photo']
        if 'user_role' in request.session:
            del request.session['user_role']
    return HttpResponseRedirect(reverse("accueil"))

def profil(request):
    redirection = verifier_connexion(request)
    if redirection:
        return redirection

    user_id = request.session['user_id']
    user_role = request.session.get('user_role')
    utilisateur = Utilisateur.objects.get(id=user_id)
    
    # Adapter selon le rôle
    if user_role in ['ETU', 'ANC']:
        # Pour étudiants et anciens, utiliser Etudiant
        try:
            etudiant = Etudiant.objects.get(id=user_id)
            return render(request, "UniShare/Authentification/profil.html", {
                "utilisateur": etudiant,
                "user_role": user_role
            })
        except Etudiant.DoesNotExist:
            pass
    
    # Pour admins et autres
    return render(request, "UniShare/Authentification/profil.html", {
        "utilisateur": utilisateur,
        "user_role": user_role
    })

def modifierProfil(request):
    redirection = verifier_connexion(request)
    if redirection:
        return redirection

    user_id = request.session['user_id']
    user_role = request.session.get('user_role')
    utilisateur = Utilisateur.objects.get(id=user_id)

    if request.method == 'POST':
        user_form = UtilisateurForm(request.POST, request.FILES, instance=utilisateur)
        
        if user_role in ['ETU', 'ANC']:
            # Pour étudiants et anciens
            try:
                etudiant = Etudiant.objects.get(id=user_id)
                etu_form = EtudiantForm(request.POST, instance=etudiant)
                if user_form.is_valid() and etu_form.is_valid():
                    user_form.save()
                    etu_form.save()
                    return HttpResponseRedirect(reverse("profil"))
            except Etudiant.DoesNotExist:
                pass
        else:
            # Pour admins
            if user_form.is_valid():
                user_form.save()
                return HttpResponseRedirect(reverse("profil"))
    else:
        user_form = UtilisateurForm(instance=utilisateur)
        if user_role in ['ETU', 'ANC']:
            try:
                etudiant = Etudiant.objects.get(id=user_id)
                etu_form = EtudiantForm(instance=etudiant)
            except Etudiant.DoesNotExist:
                etu_form = EtudiantForm()
        else:
            etu_form = None

    return render(request, "UniShare/Authentification/modifierProfil.html", {
        "user_form": user_form,
        "etu_form": etu_form if user_role in ['ETU', 'ANC'] else None,
        "user_role": user_role
    })

def supprimerProfil(request):
    redirection = verifier_connexion(request)
    if redirection:
        return redirection

    user_id = request.session['user_id']
    utilisateur = Utilisateur.objects.get(id=user_id)

    if request.method == "POST":
        # Enregistrer la demande de suppression avec délai de 30 jours
        utilisateur.demande_suppression_en_cours = True
        utilisateur.date_demande_suppression = timezone.now()
        utilisateur.save()
        
        return HttpResponseRedirect(reverse("profil"))

    # si GET, rediriger vers le profil (les confirmations se gèrent inline)
    return HttpResponseRedirect(reverse("profil"))

def annulerDemandeSuppressionProfil(request):
    """Annuler une demande de suppression de compte"""
    redirection = verifier_connexion(request)
    if redirection:
        return redirection

    user_id = request.session['user_id']
    utilisateur = Utilisateur.objects.get(id=user_id)

    if request.method == "POST":
        # Annuler la demande de suppression
        utilisateur.demande_suppression_en_cours = False
        utilisateur.date_demande_suppression = None
        utilisateur.save()
        
        return HttpResponseRedirect(reverse("profil"))

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
    # Exclure les annonces qui sont en fait des Services (héritage multi-table)
    annonces = Annonce.objects.filter(service__isnull=True).exclude(auteur=etudiant)
    
    # Exclure les annonces des comptes suspendus
    annonces = annonces.filter(auteur__statut_compte=Etudiant.StatutCompte.ACTIF)

    # Appliquer les filtres de visibilité selon le profil de l'étudiant
    from django.db.models import Q
    visibilite_filter = Q(visibilite='PUBLIC') | \
                       Q(visibilite='ECOLE', auteur__ecole=etudiant.ecole) | \
                       Q(visibilite='PROMO', auteur__ecole=etudiant.ecole, auteur__promo=etudiant.promo)
    annonces = annonces.filter(visibilite_filter)

    # Récupérer les paramètres de filtrage et tri
    categorie = request.GET.get('categorie', '')
    visibilite = request.GET.get('visibilite', '')
    afficher_expirees = request.GET.get('afficher_expirees', 'false').lower() == 'true'
    sort_by = request.GET.get('sort', '-date_creation')  # Par défaut: plus récent en premier

    # Filtrer par catégorie
    if categorie and categorie != 'TOUS':
        annonces = annonces.filter(categorie=categorie)

    # Filtrer par visibilité
    if visibilite and visibilite != 'TOUS':
        annonces = annonces.filter(visibilite=visibilite)
    from django.db.models import Q
    # Filtrer par date d'expiration
    if not afficher_expirees:
        # Afficher seulement les annonces non expirées (sans date expiration ou date future)
        annonces = annonces.filter(Q(date_expiration__isnull=True) | Q(date_expiration__gte=timezone.now()))

    # Tri
    if sort_by == '-date_creation':
        annonces = annonces.order_by('-date_creation')
    elif sort_by == 'date_creation':
        annonces = annonces.order_by('date_creation')
    elif sort_by == '-date_expiration':
        annonces = annonces.order_by('-date_expiration')
    elif sort_by == 'date_expiration':
        annonces = annonces.order_by('date_expiration')

    # Préparer les choix pour les selects
    categories_choices = Annonce.Categorie.choices
    visibilites_choices = Annonce.Visibilite.choices

    return render(request, "UniShare/Annonce/listeAnnonces.html", {
        "lesannonces": annonces,
        "etudiant": etudiant,
        "categories_choices": categories_choices,
        "visibilites_choices": visibilites_choices,
        "selected_categorie": categorie,
        "selected_visibilite": visibilite,
        "afficher_expirees": afficher_expirees,
        "sort_by": sort_by,
    })

""" détail d'une annonce """
def annonceDetail(request, id):
    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection
    
    annonce = Annonce.objects.get(id_annonce=id)
    
    # Vérifier le rôle de l'utilisateur
    user_role = request.session.get('user_role')
    is_admin = user_role == "ADM"
    
    return render(request, "UniShare/Annonce/annonceDetail.html", {
        "annonce": annonce,
        "is_admin": is_admin
    })


""" Liste des annonces de la personne connectée """
def mesAnnonces(request):
    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection

    user_id = request.session['user_id']

    # seuls étudiants publient des annonces).
    auteur = Etudiant.objects.get(id=user_id)

    # Exclure les services (qui héritent de Annonce) et ne pas afficher les annonces expirées
    from django.db.models import Q
    annonces = Annonce.objects.filter(auteur=auteur, service__isnull=True)
    annonces = annonces.filter(Q(date_expiration__isnull=True) | Q(date_expiration__gte=timezone.now()))
    # Récupérer aussi les services de l'utilisateur pour afficher le compteur
    services = Service.objects.filter(auteur=auteur)

    return render(request, "UniShare/Annonce/mesAnnonces.html", {
        "lesannonces": annonces,
        "lesservices": services
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
    user_role = request.session.get('user_role')
    
    # Si c'est un admin, rediriger vers la page de notification
    if user_role == "ADM":
        return HttpResponseRedirect(reverse("notificationSuppression", args=[id]))
    
    # Sinon, vérifier que c'est l'auteur
    etudiant = Etudiant.objects.get(id=request.session['user_id'])
    if annonce.auteur != etudiant:
        return HttpResponseRedirect(reverse("mesAnnonces"))
    
    if request.method == "POST":
        annonce.delete()
        return HttpResponseRedirect(reverse("mesAnnonces"))

    # si GET, rediriger vers la liste (les confirmations se gèrent inline)
    return HttpResponseRedirect(reverse("mesAnnonces"))

""" Notification suppression annonce (admin) """
def notificationSuppression(request, id):
    """Gère la suppression d'annonces et de services avec notification"""
    if 'user_id' not in request.session or request.session.get('user_role') != "ADM":
        return HttpResponseRedirect(reverse("connexion"))
    
    # Déterminer le type d'objet (Annonce ou Service)
    objet = None
    objet_type = None
    liste_admin_url = None
    type_notification = None
    
    try:
        objet = Service.objects.get(id_service=id)
        objet_type = 'service'
        liste_admin_url = 'listeServicesAdmin'
        type_notification = 'SERVICE'
    except Service.DoesNotExist:
        try:
            objet = Annonce.objects.get(id_annonce=id)
            # Vérifier que ce n'est pas un Service (qui hérite de Annonce)
            try:
                Service.objects.get(id_annonce=id)
            except Service.DoesNotExist:
                objet_type = 'annonce'
                liste_admin_url = 'listeAnnoncesAdmin'
                type_notification = 'ANNONCE'
        except Annonce.DoesNotExist:
            return HttpResponseRedirect(reverse('listeAnnoncesAdmin'))
    
    if objet is None:
        return HttpResponseRedirect(reverse('listeAnnoncesAdmin'))
    
    if request.method == "POST":
        titre = request.POST.get('titre', f"{objet_type.capitalize()} supprimée")
        message = request.POST.get('message', f"Votre {objet_type} a été supprimée.")
        
        # Créer une notification
        notification = Notification.objects.create(
            titre=titre,
            message=message,
            type_notification=type_notification
        )
        
        # Si c'est un Service, supprimer les réservations et notifier les demandeurs
        if objet_type == 'service':
            reservations = Reservation.objects.filter(service=objet)
            for reservation in reservations:
                # Créer une notification pour chaque demandeur
                notif = Notification.objects.create(
                    titre=titre,
                    message=message,
                    type_notification=type_notification
                )
                reservation.delete()
        
        # Supprimer l'objet
        objet.delete()
        
        return HttpResponseRedirect(reverse(liste_admin_url))
    
    return render(request, "UniShare/Administrateur/notificationSuppression.html", {
        "objet": objet,
        "objet_type": objet_type,
        "is_service": objet_type == 'service'
    })

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

    # Exclure les services des comptes suspendus
    services = services.filter(auteur__statut_compte=Etudiant.StatutCompte.ACTIF)

    # Appliquer les filtres de visibilité selon le profil de l'étudiant
    from django.db.models import Q
    visibilite_filter = Q(visibilite='PUBLIC') | \
                       Q(visibilite='ECOLE', auteur__ecole=etudiant.ecole) | \
                       Q(visibilite='PROMO', auteur__ecole=etudiant.ecole, auteur__promo=etudiant.promo)
    services = services.filter(visibilite_filter)

    # Ne pas afficher les services réservés
    services = services.filter(statut='DISPO')

    # Filtrer par date d'expiration - ne pas afficher les services expirés par défaut
    services = services.filter(Q(date_expiration__isnull=True) | Q(date_expiration__gte=timezone.now()))

    # Récupérer les paramètres de filtrage et tri
    type_service = request.GET.get('type_service', '')
    sort_by = request.GET.get('sort', '-date_creation')
    visibilite = request.GET.get('visibilite', '')
    # filtre par lieu sélectionné (valeur texte du lieu de rencontre)
    lieu = request.GET.get('lieu', '')

    # Filtrer par visibilité si demandé
    if visibilite and visibilite != 'TOUS':
        services = services.filter(visibilite=visibilite)

    # Filtrer par type de service
    if type_service and type_service != 'TOUS':
        services = services.filter(type_service=type_service)

    # Filtrer par lieu de rencontre choisi
    if lieu:
        services = services.filter(lieu_rencontre=lieu)

    # Tri
    if sort_by == '-date_creation':
        services = services.order_by('-date_creation')
    elif sort_by == 'date_creation':
        services = services.order_by('date_creation')
    elif sort_by == '-date_rencontre':
        services = services.order_by('-date_rencontre')
    elif sort_by == 'date_rencontre':
        services = services.order_by('date_rencontre')

    # Préparer les choix pour les selects
    types_choices = Service.TypeService.choices
    visibilites_choices = Service._meta.get_field('visibilite').choices
    # récupérer la liste distincte des lieux de rencontre non vides
    lieux_choices = list(Service.objects.exclude(lieu_rencontre__isnull=True).exclude(lieu_rencontre='').values_list('lieu_rencontre', flat=True).distinct())

    # récupérer les ids des services déjà réservés par l'utilisateur courant
    reserved_ids = list(Reservation.objects.filter(demandeur=etudiant).values_list('service__id_service', flat=True))

    return render(request, "UniShare/Service/listeServices.html", {
        "lesservices": services,
        "etudiant": etudiant,
        "reserved_ids": reserved_ids,
        "types_choices": types_choices,
        "selected_type_service": type_service,
        "selected_visibilite": visibilite,
        "selected_lieu": lieu,
        "lieux_choices": lieux_choices,
        "visibilites_choices": visibilites_choices,
        "sort_by": sort_by,
    })

""" détail d'une service """
def serviceDetail(request, id):
    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection
    
    service = Service.objects.get(id_service=id)
    
    # Vérifier le rôle de l'utilisateur
    user_role = request.session.get('user_role')
    is_admin = user_role == "ADM"
    
    # Vérifier si le service est réservé et que l'utilisateur n'en est pas l'auteur (pas pour l'admin)
    user_id = request.session.get('user_id')
    if service.statut == 'RES' and user_id != service.auteur.id and not is_admin:
        return HttpResponseRedirect(reverse("listeServices"))

    # vérifier si l'utilisateur connecté a déjà une réservation pour ce service
    already_reserved = False
    if user_id and not is_admin:
        already_reserved = Reservation.objects.filter(service=service, demandeur__id=user_id).exists()

    return render(request, "UniShare/Service/serviceDetail.html", {
        "service": service,
        "already_reserved": already_reserved,
        "is_admin": is_admin
    })


""" Liste des services de la personne connectée """
def mesServices(request):
    # vérification de connexion
    redirection = verifier_connexion(request)
    if redirection:
        return redirection

    user_id = request.session['user_id']

    # si étudiant => auteur = Etudiant(id=user_id)
    # seuls étudiants publient des services).
    auteur = Etudiant.objects.get(id=user_id)

    services = Service.objects.filter(auteur=auteur)
    # Récupérer aussi les annonces (hors services) de l'utilisateur pour afficher le compteur
    annonces = Annonce.objects.filter(auteur=auteur, service__isnull=True)

    return render(request, "UniShare/Service/mesServices.html", {
        "lesservices": services,
        "lesannonces": annonces
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
    user_role = request.session.get('user_role')
    
    # Si c'est un admin, rediriger vers la page de notification
    if user_role == "ADM":
        return HttpResponseRedirect(reverse("notificationSuppressionService", args=[id]))
    
    # Sinon, vérifier que c'est l'auteur
    etudiant = Etudiant.objects.get(id=request.session['user_id'])
    if service.auteur != etudiant:
        return HttpResponseRedirect(reverse("mesServices"))
    
    if request.method == "POST":
        service.delete()
        return HttpResponseRedirect(reverse("mesServices"))

    # si GET, rediriger vers la liste (les confirmations se gèrent inline)
    return HttpResponseRedirect(reverse("mesServices"))


def changerStatutService(request, id):
    """Permet à l'auteur du service de changer son statut"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))
    
    service = Service.objects.get(id_service=id)
    etudiant = Etudiant.objects.get(id=request.session['user_id'])
    
    if service.auteur != etudiant:
        return HttpResponseRedirect(reverse("mesServices"))
    
    if request.method == "POST":
        nouveau_statut = request.POST.get('statut')
        if nouveau_statut in dict(Service.StatutService.choices):
            service.statut = nouveau_statut
            service.save()
        return HttpResponseRedirect(reverse("mesServices"))
    
    return render(request, "UniShare/Service/changerStatutService.html", {
        "service": service,
        "statuts": Service.StatutService.choices
    })

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

        return HttpResponseRedirect(reverse("detailReservation", args=[reservation.id_reservation]))

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

    service = Service.objects.get(id_service=id)
    etudiant = Etudiant.objects.get(id=request.session['user_id'])

    if service.auteur != etudiant:
        return HttpResponseRedirect(reverse("listeServices"))

    reservations = Reservation.objects.filter(service=service)
    
    # Compter les réservations en attente
    reservations_en_attente = reservations.filter(statut="ATT").count()

    return render(request, "UniShare/Reservation/reservationsService.html", {
        "lesreservations": reservations,
        "service": service,
        "reservations_en_attente": reservations_en_attente
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

    reservation.statut = "ACC"
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

    reservation.statut = "REF"
    reservation.save()

    notification = Notification.objects.create(
        reservation=reservation,    
        message=f"Votre réservation pour le service '{service.titre}' a été refusée.",
        type_notification=Notification.TypeNotification.RESERVATION
    )

    return HttpResponseRedirect(reverse("reservationsService", args=[service.id_service]))

""" Accepter une réservation et refuser toutes les autres (pour le propriétaire du service)"""
def accepterEtRefuserAutres(request, id_reservation):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    reservation = Reservation.objects.get(id_reservation=id_reservation)
    service = reservation.service
    etudiant = Etudiant.objects.get(id=request.session['user_id'])

    if service.auteur != etudiant:
        return HttpResponseRedirect(reverse("listeServices"))

    # Accepter la réservation sélectionnée
    reservation.statut = "ACC"
    reservation.save()

    notification = Notification.objects.create(
        reservation=reservation,
        message=f"Votre réservation pour le service '{service.titre}' a été acceptée.",
        type_notification=Notification.TypeNotification.RESERVATION
    )

    # Refuser toutes les autres réservations du même service
    autres_reservations = Reservation.objects.filter(service=service).exclude(id_reservation=id_reservation)
    for autre_res in autres_reservations:
        autre_res.statut = "REF"
        autre_res.save()
        
        Notification.objects.create(
            reservation=autre_res,
            message=f"Votre réservation pour le service '{service.titre}' a été refusée.",
            type_notification=Notification.TypeNotification.RESERVATION
        )

    return HttpResponseRedirect(reverse("reservationsService", args=[service.id_service]))

"""Actions Admin pour Annonces et Services"""

def listeAnnoncesAdmin(request):
    """Admin peut voir TOUTES les annonces"""
    if 'user_id' not in request.session or request.session.get('user_role') != "ADM":
        return HttpResponseRedirect(reverse("connexion"))

    # Récupérer TOUTES les annonces (sans filtre d'auteur)
    annonces = Annonce.objects.filter(service__isnull=True)

    # Paramètres de filtrage
    categorie = request.GET.get('categorie', '')
    visibilite = request.GET.get('visibilite', '')
    afficher_expirees = request.GET.get('afficher_expirees', 'false').lower() == 'true'
    sort_by = request.GET.get('sort', '-date_creation')

    from django.db.models import Q
    
    # Filtrer par catégorie
    if categorie and categorie != 'TOUS':
        annonces = annonces.filter(categorie=categorie)

    # Filtrer par visibilité
    if visibilite and visibilite != 'TOUS':
        annonces = annonces.filter(visibilite=visibilite)

    # Filtrer par expiration si demandé
    if not afficher_expirees:
        annonces = annonces.filter(Q(date_expiration__isnull=True) | Q(date_expiration__gte=timezone.now()))

    # Tri
    if sort_by == '-date_creation':
        annonces = annonces.order_by('-date_creation')
    elif sort_by == 'date_creation':
        annonces = annonces.order_by('date_creation')
    elif sort_by == '-date_expiration':
        annonces = annonces.order_by('-date_expiration')
    elif sort_by == 'date_expiration':
        annonces = annonces.order_by('date_expiration')

    if request.method == "POST":
        # Supprimer les annonces sélectionnées
        annonce_ids = request.POST.getlist('annonce_ids[]')
        if annonce_ids:
            Annonce.objects.filter(id_annonce__in=annonce_ids, service__isnull=True).delete()
        return HttpResponseRedirect(reverse("listeAnnoncesAdmin"))

    # Préparer les choix pour les selects
    categories_choices = Annonce.Categorie.choices
    visibilites_choices = Annonce.Visibilite.choices

    return render(request, "UniShare/Administrateur/listeAnnoncesAdmin.html", {
        "lesannonces": annonces,
        "categories_choices": categories_choices,
        "visibilites_choices": visibilites_choices,
        "selected_categorie": categorie,
        "selected_visibilite": visibilite,
        "afficher_expirees": afficher_expirees,
        "sort_by": sort_by
    })

def listeServicesAdmin(request):
    """Admin peut voir TOUS les services"""
    if 'user_id' not in request.session or request.session.get('user_role') != "ADM":
        return HttpResponseRedirect(reverse("connexion"))

    # Récupérer TOUS les services
    services = Service.objects.all()

    # Paramètres de filtrage
    type_service = request.GET.get('type_service', '')
    visibilite = request.GET.get('visibilite', '')
    afficher_expirees = request.GET.get('afficher_expirees', 'false').lower() == 'true'
    sort_by = request.GET.get('sort', '-date_creation')

    from django.db.models import Q
    
    # Filtrer par type de service
    if type_service and type_service != 'TOUS':
        services = services.filter(type_service=type_service)

    # Filtrer par visibilité
    if visibilite and visibilite != 'TOUS':
        services = services.filter(visibilite=visibilite)

    # Filtrer par expiration si demandé
    if not afficher_expirees:
        services = services.filter(Q(date_expiration__isnull=True) | Q(date_expiration__gte=timezone.now()))

    # Tri
    if sort_by == '-date_creation':
        services = services.order_by('-date_creation')
    elif sort_by == 'date_creation':
        services = services.order_by('date_creation')
    elif sort_by == '-date_rencontre':
        services = services.order_by('-date_rencontre')
    elif sort_by == 'date_rencontre':
        services = services.order_by('date_rencontre')
    elif sort_by == '-date_expiration':
        services = services.order_by('-date_expiration')
    elif sort_by == 'date_expiration':
        services = services.order_by('date_expiration')

    if request.method == "POST":
        # Supprimer les services sélectionnés
        service_ids = request.POST.getlist('service_ids[]')
        if service_ids:
            Service.objects.filter(id_service__in=service_ids).delete()
        return HttpResponseRedirect(reverse("listeServicesAdmin"))

    # Préparer les choix pour les selects
    types_choices = Service.TypeService.choices
    visibilites_choices = Service._meta.get_field('visibilite').choices

    return render(request, "UniShare/Administrateur/listeServicesAdmin.html", {
        "lesservices": services,
        "types_choices": types_choices,
        "visibilites_choices": visibilites_choices,
        "selected_type_service": type_service,
        "selected_visibilite": visibilite,
        "afficher_expirees": afficher_expirees,
        "sort_by": sort_by
    })

"""Actions Admin"""
""" Liste des utilisateurs (admin)"""
def listeUtilisateurs(request):
    redirection = verifier_admin(request)
    if redirection:
        return redirection

    utilisateurs = Utilisateur.objects.all()
    
    # Paramètres de filtrage
    role_filter = request.GET.get('role', '')
    statut_filter = request.GET.get('statut', '')
    show_deletion_pending = request.GET.get('show_deletion_pending', 'false').lower() == 'true'

    # Filtrer par rôle
    if role_filter and role_filter != 'TOUS':
        utilisateurs = utilisateurs.filter(role=role_filter)

    # Filtrer par statut (seulement pour Etudiant)
    if statut_filter and statut_filter != 'TOUS':
        utilisateurs = utilisateurs.filter(etudiant__statut_compte=statut_filter)

    # Filtrer par demande de suppression si demandé
    if show_deletion_pending:
        utilisateurs = utilisateurs.filter(demande_suppression_en_cours=True)
    else:
        # Par défaut, afficher seulement les comptes non en attente de suppression
        utilisateurs = utilisateurs.filter(demande_suppression_en_cours=False)

    return render(request, "UniShare/Administrateur/listeUtilisateurs.html", {
        "utilisateurs": utilisateurs,
        "selected_role": role_filter,
        "selected_statut": statut_filter,
        "show_deletion_pending": show_deletion_pending,
        "roles_choices": [('ETU', 'Étudiant'), ('ANC', 'Ancien'), ('ADM', 'Admin')],
        "statut_choices": [('ACTIF', 'Actif'), ('SUSP', 'Suspendu')]
    })

""" Voir le profil public d'un utilisateur (admin seulement) """
def afficherProfilUtilisateur(request, id):
    if 'user_id' not in request.session or request.session.get('user_role') != "ADM":
        return HttpResponseRedirect(reverse("connexion"))

    utilisateur = Utilisateur.objects.get(id=id)
    
    # Récupérer les infos étudiant si applicable
    etudiant = None
    if utilisateur.role in ['ETU', 'ANC']:
        try:
            etudiant = Etudiant.objects.get(id=id)
        except Etudiant.DoesNotExist:
            pass
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'supprimer':
            utilisateur.delete()
            return HttpResponseRedirect(reverse("listeUtilisateurs"))
        elif action == 'suspendre':
            if etudiant:
                etudiant.statut_compte = 'SUSP'
                etudiant.save()
                return HttpResponseRedirect(reverse("afficherProfilUtilisateur", args=[id]))
        elif action == 'reactiver':
            if etudiant:
                etudiant.statut_compte = 'ACTIF'
                etudiant.save()
                return HttpResponseRedirect(reverse("afficherProfilUtilisateur", args=[id]))
    
    return render(request, "UniShare/Administrateur/afficherProfilUtilisateur.html", {
        "utilisateur": utilisateur,
        "etudiant": etudiant
    })

""" Supprimer un utilisateur (admin)"""
def supprimerUtilisateur(request, id):
    if 'user_id' not in request.session or request.session.get('user_role') != "ADM":
        return HttpResponseRedirect(reverse("connexion"))

    utilisateur = Utilisateur.objects.get(id=id)

    if request.method == "POST":
        utilisateur.delete()
        return HttpResponseRedirect(reverse("listeUtilisateurs"))

    return render(request, "UniShare/Admin/supprimerUtilisateur.html", {"utilisateur": utilisateur})

""" Dashboard admin"""
def dashboardAdmin(request):
    if 'user_id' not in request.session or request.session.get('user_role') != "ADM":
        return HttpResponseRedirect(reverse("connexion"))

    # Nettoyer les comptes dont la demande de suppression a dépassé 30 jours
    from datetime import timedelta
    limite_suppression = timezone.now() - timedelta(days=30)
    comptes_a_supprimer = Utilisateur.objects.filter(
        demande_suppression_en_cours=True,
        date_demande_suppression__lt=limite_suppression
    )
    
    # Supprimer les comptes
    for compte in comptes_a_supprimer:
        compte.delete()

    # Statistiques utilisateurs
    nb_utilisateurs = Utilisateur.objects.count()
    nb_etudiants = Etudiant.objects.count()
    nb_admins = Utilisateur.objects.filter(role='ADM').count()
    nb_anciens = Utilisateur.objects.filter(role='ANC').count()
    nb_comptes_actifs = Etudiant.objects.filter(statut_compte='ACTIF').count()
    nb_comptes_suspendus = Etudiant.objects.filter(statut_compte='SUSP').count()
    
    # Statistiques annonces/services
    nb_annonces = Annonce.objects.filter(service__isnull=True).count()
    nb_services = Service.objects.count()
    
    # Comptes en attente de suppression
    nb_comptes_suppression_pending = Utilisateur.objects.filter(demande_suppression_en_cours=True).count()

    return render(request, "UniShare/Administrateur/dashboardAdmin.html", {
        "nb_utilisateurs": nb_utilisateurs,
        "nb_etudiants": nb_etudiants,
        "nb_admins": nb_admins,
        "nb_anciens": nb_anciens,
        "nb_comptes_actifs": nb_comptes_actifs,
        "nb_comptes_suspendus": nb_comptes_suspendus,
        "nb_annonces": nb_annonces,
        "nb_services": nb_services,
        "nb_comptes_suppression_pending": nb_comptes_suppression_pending
    })

""" Gérer les annonces et services expirés (admin)"""
def gererAnnoncesExpirees(request):
    if 'user_id' not in request.session or request.session.get('user_role') != "ADM":
        return HttpResponseRedirect(reverse("connexion"))

    # Récupérer les annonces expirées (sauf les services)
    annonces_expirees = Annonce.objects.filter(
        date_expiration__lt=timezone.now(),
        service__isnull=True
    )

    # Récupérer les services expirés
    services_expires = Service.objects.filter(
        date_expiration__lt=timezone.now()
    )

    if request.method == "POST":
        action = request.POST.get('action')
        annonces_ids = request.POST.getlist('annonce_ids[]')
        services_ids = request.POST.getlist('service_ids[]')

        if action == 'supprimer':
            # Supprimer les annonces sélectionnées
            if annonces_ids:
                Annonce.objects.filter(id_annonce__in=annonces_ids, service__isnull=True).delete()
            # Supprimer les services sélectionnés
            if services_ids:
                Service.objects.filter(id_service__in=services_ids).delete()

        return HttpResponseRedirect(reverse("gererAnnoncesExpirees"))

    return render(request, "UniShare/Administrateur/gererAnnoncesExpirees.html", {
        "annonces_expirees": annonces_expirees,
        "services_expires": services_expires
    })

def gererComptesEnSuppression(request):
    """Gérer les comptes en attente de suppression"""
    if 'user_id' not in request.session or request.session.get('user_role') != "ADM":
        return HttpResponseRedirect(reverse("connexion"))

    # Récupérer les comptes en attente de suppression
    comptes_suppression = Utilisateur.objects.filter(demande_suppression_en_cours=True).order_by('date_demande_suppression')

    if request.method == "POST":
        action = request.POST.get('action')
        compte_ids = request.POST.getlist('compte_ids[]')

        if action == 'supprimer':
            # Supprimer les comptes sélectionnés
            if compte_ids:
                comptes_a_supprimer = Utilisateur.objects.filter(id__in=compte_ids)
                for compte in comptes_a_supprimer:
                    compte.delete()

        elif action == 'annuler':
            # Annuler la suppression des comptes sélectionnés
            if compte_ids:
                Utilisateur.objects.filter(id__in=compte_ids).update(
                    demande_suppression_en_cours=False,
                    date_demande_suppression=None
                )

        return HttpResponseRedirect(reverse("gererComptesEnSuppression"))

    return render(request, "UniShare/Administrateur/gererComptesEnSuppression.html", {
        "comptes_suppression": comptes_suppression
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

""" Marquer une notification comme lue"""
def marquerNotificationCommeLue(request, id):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    notification = Notification.objects.get(id=id)
    notification.lue = True
    notification.save()

    return HttpResponseRedirect(reverse("mesNotifications"))

""" Marquer toutes les notifications comme lues"""
def marquerToutesNotificationsCommeLues(request):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))

    user_id = request.session['user_id']
    etudiant = Etudiant.objects.get(id=user_id)

    notifications = Notification.objects.filter(reservation__demandeur=etudiant, lue=False)
    notifications.update(lue=True)

    return HttpResponseRedirect(reverse("mesNotifications"))
