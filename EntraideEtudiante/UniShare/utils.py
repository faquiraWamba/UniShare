# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 10:21:10 2026

@author: Faquira
"""

from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse


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
    if request.session.get('user_role') != "ADMIN":
        return render(request, "UniShare/Annonce/listeAnnonces.html", {
            "erreur": "Accès réservé aux administrateurs."
        })
    return None

def verifier_proprietaire(request, objet):
    if objet.auteur.id != request.session['user_id']:
        return render(request, "UniShare/Annonce/listeAnnonces.html", {
            "erreur": "Vous n'avez pas les droits pour effectuer cette action."
        })
    return None