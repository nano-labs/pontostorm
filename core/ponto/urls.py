from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    url(r'funcionario/$', 'ponto.views.funcionario', name='funcionario'),
)
