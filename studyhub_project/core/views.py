import json

from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.shortcuts import render, redirect

from .forms import FeedbackForm


resources = [
    {
        "id": 1,
        "title": "Python Basics",
        "type": "Article",
        "description": "Learn the fundamentals of Python programming.",
        "url": "https://docs.python.org/3/tutorial/",
    },
    {
        "id": 2,
        "title": "Django Documentation",
        "type": "Documentation",
        "description": "Official Django documentation and tutorials.",
        "url": "https://docs.djangoproject.com/",
    },
    {
        "id": 3,
        "title": "HTML and CSS Guide",
        "type": "Article",
        "description": "Review essential HTML and CSS concepts for web development.",
        "url": "https://developer.mozilla.org/",
    },
    {
        "id": 4,
        "title": "Git and GitHub",
        "type": "Video",
        "description": "Learn basic Git commands and GitHub workflow.",
        "url": "https://git-scm.com/doc",
    },
]


def get_theme(request):
    theme = request.COOKIES.get("theme", "light")

    if theme not in ["light", "dark"]:
        theme = "light"

    return theme


def home(request):
    context = {
        "theme": get_theme(request),
        "resource_count": len(resources),
    }

    return render(request, "core/home.html", context)


def resource_list(request):
    resource_type = request.GET.get("type")

    filtered_resources = resources

    if resource_type:
        filtered_resources = [
            resource
            for resource in resources
            if resource["type"].lower() == resource_type.lower()
        ]

    context = {
        "theme": get_theme(request),
        "resources": filtered_resources,
        "selected_type": resource_type,
    }

    return render(request, "core/resource_list.html", context)



def resource_detail(request, id):
    resource = next(
        (resource for resource in resources if resource["id"] == id),
        None,
    )

    if resource is None:
        raise Http404("Resource not found")

    tab = request.GET.get("tab", "details")

    context = {
        "theme": get_theme(request),
        "resource": resource,
        "tab": tab,
    }

    return render(request, "core/resource_detail.html", context)


def favorites(request):
    favorite_ids = request.session.get("favorites", [])

    favorite_resources = [
        resource
        for resource in resources
        if resource["id"] in favorite_ids
    ]

    context = {
        "theme": get_theme(request),
        "resources": favorite_resources,
    }

    return render(request, "core/favorites.html", context)


def add_favorite(request, id):

    if request.method != "POST":
        raise Http404("Invalid request")

    resource_exists = any(
        resource["id"] == id
        for resource in resources
    )

    if not resource_exists:
        raise Http404("Resource not found")

    favorites_list = request.session.get("favorites", [])

    if id not in favorites_list:

        favorites_list.append(id)

        request.session["favorites"] = favorites_list

        messages.success(
            request,
            "Resource added to Favorites successfully!"
        )

    else:
        messages.info(
            request,
            "This resource is already in your Favorites."
        )

    return redirect("core:resource_detail", id=id)


def remove_favorite(request, id):

    if request.method != "POST":
        raise Http404("Invalid request")

    favorites_list = request.session.get("favorites", [])

    if id in favorites_list:
        favorites_list.remove(id)
        request.session["favorites"] = favorites_list

    return redirect("core:favorites")


def preferences(request):
    if request.method == "POST":
        selected_theme = request.POST.get("theme")

        if selected_theme not in ["light", "dark"]:
            selected_theme = "light"

        response = redirect("core:preferences")
        response.set_cookie(
            "theme",
            selected_theme,
            max_age=60 * 60 * 24 * 30,
        )

        return response

    context = {
        "theme": get_theme(request),
    }

    return render(request, "core/preferences.html", context)




def feedback(request):

    if request.method == "POST":

        form = FeedbackForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            feedback_data = form.cleaned_data

            # Store the optional image.
            image_path = None

            image = feedback_data["image"]

            if image:

                storage = FileSystemStorage(
                    location=settings.MEDIA_ROOT / "feedback",
                )

                filename = storage.save(
                    image.name,
                    image,
                )

                image_path = f"feedback/{filename}"

            # Prepare the JSON storage directory.
            data_dir = settings.BASE_DIR / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            file_path = data_dir / "feedback.json"

            # Load existing feedback submissions.
            if file_path.exists():

                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                ) as file:

                    feedback_list = json.load(file)

            else:
                feedback_list = []

            # Prepare the new feedback entry.
            new_feedback = {
                "name": feedback_data["name"],
                "email": feedback_data["email"],
                "message": feedback_data["message"],
                "rating": feedback_data["rating"],
                "image": image_path,
                "submitted_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            # Save the new submission.
            feedback_list.append(new_feedback)

            with open(
                file_path,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    feedback_list,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

            return redirect("core:feedback_thanks")

    else:
        form = FeedbackForm()

    context = {
        "theme": get_theme(request),
        "form": form,
    }

    return render(
        request,
        "core/feedback.html",
        context,
    )


def feedback_thanks(request):
    context = {
        "theme": get_theme(request),
    }

    return render(request, "core/feedback_thanks.html", context)
