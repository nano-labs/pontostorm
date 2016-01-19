# -*- encoding: utf-8 -*-
"""Provavelmente o unico admin do projeto."""

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.template import loader

from ponto.models import format_minutes
from ponto.models import (Funcionario, Feriado, Ponto, Departamento,
                          Permanencia, Anexo)

SEMANA = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")


class PermanenciaInline(admin.TabularInline):
    model = Permanencia
    extra = 0


class AnexoInline(admin.TabularInline):
    model = Anexo
    extra = 0


@admin.register(Ponto)
class PontoAdmin(admin.ModelAdmin):

    u"""Customização do admin de entradas de ponto."""

    def permanencias(self, obj):
        t = loader.get_template('tabela_permanencias_admin.html')
        return t.render({"obj": obj})
    permanencias.short_description = u'Permanências'

    def dia_calendario(self, obj):
        return "%s - %s" % (obj.dia.strftime("%d/%m/%Y"),
                            SEMANA[obj.dia.weekday()])
    dia_calendario.short_description = u'Dia'

    def trabalhado(self, obj):
        return format_minutes(obj.expediente_trabalhado)
    trabalhado.short_description = u'Trabalhado'

    def extras(self, obj):
        return format_minutes(obj.extra)
    extras.short_description = u'Extras'

    list_display = ("dia_calendario", "funcionario", "tipo", "permanencias",
                    "trabalhado", "extras")
    list_filter = ("dia", "funcionario", "tipo")
    inlines = (PermanenciaInline, AnexoInline)


admin.site.register(Funcionario)
admin.site.register(Feriado)
admin.site.register(Departamento)
