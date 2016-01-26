# -*- encoding: utf-8 -*-

from django import template
from ponto.models import format_minutes, SALDO_LIMITE

register = template.Library()


@register.filter(name='to_time')
def to_time(value):
    u"""Converte um valor de minutos em HHH:MM."""
    if not value and not value == 0:
        return ""
    return format_minutes(int(value))


@register.filter(name='alarm_color')
def alarm_color(value):
    u"""Retorna em rgb a cor do alarme de acordo com o saldo."""
    value = int(value or 0)
    cor = "rgba(255,0,0,%.1f)"
    limite = SALDO_LIMITE["min"]
    if value > 0:
        cor = "rgba(0,255,0,%.1f)"
        limite = SALDO_LIMITE["max"]

    alfa = (value / float(limite))
    return cor % alfa
