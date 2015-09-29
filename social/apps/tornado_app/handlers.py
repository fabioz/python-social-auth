from tornado.web import RequestHandler

from social.apps.tornado_app.utils import psa
from social.actions import do_auth, do_complete, do_disconnect
import json
from social.exceptions import NotAllowedToDisconnect


class _SessionApi(object):
    
    def __init__(self, request_handler):
        self.request_handler = request_handler
        
    def get(self, key):
        ret = self.request_handler.get_secure_cookie(key)
        if ret:
            return json.loads(ret.decode('utf-8'))
        return ret
    
    def __setitem__(self, key, val):
        self.request_handler.set_secure_cookie(key, json.loads(val.encode('utf-8')))
        
    def pop(self, key):
        value = self.get(key)
        self.request_handler.clear_cookie(key)
        return value

class BaseHandler(RequestHandler):
    
    # Clients may monkey-patch to handle session in some other way.
    # Receives the handler as a parameter.
    _create_session_api = _SessionApi
    
    def get_session_data(self):
        return BaseHandler._create_session_api(self)
    
    @property
    def session_data(self):
        return self.get_session_data()
    
    def user_id(self):
        return self.session_data.get('user_id')

    def get_current_user(self):
        user_id = self.user_id()
        if user_id is not None:
            return self.backend.strategy.get_user(int(user_id))

    def login_user(self, user):
        self.session_data['user_id'] = user.id


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
    
    @psa('disconnect')
    def post(self, backend, association_id):
        current_user = self.current_user
        if current_user is None:
            self.finish('Error: user must be logged in to disconnect association.')
            return
        
        try:
            do_disconnect(self.backend, current_user, association_id)
        except NotAllowedToDisconnect:
            self.finish('Error: cannot disconnect because this is the last association for this account.')
            return
    get = post
