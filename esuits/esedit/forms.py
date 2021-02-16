from django import forms
from django.db.models import fields
from django.forms import widgets
from ..models import QuestionModel, EntrySheetesModel, AnswerModel


# class AnswerQuestionForm(forms.ModelForm):
#     '''ポスト (ESの中の一つの質問) に答えるためのフォーム'''
#     class Meta:
#         model = QuestionModel
#         fields = (
#             'answer',
#         )


# AnswerQuestionFormSet = forms.inlineformset_factory(
#     parent_model=EntrySheetesModel,
#     model=QuestionModel,
#     form=AnswerQuestionForm,
#     extra=0,
#     can_delete=False
# )


class AnswerForm(forms.Form):
    question_pk = forms.IntegerField(widget=forms.HiddenInput)
    answer = forms.CharField(widget=forms.Textarea)


AnswerFormSet = forms.formset_factory(
    form=AnswerForm,
    extra=0,
)


AnswerUpdateFormSet = forms.modelformset_factory(
    model=AnswerModel,
    fields=('answer',),
    extra=0
)
