"""
slack integration helpers


This module provides classes to deal with Slack requests that mirror those provided by Django
to deal with regular http requests

- **Request Objects** encapsulate the information provided in the Slack API call

- **Response Objects** encapsulate a response provided to Slack

- **View Objects** are the workhorse objects that take a Slack request object, and that return
    a Slack response object

EXAMPLE
    see top of the file `tests_slack.py`
    
SETTINGS

this module requires the following settings:

    # SLACK_ACCESS determines whether or not a certain Slack request is genuine; there are two ways
    # to encode this: either a team and a token is given, in which case both the token and the team ID
    # must be matched, or only a token is given in which case every team with this token works

    SLACK_ACCESS = {
        '758ghnsw487ghonivnw574htgbeohjlg' : 'T0ET1EF89', # token: team
        '435uytbhkjgb487gy454w5hgb45hbgw4' : True, # token only
    }

    # SLACK_USERS is a per-user permission management tool; it is not enforced at the library level,
    # but the actual Slack views can implement restrictions based on this (note: chances are that
    # this will change in a future version; at the moment the SlackRequest object provides some
    # support, but this should be considered deprecated)
    SLACK_USERS = {
        # userid:
        'id':      [slack.READ]
    }

INTEGRATION

go to https://-yourteam-.slack.com/apps/build/custom-integration to configure the integration

LINKS

    <http://slackhq.com/post/117724460915/a-beginners-guide-to-your-first-bot>
    <https://github.com/mccreath/isitup-for-slack/blob/master/docs/TUTORIAL.md>
    <https://api.slack.com/docs/formatting>
    <https://api.slack.com/custom-integrations>
    <https://api.slack.com/docs/attachments>
    <https://api.slack.com/docs/unfurling>
    <https://get.slack.help/hc/en-us/articles/202288908-How-can-I-add-formatting-to-my-messages->

COPYRIGHT & LICENSE

(c) Stefan LOESCH, oditorium 2015-16. All Rights Reserved.
Licensed under the MIT License <https://opensource.org/licenses/MIT>.
"""
__version__="1.5"
__version_dt__="2015-03-26"
__copyright__="Stefan LOESCH 2016"
__license__="MIT License"


from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.core.handlers.wsgi import WSGIRequest
from django.views.decorators.csrf import csrf_exempt


import re
import argparse
import json
from functools import reduce

##############################################################################################
## CONSTANTS

NOACCESS = 0
READ = 1
EXECUTE = 2


##############################################################################################
## SUNDRY HELPER FUNCTIONS AND OBJECTS

## ARGUMENT PARSER
class _ArgumentParser(argparse.ArgumentParser):
    """
    subclasses the argument parser to suppress the error message

    see http://stackoverflow.com/questions/18651705/argparse-unit-tests-suppress-the-help-message
    """
    def error(s, message):
        s._error = message
        raise SystemExit(message)

    def print_help(s, file=None):
        s._error = ""
        raise SystemExit()

def _Http403(message=None):
    """returns a simple 403 status response"""
    if message == None: message="access denied"
    return HttpResponse(message, status=403)

###################################################################################################
## SLACK REQUEST SECTION
###################################################################################################

    # Slack Requests are similar to Django requests

##############################################################################################
## SLACK REQUEST MIXIN
class SlackRequestMixin():
    """
    defines extra fields that Slack request provides over and beyond a Django request (see `SlackRequest`)
    """

    @property
    def slack_token(s):
        """token"""
        raise NotImplementedError

    @property
    def slack_command(s):
        """command"""
        raise NotImplementedError

    @property
    def slack_text(s):
        """text"""
        raise NotImplementedError

    @property
    def slack_uid(s):
        """user ID"""
        raise NotImplementedError

    @property
    def slack_uname(s):
        """user name"""
        raise NotImplementedError

    @property
    def slack_cid(s):
        """channel ID"""
        raise NotImplementedError

    @property
    def slack_cname(s):
        """channel name"""
        raise NotImplementedError

    @property
    def slack_cname(s):
        """channel name"""
        raise NotImplementedError

    @property
    def slack_tid(s):
        """team ID"""
        raise NotImplementedError

    @property
    def slack_tdomain(s):
        """team domain"""
        raise NotImplementedError

    @property
    def slack_rurl(s):
        """response URL"""
        raise NotImplementedError



##############################################################################################
## SLACK REQUEST OBJECT

