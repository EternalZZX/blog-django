from django.http import JsonResponse

from blog.common.base import Dictable, Response


def json_response(fun):
    def wrapper(*args, **kwargs):
        result = fun(*args, **kwargs)
        if isinstance(result, Response):
            data, status_code = result.data, result.code
        elif isinstance(result, dict):
            data, status_code = result, 200
        elif isinstance(result, Dictable):
            data, status_code = result.dict(), 200
        else:
            data, status_code = {}, 500
        return JsonResponse(data, status=status_code)
    wrapper.__name__ = fun.__name__
    return wrapper
