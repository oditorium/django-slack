# django-slack
_Slack integration for Django_

## Installation

### Example Installation

This repo contains an entire Django project that should run out of the box, and that
contains the Slack integration library as part of the `slack` app. It should run on 
any server that has `Django 1.9+` and `Python 3.5+` installed. For security reasons,
it should only be accessible via SSL, so it should be behind an SSL capable front end 
server. For testing purposes it could also use [sslserver][sslserver]
that allows running an SSL-capable test server:
[sslserver]: https://github.com/teddziuba/django-sslserver

	export SSLSERVER=1
	export CERTS=/path/to/my/cert
	python3 manage.py runsslserver 0.0.0.0:443 --certificate $CERTS.crt --key $CERTS.key


To install on an Ubuntu server (or most other Linux servers for that matter) use the
following commands:

	git clone https://github.com/oditorium/django-slack.git
	cd django-slack
	python3 manage.py test
	python3 manage.py runserver

This launches a server on <http://localhost:8000>. If you navigate to [/version](/version)
you should get a message along the lines of _Slack Library Version v1.5_ or whatever the 
latest version of the library is.

The easier alternative is to install it on [Heroku](https://www.heroku.com/) which takes 
care of the SSL connection and the necessary certificates. After installing the Heroku
[Toolbelt](https://toolbelt.heroku.com/) run the following commands:

	git clone https://github.com/oditorium/django-slack.git
	cd django-slack
	heroku create
	heroku config:set HEROKU=1
	git push heroku +master


### Installing the Library

In most cases you probably want to install the library into one of your own Django projects.
The minimal installation would be to only use the library file (and probably the test files)

- `slack.py`
- `tests_slack.py`
- `test.py`

An example Slack view (call `SlackViewExample`) can be found in `tests_slack.py`, and the files
`views.py` and `urls.py` show how it should be connected. The file `test.py` (if used at all) 
should be adapted to the local configuration--its purpose is to ensure that all necessary settings
are there and that the API is at the location where Slack expects it to be.

Speaking about settings, the following lines need to be added to `settings.py`

	SLACK_ACCESS = {
	    'ULtA9InSFLTGpEz0EsMkVBKl': True,
	}
    
	SLACK_USERS = {
	    'U0CIOKE53U': 3,
	}

where the key(s) in `SLACK_ACCESS` must correspond to the Slack integration token(s). `SLACK_USERS`
must be present, but it is deprecated (it works with the current permissions model that we will remove
at one point).

Alternatively you can copy the entire `slack` app and change the files as you see fit. Most likely, the
definition of your `MySlackView` view would end up in `views.py` and would be connected in the `urls.py` as
follows:

	from .views import MySlackView
	
	urlpatterns = [
	    url(r'^slack/api$', MySlackView.as_view(), name='slack_api'),
	]


## Using the Library

Please see the extensive docstrings in `slack.py` for details, as code here might become stale. The idea
is that a slack view derives from `SlackViewBase` and the slack commands are connected with the `run_`
prefix (so `run_mycommand` would be called by the `mycommand` subcommand)
	
	class MySlackView(SlackViewBase):
	
		def run_mycommand(parser):
			...
	
The `run_xxx` functions are being called with a parser which is essentially an instance of `argparse`,
so all the usual methods for defining arguments apply. It has been extended with a `run` method that
adds a final field `remainder` collecting all not-previously-parsed arguments, and runs the parser on
the provided command:

	parser.add_argument("-c", "--channel", action="count")
	parse_obj = parser.run()
		# parse_obj.channel contains the number of times the --channel / -c argument was used
		# parse_obj.remainder contains the list of arguments after that

The view function then assembles a Slack response, possible with attachments (see `SlackViewExample` for
a more complete example):

	response = SlackResponse("that's the text before the attachment")
	attachment = slack.Attachment("that's the attachment text")
	attachment.add(  att.Image("/path/to/image.jpg", "/path/to/thumb.jpg")  )
	response.add(attachment)
	return response


## Contributions

Contributions welcome. Send us a pull request!


## Change Log


The idea is to use [semantic versioning](http://semver.org/), even though initially we might make some minor
API changes without bumping the major version number. Be warned!

- **v1.6** changed `self.slack_request` to `self.request` to be consistent with Django; bugfix when running a subcommand; added `url` method to `SlackResponseBase` and module; added `positional_args` decorator; renamed `remainder` args to `posn`; added possibility to add alias'

- **v1.5** Initial Release