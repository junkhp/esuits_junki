from django.db.models.query import QuerySet
from django.forms.formsets import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import View
from django.http.response import JsonResponse
from django.conf import settings
from django import forms
from pprint import pprint

from .forms import AnswerUpdateFormSet
from ..models import (AnswerModel, CustomUserModel, TagModel, QuestionModel
,EntrySheetesModel, CompanyHomepageURLModel)
from ..esuits_utils.newsapi import newsapi
from ..esuits_utils.wordcloudapi.get_wordcloud import get_wordcloud
# Create your views here.
QuerySet

class EsEditView(View):
    '''
    ESの質問に回答するページ
    '''

    # 過去に投稿したポストのうち関連するものを取得
    def _get_related_posts_list(self, request, es_id):
        post_set = QuestionModel.objects.filter(entry_sheet=es_id)
        all_posts_by_login_user = QuestionModel.objects.filter(entry_sheet__author=request.user)

        related_posts_list = [
            all_posts_by_login_user
            .filter(tags__in=post.tags.all())
            .exclude(pk=post.pk)
            for post in post_set
        ]
        return related_posts_list

    # 関連するニュースの取得 (いまはダミー)
    def _get_news_list(self, request, es_group_id):
        news_list = [
            {'title': 'ダミーニュース1', 'url': 'https://news.yahoo.co.jp/pickup/6375312'},
            {'title': 'ダミーニュース2', 'url': 'https://news.yahoo.co.jp/pickup/6375301'},
        ]
        return news_list

    # 企業の情報を取得
    def _get_company_info(self, request, es_id):
        es_info = EntrySheetesModel.objects.get(pk=es_id)
        company_url_info = CompanyHomepageURLModel.objects.get(pk=es_info.homepage_url.pk)
        company_url = company_url_info.homepage_url

        # 現状デプロイ時にワードクラウドは使用しない
        if settings.DEBUG:
            print('開発環境')
            wordcloud_path = get_wordcloud(company_url)
            company_info = {"wordcloud_path": wordcloud_path[1:]}
        else:
            wordcloud_path = '/static/esuits/images/kanban_jyunbi.png'
            company_info = {"wordcloud_path": wordcloud_path}
        return company_info

    # 回答の文字数を計算
    def _get_char_num(self, answer_text):
        return len(answer_text)

    def _get_queryset_for_answer_update_formset(self, es_pk, questions):
        form_num = len(questions)
        all_answers = AnswerModel.objects.filter(question__in=questions)
        initial = []
        for question in questions:
            version = question.selected_version
            answer_record = all_answers.get(question=question, version=version)
            initial.append(answer_record.pk)
        return AnswerModel.objects.filter(pk__in=initial).order_by('question__pk')

    def _make_post_information(self, request_post, questions):
        post_information_dict = {}
        question_num = int(request_post['form-TOTAL_FORMS'])
        question_pk = request_post['question_pk']
        post_information_dict['question_num'] = question_num
        post_information_dict['question_pk'] = question_pk
        for i, question in enumerate(questions):
            # answer_pk = int(request_post['form-{}-id'.format(i)])
            answer_text = request_post['form-{}-answer'.format(i)]
            post_information_dict[str(question.pk)] = answer_text
        print('post information')
        print(post_information_dict)
        return post_information_dict
    def get(self, request, es_id):
        template_name = 'esuits/es_edit.html'
        if EntrySheetesModel.objects.filter(pk=es_id).exists():
            # ESの存在を確認
            es_info = EntrySheetesModel.objects.get(pk=es_id)

            if (es_info.author == request.user):
                # 指定されたESが存在し，それが自分のESの場合
                post_set = QuestionModel.objects.filter(entry_sheet=es_id).order_by('pk')
                query_set = self._get_queryset_for_answer_update_formset(es_id, post_set)
                query_set[0].answer = 'aaa'
                print(query_set[0].answer)
                formset = AnswerUpdateFormSet(
                    queryset=query_set,
                )
                # print(formset)
                print(formset[0]['answer'])
                print(type(formset[0]['answer']))
                # formset = AnswerQuestionFormSet(instance=es_info)f
                # print(formset)
                print(formset[0]['answer'])
                test = formset.save(commit=False)
                print(type(test))
                print(test)
                for form in test:
                    form.answer = 'aaa'
                print(test[0].answer)
                print(formset[0]['answer'])
                # 編集→履歴→編集の場合
                post_information_key = 'post_information'
                if post_information_key in request.session:
                    print('履歴処理')
                    post_information = request.session[post_information_key]
                    del request.session[post_information_key]
                    questions = QuestionModel.objects.filter(entry_sheet=es_id).order_by('pk')
                    # for question in questions:
                    #     key = question.pk
                    #     if key in request.session:
                    #         del request.session[key]

                # 関連したポスト一覧
                related_posts_list = self._get_related_posts_list(request, es_id)
                # ニュース関連
                news_list = newsapi.get_news(es_info.company)
                # 企業の情報(ワードクラウドなど)
                '''
                下記のコードだと「先に画面遷移してからワードクラウド作成」ができない
                company_info = self._get_company_info(request, es_id)
                '''
                # company_info(= 作成されたワードクラウドのパス)の取得はフロント側でやる
                company_info = None

                context = {
                    'message': 'OK',
                    'es_info': es_info,
                    'formset_management_form': formset.management_form,
                    'zipped_posts_info': zip(post_set, formset, related_posts_list),
                    'news_list': news_list,
                    'company_info': company_info,
                    'es_group_id': es_id,
                    'num_related_posts': len(related_posts_list)
                }
                # return render(request, template_name, context)
            else:
                # 指定されたESが存在するが，それが違う人のESの場合
                context = {
                    'message': '違う人のESなので表示できません',
                    'es_info': {},
                    'zipped_posts_info': (),
                }
                # return render(request, template_name, context)
        else:
            # 指定されたESが存在しない場合
            context = {
                'message': '指定されたESは存在しません',
                'es_info': {},
                'zipped_posts_info': (),
            }
        return render(request, template_name, context)

    def post(self, request, es_id):
        save_message = 'save'
        question_pk_message = 'question_pk'
        template_name = 'esuits/es_edit.html'
        # 押されたボタンが保存の場合
        if save_message in request.POST:
            if EntrySheetesModel.objects.filter(pk=es_id).exists():
                # ESの存在を確認
                es_info = EntrySheetesModel.objects.get(pk=es_id)

                if (es_info.author == request.user):
                    # 指定されたESが存在し，それが自分のESの場合
                    questions = QuestionModel.objects.filter(entry_sheet=es_id).order_by('pk')
                    query_set = self._get_queryset_for_answer_update_formset(es_id, questions)
                    formset = AnswerUpdateFormSet(
                        request.POST, queryset=query_set)
                    # formset = AnswerQuestionFormSet(data=request.POST, instance=es_info)
                    forms = formset.save(commit=False)
                    # print(forms)
                    # return redirect('esuits:home')
                    if formset.is_valid():
                        for question, form in zip(questions, forms):
                            print(form.version)
                            form.char_num = self._get_char_num(form.answer)
                            
                            # form.char_num = self._get_char_num(form)

                            # 更新する回答レコードを作成
                            # upd_answer_record = AnswerModel.objects.get(
                            #     question=form, version=form.selected_version)
                            # upd_answer_record.answer = form.answer
                            # upd_answer_record.char_num = form.char_num

                            # 更新
                            form.save()
                            # upd_answer_record.save()
                        formset.save()
                        return redirect('esuits:home')

                    # 関連したポスト一覧
                    related_posts_list = self._get_related_posts_list(request, es_id)

                    # ニュース関連
                    news_list = newsapi.get_news(es_info.company)

                    # 企業の情報(ワードクラウドなど)
                    company_info = self._get_company_info(request, es_id)

                    context = {
                        'message': 'OK',
                        'es_info': es_info,
                        'formset_management_form': formset.management_form,
                        'zipped_posts_info': zip(questions, formset, related_posts_list),
                        'news_list': news_list,
                        'company_info': company_info,
                    }
                    return render(request, template_name, context)
                else:
                    # 指定されたESが存在するが，それが違う人のESの場合
                    context = {
                        'message': '違う人のESなので表示できません',
                        'es_info': {},
                        'zipped_posts_info': (),
                    }
                    return render(request, template_name, context)
            else:
                # 指定されたESが存在しない場合
                context = {
                    'message': '指定されたESは存在しません',
                    'es_info': {},
                    'zipped_posts_info': (),
                }
                return render(request, template_name, context)

        # 履歴表示の場合
        if question_pk_message in request.POST:
            print(request.POST)
            questions = QuestionModel.objects.filter(entry_sheet__pk=es_id).order_by('pk')
            print('questions')
            print(questions)
            question_id = int(request.POST[question_pk_message])
            # リクエストから現状の回答を取り出してセッションに保存
            request.session['post_information'] = self._make_post_information(request.POST, questions)
            # question_num = int(request.POST['questionmodel_set-TOTAL_FORMS'])
            # request.session['question_num'] = question_num
            # answers_dict = {}
            # for i in range(question_num):
            #     question_key = 'questionmodel_set-{}-id'.format(i)
            #     answer_key = 'questionmodel_set-{}-answer'.format(i)
            #     answers_dict[request.POST[question_key]] = request.POST[answer_key]
            #     request.session[request.POST[question_key]] = request.POST[answer_key]
            # 履歴管理画面に遷移
            return redirect('esuits:answer_history', question_id=question_id)
        else:
            return redirect('esuits:home')


