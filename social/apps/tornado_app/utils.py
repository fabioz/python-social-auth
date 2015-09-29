import warnings

from functools import wraps

from social.utils import setting_name, module_member
from social.strategies.utils import get_strategy
from social.backends.utils import get_backend, user_backends_data


DEFAULTS = {
    'STORAGE': 'social.apps.tornado_app.models.TornadoStorage',
    'STRATEGY': 'social.strategies.tornado_strategy.TornadoStrategy'
}


def get_helper(request_handler, name, do_import=False):
    ret = request_handler.settings.get(setting_name(name),
                                        DEFAULTS.get(name, None))
    if do_import:
        return module_member(ret)
    return ret


def load_strategy(request_handler):
    strategy = get_helper(request_handler, 'STRATEGY')
    storage = get_helper(request_handler, 'STORAGE')
    return get_strategy(strategy, storage, request_handler)


def load_backend(request_handler, strategy, name, redirect_uri):
    backends = get_helper(request_handler, 'AUTHENTICATION_BACKENDS')
    Backend = get_backend(backends, name)
    return Backend(strategy, redirect_uri)

def backends(request_handler, user):
    """Load Social Auth current user data to context under the key 'backends'.
    Will return the output of social.backends.utils.user_backends_data."""
    return user_backends_data(user, get_helper(request_handler, 'AUTHENTICATION_BACKENDS'),
                              get_helper(request_handler, 'STORAGE', do_import=True))

def psa(redirect_uri=None):
    def decorator(func):
        @wraps(func)
        def wrapper(self, backend, *args, **kwargs):
            uri = redirect_uri
            if uri and not uri.startswith('/'):
                uri = self.reverse_url(uri, backend)
            self.strategy = load_strategy(self)
            self.backend = load_backend(self, self.strategy, backend, uri)
            return func(self, backend, *args, **kwargs)
        return wrapper
    return decorator


def strategy(*args, **kwargs):
    warnings.warn('@strategy decorator is deprecated, use @psa instead')
    return psa(*args, **kwargs)
