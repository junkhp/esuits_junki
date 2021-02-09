# -*- coding: utf-8 -*-
from django import VERSION
from django.db.models.enums import Choices
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from ..models import QuestionModel, AnswerModel
from .forms import AnswerHistoryCheckForm


class AnswerHistoryView(View):
    '''回答の履歴を表示・選択'''

    # 回答の文字数を計算
    def _get_char_num(self, text):
        return len(text)

    def orm_to_choice(self, orm):
        choices = []
        for answer in orm:
            choices.append((answer.version, answer.answer))
        return choices

    def get(self, request, question_id):
        login_user = request.user
        login_user_name = login_user.username
        # テンプレート
        template = 'esuits/answer_history.html'
        question = QuestionModel.objects.get(pk=question_id)
        selected_version = question.selected_version

        # form
        form = AnswerHistoryCheckForm()
        history = AnswerModel.objects.filter(question__pk=question_id).order_by('version')
        new_version = len(history) + 1
        print(question_id)
        new_answer_text = request.session[str(question_id)]
        new_answer_choice = (new_version, new_answer_text)
        choices = [new_answer_choice] + self.orm_to_choice(history)
        form.fields['select'].choices = choices
        form.fields['select'].initial = [selected_version]
        context = {
            'username': login_user_name,
            'question': question,
            'form': form,
        }
        return render(request, template, context)

    def post(self, request, question_id):
        template_name = 'esuits/es_edit.html'
        print(request.POST)
        # 質問テーブルを更新
        selected_answer_version = int(request.POST['select'])
        question_record = QuestionModel.objects.get(pk=question_id)
        try:
            selected_answer_record = AnswerModel.objects.get(
                question=question_record, version=selected_answer_version)
        except:
            new_answer_text = request.session[str(question_id)]
            selected_answer_record = AnswerModel(
                question=question_record,
                version=selected_answer_version,
                answer=new_answer_text,
                char_num=self._get_char_num(new_answer_text)
            )
            selected_answer_record.save()

        question_record.selected_version = selected_answer_version
        question_record.answer = selected_answer_record.answer
        question_record.char_num = selected_answer_record.char_num
        question_record.save()
        es_pk = question_record.entry_sheet.pk
        return redirect('esuits:es_edit', es_id=es_pk)



