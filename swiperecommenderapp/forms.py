from django import forms

from .models import UserSwipe


class SwipeActionForm(forms.Form):
    decision = forms.ChoiceField(
        choices=UserSwipe.DECISION_CHOICES,
        widget=forms.RadioSelect,
        error_messages={"required": "Debes elegir like o dislike."},
    )
