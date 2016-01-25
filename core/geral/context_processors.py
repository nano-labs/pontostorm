# -*- encoding: utf-8 -*-

from ponto.models import Funcionario


def context(request):
    u"""Define um contexto de variaveis acessíveis em todas as views."""
    return {"funcionarios": Funcionario.objects.all()}
