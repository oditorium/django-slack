"""
testing code for `slack.py`

(c) Stefan LOESCH, oditorium 2016. All Rights Reserved.
Licensed under the MIT License <https://opensource.org/licenses/MIT>.
"""
from django.test import TestCase, RequestFactory
from django.conf import settings
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponse, JsonResponse

import json

from . import slack

SLACK_VERSION = "2.1"

#########################################################################################
## SUNDRY HELPER FUNCTIONS AND OBJECTS


@slack.slack_augment
def _function_hello_world_text(request):
    return "Hello World"

@slack.slack_augment
def _function_hello_world_response(request):
    return slack.SlackResponseText("Hello World")

## SLACK REQUEST TEST
class SlackRequestDummy(slack.SlackRequestMixin):
    """a little hack for our slack request"""
    @property
    def slack_text(s):
        return s.text

## SLACK HANDLER EXAMPLE
class SlackViewExample(slack.SlackViewBase):
    """an example for a Slack handler object (for testing)"""

    def run_echo(s, parser):
        """a simple echo handler (returns the remainder)"""
        parser.add_argument('--uppercase', '-u', action='count') # https://docs.python.org/3/library/argparse.html#action
        parse_obj = parser.run()
        out = "-".join(parse_obj.posn)
        if parse_obj.uppercase: out=out.upper()
        return slack.SlackResponseText("you said: {}".format(out))

    @slack.positional_args
    def run_echob(s, posn):
        out = ":".join(posn)
        return slack.SlackResponseText("you said: {}".format(out))

    def run_show(s, parser):
        """shows off"""
        att = slack.Attachment("that's a show-off attachment")
        att.add(att.Author("Stefan Loesch", "https://twitter.com/oditorium",
                "https://pbs.twimg.com/profile_images/491834678383374336/eSPXgb6I_bigger.jpeg"))
        att.add(att.Title("Some Random Stock Photo", "https://www.pexels.com/"))
        att.add(att.Image("https://static.pexels.com/photos/57690/pexels-photo-57690-large.jpeg", 
                "https://static.pexels.com/photos/57690/pexels-photo-57690-small.jpeg"))
        att.add(att.Text("This text appears within the attachment!", "This text appears above the attachment!"))
        return slack.SlackResponse("Just showing off!", att)

    def run_version(s, parser):
        return slack.SlackResponseText("""Slack library version {}""".format(slack.__version__))

    def run_help(s, parser):
        return slack.SlackResponseText("""try the 'echo', 'show' or 'version' subcommands""")

SlackViewExample.alias("v", "version")
SlackViewExample.alias("e", "echo")


# TEST API VIEW
test_api_view = SlackViewExample.as_view()


