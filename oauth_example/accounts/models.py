# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from rauth import OAuth1Service, OAuth2Service
import requests
from datetime import datetime, timedelta


# Api keys
TWITTER_KEY = settings.TWITTER_KEY
TWITTER_SECRET = settings.TWITTER_SECRET
TWITTER_CALLBACK_URL = settings.TWITTER_CALLBACK_URL

FACEBOOK_APP_ID = settings.FACEBOOK_APP_ID 
FACEBOOK_APP_SECRET = settings.FACEBOOK_APP_SECRET
FACEBOOK_CALLBACK_URL = settings.FACEBOOK_CALLBACK_URL

YOUTUBE_CLIENT_ID = settings.YOUTUBE_CLIENT_ID 
YOUTUBE_CLIENT_SECRET = settings.YOUTUBE_CLIENT_SECRET
YOUTUBE_CALLBACK_URL = settings.YOUTUBE_CALLBACK_URL


# rauth sessions
def get_twitter_service():
    twitter = OAuth1Service(
        consumer_key=TWITTER_KEY,
        consumer_secret=TWITTER_SECRET,
        name='twitter',
        access_token_url='https://api.twitter.com/oauth/access_token',
        authorize_url='https://api.twitter.com/oauth/authorize',
        request_token_url='https://api.twitter.com/oauth/request_token',
        base_url='https://api.twitter.com/1.1/'
    )
    return twitter

def get_facebook_service():
    facebook = OAuth2Service(
        client_id=FACEBOOK_APP_ID,
        client_secret=FACEBOOK_APP_SECRET,
        name='facebook',
        authorize_url='https://www.facebook.com/dialog/oauth',
        access_token_url='https://graph.facebook.com/oauth/access_token',
        base_url='https://graph.facebook.com/'
    )
    return facebook

def get_youtube_service():
    youtube = OAuth2Service(
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        name='youtube',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        base_url='https://www.googleapis.com/youtube/v3/'
    )
    return youtube


PROVIDER_CHOICES = (
    (u'twitter', u'Twitter'),
    (u'facebook', u'Facebook'),
    (u'youtube', u'Youtube'),
)


class Account(models.Model):

    user = models.ForeignKey(
        User,
        verbose_name=u'Usuário',
        related_name='accounts'
    )

    provider = models.CharField(
        u'Provedor',
        max_length=20,
        db_index=True,
        choices=PROVIDER_CHOICES
    )

    provider_id = models.CharField(
        u'Id no Provedor',
        max_length=100
    )

    provider_username = models.CharField(
        u'Login no Provedor',
        max_length=100
    )

    oauth_token = models.CharField(
        u'OAuth Token',
        max_length=200
    )

    oauth_token_secret = models.CharField(
        u'OAuth Token Secret',
        max_length=200
    )

    refresh_token = models.CharField(
        u'Refresh Token',
        max_length=200
    )

    expires_in = models.DateTimeField(
        u'Expires in',
        null=True
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'Provedor: {0} - Login: {1}'.format(
            self.provider, self.provider_username
        )

    class Meta:
        verbose_name = u'Conta'
        verbose_name_plural = u'Contas'

    def is_expired(self):
        if self.expires_in:
            return datetime.now() > self.expires_in - timedelta(minutes=10)
        return False

    def get_client(self):
        client = None

        if self.provider == 'twitter':
            client = get_twitter_service().get_session(
                token=(self.oauth_token, self.oauth_token_secret)
            )
        elif self.provider == 'facebook':
            client = get_facebook_service().get_session(
                token=self.oauth_token
            )
        elif self.provider == 'youtube':
            self.google_refresh_token()
            client = get_youtube_service().get_session(
                token=self.oauth_token
            )

        return client

    def google_refresh_token(self):
        client_id = YOUTUBE_CLIENT_ID
        client_secret = YOUTUBE_CLIENT_SECRET
        if self.is_expired():
            # make payload and set url
            payload = {
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            url = 'https://accounts.google.com/o/oauth2/token'

            # make request
            r = requests.post(url, data=payload)
            data = r.json()
            self.access_token = data['access_token']
            self.expires_in = datetime.now() + timedelta(seconds=int(data['expires_in']))

            # save social account
            self.save()
