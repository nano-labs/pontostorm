# -*- encoding: utf-8 -*-

#from django.core.cache import cache
from django.shortcuts import render


def generic_view(request):
    context = {'text': 'hello world'}
    return render(request, 'generic_template.html', context)
