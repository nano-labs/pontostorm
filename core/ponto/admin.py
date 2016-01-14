# -*- encoding: utf-8 -*-
"""Provavelmente o unico admin do projeto."""

from django.contrib import admin

# Register your models here.

from ponto.models import (Funcionario, Feriado, Ponto, Departamento)


admin.site.register(Ponto)
admin.site.register(Funcionario)
admin.site.register(Feriado)
admin.site.register(Departamento)
