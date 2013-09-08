#!/usr/bin/env python3.2
import json
import logging
import os

from tornado import web
from tornado.ioloop import IOLoop

from rent import controllers
from rent.model import RentModel
import rent.ui_methods

APP_PATH = os.path.join(os.path.dirname(__file__), os.pardir)
SETTINGS_PATH = os.path.join(APP_PATH, 'settings.json')
STATIC_PATH = os.path.join(APP_PATH, 'static')
TEMPLATE_PATH = os.path.join(APP_PATH, 'templates')

ROUTES = [
    web.url(r'/', controllers.HomeHandler, name='home'),
    web.url(r'/transactions', controllers.TransactionsHandler, name='transactions'),
    web.url(r'/login', controllers.LoginHandler),
    web.url(r'/logout', controllers.LogoutHandler, name='logout'),
    web.url(r'/pay', controllers.PayHandler, name='pay'),
]

SETTINGS = {
    'cookie_secret': None, # Define this in settings.json
    'database': None, # Define this in settings.json
    'debug': False,
    'login_url': '/login',
    'static_path': STATIC_PATH,
    'template_path': TEMPLATE_PATH,
    'ui_methods': rent.ui_methods,
    'xsrf_cookies': True,
}
try:
    SETTINGS.update(json.load(open(SETTINGS_PATH)))
except IOError:
    logging.warn("Unable to load settings from %s", SETTINGS_PATH)

def main():
    logging.basicConfig(level=logging.INFO)

    model = RentModel(SETTINGS['database'])
    app = web.Application(ROUTES,
                          model = model,
                          **SETTINGS)
    app.listen(26062, address='0.0.0.0')
    IOLoop.instance().start()

def script():
    global model
    model = RentModel(SETTINGS['database'])

if __name__ == '__main__':
    main()
