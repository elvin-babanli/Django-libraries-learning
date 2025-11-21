from django.shortcuts import render, redirect


def index(request):
    return render(request, "index.html")

# Frameworks____________________________________________
def get_django(request):
    return render(request, "django.html")

def get_flask(request):
    return render(request, "flask.html")


# Libraries_____________________________________________
def get_pandas(request):
    return render(request,"pandas.html")

# Pages_________________________________________________

def get_git(request):
    return render(request,"git.html")

def get_crud(request):
    return render(request,"crud.html")