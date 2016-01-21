# -*- encoding: utf-8 -*-

from django import template
from ponto.models import format_minutes

register = template.Library()


@register.filter(name='to_time')
def to_time(value):
    u"""Converte um valor de minutos em HHH:MM."""
    if not value:
        return ""
    return format_minutes(int(value))
