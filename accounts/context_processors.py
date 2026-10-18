from .views import is_methodist


def user_role(request):
    return {
        'is_methodist': (
            request.user.is_authenticated
            and is_methodist(request.user)
        )
    }