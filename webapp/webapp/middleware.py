from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated or request.path in [reverse('login'), reverse('logout'), reverse('home')]\
                or '/api/' in request.path or '/home-terminal/' in request.path or '/swagger/' in request.path\
                or '/api-token-auth/' in request.path or '/redoc/' in request.path or '/update-t/' in request.path\
                or '/create-sale-terminal/' in request.path or '/services/create/' in request.path\
                or '/get-events/' in request.path or '/filtered-events/' in request.path\
                or '/filtered-event-times/' in request.path or '/filtered-services/' in request.path\
                or '/get-events-dates/' in request.path or '/get-service-cost/' in request.path\
                or '/payment-process-terminal/' in request.path or '/check-payment-status-terminal/' in request.path:
            response = self.get_response(request)
            return response

        return redirect('login')
