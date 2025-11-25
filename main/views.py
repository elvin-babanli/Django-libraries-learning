import requests, time
from django.shortcuts import render, redirect
from .home_news import get_home_feed

from django.http import HttpResponse

def home(request):
    return HttpResponse("Elvin CodeBase — It works!")



# 4o4-page_____________________________________________

def get4o4(request):
    return render(request,"4o4.html")


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

def get_python_basics(request):
    return render(request,"python_basics.html")

# Projects______________________________________________

# def weather_app(request):
#     return render(request, "weather_app.html")

# Home__________________________________________________


def index(request):
    articles = get_home_feed()
    return render(request, "index.html", {"articles": articles})





FEEDS = [
    "https://www.python.org/blogs/rss/",
    "https://pyfound.blogspot.com/feeds/posts/default?alt=rss",
    "https://realpython.com/atom.xml",
]
CACHE = {"items": [], "ts": 0}
TTL = 60 * 60  # 1 saat

def fetch_news():
    items = []
    for url in FEEDS:
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            text = r.text
            # çox sadə parsing: başlıqları tapırıq (tam parser istəyirsənsə feedparser istifadə et)
            # Burada minimal saxlayıram; prod-da feedparser tövsiyədir.
            for line in text.splitlines():
                if "<title>" in line and "</title>" in line:
                    title = line.split("<title>")[1].split("</title>")[0]
                    if title and "Python.org" not in title:
                        items.append({"title": title[:120], "link": url})
        except Exception:
            continue
    # təmizləmə & limit
    uniq = []
    seen = set()
    for it in items:
        t = it["title"]
        if t not in seen:
            seen.add(t)
            uniq.append(it)
        if len(uniq) >= 8:
            break
    return uniq




def home(request):
    articles_ai = get_home_feed()
    
    context = {
        "articles_ai": articles_ai,       
        "articles": articles_ai,  
        # lazım ola biləcək digər listlər də varsa, hamısına boş dəyər ver:
        # "projects": [],
        # "news": [],
        # "tools": [],
    }
    return render(request, "index.html", context)


def about(request):
    profile = {
        "name": "Elvin Babanlı",
        "title": "AI Engineer & Web Developer · Python ",
        "location": "Warsaw, Poland",
        "email": "elvinbabanli0@gmail.com",
        "github": "https://github.com/elvin-babanli",
        "linkedin": "https://www.linkedin.com/in/elvin-babanl%C4%B1-740038240/",
        "instagram": "https://www.instagram.com/elvin_babanli/",
        "skills": [
            "Python",
            "Django",
            "Flask",
            "FastAPI",
            "REST API",
            "Machine Learning-Basics",
            "Pandas",
            "NumPy",
            "TensorFlow-Basics",
            "HTML/CSS",
            "Bootstrap",
            "SQL",
            "PostgreSQL",
            "Git",
            "GitHub",
            "APIs & Integrations",
            "Automation Scripts"
        ],
        "projects": [
            {"name":"Django Store","url":"https://github.com/elvin-babanli/Django-store"},
            {"name":"Django CRUD","url":"https://github.com/elvin-babanli/Django-CRUD"},
            {"name":"Summarizer","url":"https://github.com/elvin-babanli/summerizer"},
            {"name":"Django Web Online","url":"https://github.com/elvin-babanli/Django-web-online"},
            {"name":"Cheap Flight Finder","url":"https://github.com/elvin-babanli/Cheap_Flight_Finder"},
            {"name":"Stock Predictor","url":"https://github.com/elvin-babanli/Stock_Predictor"},
            {"name":"Weather Control App","url":"https://github.com/elvin-babanli/Weather-control-app"},
            {"name":"Cashly V1.9","url":"https://github.com/elvin-babanli/Cashly_V1.9"},
        ],
    }
    return render(request, "about.html", {"profile": profile})