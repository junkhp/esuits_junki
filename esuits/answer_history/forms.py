# -*- coding: utf-8 -*-
from django import forms


class AnswerHistoryCheckForm(forms.Form):
    select = forms.ChoiceField(
        required=True,
        disabled=False,
        widget=forms.RadioSelect(attrs={
            'id': 'hisradio', 
            'class': 'ans-history-radio-input'
            })
    )
