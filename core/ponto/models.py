# -*- encoding: utf-8 -*-
"""Provavelmente o unico mudel do projeto."""
from __future__ import unicode_literals

from math import sqrt
from datetime import datetime, time, timedelta
from django.contrib.auth.models import User
from django.db import models

from importador.models import le_planilha_funcionarios, le_planilha_ponto
from utils.models import BaseModel

JORNADA_PADRAO = time(8, 0, 0)


def format_minutes(minutes):
    u"""Converte um tempo de total de minutos para string."""
    positive_minutes = abs(minutes)
    horas = positive_minutes / 60
    minutos = positive_minutes % 60
    return "%s%.02d:%.02d" % (["", "-"][minutes < 0], horas, minutos)


def time_to_minutes(time_object):
    """Recebe um objeto datetime.time e retorna o total de minutos."""
    return (time_object.hour * 60) + time_object.minute


def media_e_desvio(l):
    u"""Retorna a média e desvio padrão com base numa lista de valores."""
    l = [i for i in l if i]
    media = 0
    dp = 0
    if len(l) >= 2:
        media = sum(l) / float(len(l))
        dp = sqrt((sum([i ** 2 for i in l]) - ((sum(l) ** 2) / len(l))) / (len(l) - 1))
    media = int(media)
    dp = int(dp)
    return media, dp


class Departamento(BaseModel):

    """Categoriza os departamentos da empresa."""

    nome = models.CharField("Nome", max_length=255)

    def __unicode__(self):
        u"""Unicode para exibição do objeto."""
        return u"Departamento %s" % self.nome

    class Meta:
        ordering = ("nome",)


