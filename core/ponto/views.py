# -*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from django.shortcuts import render

from ponto.models import Funcionario, Feriado, Ponto


def funcionario(request):
    u"""Relatório de um dado funcionário."""
    def insere_lacunas(entradas):
        u"""Insere no relatório os campos de fins de semana e feriados."""
        inicio = entradas[0]["dia"]
        fim = entradas[-1]["dia"]
        entradas = {e["dia"]: e for e in entradas}
        resultado = []
        for indice in xrange((fim - inicio).days):
            dia = inicio + timedelta(days=indice)
            e = entradas.get(dia)
            if not e:
                feriado = Feriado.objects.get_or_none(dia=dia)
                e = {"dia": dia}
                if dia.weekday() in [5, 6]:
                    e["ponto"] = {"tipo": "fim_de_semana"}
                elif feriado:
                    e["ponto"] = {"tipo": Ponto.FOLGA,
                                  "get_tipo_display": feriado.descricao}

            resultado.append(e)
        return resultado

    funcionario = Funcionario.objects.get(id=38)
    inicio = datetime(2014, 11, 30)
    fim = datetime.now().date()
    relatorio = funcionario.relatorio(inicio=inicio, fim=fim)
    relatorio["entradas"] = insere_lacunas(relatorio["entradas"])
    context = {"relatorio": relatorio,
               "funcionario": funcionario,
               "inicio": inicio,
               "fim": fim}
    return render(request, "tabela_funcionario.html", context)