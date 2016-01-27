# -*- encoding: utf-8 -*-
from django.shortcuts import render, redirect
from django.contrib import messages

from ponto.models import Funcionario


def home(request):
    u"""Página principal do sistema."""
    sem_email = Funcionario.objects.filter(usuario__isnull=True)
    pendencias = {"sem_email": sem_email}
    context = {"pendencias": pendencias}
    return render(request, "home.html", context)

def definir_email(request):
    u"""Vincula um email ao funcionário."""
    post = request.POST.get
    try:
        # Pois estou com preguiça de tratar tudo
        id_funcionario = int(post("funcionario"))
        email = post("email")
        funcionario = Funcionario.objects.get(id=id_funcionario)
        funcionario.set_email(email)
        mensagem = u"Email '%s' associado ao funcionário %s" % (
                    email, funcionario.nome)
        messages.add_message(request, messages.SUCCESS, mensagem)
    except Exception, e:
        messages.add_message(request, messages.ERROR, str(e))

    return redirect("home")