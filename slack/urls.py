"""
Slack integration Django app - Example URLs

Copyright (c) Stefan LOESCH, oditorium 2016. All rights reserved.
Licensed under the Mozilla Public License, v. 2.0 <https://mozilla.org/MPL/2.0/>
"""
from django.conf.urls import url
from . import views
from .tests_slack import SlackViewExample

# Example URL patterns
urlpatterns = [
    url(r'^api1$', views.api1, name='api1'),
    url(r'^api2$', views.api2, name='api2'),
    url(r'^api3$', SlackViewExample.as_view(), name='api3'),
    url(r'^apit$', views.apit, name='apit'),
    url(r'^version$', views.version, name='version'),
]

# URL pattern required for tests in tests_slack.py to run properly
urlpatterns += [
    url(r'^slack_test_api$', SlackViewExample.as_view(), name='slack_test_api'),
]

# URL pattern required for the implementation tests in tests.py to run properly
# this is also the URL to which Slack should actually be pointed
urlpatterns += [
    url(r'^slack/api$', SlackViewExample.as_view(), name='slack_api'),
]



