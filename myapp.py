import os
# library for template directory path
import urllib
# for creating url connection for the profanity check
import cgi
# HTML escaping for the server side

from google.appengine.api import users
# [START import_ndb]
from google.appengine.ext import ndb
# [END import_ndb]

import jinja2
# template engine
import webapp2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)

DEFAULT_COMMENTS_NAME = 'default_comments'
comments_key = ndb.Key('Feedback', DEFAULT_COMMENTS_NAME)

def check_profanity(text_to_check):
	"""Takes string as parameter and checks for obscenities."""
	connection = urllib.urlopen("http://www.wdyl.com/profanity?q=" + text_to_check)
	output = connection.read()
	connection.close()
	if "true" in output:
		return True
	else:
		return

class Author(ndb.Model):
	"""Submodel for post author."""
	identity = ndb.StringProperty(indexed=False)
	email = ndb.StringProperty(indexed=False)

class Comment(ndb.Model):
	"""Main model for comments."""
	author = ndb.StructuredProperty(Author)
	title = ndb.StringProperty(indexed=False)
	content = ndb.StringProperty(indexed=False)
	date = ndb.DateTimeProperty(auto_now_add=True)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

def fetch_comments(self):
	comments_query = Comment.query(ancestor=comments_key).order(-Comment.date)
	comments = comments_query.fetch(10)

	user = users.get_current_user()
	if user:
		url = users.create_logout_url(self.request.uri)
		url_linktext = 'Logout'
	else:
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'

	template_values = {
	'user': user,
	'comments': comments,
	'users_prompt': "Google users please",
	'url': url,
	'url_linktext': url_linktext
	}
	return template_values

class MainPage(Handler):

	def get(self):

		template_values = fetch_comments(self)

		self.render("comments.html", template_values = template_values)

	def post(self):
		comment = Comment(parent=comments_key)

		if users.get_current_user():
			comment.author = Author(
				identity = users.get_current_user().user_id(),
				email = users.get_current_user().email())

		content = self.request.get('content')
		comment.content = content.strip()
		title = self.request.get('title')
		comment.title = title.strip()

		if comment.title and comment.content:
			if (check_profanity(comment.title) or check_profanity(comment.content)):
				msg = "No profanities please!!!"
				title = comment.title
				content = comment.content
				added_values = {
					'error': msg,
					'title': title,
					'content': content
				}
				template_values = fetch_comments(self)
				template_values.update(added_values)
				self.render('comments.html', template_values = template_values)
			else:
				comment.put()
				self.redirect('/#comments')
		else:
			added_values = { 'error': "Please enter title and comment!"}
			template_values = fetch_comments(self)
			template_values.update(added_values)
			self.render('comments.html', template_values = template_values)

app = webapp2.WSGIApplication([
	('/', MainPage),
], debug=True)