from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated or request.path in [reverse('login'), reverse('logout'), reverse('home')]\
                or '/api/' in request.path or '/home-terminal/' in request.path:
            response = self.get_response(request)
            return response

        return redirect('login')
