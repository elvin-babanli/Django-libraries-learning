from django.shortcuts import render, redirect


def index(request):
    return render(request, "index.html")

def get_django(request):
    return render(request, "django.html")