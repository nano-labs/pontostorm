# -*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from django.shortcuts import render

from ponto.models import Funcionario


def funcionario(request):
    u"""Relatório de um dado funcionário."""
    funcionario = Funcionario.objects.get(id=38)
    inicio = datetime(2014, 11, 5)
    fim = datetime.now().date()
    relatorio = funcionario.relatorio(inicio=inicio, fim=fim)
    context = {"relatorio": relatorio,
               "funcionario": funcionario,
               "inicio": inicio,
               "fim": fim}
    return render(request, "tabela_funcionario.html", context)