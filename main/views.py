from django.shortcuts import render, redirect


def index(request):
    return render(request, "index.html")

def get_django(request):
    return render(request, "django.html")

def get_flask(request):
    return render(request, "flask.html")

def get_pandas(request):
    return render(request,"pandas.html")