class SlackRequest(SlackRequestMixin, WSGIRequest):
    """
    augmented HttpRequest object for use in Slack requests

    - the `augment` method augments an `HttpRequest` object into `SlackRequest` object (see also
        the @slack_augment decorator in this respect)
        
    - the `slack_xxx` methods (overriding those in `SlackRequestMixin` allow access to the data
        that has been provided by Slack
        
    - the `slack_access` method should be considered deprecated

    """


    ##############################################################
    ## SLACK ACCESS
    def slack_access(s, level=READ):
        """
        checks whether the user has access at the given level (DEPRECATED!)

        RETURNS
            True if access, False if not (if level == NOACCESS always returns False)

        NOTE
            per-user access levels are read from settings.SLACK_USERS
        """
        try: slack_access_level = settings.SLACK_USERS[s.slack_uid]
        except: return False
        return (slack_access_level & level) != 0


    ##############################################################
    ## AUGMENT

    @classmethod
    def augment(s, request):
        """augments a HttpRequest object into a SlackRequest"""
        request.__class__ = s
        return None


    ##############################################################
    ## PROPERTIES

    @property
    def slack_token(s):
        """token"""
        return s.POST['token']

    @property
    def slack_command(s):
        """command"""
        return s.POST['command']

    @property
    def slack_text(s):
        """
        text

        note: Slack replaces -- with em-dashes; this property undoes this replacement
        (meaning _all_ em-dashed are replaced with '--')
        """
        return s.POST['text'].replace('—', '--')

    @property
    def slack_uid(s):
        """user ID"""
        return s.POST['user_id']

    @property
    def slack_uname(s):
        """user name"""
        return s.POST['user_name']

    @property
    def slack_cid(s):
        """channel ID"""
        return s.POST['channel_id']

    @property
    def slack_cname(s):
        """channel name"""
        return s.POST['channel_name']

    @property
    def slack_tid(s):
        """team ID"""
        return s.POST['team_id']

    @property
    def slack_tdomain(s):
        """team domain"""
        return s.POST['team_domain']

    @property
    def slack_rurl(s):
        """response URL"""
        return s.POST['response_url']


###################################################################################################
## SLACK RESPONSE SECTION
###################################################################################################


##############################################################################################
## SLACK ATTACHMENT COMPONENTS (for response attachments)

## BASE
class AttachmentBase():
    """abstract base class for an attachment component"""
    def as_dict(s):
        """returns the component items as dict"""
        raise NotImplemented

## TEXT
class Text(AttachmentBase):
    """Slack attachment component: text"""
    def __init__(s, text, pretext=None):
        s.text = text
        if pretext == None: pretext=''
        s.pretext = pretext
    def as_dict(s):
        return {"text": s.text, "pretext": s.pretext}

## AUTHOR
class Author(AttachmentBase):
    """Slack attachment component: author"""
    def __init__(s, name, link, icon):
        s.name = name
        s.link = link
        s.icon = icon
    def as_dict(s):
        return {"author_name": s.name, "author_link": s.link,"author_icon": s.icon,}

## TITLE
class Title(AttachmentBase):
    """Slack attachment component: title"""
    def __init__(s, title, link):
        s.title = title
        s.link = link
    def as_dict(s):
        return {"title": s.title, "title_link": s.link}

## IMAGE
class Image(AttachmentBase):
    """Slack attachment component: image"""
    def __init__(s, image, thumb):
        s.image = image
        s.thumb = thumb
    def as_dict(s):
        return {"image_url": s.image, "thumb_url": s.thumb}

##############################################################################################
## SLACK ATTACHMENT
class Attachment(AttachmentBase):
    """represents a single Slack attachment, made up from components"""
    def __init__(s, fallback, components=None):
        s.fallback = fallback
        if components == None: components = []
        s.components = components

    Text = Text
    Author = Author
    Title = Title
    Image = Image

    def add(s, components):
        """appends one or more components"""
        if isinstance(components, AttachmentBase): components = [components]
        s.components.extend(components)

    def as_dict(s):
        thedict = {'fallback': s.fallback}
        for c in s.components: thedict.update(c.as_dict())
        return thedict

##############################################################################################
## SLACK RESPONSE

## SLACK RESPONSE BASE
class SlackResponseBase():
    """abstract base class for Slack response"""

    ## AS DICT
    def as_dict(s):
        """returns the response as a python dict"""
        raise NotImplemented

    ## AS JSON
    def as_json(s):
        """returns the response as a json string"""
        return json.dumps(s.as_dict())

    ## AS JSON RESPONSE
    def as_json_response(s):
        """returns the response as a Django JsonResponse object"""
        return JsonResponse(s.as_dict(), safe=False)

    ## URL
    @staticmethod
    def url(url, friendly=None):
        """returns url in proper format for slack markdown"""
        if not friendly: return "<{}>".format(url)
        return "<{}|{}>".format(url, friendly)