#########################################################################################
## SLACK API OBJECTS TEST
class SlackAPIObjectsTest(TestCase):
    """testing the Slack API without need for a working URL"""

    SLACK_ACCESS = {
        '-token-': '-team-',
    }
    SLACK_USERS = {
        'user-0':  (),                           # no permissions (whatever that means)
        'user-r':  (slack.READ,),                # read permissions
        'user-rx': (slack.READ|slack.EXECUTE,),  # read and execute permissions
        'user-x':  (slack.EXECUTE,),             # only execute permissions (whatever that means)
    }

    def setUp(s):
        s.factory = RequestFactory()
        s.request = s.factory.post('/url/does/not/matter', {
            'token': '-token-',
            'command': '-command-',
            'text': '-text-',
            'user_id': '-user_id-',
            'user_name': '-user_name-',
            'channel_id': '-channel_id-',
            'channel_name': '-channel_name-',
            'team_id': '-team-',
            'team_domain': '-team_domain-',
            'response_url': '-response_url-',
        })


    ####################################################################
    ## TEST SLACK VERSION
    def test_slack_version(s):
        """ensure the version number is correct"""
        s.assertEqual(slack.__version__, SLACK_VERSION)


    ####################################################################
    ## TEST SLACK AUGMENT
    def test_slack_augment(s):
        """testing the @slack_augment decorator"""
        with s.settings(SLACK_ACCESS=s.SLACK_ACCESS, SLACK_USERS=s.SLACK_USERS):

            resp = _function_hello_world_text(s.request)
            s.assertTrue(isinstance(resp, str))
            s.assertEqual(resp, "Hello World")

            resp = _function_hello_world_response(s.request)
            s.assertTrue(isinstance(resp, JsonResponse))
            #s.assertEqual(resp.content, b"Hello World")
            #s.assertEqual(resp.content_type, "text/plain")
            s.assertEqual(resp.status_code, 200)


    ####################################################################
    ## TEST SLACK RESPONSE
    def test_slack_response_text(s):
        """testing the SlackResponseText object"""
        resp = slack.SlackResponseText("the response")
        s.assertEqual (resp.as_dict()['text'], "the response")
        s.assertEqual (resp.as_dict()['response_type'], "ephemeral")
        s.assertEqual (json.loads(resp.as_json()), resp.as_dict())
        s.assertEqual (resp.as_json_response().status_code, 200)
        s.assertTrue (isinstance (resp.as_json_response(), JsonResponse))

        resp = slack.SlackResponseText("the response", in_channel=True)
        s.assertEqual (resp.as_dict()['text'], "the response")
        s.assertEqual (resp.as_dict()['response_type'], "in_channel")
        s.assertEqual (json.loads(resp.as_json()), resp.as_dict())
        s.assertEqual (resp.as_json_response().status_code, 200)
        s.assertTrue (isinstance (resp.as_json_response(), JsonResponse))

    ####################################################################
    ## TEST SLACK ATTACHMENT OBJECTS
    def test_slack_attachment(s):
        """tests the various Slack attachment objects"""

        text=slack.Text('mytext', 'pretext')
        author=slack.Author('name', 'link', 'icon')
        title=slack.Title('title', 'link')
        image=slack.Image('image', 'thumb')
        s.assertEqual(text.as_dict(), {'text': 'mytext', 'pretext': 'pretext'})
        s.assertEqual(author.as_dict(),{"author_name": 'name', "author_link": 'link',"author_icon": 'icon'})
        s.assertEqual(title.as_dict(), {"title": 'title', "title_link": 'link'})
        s.assertEqual(image.as_dict(), {"image_url": 'image', "thumb_url": 'thumb'})

        attach=slack.Attachment('fallback', [text, author, title, image])
        thedict = attach.as_dict()
        s.assertEqual(thedict['fallback'], "fallback")
        s.assertEqual(thedict['text'], "mytext")
        s.assertEqual(thedict['author_link'], "link")
        s.assertEqual(thedict['title'], "title")
        s.assertEqual(thedict['image_url'], "image")

        attach=slack.Attachment('fallback')
        s.assertEqual(attach.as_dict(), {'fallback': 'fallback'})
        attach.add(text)
        s.assertEqual(attach.as_dict(), {'fallback': 'fallback', 'text': 'mytext', 'pretext': 'pretext'})
        attach.add([author, title, image])
        thedict = attach.as_dict()
        s.assertEqual(thedict['author_link'], "link")
        s.assertEqual(thedict['title'], "title")
        s.assertEqual(thedict['image_url'], "image")

        s.assertEqual(attach.Text, slack.Text)
        s.assertEqual(attach.Author, slack.Author)
        s.assertEqual(attach.Title, slack.Title)
        s.assertEqual(attach.Image, slack.Image)


    ####################################################################
    ## TEST SLACK RESPONSE
    def test_slack_response(s):
        """tests the various Slack response objects"""
        att1=slack.Attachment('Attachment 1')
        att2=slack.Attachment('Attachment 2')
        
        resp=slack.SlackResponse('text')
        s.assertEqual(resp.as_dict(), {'text': 'text', 'response_type': 'ephemeral', 'attachments': []})

        resp=slack.SlackResponse('text', att1)
        s.assertEqual(resp.as_dict(), {'text': 'text', 'response_type': 'ephemeral', 'attachments': [{'fallback': 'Attachment 1'}]})
        
        resp=slack.SlackResponse('text', [att1])
        s.assertEqual(resp.as_dict(), {'text': 'text', 'response_type': 'ephemeral', 'attachments': [{'fallback': 'Attachment 1'}]})

        resp=slack.SlackResponse('text', [att1,att2])
        s.assertEqual(resp.as_dict()['attachments'][1], {'fallback': 'Attachment 2'})

        resp=slack.SlackResponse('text')
        resp.add(att1)
        s.assertEqual(resp.as_dict(), {'text': 'text', 'response_type': 'ephemeral', 'attachments': [{'fallback': 'Attachment 1'}]})

        resp=slack.SlackResponse('text')
        resp.add([att1])
        s.assertEqual(resp.as_dict(), {'text': 'text', 'response_type': 'ephemeral', 'attachments': [{'fallback': 'Attachment 1'}]})

        resp=slack.SlackResponse('text')
        resp.add([att1,att2])
        s.assertEqual(resp.as_dict()['attachments'][1], {'fallback': 'Attachment 2'})


    ####################################################################
    ## TEST SLACK URL
    def test_slack_url(s):
        """ensure the slack url is produced correctly"""
        r=slack.SlackResponse('text')
        s.assertEqual(r.url('https://my.server.com', "myserver"), "<https://my.server.com|myserver>")
        s.assertEqual(r.url('https://my.server.com'), "<https://my.server.com>")
        s.assertEqual(slack.url('https://my.server.com', "myserver"), "<https://my.server.com|myserver>")
        s.assertEqual(slack.url('https://my.server.com'), "<https://my.server.com>")

    ####################################################################
    ## TEST SLACK HANDLER BASE
    def test_slack_view_base(s):
        """testting the SlackViewBase object"""
        
        request = SlackRequestDummy()
        
        request.text = "thecmd and remainder"
        view = slack.SlackViewBase(request)
        response = view.dispatch()
        s.assertEqual(response.response_text, "unknown subcommand 'thecmd'; try 'help'")
        parser = view._parser("and remainder")
        parse_obj = parser.run()
        s.assertEqual(parse_obj.error, False)
        s.assertEqual(parse_obj.posn, ["and", "remainder"])

        request.text = "help"
        response = slack.SlackViewBase(request).dispatch()
        s.assertEqual(response.response_text, "help functionality is not currently implemented")


    ####################################################################
    ## TEST SLACK VIEW EXAMPLE
    def test_slack_view_example(s):
        """testing the SlackViewExample object"""

        request = SlackRequestDummy()

        request.text = "echo I say hello"
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "you said: I-say-hello")               

        request.text = "ECHO I say hello"
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "you said: I-say-hello") 

        request.text = "e I say hello"
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "you said: I-say-hello") 

        request.text = "E I say hello"
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "you said: I-say-hello") 

        request.text = "echo -u I say hello"
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "you said: I-SAY-HELLO")   

        request.text = "echo --uppercase I say hello"
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "you said: I-SAY-HELLO")   

        request.text = "echob I say hello"
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "you said: I:say:hello")   

        request.text = "ECHOO I say hello"
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "unknown subcommand 'ECHOO'; try 'help'") 

        request.text = "cmd"
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "unknown subcommand 'cmd'; try 'help'") 

        request.text = ""
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "unknown subcommand ''; try 'help'") 

        request.text = "     "
        response = SlackViewExample(request).dispatch()
        s.assertEqual(response.response_text, "unknown subcommand ''; try 'help'")


