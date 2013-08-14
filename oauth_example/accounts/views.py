# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from datetime import datetime, timedelta
from urlparse import parse_qs

from accounts.models import (
    Account, get_twitter_service, get_facebook_service, get_youtube_service,
    FACEBOOK_CALLBACK_URL, YOUTUBE_CALLBACK_URL
)


@login_required
def account_list(request):
    account_list = Account.objects.filter(user=request.user)
    return render(
        request,
        'accounts/account_list.html', 
        {'account_list': account_list}
    )


@login_required
def twitter_new(request):
    # get session
    twitter = get_twitter_service()
    
    # get request token
    request_token, request_token_secret = twitter.get_request_token() 

    # store token secret in session
    request.session['oauth_token_secret'] = request_token_secret

    # redirect to twitter
    redirect_url = twitter.get_authorize_url(request_token)
    return redirect(redirect_url)


@login_required
def twitter_callback(request):
    # get/check params
    oauth_token = request.GET.get('oauth_token', None)
    oauth_verifier = request.GET.get('oauth_verifier', None)
    if not oauth_token or not oauth_verifier:
        messages.error(request, u'Ocorreu um erro ao adicionar a conta do twitter.')
        return redirect('accounts_account_list')

    # get/check token secret from session
    oauth_token_secret = request.session.get('oauth_token_secret', None)
    if not oauth_token_secret:
        messages.error(request, u'Ocorreu um erro ao adicionar a conta do twitter.')
        return redirect('accounts_account_list')

    # get session
    twitter = get_twitter_service()

    # fetch access token
    request_token, request_token_secret = twitter.get_access_token(
        oauth_token, 
        oauth_token_secret,
        data={'oauth_verifier': oauth_verifier}
    )

    # get information about user
    client = twitter.get_session(
        token=(request_token, request_token_secret)
    )
    data = client.get('account/verify_credentials.json').json()

    # create social account
    account, created = Account.objects.get_or_create(
        user=request.user, 
        provider='twitter', 
        provider_id=unicode(data['id']),
        provider_username=unicode(data['screen_name'])
    )
    account.oauth_token = request_token
    account.oauth_token_secret = request_token_secret
    account.save()

    # redirect
    messages.success(request, u'Conta do twitter adicionada com sucesso.')
    return redirect('accounts_account_list')


@login_required
def facebook_new(request):
    # get session
    facebook = get_facebook_service()

    # redirect to dialog
    params = {
        'redirect_uri': FACEBOOK_CALLBACK_URL
    }
    authorization_url = facebook.get_authorize_url(**params)
    return redirect(authorization_url)


@login_required
def facebook_callback(request):
    # get/check params
    redirect_uri = FACEBOOK_CALLBACK_URL
    code = request.GET.get('code', None)
    if not code:
        messages.error(request, u'Ocorreu um erro ao adicionar a conta do facebook.')
        return redirect('accounts_account_list')

    # get session
    facebook = get_facebook_service()

    # fetch tokens
    data = {'code':code, 'redirect_uri':redirect_uri}
    r = facebook.get_raw_access_token(data=data)
    credentials = parse_qs(r.content)
    access_token = credentials.get('access_token')[0]
    expires = credentials.get('expires')[0]

    # get information about user
    client = facebook.get_session(token=access_token)
    me = client.get('me').json()

    # create new social account
    account, created = Account.objects.get_or_create(
        user=request.user,
        provider='facebook', 
        provider_id=me['id'],
        provider_username=me['username']
    )
    account.oauth_token = access_token
    account.expires_in = datetime.now() + timedelta(seconds=int(expires))
    account.save()

    # redirect
    messages.success(request, u'Conta do facebook adicionada com sucesso.')
    return redirect('accounts_account_list')


@login_required
def youtube_new(request):
    # set scope
    scope = u'{0} {1} {2}'.format(
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email'
    )

    # create session
    youtube = get_youtube_service()

    # redirect to dialog
    params = {
        'scope': scope,
        'access_type':'offline',
        'approval_prompt':'force',
        'response_type': 'code',
        'redirect_uri': YOUTUBE_CALLBACK_URL
    }
    authorization_url = youtube.get_authorize_url(**params)
    return redirect(authorization_url)

@login_required
def youtube_callback(request):
    # get/check params
    redirect_uri = YOUTUBE_CALLBACK_URL
    code = request.GET.get('code', None)
    if not code:
        messages.error(request, u'Ocorreu um erro ao adicionar a conta do youtube.')
        return redirect('accounts_account_list')

    # create session
    youtube = get_youtube_service()

    # fetch tokens
    data = {'code':code, 'redirect_uri':redirect_uri, 'grant_type': 'authorization_code'}
    r = youtube.get_raw_access_token(data=data).json()
    access_token = r['access_token']
    expires = r['expires_in']
    refresh_token = r['refresh_token']

    # get information about user
    client = youtube.get_session(token=access_token)
    me = client.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

    # create new social account
    account, created = Account.objects.get_or_create(
        user=request.user,
        provider='youtube',
        provider_id=me['id'],
        provider_username=me['email']
    )
    account.refresh_token = refresh_token
    account.oauth_token = access_token
    account.expires_in = datetime.now() + timedelta(seconds=int(expires))
    account.save()

    # redirect
    messages.success(request, u'Conta do youtube adicionada com sucesso.')
    return redirect('accounts_account_list')
