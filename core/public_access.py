"""Fail-closed, unauthenticated market-only deployment boundary."""
from django.conf import settings
from django.http import JsonResponse
from django.urls import Resolver404, resolve

PUBLIC_VIEWS = frozenset({
    'index', 'market', 'api_candlesticks', 'api_ticker', 'api_funding_rate',
    'api_funding_rate_history', 'api_contract_basis', 'api_contract_basis_history',
    'api_sources', 'api_symbols', 'api_source_capabilities', 'api_source_documentation',
    'api_option_instruments', 'api_option_ticker',
})


class PublicAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.TIDE_PUBLIC_READ_ONLY:
            return self.get_response(request)
        if request.method not in {'GET', 'HEAD'}:
            return JsonResponse({'error': 'Public market viewer is read-only'}, status=405)
        # Only the built frontend assets are public, not arbitrary static/admin assets.
        if not request.path_info.startswith('/static/dist/'):
            try:
                name = resolve(request.path_info).view_name
            except Resolver404:
                name = None
            if name not in PUBLIC_VIEWS:
                return JsonResponse({'error': 'Not available on the public market viewer'}, status=404)
        for key, values in request.GET.lists():
            if len(key) > 64 or any(len(value) > 128 for value in values):
                return JsonResponse({'error': 'Query parameter too long'}, status=400)
        for key in ('limit', 'before', 'after'):
            value = request.GET.get(key)
            if value is not None:
                try:
                    number = int(value)
                except (TypeError, ValueError):
                    return JsonResponse({'error': 'Invalid numeric parameter'}, status=400)
                if not (1 <= number <= (1000 if key == 'limit' else 9999999999999)):
                    return JsonResponse({'error': 'Numeric parameter out of range'}, status=400)
        response = self.get_response(request)
        response['X-Tide-Mode'] = 'public-market-only'
        return response