url = SlackResponseBase.url
    # url method is being made available at module level for convenience


## SLACK RESPONSE TEXT
class SlackResponseText(SlackResponseBase):
    """implements a text-only Slack response"""
    def __init__(s, response_text):
        s.response_text = response_text

    def as_dict(s):
        return {'text': str(s.response_text)}


## SLACK RESPONSE
class SlackResponse(SlackResponseBase):
    """implements a Slack response with text and attachment(s)"""
    def __init__(s, text, attachments=None):
        s.text = text
        if attachments == None: attachments = []
        if isinstance(attachments, Attachment): attachments = [attachments]
        s.attachments = attachments

    def add(s, attachments):
        """adds one ore more attachments"""
        if isinstance(attachments, Attachment): attachments = [attachments]
        s.attachments.extend(attachments)

    def as_dict(s):
        return {'text': str(s.text), 'attachments': [a.as_dict() for a in s.attachments]}



###################################################################################################
## SLACK VIEW SECTION
###################################################################################################

##############################################################################################
## SLACK VIEW BASE OBJECT
class SlackViewBase():
    """
    base class for the equivalent of a Django view object, but for Slack requests

    - it is instantiated by providing a `SlackRequest` object (if called within a classic view, the 
        `@slack_augment` decorator will take care of converting the HttpRequest object)
    
    - the main entry is the `dispatch` function which looks at the Slack command (in `.slack_text`) and
        interprets its first token as subcommand; it then runs a method called `run_<subcommand>` provided
        that it is available (would usually be provided by the subclass); otherwise it runs the method
        called `run_unknown_command`

    - it also provides and `as_view` classmethod that can be used like Django's class-based views
        
    - it provides functionality for derived classes to execute `argparse` on the command string; a new argparse 
        parser can be instantiated with the `parser` method; this parser would usually be told about the expected
        arguments using `add_argument`

    - the parsing itself is executed in the `parse` method which also adds a final argument called `remainder`
        which collects all arguments that have not been previously assing (so a function having _only_ positional
        arguments can simply look at remainder)

    - all `run_xxx` functions are given a fresh `parser` as argument, so there is generally no need for them to call
        `_parser` explicitly; this parser is augmented with a `run` method that is already set up with the correct
        environment
            
    EXAMPLE
    for a working example see `SlackHandlerExample` in `slack_tests.py`

    """
    def __init__(s, slack_request):
        s.request = slack_request

    ############################################################
    ## DISPATCH
    def dispatch(s):
        """main entrance point for Slack requests"""
        splt = re.split(r'[^a-zA-Z]', s.request.slack_text, maxsplit=1)
        
        try: subcommand = splt[0]
        except: subcommand = ""
        
        try: parser = s._parser(splt[1])
        except: parser = s._parser("")
        del splt

        try: run_subcommand = getattr(s, 'run_'+subcommand.lower())
        except AttributeError: return s.unknown_command(subcommand, parser)

        return run_subcommand(parser)
            # eg if subcommand == 'list' then we see whether there is a method `run_list`
            # is yes, it is called, with `remainder` as argument
    
    ############################################################
    ## AS VIEW
    @classmethod 
    def as_view(cls):
        """returns a Django view that is based on that Slack view object

        USAGE
            url(r'^api$', views.MySlackView.as_view(), name='api'),
        """
        
        @csrf_exempt
        @slack_augment
        def view(request):
            return cls(request).dispatch()
        return view
    
    ############################################################
    ## AS VIEW
    @classmethod 
    def alias(cls, alias, original):
        """
        creates an alias for a `run_` method
        
        USAGE
            class MySlackView(SlackViewBase):
                def run_foo(s, ...):
                    ...
                
            MySlackView.alias('foo', 'bar')
        """
        original = 'run_'+original
        alias = 'run_'+alias
        setattr(cls, alias, getattr(cls, original))

        
    ############################################################
    ## RUN COMMANDS
    def unknown_command(s, subcommand, parser):
        """default handler for unknown (sub)command"""
        return SlackResponseText("unknown subcommand '{}'; try 'help'".format(subcommand))
    
    def run_help(s, remainder):
        """handler for the help command (derived classes should overwrite)"""
        return SlackResponseText("help functionality is not currently implemented")

        
    ############################################################
    ## PARSING METHODS

    def _parser(s, remainder):
        """
        returns a fresh `argparse` parser object, augmented with the `run` method
        """
        parser = _ArgumentParser()
        def run():
            return s.parse(parser, remainder)
        parser.run = run
        return parser 
        
    def parse(s, parser, remainder):
        """runs the parser and the remainder text

        EXAMPLE
            parser = s.parser() # creates a new parser
            parser.add_argument("-c", "--channel", action="count")
                # see https://docs.python.org/3/library/argparse.html#action
            ...
            parse_obj = parse(parser, remainder) # remainder is part after subcommand
            parse_obj.error # True or False
            parse_obj.errmsg # only if .error == True
            parse_obj.remainder # all arguments not explicitly declared (as list!)

        NOTE 
        if the parser provided to the run function is used this can be simplified:
            
            def run_xxx(remainder, parser)
                parser.add_argument("-c", "--channel", action="count")
                parse_obj = parser.run()
                ...as above
                
        """
        params = remainder.split(' ')
        if params == ['']: params = []
        parser.add_argument('posn', nargs='*')
            # collects all positional arguments that have not been collected before into a list
            
        try:
            parse_obj = parser.parse_args(params)
            parse_obj.error = False
                # the results of the parsing are provides as an object; we also set .error=False
                # it is possible to convert it to a dict using vars(parse_obj)
        except SystemExit: 
            parse_obj = argparse.Namespace(error=True, errmsg=parser._error)
                # if there is an error we set .error=True, and the message goes into .errmsg
        return parse_obj


