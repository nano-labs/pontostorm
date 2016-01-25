# -*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404

from ponto.models import Funcionario, Feriado, Ponto


def funcionario(request):
    u"""Relatório de um dado funcionário."""
    def insere_lacunas(entradas):
        u"""Insere no relatório os campos de fins de semana e feriados."""
        if not entradas:
            return entradas
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

    pis = request.GET.get("pis")
    funcionario = Funcionario.objects.get_or_none(pis=request.GET.get("pis"))
    if not funcionario:
        return render(request, "tabela_funcionario.html", {})

    ultimo_dia = funcionario.ultimo_dia
    primeiro_dia = funcionario.primeiro_dia
    range_dias = [primeiro_dia + timedelta(days=d)
                  for d in xrange((ultimo_dia - primeiro_dia).days)]

    try:
        inicio = datetime.strptime(request.GET.get("inicio", ""), "%d/%m/%Y")
    except ValueError:
        inicio = primeiro_dia
    try:
        fim = datetime.strptime(request.GET.get("fim", ""), "%d/%m/%Y")
    except ValueError:
        fim = ultimo_dia
    relatorio = funcionario.relatorio(inicio=inicio, fim=fim)
    relatorio["entradas"] = insere_lacunas(relatorio["entradas"])
    context = {"relatorio": relatorio,
               "funcionario": funcionario,
               "inicio": inicio,
               "fim": fim,
               "range_dias": range_dias}
    return render(request, "tabela_funcionario.html", context)
