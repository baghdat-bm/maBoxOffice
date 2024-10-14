import requests
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django_celery_beat.utils import make_aware

from ticket_sales.models import TerminalSettings


@permission_required('ticket_sales.change_terminalsettings', raise_exception=True)
def register_terminal(request):
    ip_address = request.GET.get('ip_address')
    port = request.GET.get('port')
    use_https = request.GET.get('use_https') == 'true'
    username = request.GET.get('username')
    app_type = request.GET.get('app_type')

    if not ip_address or not username or not port:
        message = 'Необходимо заполнить поля IP Address, Port и Username'
        messages.error(request, message)
        return JsonResponse({'error': message}, status=400)

    protocol = 'https' if use_https else 'http'
    url = f"{protocol}://{ip_address}:{port}/register?name={username}"

    try:
        response = requests.get(url, timeout=40, verify=False)

        if response.status_code == 200:
            data = response.json()
            expiration_date = make_aware(parse_datetime(data['expirationDate']))
            settings = TerminalSettings.objects.filter(app_type=app_type).first()
            if settings:
                settings.ip_address = ip_address
                settings.port = port
                settings.use_https = use_https
                settings.username = username
                settings.access_token = data['accessToken']
                settings.refresh_token = data['refreshToken']
                settings.expiration_date = expiration_date
            else:
                settings = TerminalSettings(
                    app_type=app_type,
                    ip_address=ip_address,
                    port=port,
                    use_https=use_https,
                    username=username,
                    access_token=data['accessToken'],
                    refresh_token=data['refreshToken'],
                    expiration_date=expiration_date,
                )
            settings.save()
            messages.success(request, "Регистрация прошла успешно.")
            return JsonResponse({'status': 'success'})
        elif response.status_code == 500:
            return JsonResponse({'error': response.json().get('message', 'Unknown error')}, status=500)
        else:
            return JsonResponse({'error': 'Unknown error occurred during registration.'}, status=response.status_code)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Connection error: {str(e)}'}, status=500)