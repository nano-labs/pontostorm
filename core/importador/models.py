# -*- encoding: utf-8 -*-
"""Provavelmente o unico mudel do projeto."""

from __future__ import unicode_literals
from datetime import datetime, timedelta
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


def le_planilha_ponto(arquivo):
    u"""Le a planilha de ponto e retorna uma estrutura python útil."""
    planilha = parse_xls(arquivo)[0]
    funcionarios = []
    linhas_funcionario = []

    def time_parse(linha):
        """Converte os valores das entradas em datetime."""
        dia = datetime.strptime(linha[0].split(" - ")[0], "%d/%m/%y")
        valores = []
        for e in linha[1:5]:
            try:
                v = timedelta(minutes=e * 24 * 60)
                entrada = dia
                v = entrada + v
            except:
                v = None
            valores.append(v)
        return {"dia": dia, "entradas": valores}

    def escala_para_horas(valores):
        u"""Converte os horários da escala em um objeto time."""
        vs = []
        for v in valores:
            try:
                v = timedelta(minutes=v * 24 * 60)
            except TypeError:
                v = timedelta(minutes=0)
            vs.append(v)
        total = vs[1] - vs[0] + vs[3] - vs[2] + vs[5] - vs[4]
        return (datetime.min + total).time()

    def le_funcionario(linhas):
        u"""Retira do conjunto de linha as informações de um funcionário."""
        ctps = None
        horarios = {}
        entradas = []

        for linha in linhas:
            if linha[6] in ["SEG", "TER", "QUA", "QUI", "SEX", u"S\xc1B", "DOM"]:
                horarios[{"SEG": "segunda",
                          "TER": "terca",
                          "QUA": "quarta",
                          "QUI": "quinta",
                          "SEX": "sexta",
                          u"S\xc1B": "sabado",
                          "DOM": "domingo"}[linha[6]]] = escala_para_horas(linha[7:])
            if linha[0] == "Nome":
                nome = linha[1]
            elif linha[0] == "CTPS":
                ctps = linha[1]

            elif any([linha[0].endswith(i)
                      for i in ["seg", "ter", "qua", "qui", "sex",
                                u"s\xe1b", "dom"]]):
                entradas.append(time_parse(linha))

        if not ctps:
            return None

        return {"nome": nome,
                "ctps": ctps,
                "horarios": horarios,
                "entradas": entradas}

    for linha in planilha[3:]:
        if u'Hor\xe1rio de Trabalho' in linha:
            # Inicio de novo funcionario
            funcionario = le_funcionario(linhas_funcionario)
            funcionarios.append(funcionario)
            linhas_funcionario = [linha]
        else:
            linhas_funcionario.append(linha)

    funcionario = le_funcionario(linhas_funcionario)
    funcionarios.append(funcionario)
    return [f for f in funcionarios if f]






















