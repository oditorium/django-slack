"""
Slack integration Django app - Example Views

(c) Stefan Loesch, oditorium 2015-16. All rights reserved.
Licensed under the MIT License <https://opensource.org/licenses/MIT>.
"""
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .slack import *
from .slack import __version__
from .tests_slack import SlackViewExample

##############################################################################################
## API

@csrf_exempt
@slack_augment
def api1(slackrq):
    """manually pulls in the SlackViewExample object"""
    return SlackViewExample(slackrq).dispatch()

api2 = SlackViewExample.as_view()
	# api2 is fully equivalent to api ()
	
# api3: defined in urls.py

##############################################################################################
## VERSION

def version(request):
    return HttpResponse('Slack Library Version {}'.format(__version__))

##############################################################################################
## TEMPLATE RESPONSES 

@csrf_exempt
@slack_augment
def apit(slackrq):
    """renders a template response"""
    return JsonResponse(_template_response_1)


## TEMPLATES
	# see https://api.slack.com/docs/formatting

_template_response_1 = {
    "text": "By default one can write *text* _with_ Slack `markup` :smile:",
}

_template_response_2 = {
    "text": "Settings can be such that *text* _with_ Slack `markup` is ignored:smile:",
    "mrkdwn": False,
}

_template_response_3 ={
    "text": "some text",
    "attachments": [
        {
            "title": "Title",
            "pretext": "Pretext _supports_ mrkdwn",
            "text": "Testing *right now!*",
            "mrkdwn_in": ["text", "pretext"]
        },
    ]
}

_template_response_4 = {

    "text": "This is a response with an attachment, and this is the response text that comes before the attachment.",

    "attachments": [
        {
            "fallback": "Required plain-text summary of the attachment.",

            "color": "#36a64f",

            "pretext": "Optional text that appears above the attachment block",

            "author_name": "Stefan Loesch",
            "author_link": "https://twitter.com/oditorium",
            "author_icon": "https://pbs.twimg.com/profile_images/491834678383374336/eSPXgb6I_bigger.jpeg",

            "title": "Some Random Stock Photo",
            "title_link": "https://www.pexels.com/",

            "text": "Optional text that appears within the attachment",

            "fields": [
                {
                    "title": "Priority",
                    "value": "High",
                    "short": False
                }
            ],

            "image_url": "https://static.pexels.com/photos/57690/pexels-photo-57690-large.jpeg",
            "thumb_url": "https://static.pexels.com/photos/57690/pexels-photo-57690-small.jpeg"
        }
    ]
}    