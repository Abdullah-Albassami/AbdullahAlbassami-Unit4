
from pathlib import Path

from django import forms
from PIL import Image, UnidentifiedImageError


class FeedbackForm(forms.Form):

    name = forms.CharField(
        max_length=100,
        label="Name",
    )

    email = forms.EmailField(
        label="Email",
    )

    message = forms.CharField(
        widget=forms.Textarea,
        label="Message",
    )

    rating = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        label="Rating (Optional)",
    )

    image = forms.ImageField(
        required=False,
        label="Attach Screenshot (Optional)",
        help_text="JPG, JPEG, or PNG only. Maximum size: 2 MB.",
    )

    def clean_message(self):
        message = self.cleaned_data["message"].strip()

        if len(message) < 10:
            raise forms.ValidationError(
                "Message must be at least 10 characters long."
            )

        return message

    
    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        if not all(char.isalpha() or char.isspace() for char in name):
            raise forms.ValidationError(
                "Name must contain letters and spaces only."
            )

        return name

    def clean_image(self):
        image = self.cleaned_data.get("image")

        # The image is optional.
        if not image:
            return None

        allowed_extensions = {".jpg", ".jpeg", ".png"}
        allowed_formats = {"JPEG", "PNG"}
        max_size = 2 * 1024 * 1024

        extension = Path(image.name).suffix.lower()

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "Only JPG, JPEG, and PNG files are allowed."
            )

        if image.size > max_size:
            raise forms.ValidationError(
                "Image size must not exceed 2 MB."
            )

        try:
            image.seek(0)

            with Image.open(image) as img:
                if img.format not in allowed_formats:
                    raise forms.ValidationError(
                        "Only JPEG and PNG image formats are supported."
                    )

                img.verify()

        except (UnidentifiedImageError, OSError, ValueError):
            raise forms.ValidationError(
                "The uploaded file is not a valid image."
            )

        finally:
            image.seek(0)

        return image