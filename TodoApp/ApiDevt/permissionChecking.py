from functools import wraps
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate

def permission_required(permissions):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if 'Authorization' in request.headers:
                try:
                    token_key = request.headers['Authorization']
                    token = Token.objects.get(key=token_key)
                    user = token.user
                    request.user = user
                except Token.DoesNotExist:
                    return Response({'Access': 'Invalid token'})
            else:
                return Response({'Access': 'Token missing'})

            if user:
                for permission in permissions:
                    # if user.has_perm(permission):
                        return view_func(request, *args, **kwargs)
                
                return Response({'Access': "You don't have required access"})
            else:
                return Response({'Access': "Invalid user"})
        return wrapper
    return decorator
