# -*- encoding: utf-8 -*-
"""Provavelmente o unico mudel do projeto."""
from __future__ import unicode_literals

from math import sqrt
from datetime import datetime, time, timedelta
from django.contrib.auth.models import User
from django.db import models

from importador.models import le_planilha_funcionarios, le_planilha_ponto
from utils.models import BaseModel, PermanentModel

JORNADA_PADRAO = time(8, 0, 0)
SALDO_LIMITE = {"min": -30 * 60,
                "max": 30 * 60}


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

    @property
    def primeiro_dia(self):
        u"""Primeiro dia de ponto deste funcionário."""
        p = self.pontos.order_by("dia").first()
        return p.dia if p else datetime.today().date()

    @property
    def ultimo_dia(self):
        u"""Último dia de ponto deste funcionário."""
        p = self.pontos.order_by("dia").last()
        return p.dia if p else datetime.today().date()

    def send_message(self, message, subject=None):
        u"""Envia um email ao funcionário."""
        address = self.usuario.email
        if not email:
            raise Exception("Funcionario %s nao possui email cadastrado" %
                            self.nome)
        subject = u"[Clockwork Storm] %s" % subject
        context = {"message": message,
                   "subject": subject}
        template = "email_padrao.html"
        email = TemplatedEmail(address, subject, template, context)
        email.send()

    def checkup(self, inicio=None, fim=None):
        u"""Verifica incongruências nos pontos, aplica faltas etc."""
        pontos = self.pontos_filtrados(inicio, fim).order_by("dia")
        inicio = inicio or self.primeiro_dia
        fim = fim or self.ultimo_dia

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
        inicio = inicio or self.primeiro_dia
        fim = fim or self.ultimo_dia

        saldo_anterior = 0
        faltas_anteriores = 0
        ponto_anterior = self.pontos.filter(dia__lt=inicio).order_by("dia").last()
        if ponto_anterior:
            saldo_anterior = ponto_anterior.saldo()
            faltas_anteriores = ponto_anterior.faltas()

        pontos = self.pontos.filter(dia__gte=inicio, dia__lte=fim).order_by("dia")
        saldo_acumulado = 0
        faltas_acumuladas = 0
        entradas = []
        for p in pontos:
            saldo_acumulado += p.extra
            faltas_acumuladas += int(p.tipo == Ponto.FALTA)

            entrada = {"dia": p.dia,
                       "saldo_periodo": saldo_acumulado,
                       "faltas_periodo": faltas_acumuladas,
                       "saldo_total": saldo_acumulado + saldo_anterior,
                       "faltas_totais": faltas_acumuladas + faltas_anteriores,
                       "ponto": p}
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
        saldo = self.tempo_trabalhado(inicio, fim) - self.tempo_esperado(inicio, fim)
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
        pontos = self.pontos_filtrados(inicio, fim)
        entradas = [time_to_minutes(i.horario.time())
                    for i in [p.chegada for p in pontos] if i]
        return media_e_desvio(entradas)

    def saida_media(self, inicio=None, fim=None):
        u"""
        Retorna a hora media e desvio padrão de saída no período.

        Caso não seja informado 'inicio' será considerado o periodo desde sua
        primeira entrada no sistema.

        Caso não seja informado 'fim' será considerado o periodo até sua última
        entrada no sistema.
        """
        pontos = self.pontos_filtrados(inicio, fim)
        saidas = [time_to_minutes(i.horario.time())
                  for i in [p.saida for p in pontos] if i]
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
                    for e in entrada["entradas"]:
                        if e:
                            Registro.objects.create(ponto=p, horario=e)
                    if p.registros.count() == 0:
                        p.delete()

    @property
    def chegada(self):
        u"""Registro de entrada do funcionário."""
        return self.registros.first()

    @property
    def saida_almoco(self):
        u"""Registro da saida para almoço do funcionário."""
        if self.registros.count() >= 3:
            return self.registros.all()[1]
        return None

    @property
    def volta_almoco(self):
        u"""Registro da volta do almoço do funcionário."""
        if self.registros.count() >= 3:
            return self.registros.all()[2]
        return None

    @property
    def saida(self):
        u"""Registro da saída do funcionário."""
        quantidade = self.registros.count()
        if quantidade == 2:
            return self.registros.all()[1]
        elif quantidade >= 4:
            return self.registros.all()[3]
        return None

    @property
    def outros_registros(self):
        u"""Outros registros que não se encaixam no padrão de 4 registros."""
        return self.registros.all()[4:]

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
        registros = list(self.registros.all())
        if len(registros) == 1:
            # Numero impar de registros
            return 0
        total = 0
        tuplas = zip(range(1, len(registros), 2), range(0, len(registros), 2))
        for saida, entrada in tuplas:
            delta = registros[saida].horario - registros[entrada].horario
            total += int(delta.total_seconds() / 60)
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


class Registro(PermanentModel):

    u"""Passagem de um funcionário pelo relógio de ponto."""

    ponto = models.ForeignKey(Ponto, verbose_name="Ponto",
                              related_name="registros")
    horario = models.DateTimeField("Horário")
    registro_manual = models.BooleanField("Registro feito manualmente",
                                          default=False)

    def __unicode__(self):
        u"""Unicode para exibição."""
        return u"%s - %s%s" % (self.ponto.funcionario.nome, self.horario,
                               ["", "*"][self.registro_manual])

    class Meta:
        ordering = ("horario", )
        verbose_name = "Registro"
        verbose_name_plural = "Registros"


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
