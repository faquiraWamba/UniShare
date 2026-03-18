# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 10:21:10 2026

@author: Faquira
"""

from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse
from .models import Etudiant, Notification
from django.db.models import Q


def verifier_connexion(request):
    if 'user_id' not in request.session:
        return HttpResponseRedirect(reverse("connexion"))
    return None


def verifier_etudiant(request):
    if request.session.get('user_role') != "ETU":
        return render(request, "UniShare/Annonce/listeAnnonces.html", {
            "erreur": "Accès réservé aux étudiants."
        })
    return None

def verifier_admin(request):
    if request.session.get('user_role') != "ADM":
        return render(request, "UniShare/Authentification/connexion.html", {
            "erreur": "Accès réservé aux administrateurs."
        })
    return None

def verifier_proprietaire(request, objet):
    if objet.auteur.id != request.session['user_id']:
        return render(request, "UniShare/Annonce/listeAnnonces.html", {
            "erreur": "Vous n'avez pas les droits pour effectuer cette action."
        })
    return None

def global_notifications(request):
    nb_notif = 0
    if request.session.get('user_id'):
        try:
            etudiant = Etudiant.objects.get(id=request.session['user_id'])
            notifications = Notification.objects.filter(auteur=etudiant, lu=False).order_by('-date')
            nb_notif = notifications.count()
        except Etudiant.DoesNotExist:
            nb_notif = 0
    return {
        'nb_notif': nb_notif
    }