class Funcionario(BaseModel):

    u"""
    Representa um funcionário da empresa.

    Possui vinculo com um usuário do django para que o funcionário possa
    logar e ver seus proprios dados.
    """

    pis = models.CharField("PIS/PASEP", max_length=40, unique=True,
                           db_index=True, blank=False, null=False)
    nome = models.CharField("Nome", max_length=255, blank=False, null=False)
    ctps = models.CharField("Carteira de trabalho", max_length=255,
                            unique=True, blank=False, null=False)
    funcao = models.CharField("Função", max_length=255, blank=True, null=True)
    departamento = models.ForeignKey(Departamento, verbose_name="Departamento",
                                     related_name="funcionarios")
    data_admissao = models.DateField("Data de Admissão")
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True,
                                   verbose_name="Usuario de acesso",
                                   related_name="funcionario", blank=True)

    # Jornada de trabalho
    # TODO: Pensar numa forma melhor de gerenciar isso
    segunda = models.TimeField("Segunda Feira", default=JORNADA_PADRAO)
    terca = models.TimeField("Terça Feira", default=JORNADA_PADRAO)
    quarta = models.TimeField("Quarta Feira", default=JORNADA_PADRAO)
    quinta = models.TimeField("Quinta Feira", default=JORNADA_PADRAO)
    sexta = models.TimeField("Sexta Feira", default=JORNADA_PADRAO)
    sabado = models.TimeField("Sábado", default=time(0, 0, 0))
    domingo = models.TimeField("Domingo", default=time(0, 0, 0))

    @property
    def expedientes(self):
        """Agrupa os expedientes usando como chave a resposta de weekday()."""
        return {0: self.segunda,
                1: self.terca,
                2: self.quarta,
                3: self.quinta,
                4: self.sexta,
                5: self.sabado,
                6: self.domingo}

    @classmethod
    def importar_planilha(cls, arquivo):
        """Importa a planilha de funcionarios e atualiza a tabela."""
        # O codigo abaixo está feio pra burro pois pretendo jogá-lo fora
        # quando lermos os dados diretamente do relógio de ponto
        def get_departamento(nome):
            u"""Retorna uma instância de Departamento."""
            return Departamento.objects.get_or_create(nome=nome)[0]

        funcionarios = le_planilha_funcionarios(arquivo)
        for funcionario in funcionarios:
            f = cls.objects.get_or_none(pis=funcionario["pis"])
            if not f:
                f = cls()
            f.pis = funcionario["pis"]
            f.nome = funcionario["nome"]
            f.ctps = funcionario["ctps"]
            f.funcao = funcionario["funcao"]
            f.data_admissao = funcionario["data_admissao"]

            f.departamento = get_departamento(funcionario["departamento"])
            f.save()

    def checkup(self, inicio=None, fim=None):
        u"""Verifica incongruências nos pontos, aplica faltas etc."""
        pontos = self.pontos_filtrados(inicio, fim).order_by("dia")
        inicio = pontos.first()
        inicio = inicio.dia if inicio else datetime.today()
        fim = pontos.last()
        fim = fim.dia if fim else datetime.today()

        pontos = {p.dia: p for p in pontos}
        for d in xrange((fim - inicio).days):
            dia = inicio + timedelta(days=d)
            ponto = pontos.get(dia)
            if self.expediente_esperado(dia) > 0 and not ponto:
                # Falta
                Ponto.objects.create(funcionario=self, tipo=Ponto.FALTA,
                                     dia=dia)
                print dia, "Falta"
            else:
                print dia, ponto
        # TODO: Verificar incongruencias

    def relatorio(self, inicio, fim):
        u"""Retorna todos os dados para o relatório deste funcionário."""
        # DIA, ENTRADAS e SAIDAS, TIPO, TRABALHADO, EXTRA, SALDO_PERIODO, FALTAS_PERIODO, SALDO_EVER, FALTAS_EVER
        def logica_permanencias(permanencias):
            chegada, almoco, volta, saida, outros = None, None, None, None, []
            if len(permanencias) == 1:
                chegada = (permanencias[0].entrada, permanencias[0].entrada_manual)
                saida = (permanencias[0].saida, permanencias[0].saida_manual)
            elif len(permanencias) >= 2:
                chegada = (permanencias[0].entrada, permanencias[0].entrada_manual)
                almoco = (permanencias[0].saida, permanencias[0].saida_manual)
                volta = (permanencias[1].entrada, permanencias[1].entrada_manual)
                saida = (permanencias[1].saida, permanencias[1].saida_manual)
            if len(permanencias) > 2:
                for p in permanencias[2:]:
                    outros.append((p.entrada, p.entrada_manual))
                    outros.append((p.saida, p.saida_manual))
            return chegada, almoco, volta, saida, outros

        saldo_anterior = 0
        faltas_anteriores = 0
        ponto_anterior = self.pontos.filter(dia__lt=inicio).order_by("dia").last()
        if ponto_anterior:
            saldo_anterior = ponto_anterior.saldo()
            faltas_anteriores = ponto_anterior.faltas()
        # import ipdb; ipdb.set_trace()

        pontos = self.pontos.filter(dia__gte=inicio, dia__lte=fim).order_by("dia")
        saldo_acumulado = 0
        faltas_acumuladas = 0
        entradas = []
        for p in pontos:
            saldo_acumulado += p.extra
            faltas_acumuladas += int(p.tipo == Ponto.FALTA)
            chegada, almoco, volta, saida, outros = logica_permanencias(p.permanencias.all())

            entrada = {"dia": p.dia,
                       "chegada": chegada,
                       "almoco": almoco,
                       "volta": volta,
                       "saida": saida,
                       "outros": outros,
                       "trabalhado": p.expediente_trabalhado,
                       "tipo": p.get_tipo_display(),
                       "extra": p.extra,
                       "saldo_periodo": saldo_acumulado,
                       "faltas_periodo": faltas_acumuladas,
                       "saldo_total": saldo_acumulado + saldo_anterior,
                       "faltas_totais": faltas_acumuladas + faltas_anteriores,
                       "objeto": p}
            entradas.append(entrada)
        return {"entradas": entradas,
                "saldo_periodo": saldo_acumulado,
                "faltas_periodo": faltas_acumuladas,
                "saldo_total": saldo_acumulado + saldo_anterior,
                "faltas_totais": faltas_acumuladas + faltas_anteriores,
                "disponibilidade": self.disponibilidade(inicio, fim),
                "assiduidade": self.assiduidade(inicio, fim),
                "entrada_media": self.entrada_media(inicio, fim),
                "saida_media": self.saida_media(inicio, fim),
                "saldo_anterior": saldo_anterior,
                "faltas_anteriores": faltas_anteriores}

    def pontos_filtrados(self, inicio=None, fim=None, filtros=None):
        """Retorna o queryset de pontos filtrados."""
        filtros = filtros or {}
        if inicio:
            filtros["dia__gte"] = inicio
        if fim:
            filtros["dia__lte"] = fim
        return self.pontos.filter(**filtros)

    def tempo_trabalhado(self, inicio=None, fim=None):
        u"""
        Retorna o total de tempo trabalhado, em minutos, no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        pontos = self.pontos_filtrados(inicio, fim)
        total = 0
        for p in pontos:
            total += p.expediente_trabalhado
        return total

    def tempo_esperado(self, inicio=None, fim=None):
        u"""
        Retorna o total de tempo esperado de trabalho, em minutos, no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        pontos = self.pontos_filtrados(inicio, fim)
        total = 0
        for p in pontos:
            total += p.expediente_esperado
        return total

    def disponibilidade(self, inicio=None, fim=None):
        u"""
        Retorna o tempo trabalhado, esperado e disponibilidade no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        trabalhado = self.tempo_trabalhado(inicio, fim)
        esperado = self.tempo_esperado(inicio, fim)
        disponibilidade = 0.0
        if esperado > 0:
            disponibilidade = trabalhado / float(esperado) * 100
        return {"trabalhado": trabalhado,
                "esperado": esperado,
                "disponibilidade": disponibilidade}

    def saldo(self, inicio=None, fim=None):
        u"""
        Retorna o saldo de horas, em minutos, do funcionário no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        saldo = self.tempo_esperado(inicio, fim) - self.tempo_trabalhado(inicio, fim)
        return saldo

    def faltas(self, inicio=None, fim=None):
        u"""
        Retorna o total de faltas do funcionário no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        return self.pontos_filtrados(inicio, fim, {"tipo": Ponto.FALTA}).count()

    def presencas(self, inicio=None, fim=None):
        u"""
        Retorna o total de presenças do funcionário no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        return self.pontos_filtrados(inicio, fim, {"tipo": Ponto.DIA_UTIL}).count()

    def assiduidade(self, inicio=None, fim=None):
        u"""
        Retorna a assiduidade do funcionario no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        presencas = self.presencas(inicio, fim)
        faltas = self.faltas(inicio, fim)
        total = presencas + faltas
        assiduidade = 0.0
        if total > 0:
            assiduidade = presencas / float(total) * 100
        return {"presencas": presencas,
                "faltas": faltas,
                "total": total,
                "assiduidade": assiduidade}

    def entrada_media(self, inicio=None, fim=None):
        u"""
        Retorna a hora media e desvio padrão de entrada no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        entradas = []
        pontos = self.pontos_filtrados(inicio, fim)
        for ponto in pontos:
            permanencia = ponto.permanencias.first()
            if permanencia:
                entradas.append(time_to_minutes(permanencia.entrada.time()))
        return media_e_desvio(entradas)

    def saida_media(self, inicio=None, fim=None):
        u"""
        Retorna a hora media e desvio padrão de saída no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        saidas = []
        pontos = self.pontos_filtrados(inicio, fim)
        for ponto in pontos:
            permanencia = ponto.permanencias.last()
            if permanencia:
                saidas.append(time_to_minutes(permanencia.saida.time()))
        return media_e_desvio(saidas)

    def expediente_esperado(self, dia):
        """Retorna o tempo, em minutos, de expediente esperado neste dia."""
        # Cuidado com a lógica abaixo para não gerar recursividade infinita
        ponto = self.pontos.get_or_none(dia=dia)
        if ponto:
            if ponto.tipo in [ponto.FOLGA, ponto.FALTA_ABONADA]:
                return 0

            if ponto.is_holiday:
                return 0

        if Feriado.objects.get_or_none(dia=dia):
            return 0
        return time_to_minutes(self.expedientes[dia.weekday()])

    def __unicode__(self):
        u"""Unicode para exibição do usuário."""
        return u"%s" % self.nome

    class Meta:
        ordering = ("nome",)
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"


class Ponto(BaseModel):

    u"""Registra os pontos batidos pelos funcionários."""

    DIA_UTIL = 0
    FOLGA = 1
    FALTA = 2
    FALTA_ABONADA = 3
    CONSUMO = 4
    CHOICES_TIPO = ((DIA_UTIL, "Dia útil"),
                    (FOLGA, "Folga ou feriado"),
                    (FALTA, "Falta"),
                    (FALTA_ABONADA, "Falta abonada"),
                    (CONSUMO, "Consumo de hora extra"))

    funcionario = models.ForeignKey(Funcionario, verbose_name="Funcionário",
                                    related_name="pontos", null=False)
    dia = models.DateField("Dia", null=False, blank=False)
    tipo = models.PositiveSmallIntegerField("Tipo", choices=CHOICES_TIPO,
                                            default=DIA_UTIL)
    observacoes = models.TextField("Observações", blank=True, null=True)
    # anexos
    # permanencias

    @classmethod
    def importar_planilha(cls, arquivo):
        """Le a planilha exportada pelo Seculum e importa os dados."""
        # O codigo abaixo está feio pra burro pois pretendo jogá-lo fora
        # quando lermos os dados diretamente do relógio de ponto
        funcionarios = le_planilha_ponto(arquivo)
        for f in funcionarios:
            funcionario = Funcionario.objects.get_or_none(ctps=f["ctps"])
            if funcionario:
                funcionario.segunda = f["horarios"]["segunda"]
                funcionario.terca = f["horarios"]["terca"]
                funcionario.quarta = f["horarios"]["quarta"]
                funcionario.quinta = f["horarios"]["quinta"]
                funcionario.sexta = f["horarios"]["sexta"]
                funcionario.sabado = f["horarios"]["sabado"]
                funcionario.domingo = f["horarios"]["domingo"]
                funcionario.save()

                entradas = f["entradas"]
                for entrada in entradas:
                    if not any(entrada["entradas"]):
                        continue
                    p = cls()
                    p.funcionario = funcionario
                    p.dia = entrada["dia"]
                    p.save()
                    if entrada["entradas"][0] and entrada["entradas"][1]:
                        Permanencia.objects.create(ponto=p, entrada=entrada["entradas"][0],
                                           saida=entrada["entradas"][1])
                    if entrada["entradas"][2] and entrada["entradas"][3]:
                        Permanencia.objects.create(ponto=p, entrada=entrada["entradas"][2],
                                           saida=entrada["entradas"][3])
                    if all([entrada["entradas"][0], entrada["entradas"][3],
                            not entrada["entradas"][1],
                            not entrada["entradas"][2]]):
                        Permanencia.objects.create(ponto=p, entrada=entrada["entradas"][0],
                                           saida=entrada["entradas"][3])
                    if p.permanencias.count() == 0:
                        p.delete()

    @property
    def is_weekend(self):
        u"""Boleano que informa se este dia é ou não fim de semana."""
        return self.dia.weekday() in [5, 6]

    @property
    def is_holiday(self):
        u"""Boleano que informa se este dia é ou não feriado."""
        feriado = Feriado.objects.get_or_none(dia=self.dia)
        if feriado:
            return True
        return False

    @property
    def expediente_esperado(self):
        u"""Retorna o tempo, em minutos, de expediente esperado neste dia."""
        # Cuidado com a lógica abaixo para não gerar recursividade infinita.
        return self.funcionario.expediente_esperado(self.dia)

    @property
    def expediente_trabalhado(self):
        u"""Retorna o tempo, em minutos, de expediente trabalhado neste dia."""
        total = 0
        for p in self.permanencias.all():
            total += p.trabalhado
        return total

    @property
    def extra(self):
        u"""Tempo, em minutos, extras trabalhadas hoje."""
        return self.expediente_trabalhado - self.expediente_esperado

    def saldo(self, inicio=None):
        u"""
        Retorna o saldo de horas, em minutos, do funcionário no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.
        """
        return self.funcionario.saldo(inicio, self.dia)

    def faltas(self, inicio=None):
        u"""
        Retorna o total de faltas do funcionário até hoje.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.
        """
        return self.funcionario.faltas(inicio, self.dia)

    def presencas(self, inicio=None):
        u"""
        Retorna o total de presenças do funcionário até hoje.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.
        """
        return self.funcionario.presencas(inicio, self.dia)

    def tempo_trabalhado(self, inicio=None):
        u"""
        Retorna o total de tempo trabalhado, em minutos, no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.
        """
        return self.funcionario.tempo_trabalhado(inicio, self.dia)

    def tempo_esperado(self, inicio=None):
        u"""
        Retorna o total de tempo esperado de trabalho, em minutos, no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        return self.funcionario.tempo_esperado(inicio, self.dia)

    def disponibilidade(self, inicio=None):
        u"""
        Retorna o tempo trabalhado, esperado e disponibilidade no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        return self.funcionario.disponibilidade(inicio, self.dia)

    def __unicode__(self):
        """Unicode do objeto."""
        return u"%s - %s" % (self.dia, self.funcionario.nome)

    class Meta:
        ordering = ("-dia", "funcionario__nome")
        verbose_name = "Registro de ponto"
        verbose_name_plural = "Registros de ponto"
        unique_together = (("funcionario", "dia"),)


class Permanencia(BaseModel):

    u"""Entrada e saída de um dado funcionario em um dado dia."""

    ponto = models.ForeignKey(Ponto, verbose_name="Ponto",
                              related_name="permanencias")
    entrada = models.DateTimeField("Entrada")
    saida = models.DateTimeField("Saída")
    entrada_manual = models.BooleanField("Entrada registrada manualmente",
                                         default=False)
    saida_manual = models.BooleanField("Saída registrada manualmente",
                                       default=False)

    @property
    def trabalhado(self):
        u"""Retorna o tempo, em minutos, trabalhado nesta permanência."""
        if self.entrada and self.saida:
            total = self.saida - self.entrada
        return int(total.total_seconds() / 60)

    def __unicode__(self):
        u"""Unicode para exibição."""
        return u"%s entrou em %s%s e saiu em %s%s" % (
               self.ponto.funcionario.nome, self.entrada,
               ["", "*"][self.entrada_manual],
               self.saida,
               ["", "*"][self.saida_manual])

    class Meta:
        ordering = ("entrada", )
        verbose_name = "Permanência"
        verbose_name_plural = "Permanências"


class Anexo(BaseModel):

    u"""Anexos genéricos para guardar atestados, comprovantes, etc."""

    ponto = models.ForeignKey(Ponto, verbose_name="Ponto",
                              related_name="anexos")
    arquivo = models.FileField("Arquivo")

    @property
    def is_image(self):
        u"""Retorna se o arquivo é uma imagem ou não."""
        # TODO
        return False

    def __unicode__(self):
        u"""Unicode para exibição."""
        return u"Anexo referente ao dia %s do funcionario %s" % (
               self.ponto.dia, self.ponto.funcionario.nome)


class Feriado(BaseModel):

    u"""Pré-define os dias em que será feriado."""

    dia = models.DateField("Dia", blank=False, null=False)
    descricao = models.CharField("Descrição", max_length=255, blank=False,
                                 null=False, help_text="Ex: Dia da marmota")

    def __unicode__(self):
        u"""Unicode para exibição."""
        return u"%s - %s" % (self.dia, self.descricao)

    class Meta:
        ordering = ("dia",)
