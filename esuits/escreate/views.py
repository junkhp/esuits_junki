# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.urls import reverse_lazy, reverse
from django.views import View

from .forms import CreateEntrySheetForm, CreateQuestionForm
from ..models import AnswerModel, CompanyHomepageURLModel, CompanyModel, CustomUserModel, TagModel, EntrySheetesModel, QuestionModel
# Create your views here.


class ESCreateView(View):
    '''エントリーシートそのものと質問を作成'''

    def get(self, request, *args, **kwargs):
        login_user_id = request.user.id
        template = 'esuits/es_create.html'
        tags = TagModel.objects.filter(authors=login_user_id)
        num_tags = len(tags)
        # ポストフォームはformsetを使用
        QuestionFormset = forms.formset_factory(
            # PostModel,
            form=CreateQuestionForm,
            extra=1,
        )
        context = {
            'es_form': CreateEntrySheetForm(),
            # 'post_form': CreatePostForm(),
            'question_formset': QuestionFormset(form_kwargs={'user': request.user}),
            'tags': tags,
            'num_tags': num_tags,
            'user_id': login_user_id,
        }
        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        login_user_id = request.user.id
        author = CustomUserModel.objects.get(pk=login_user_id)
        # request.POSTを修正するためにコピーする．もっといい方法ありそう
        request_post_copy = request.POST.copy()

        # ESテーブルを更新ここから
        '''
        ESを保存するときにやること
        1.企業名から企業テーブルのIDを特定．ない場合は新規登録
        2.企業URLテーブルからURLのIDを特定．ない場合は新規登録
        '''
        # 企業名から企業テーブルのIDを特定．ない場合は新規登録
        company_name = request.POST['company']
        try:
            company_record = CompanyModel.objects.get(company_name=company_name)
        except CompanyModel.DoesNotExist:
            company_record = CompanyModel(company_name=company_name)
            company_record.save()
        request_post_copy['company'] = company_record

        # 企業URLテーブルからURLのIDを特定．ない場合は新規登録
        homepage_url = request.POST['homepage_url']
        try:
            homepage_url_record = CompanyHomepageURLModel.objects.get(homepage_url=homepage_url)
        except CompanyHomepageURLModel.DoesNotExist:
            homepage_url_record = CompanyHomepageURLModel(company=company_record, homepage_url=homepage_url)
            homepage_url_record.save()
        request_post_copy['homepage_url'] = homepage_url_record

        # ESを登録
        es_form = CreateEntrySheetForm(request_post_copy)
        es_record = None
        if es_form.is_valid():
            es_record = es_form.save(commit=False)
            es_record.author = author
            es_record.is_editing = True
            es_record.save()
            print('saved es_form')
        else:
            # ESを登録できなかった場合のエラー処理を書かないといけない
            print('failed save es_form')
        # ESテーブル更新ここまで

        # 質問テーブルを更新ここから
        question_num = int(request.POST['form-TOTAL_FORMS'])
        # 回答の文字数を取得
        # request_copy['char_num'] = len(request.POST['answer'])
        # request_copy['es_group_id'] = es_group_id

        QuestionFormset = forms.modelformset_factory(
            model=QuestionModel,
            form=CreateQuestionForm,
            extra=question_num,
        )
        
        question_formset = QuestionFormset(request_post_copy, form_kwargs={'user': request.user})
        question_forms = question_formset.save(commit=False)

        if question_formset.is_valid():
            for question_record in question_forms:
                question_record.entry_sheet = es_record
                question_record.save()
                # 回答テーブルを更新
                new_answer_record = AnswerModel(question=question_record)
                print(new_answer_record)
                new_answer_record.save()
            question_formset.save_m2m()
            print('saved post_form')
        else:
            print('failed save post_form')
        # 質問テーブルここまで
        return redirect('esuits:es_edit', es_id=es_record.pk)
