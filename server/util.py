from functools import wraps

def handle_errors() -> object:
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                if isinstance(e, ValueError):
                    return {'message': e.args[0], 'type': 'ValueError'}, 400
                elif isinstance(e, AttributeError):
                    return {'message': e.args[0], 'type': 'AttributeError'}, 400
                elif isinstance(e, KeyError):
                    return {'message': e.args[0], 'type': 'KeyError'}, 400
                elif isinstance(e, TypeError):
                    return {'message': e.args[0], 'type': 'TypeError'}, 400
                else:
                    return {'message': str(e), 'type': 'InternalServerError'}, 500
        return wrapped
    return wrapper
