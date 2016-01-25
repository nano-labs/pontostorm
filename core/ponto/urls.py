from django.conf.urls import patterns, include, url

from ponto.views import funcionario

urlpatterns = [
    # Examples:
    url(r'funcionario/$', funcionario, name='funcionario'),
]
