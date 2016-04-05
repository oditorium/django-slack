"""
minimal settings file - DO NOT RUN IN PRODUCTION!
"""


###################################################
## SLACK-SPECIFIC SETTINGS (REQUIRED)
SLACK_ACCESS = {
    # the keys in this dict correspond to the Slack access tokens that have been generated
    # in the Slack integration page (for each Slack team that uses this plugin the key must
    # exist in the above array, lest access will be denied)
    'ULtA9InSFLTGpEz0EsMkVBKl': True,
}


###################################################
## GENERAL SETTINGS
import os
import dj_database_url as dburl

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'f&pppjiw^qpup1_*02+)yeoli3-p@t(-+gwo7s&g*akgv=bfis'
DEBUG = True
ALLOWED_HOSTS = ['*']

def environ(key):
    """returns True if the key exists in os.environ[] and it is not false'ish"""
    if not key in os.environ.keys(): return False
    if os.environ[key] and os.environ[key] != '0': return True
    return False


INSTALLED_APPS = [
    #'django.contrib.admin',
    #'django.contrib.auth',
    #'django.contrib.contenttypes',
    #'django.contrib.sessions',
    #'django.contrib.messages',
    'django.contrib.staticfiles',
    'slack',
]

if environ('SSLSERVER'):
    # to launch the sslserver use the following command:
    #    export SSLSERVER=1
    #    export CERTS=/path/to/my/cert
    #    python3 manage.py runsslserver 0.0.0.0:443 --certificate $CERTS.crt --key $CERTS.key
    INSTALLED_APPS += ['sslserver']

MIDDLEWARE_CLASSES = [
    #'django.middleware.security.SecurityMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
    #'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                #'django.contrib.auth.context_processors.auth',
                #'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = '_project.wsgi.application'


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR + '/staticfiles'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

###################################################
## HEROKU SPECIFIC SETTINGS

if environ('HEROKU'):
    
    # this assumes the on Heroku an environment called 'HEROKU' is set and true'ish
    # the below code adusts the settings accordingly
    # 
    # to create an app on Heroku and set the environment set
    #   heroku create
    #   git push heroku +master
    #   heroku config:set HEROKU=1
    #   heroku run python manage.py migrate
    DATABASES['default'] =  dburl.config()
    DATABASES['default']['CONN_MAX_AGE'] = 500
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'
    WSGI_APPLICATION = '_project.wsgi-whitenoise.application'