##############################################################
## POSITIONAL ARGS (decorator)
def positional_args(func):
    """
    decorator that retrieves all positional arguments

    USAGE
        class MySlackView(SlackViewBase)

            @positional_args
            def run_mycommmand(s, posn)
                if posn[0] == ...
    """
    def inner(s, parser, *args, **kwargs):
        clargs = parser.run()
        return func(s, clargs.posn, *args, **kwargs)
    
    if (func.__doc__ != None): inner.__doc__=func.__doc__+"\n\n[decorated by @positional_arguments]\n"
    inner.__name__=func.__name__
    return inner


##############################################################
## SLACK AUGMENT (decorator)
def slack_augment(function):
    """
    decorator augmenting the view with slack parameters and checking access

    NOTE
    - access ischecked using settings.SLACK_ACCESS
    - if the called function returns a SlackResponse, the associated HttpResponse is returned

    USAGE
        @slack_augment
        def myview(slack_request):
            ...
            return SlackResponse (...)
    """

    def wrapped(request, *args, **kwargs):
        SlackRequest.augment(request)
        #print ("token: {0.slack_token}".format(request))
        #print ("team id: {0.slack_tid}".format(request))
        try:
            teamid = settings.SLACK_ACCESS[request.slack_token]
            if teamid != True: # True means that every team matches
                if not  teamid == request.slack_tid:
                    return _Http403()
        except: return _Http403()
        response = function(request, *args, **kwargs)
        if isinstance(response, SlackResponseBase): return response.as_json_response()
        return response

    if (function.__doc__ != None): wrapped.__doc__=function.__doc__+"\n\n[decorated by @slack_augment]\n"
    wrapped.__name__=function.__name__
    return wrapped   



    
###################################################################################################
## DEPRECATED
###################################################################################################

##############################################################
## @slack_read_required
def slack_read_required(function):
    """
    decorator requiring Slack READ permission

    note: the object must already be a SlackRequest object, not a simple HttpRequest 
    """

    def wrapped(request, *args, **kwargs):
        if not instanceof (request, SlackRequest):
            raise RuntimeError("wrapped object must be instance of SlackRequest")
        
        if not request.slack_access(READ): return _Http403()
        return function(request, *args, **kwargs)

    if (function.__doc__ != None):
        wrapped.__doc__=function.__doc__+"\n\n[decorated by @slack_read_required]\n"
    wrapped.__name__=function.__name__
    return wrapped


##############################################################
## @slack_execute_required
def slack_execute_required(function):
    """
    decorator requiring Slack EXECUTE permission

    note: the object must already be a SlackRequest object, not a simple HttpRequest 
    """

    def wrapped(request, *args, **kwargs):
        if not instanceof (request, SlackRequest):
            raise RuntimeError("wrapped object must be instance of SlackRequest")

        if not request.slack_access(EXECUTE): return _Http403()
        return function(request, *args, **kwargs)

    if (function.__doc__ != None):
        wrapped.__doc__=function.__doc__+"\n\n[decorated by @slack_execute_required]\n"
    wrapped.__name__=function.__name__
    return wrapped


