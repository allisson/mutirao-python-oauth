# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url


urlpatterns = patterns(
    'accounts.views',
    # admin app
    url(r'^$', 'account_list', name='accounts_account_list'),

    url(r'^new/twitter/$', 'twitter_new', name='accounts_twitter_new'),

    url(r'^new/twitter/callback/$', 'twitter_callback', name='accounts_twitter_callback'),

    url(r'^new/facebook/$', 'facebook_new', name='accounts_facebook_new'),

    url(r'^new/facebook/callback/$', 'facebook_callback', name='accounts_facebook_callback'),

    url(r'^new/youtube/$', 'youtube_new', name='accounts_youtube_new'),

    url(r'^new/youtube/callback/$', 'youtube_callback', name='accounts_youtube_callback'),
)
