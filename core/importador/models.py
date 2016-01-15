# -*- encoding: utf-8 -*-
"""Provavelmente o unico mudel do projeto."""

from __future__ import unicode_literals
from datetime import datetime
import xlrd


def parse_xls(arquivo):
    u"""
    Lê o arquivo XLS e retorna uma uma estrutura python.

    Estrutura:
    [[[v, v, v, v, v, v, v, v],
      [v, v, v, v, v, v, v, v]],
     [[w, w, w, w, w],
      [w, w, w, w, w]]]
    Uma lista de 'sheets' contendo
    Uma lista de 'linhas' contendo
    Uma lista de 'valores de celulas'

    Então:
    >>> parsed = parse_xls("arquivo_qualquer.xls")
    >>> planilha_1 = parsed[0]
    >>> planilha_3 = parsed[2]
    >>> celula_A1_planilha_1 = parsed[0][0][0]
    >>> celula_E24_planilha_2 = parsed[1][4][23]
    """
    book = xlrd.open_workbook(arquivo)
    planilhas = [book.sheet_by_index(p) for p in xrange(book.nsheets)]
    parsed = []
    for p in planilhas:
        planilha = []
        for linha in xrange(p.nrows):
            planilha.append(p.row_values(linha))
        parsed.append(planilha)
    return parsed


def le_planilha_funcionarios(arquivo):
    u"""Le a planilha de usuarios e retorna uma estrutura utilizável."""
    # .
    def le_funcionario(linhas):
        u"""Retira do conjunto de linha as informações de um funcionário."""
        pis = None

        for linha in linhas:
            if "NOME" in linha:
                nome = linha.split("NOME")[1].strip()
            elif "PIS/PASEP" in linha:
                pis = linha.split("PASEP")[1].strip()
            elif u"FUN\xc7\xc3O" in linha:
                funcao = linha.split(u"FUN\xc7\xc3O")[1].strip()
            elif "CTPS" in linha:
                ctps_departamento = linha.split("CTPS")[1]
                ctps, departamento = ctps_departamento.split("DEPARTAMENTO")
                ctps, departamento = ctps.strip(), departamento.strip()
            elif u"ADMISS\xc3O" in linha:
                data_admissao = linha.split(u"ADMISS\xc3O")[1].strip()
                data_admissao = datetime.strptime(data_admissao, "%d/%m/%Y")

        if not pis:
            return None

        return {"nome": nome,
                "pis": pis,
                "ctps": ctps,
                "funcao": funcao,
                "departamento": departamento,
                "data_admissao": data_admissao}

    planilha = parse_xls(arquivo)[0]
    funcionarios = []
    linhas_funcionario = []

    for linha in planilha[3:]:
        linha = linha[0]
        if linha.startswith(u'N\xba Folha'):
            # Inicio de novo funcionário
            funcionario = le_funcionario(linhas_funcionario)
            funcionarios.append(funcionario)
            linhas_funcionario = [linha]
        else:
            linhas_funcionario.append(linha)

    funcionario = le_funcionario(linhas_funcionario)
    funcionarios.append(funcionario)
    return [f for f in funcionarios if f]