def get_related_post(request):
    print(request.GET.get('pk', ''))
    pk = request.GET.get('pk', '')
    es = QuestionModel.objects.get(pk=pk)
    print(es.question, es.answer, sep='¥n')
    return JsonResponse({'question': es.question, 'answer': es.answer})


def get_wordcloud_path(request):
    es_id = request.GET.get('es_group_id', '')
    es_info = EntrySheetesModel.objects.get(pk=es_id)
    company_url_info = CompanyHomepageURLModel.objects.get(homepage_url=es_info.homepage_url)
    company_url = company_url_info.homepage_url

    # 現状デプロイ時にワードクラウドは使用しない
    if not settings.DEBUG:
        return JsonResponse({'image_path': '/static/esuits/images/kanban_jyunbi.png'})

    # 以下開発環境
    # CompanyHomepageURLModelにwordcloud_pathが存在している場合はその画像のパスを取り出す
    try:
        wordcloud_path = CompanyHomepageURLModel\
            .objects.get(homepage_url=company_url).word_cloud_path

    # 存在しない場合は新しくワードクラウドを作成
    except CompanyHomepageURLModel.DoesNotExist:
        try:
            wordcloud_path = get_wordcloud(company_url)[1:]
             # データベースに保存

            new_word_cloud = CompanyHomepageURLModel(company=es_info.company,
                    homepage_url=company_url, word_cloud_path=wordcloud_path)
            new_word_cloud.save()
            print('created new word cloud')
        except:
            print('error from word_cloud')
            return JsonResponse({'image_path': '/static/esuits/images/wordcloud_failed.png'})

    # return JsonResponse({'image_path': wordcloud_path})
    homepage_url_record = CompanyHomepageURLModel.objects.get(homepage_url=company_url)
    wordcloud_path = homepage_url_record.word_cloud_path
    if wordcloud_path is None or wordcloud_path == 'dummy_path':
        wordcloud_path = get_wordcloud(company_url)[1:]
        # CompanyHomepageURLModelを更新
        homepage_url_record.word_cloud_path = wordcloud_path
        homepage_url_record.save()
    return JsonResponse({'image_path': wordcloud_path})
