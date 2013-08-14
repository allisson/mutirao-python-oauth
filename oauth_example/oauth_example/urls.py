# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse_lazy as reverse


admin.autodiscover()


urlpatterns = patterns(
    '',
    # admin app
    url(r'^admin/', include(admin.site.urls)),

    # login/logout
    (r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/login/'}),

    # account app
    url(r'^accounts/', include('accounts.urls')),

    # index
    url(r'^$', RedirectView.as_view(url=reverse('accounts_account_list')), name='index'),
)


if settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )


urlpatterns += staticfiles_urlpatterns()
