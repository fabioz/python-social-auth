from tornado.web import RequestHandler

from social.apps.tornado_app.utils import psa
from social.actions import do_auth, do_complete, do_disconnect


class _SessionApi(object):
    
    def __init__(self, request_handler):
        self.request_handler = request_handler
        
    def get(self, key):
        ret = self.request_handler.get_secure_cookie(key)
        return ret.decode('utf-8')
    
    def __setitem__(self, key, val):
        self.request_handler.set_secure_cookie(key, val.encode('utf-8'))
    

class BaseHandler(RequestHandler):
    
    # Clients may monkey-patch to handle session in some other way.
    # Receives the handler as a parameter.
    _create_session_api = _SessionApi
    
    @property
    def session_data(self):
        return BaseHandler._create_session_api(self)
    
    def user_id(self):
        return self.session_data.get('user_id')

    def get_current_user(self):
        user_id = self.user_id()
        if user_id:
            return self.backend.strategy.get_user(int(user_id))

    def login_user(self, user):
        self.session_data['user_id'] = str(user.id)


class AuthHandler(BaseHandler):
    def get(self, backend):
        self._auth(backend)

    def post(self, backend):
        self._auth(backend)

    @psa('complete')
    def _auth(self, backend):
        do_auth(self.backend)


class CompleteHandler(BaseHandler):
    def get(self, backend):
        self._complete(backend)

    def post(self, backend):
        self._complete(backend)

    @psa('complete')
    def _complete(self, backend):
        do_complete(
            self.backend,
            login=lambda backend, user, social_user: self.login_user(user),
            user=self.get_current_user()
        )


class DisconnectHandler(BaseHandler):
    def post(self):
        do_disconnect()
