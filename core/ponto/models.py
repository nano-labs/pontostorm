# -*- encoding: utf-8 -*-
"""Provavelmente o unico mudel do projeto."""
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

from utils.models import BaseModel

JORNADA_PADRAO = 8


def format_minutes(minutes, format_string):
    u"""
    Converte um tempo de total de minutos para string.

    Ex:
    >>>
    """


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
                                   related_name="funcionario")

    # Jornada de trabalho
    segunda = models.PositiveSmallIntegerField("Segunda Feira",
                                               default=JORNADA_PADRAO)
    terca = models.PositiveSmallIntegerField("Terça Feira",
                                             default=JORNADA_PADRAO)
    quarta = models.PositiveSmallIntegerField("Quarta Feira",
                                              default=JORNADA_PADRAO)
    quinta = models.PositiveSmallIntegerField("Quinta Feira",
                                              default=JORNADA_PADRAO)
    sexta = models.PositiveSmallIntegerField("Sexta Feira",
                                             default=JORNADA_PADRAO)
    sabado = models.PositiveSmallIntegerField("Sábado", default=0)
    domingo = models.PositiveSmallIntegerField("Domingo", default=0)

    def saldo(self, inicio=None, fim=None):
        u"""
        Retorna o saldo de horas, em minutos, do funcionário no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        # TODO
        pass


            - Saldo atual
            - Saldo no periodo
            - Total de faltas/presenças (%) atual
            - Total de faltas/presenças (%) no periodo
            - horario médio de entrada (desvio padrao) e horario médio de saida (desvio padrao) atual
            - horario médio de entrada (desvio padrao) e horario médio de saida (desvio padrao) no periodo
            - Horas trabalhadas/horas esperadas (%) atual
            - Horas trabalhadas/horas esperadas (%) no periodo



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


class Permanencias(BaseModel):

    u"""Entrada e saída de um dado funcionario em um dado dia."""

    ponto = models.ForeignKey(Ponto, verbose_name="Ponto",
                              related_name="permanencias")
    entrada = models.DateTimeField("Entrada")
    saida = models.DateTimeField("Saída")
    entrada_manual = models.BooleanField("Entrada registrada manualmente",
                                         default=False)
    saida_manual = models.BooleanField("Saída registrada manualmente",
                                       default=False)

    def __unicode__(self):
        u"""Unicode para exibição."""
        return u"%s entrou em %s%s e saiu em %s%s" % (
               self.ponto.funcionario.nome, self.entrada,
               ["", "*"][self.entrada_manual],
               self.saida,
               ["", "*"][self.saida_manual])

    class Meta:
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
