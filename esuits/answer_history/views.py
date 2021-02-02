# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from ..models import QuestionModel, AnswerModel


class AnswerHistoryView(View):
    '''回答の履歴を表示・選択'''

    def get(self, request, question_id):
        login_user = request.user
        login_user_name = login_user.username

        # テンプレート
        template = 'esuits/answer_history.html'
        question = QuestionModel.objects.get(pk=question_id)
        print(question)
        history = AnswerModel.objects.filter(question__pk=question_id)
        context = {
            'username': login_user_name,
            'question': question,
            'answer_history': history,
        }
        return render(request, template, context)

    def post(self, request):
        pass
