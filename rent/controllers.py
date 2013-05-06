from functools import wraps

from tornado import web

def bs_to_cents(s):
    return round(float(s) * 100)

def with_session(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        with self.model.session() as session:
            f(self, session, *args, **kwargs)
    return wrapper

class BaseHandler(web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)
        self.model = self.settings['model']

    def get_current_user(self):
        return self.get_secure_cookie('user')

    def set_current_user(self, user):
        if user is None:
            self.clear_cookie('user')
        else:
            self.set_secure_cookie('user', user)

    def safe_redirect(self, url, *args, **kwargs):
        if not url.startswith('/'):
            raise web.HTTPError(404)
        self.redirect(url, *args, **kwargs)

class HomeHandler(BaseHandler):
    @web.authenticated
    @with_session
    def get(self, session):
        transactions = self.model.get_recent_transactions(session, self.current_user)
        self.render('index.html',
                    user=self.current_user,
                    transactions=transactions)

class LoginHandler(BaseHandler):
    def get(self):
        next_url = self.get_argument('next', '/')
        self.render('login.html', next_url=next_url)

    @with_session
    def post(self, session):
        username = self.get_argument('username')
        password = self.get_argument('password')
        next_url = self.get_argument('next', '/')
        if self.model.authenticate_user(session, username, password):
            self.set_current_user(username)
            self.render('login_success.html', next_url=next_url)
        self.safe_redirect('/login?failed=1')

class LogoutHandler(BaseHandler):
    def get(self):
        self.set_current_user(None)
        self.render('login_success.html', next_url=self.reverse_url('home'))

class PayHandler(BaseHandler):
    @web.authenticated
    @with_session
    def post(self, session):
        to_user = self.get_argument('to_user')
        try:
            amount = round(float(self.get_argument('amount')) * 100)
        except ValueError:
            raise web.HTTPError(400, 'bad amount')
        comment = self.get_argument('comment')
        self.model.create_transaction(session,
                                      from_user=self.current_user,
                                      to_user=to_user,
                                      amount=amount,
                                      comment=comment)
        self.safe_redirect(self.reverse_url('home'))
