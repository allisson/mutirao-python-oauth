# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from datetime import datetime, timedelta
from mock import patch

from accounts.models import Account


class TestIndexView(TestCase):

    def setUp(self):
        self.url = reverse('accounts_account_list')
        self.user = User.objects.create_user('user1', 'user1@email.com', '123456')
        self.account1 = Account.objects.create(
            user=self.user,
            provider='twitter',
            provider_id='1',
            provider_username='fulano1',
            oauth_token='708983112-iaDKF97Shz8cxZu9x86ZAj0MuYZcgNkRXNniXyzI',
            oauth_token_secret='u2spIuwwzaRtFvUHwaGFdoA7X4e1uiXXq81oWjJ9aos',
        )
        self.account2 = Account.objects.create(
            user=self.user,
            provider='facebook',
            provider_id='2',
            provider_username='fulano2',
            oauth_token='CAACo0zwBRUMBAH2Vs6GoKeeqqd4t0qxgOdqbSUF2iQLMps6pf9IKqtcV8ZAOQ9vlZA6SpqnXlxA2fdpZAbKj5s1XlTAihTWQKSCMKODCddJpZAc0EBGbIvWGxX4LqH9G1MsSIIE3xkM71UQcb10CfV9pevYUPI4ZD',
            expires_in=datetime.now() + timedelta(days=60)
        )
        self.account3 = Account.objects.create(
            user=self.user,
            provider='youtube',
            provider_id='3',
            provider_username='fulano3',
            oauth_token='ya29.AHES6ZShg0YNnCV1U2tdXGORa8RrRtXnvaBJ4_K2cD9iuns',
            refresh_token='1/00Gq_VIN9zRsdRFzhX8v-OrWgz8PfCA19ZSoRa1-Ih4',
            expires_in=datetime.now() + timedelta(hours=1)
        )
        self.client.login(username='user1', password='123456')

    def test_without_login(self):
        self.client.logout()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/login/?next=' + self.url)

    def test_render(self):
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.account1 in response.context['account_list'])
        self.assertTrue(self.account2 in response.context['account_list'])
        self.assertTrue(self.account3 in response.context['account_list'])


def twitter_get_request_token(*args, **kwargs):
    return u'request_token', u'secret_token'


class TestTwitterNewView(TestCase):
    
    def setUp(self):
        self.url = reverse('accounts_twitter_new')
        self.user = User.objects.create_user('user1', 'user1@email.com', '123456')
        self.client.login(username='user1', password='123456')

    def test_without_login(self):
        self.client.logout()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/login/?next=' + self.url)

    @patch('rauth.OAuth1Service.get_request_token', twitter_get_request_token)
    def test_render(self):
        response = self.client.get(self.url)
        self.assertEquals(
            response['Location'],
            'https://api.twitter.com/oauth/authorize?oauth_token=request_token'
        )


def twitter_get_access_token(*args, **kwargs):
    return u'oauth_token', u'oauth_token_secret'

def twitter_get(*args, **kwargs):

    class TwitterGet(object):

        def json(self):
            data = {}
            data['id'] = 38895958
            data['screen_name'] = 'theSeanCook'
            return data

    return TwitterGet()


def twitter_get_session(*args, **kwargs):
    return 'oauth_token_secret'


class TestTwitterCallbackView(TestCase):

    def setUp(self):
        self.url = reverse('accounts_twitter_callback')
        self.user = User.objects.create_user('user1', 'user1@email.com', '123456')
        self.client.login(username='user1', password='123456')

    def test_without_login(self):
        self.client.logout()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/login/?next=' + self.url)

    def test_render_without_tokens(self):
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('accounts_account_list'))
        self.assertContains(response, u'Ocorreu um erro ao adicionar a conta do twitter.')

        response = self.client.get(
            self.url, 
            {'oauth_token': 'oauth_token', 'oauth_verifier': 'oauth_verifier'}, 
            follow=True
        )
        self.assertRedirects(response, reverse('accounts_account_list'))
        self.assertContains(response, u'Ocorreu um erro ao adicionar a conta do twitter.')

    @patch('rauth.OAuth1Service.get_access_token', twitter_get_access_token)
    @patch('rauth.OAuth1Session.get', twitter_get)
    @patch('django.contrib.sessions.backends.signed_cookies.SessionStore.get', twitter_get_session)
    def test_render(self):
        session = self.client.session
        session['oauth_token_secret'] = 'oauth_token_secret'
        session.save()
        response = self.client.get(
            self.url, 
            {'oauth_token': 'oauth_token', 'oauth_verifier': 'oauth_verifier'},
            follow=True
        )
        self.assertRedirects(response, reverse('accounts_account_list'))
        self.assertContains(response, u'Conta do twitter adicionada com sucesso.')
        self.assertTrue(
            Account.objects.filter(
                provider='twitter',
                provider_id='38895958',
                provider_username='theSeanCook'
            )
        )