#########################################################################################
## SLACK API TEST
class SlackAPITest(TestCase):
    """testing the Slack API (needs a working URL)"""

    SLACK_ACCESS = {
        'token-with-team': 'my-team-id',
        'token-without-team': True,
    }
    SLACK_USERS = {
        'user-0':  (),                           # no permissions (whatever that means)
        'user-r':  (slack.READ,),                # read permissions
        'user-rx': (slack.READ|slack.EXECUTE,),  # read and execute permissions
        'user-x':  (slack.EXECUTE,),             # only execute permissions (whatever that means)
    }

    def setUp(s):
        try: s.url = reverse('slack_test_api')
        except: s.url = None

    ####################################################################
    ## TEST URL DEFINED
    def test_url_defined(s):
        try: 
            if settings.SLACK_IGNORE_MISSING_URL_FOR_TESTS: return
        except: pass
        if not s.url: print("""
{0}
the Slack API URL for testing has not been defined, so a number of the tests wont run!

in order to make it work, please insert eg the following code into a suitable `urls.py` file
(please ensure that this url file is part of the global namespace!)

    from tests_slack import SlackViewExample
    urlpatterns += [
        url(r'^slack_test_api$', SlackViewExample.as_view(), name='slack_test_api'),
    ]
{0}
""".format("+"*100))
        # if this assertion fails this means that the URL has not been defined
        s.assertTrue(s.url != None)

        
    ####################################################################
    ## TEST API ACCESS
    def test_api_access(s):
        """making sure API access only granted with proper tokens"""

        if not s.url: return # checked in test_url_defined
        c = s.client
 
        with s.settings(SLACK_ACCESS=s.SLACK_ACCESS, SLACK_USERS=s.SLACK_USERS):
            
            # GET
            response = c.get(s.url)
            #print ("{1.status_code} {1.content}".format(s.url, response))
            s.assertEqual(response.status_code, 403)
            s.assertContains(response, "denied", status_code=403)
    
            # GET correct token, correct team
            response = c.get(s.url, {'token': 'token-with-team', 'team_id': 'my-team-id'})
            s.assertContains(response, "denied", status_code=403)

            # POST no arguments
            response = c.post(s.url, {})
            #print ("{1.status_code} {1.content}".format(s.url, response))
            s.assertContains(response, "denied", status_code=403)
            
            # POST wrong token
            response = c.post(s.url, {'token': 'wrong-token', 'team_id': 'my-team-id'})
            s.assertContains(response, "denied", status_code=403)

            # POST correct token, wrong team
            response = c.post(s.url, {'token': 'token-with-team', 'team_id': 'wrong-team-id'})
            s.assertContains(response, "denied", status_code=403)

            # POST correct token, correct team
            response = c.post(s.url, {'token': 'token-with-team', 'team_id': 'my-team-id', 'text': 'help'})
            s.assertEqual(response.status_code, 200)
            #s.assertTrue('text' in response.json().keys())
            
            # POST correct no-team token, no team
            response = c.post(s.url, {'token': 'token-without-team', 'text': 'help'})
            s.assertEqual(response.status_code, 200)
            #s.assertTrue('text' in response.json().keys())
            
            # POST correct no-team token, wrong team
            response = c.post(s.url, {'token': 'token-without-team', 'team_id': 'wrong-team-id', 'text': 'help'})
            s.assertEqual(response.status_code, 200)
            #s.assertTrue('text' in response.json().keys())


    def test_api_commands(s):
        """test some of the API commands (the Example Handler must be connected!)"""

        if not s.url: return # checked in test_url_defined
        c = s.client
        with s.settings(SLACK_ACCESS=s.SLACK_ACCESS, SLACK_USERS=s.SLACK_USERS):

            # help
            response = c.post(s.url, {'token': 'token-without-team', 'text': 'help'})
            s.assertEqual(response.status_code, 200)

            # echo
            response = c.post(s.url, {'token': 'token-without-team', 'text': 'echo 123 test'})
            s.assertEqual(response.status_code, 200)

            # show
            response = c.post(s.url, {'token': 'token-without-team', 'text': 'show'})
            s.assertEqual(response.status_code, 200)

      
    ####################################################################
    ## TEST API FUNCTIONALITY
    def test_api_functionality(s):
        """making sure the API works as it should"""
        if not s.url: return # checked in test_url_defined
        c = s.client
        with s.settings(SLACK_ACCESS=s.SLACK_ACCESS, SLACK_USERS=s.SLACK_USERS):

            # dummy, to be changed 
            response = c.post(s.url, {'token': 'token-without-team', 'team_id': 'wrong-team-id', 'text': 'help'})
            #print ("{1.status_code} {1.content}".format(s.url, response))

            s.assertEqual(response.status_code, 200)
            #s.assertTrue('text' in response.json().keys())



