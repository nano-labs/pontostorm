# -*- encoding: utf-8 -*-
"""Provavelmente o unico mudel do projeto."""
from __future__ import unicode_literals

from datetime import time
from django.contrib.auth.models import User
from django.db import models

from importador.models import le_planilha_funcionarios, le_planilha_ponto
from utils.models import BaseModel

JORNADA_PADRAO = time(8, 0, 0)


def format_minutes(minutes, format_string):
    u"""
    Converte um tempo de total de minutos para string.

    Ex:
    >>> format_minutes(121, "%H:%M:%S")
    >>> "00:02:01"
    """
    pass


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

    def tempo_trabalhado(self, inicio=None, fim=None):
        u"""
        Retorna o total de tempo trabalhado, em minutos, no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        # TODO
        pass

    def tempo_esperado(self, inicio=None, fim=None):
        u"""
        Retorna o total de tempo esperado de trabalho, em minutos, no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        # TODO
        pass

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
            disponibilidade = trabalhado / float(esperado)
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
        # TODO
        pass

    def faltas(self, inicio=None, fim=None):
        u"""
        Retorna o total de faltas do funcionário no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        # TODO
        pass

    def presencas(self, inicio=None, fim=None):
        u"""
        Retorna o total de presenças do funcionário no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        # TODO
        pass

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
            assiduidade = presencas / float(total)
        return {"presencas": trabalhado,
                "faltas": esperado,
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
        # TODO
        pass

    def saida_media(self, inicio=None, fim=None):
        u"""
        Retorna a hora media e desvio padrão de saída no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        # TODO
        pass

    def expediente_esperado(self, dia):
        """Retorna o tempo, em minutos, de expediente esperado neste dia."""
        # TODO
        pass

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
        # TODO
        pass

    @property
    def is_holiday(self):
        u"""Boleano que informa se este dia é ou não feriado."""
        # TODO
        pass

    def expediente_esperado(self):
        u"""Retorna o tempo, em minutos, de expediente esperado neste dia."""
        return self.funcionario.expediente_esperado(self.dia)

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
