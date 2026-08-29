from django.http import JsonResponse
from django.shortcuts import render


def index(request):
    return render(request, 'index.html')


def health(request):
    return JsonResponse({'ok': True, 'service': 'NetHack', 'mode': 'authorized-diagnostics'})


def diagnostics_info(request):
    return JsonResponse({
        'platforms': ['Windows', 'macOS', 'Linux', 'Ubuntu', 'Android', 'iOS'],
        'note': 'Endpoint OS commands run only on a locally installed agent; Vercel cannot execute them on the visitor device.',
    })
