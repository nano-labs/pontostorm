# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('',
    url(r'generic_url/$',
        'generic_app.views.generic_view',
        name='generic_view'),
)
