"""
testing code for a specific `slack.py` installation

NOTE
the testing code here is for a specific Slack installation and should be adapted; the
main point is that the external URL actually works, as of course a Slack integration
works with absolute URLs

The main URL is defined in `SlackInstallationTest.SLACK_URL`

(c) Stefan LOESCH, oditorium 2016. All Rights Reserved.
Licensed under the MIT License <https://opensource.org/licenses/MIT>.
"""
from django.test import TestCase
from django.conf import settings
#from django.core.urlresolvers import reverse_lazy, reverse
#from django.http import HttpResponse, JsonResponse
#from . import slack

#########################################################################################
## SLACK INSTALLATION TEST

class SlackInstallationTest(TestCase):

    SLACK_URL = '/slack/api'
    SLACK_ACCESS = {
        '-token-': '-team-',
    }


    ####################################################################
    ## TEST SLACK SETTINGS
    def test_slack_settings(s):
        """ensures that the Slack API settings are defined in the setting file"""
        # make sure there are SLACK_ACCESS settings defined
        s.assertTrue(len(settings.SLACK_ACCESS)>0)
        
        # make sure there are SLACK_USERS settings defined
        s.assertTrue(len(settings.SLACK_USERS)>=0)
        
    ####################################################################
    ## TEST SLACK URLS
    def test_slack_urls(s):
        """testing the Slack URL (if this test fails, check the URL!)"""
        c = s.client

        with s.settings(SLACK_ACCESS=s.SLACK_ACCESS):

            url = s.SLACK_URL
            resp = c.get(url)
            s.assertEqual(resp.status_code, 403)
            resp = c.post(url)
            s.assertEqual(resp.status_code, 403)
            resp = c.post(url, {'token': '-token-', 'team_id': '-team-', 'text': 'help'})
            s.assertEqual(resp.status_code, 200)