class TestFacebookNewView(TestCase):
    
    def setUp(self):
        self.url = reverse('accounts_facebook_new')
        self.user = User.objects.create_user('user1', 'user1@email.com', '123456')
        self.client.login(username='user1', password='123456')

    def test_without_login(self):
        self.client.logout()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/login/?next=' + self.url)

    def test_render(self):
        response = self.client.get(self.url)
        self.assertEquals(
            response['Location'],
            'https://www.facebook.com/dialog/oauth?redirect_uri=http%3A%2F%2Fmutiraopython.org%2Faccounts%2Fnew%2Ffacebook%2Fcallback%2F&client_id=185625198282051'
        )


def facebook_get_raw_access_token(*args, **kwargs):

    class FacebookGetRaw(object):

        @property
        def content(self):
            data = 'access_token=access_token&expires=5158944'
            return data

    return FacebookGetRaw()

def facebook_get(*args, **kwargs):

    class FacebookGet(object):

        def json(self):
            data = {}
            data['id'] = 38895958
            data['username'] = 'theSeanCook'
            return data

    return FacebookGet()


class TestFacebookCallbackView(TestCase):
    
    def setUp(self):
        self.url = reverse('accounts_facebook_callback')
        self.user = User.objects.create_user('user1', 'user1@email.com', '123456')
        self.client.login(username='user1', password='123456')

    def test_without_login(self):
        self.client.logout()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/login/?next=' + self.url)

    def test_render_without_code(self):
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('accounts_account_list'))
        self.assertContains(response, u'Ocorreu um erro ao adicionar a conta do facebook.')

    @patch('rauth.OAuth2Service.get_raw_access_token', facebook_get_raw_access_token)
    @patch('rauth.OAuth2Session.get', facebook_get)
    def test_render(self):
        response = self.client.get(self.url, {'code': 'code'}, follow=True)
        self.assertRedirects(response, reverse('accounts_account_list'))
        self.assertContains(response, u'Conta do facebook adicionada com sucesso.')
        self.assertTrue(
            Account.objects.filter(
                provider='facebook',
                provider_id='38895958',
                provider_username='theSeanCook'
            )
        )


class TestYoutubeNewView(TestCase):
    
    def setUp(self):
        self.url = reverse('accounts_youtube_new')
        self.user = User.objects.create_user('user1', 'user1@email.com', '123456')
        self.client.login(username='user1', password='123456')

    def test_without_login(self):
        self.client.logout()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/login/?next=' + self.url)

    def test_render(self):
        response = self.client.get(self.url)
        self.assertEquals(
            response['Location'],
            'https://accounts.google.com/o/oauth2/auth?redirect_uri=http%3A%2F%2Fmutiraopython.org%2Faccounts%2Fnew%2Fyoutube%2Fcallback%2F&response_type=code&client_id=863393693267.apps.googleusercontent.com&approval_prompt=force&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email&access_type=offline'
        )


def youtube_get_raw_access_token(*args, **kwargs):

    class YoutubeGetRaw(object):

        def json(self):
            data = {
                'access_token': 'access_token',
                'expires_in': 5158944,
                'refresh_token': 'refresh_token'
            }
            return data

    return YoutubeGetRaw()

def youtube_get(*args, **kwargs):

    class YoutubeGet(object):

        def json(self):
            data = {}
            data['id'] = 38895958
            data['email'] = 'user@email.com'
            return data

    return YoutubeGet()


class TestYoutubeCallbackView(TestCase):
    
    def setUp(self):
        self.url = reverse('accounts_youtube_callback')
        self.user = User.objects.create_user('user1', 'user1@email.com', '123456')
        self.client.login(username='user1', password='123456')

    def test_without_login(self):
        self.client.logout()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/login/?next=' + self.url)

    def test_render_without_code(self):
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('accounts_account_list'))
        self.assertContains(response, u'Ocorreu um erro ao adicionar a conta do youtube.')

    @patch('rauth.OAuth2Service.get_raw_access_token', youtube_get_raw_access_token)
    @patch('rauth.OAuth2Session.get', youtube_get)
    def test_render(self):
        response = self.client.get(self.url, {'code': 'code'}, follow=True)
        self.assertRedirects(response, reverse('accounts_account_list'))
        self.assertContains(response, u'Conta do youtube adicionada com sucesso.')
        self.assertTrue(
            Account.objects.filter(
                provider='youtube',
                provider_id='38895958',
                provider_username='user@email.com'
            )
        )
