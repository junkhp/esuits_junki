from django.db.models.query import QuerySet
from django.forms.formsets import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import View
from django.http.response import JsonResponse
from django.conf import settings
from django import forms
from pprint import pprint

from .forms import AnswerUpdateFormSet, AnswerFormSet
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

    # 回答の文字数を計算(いらないかも)
    def _get_char_num(self, answer_text):
        return len(answer_text)

    # sessionに詰めるための辞書型の情報を作成
    def _make_post_information(self, request_post, questions):
        '''
        作成する辞書は下記の通り
        {
            question_num: 質問数
            question_pk: 履歴管理をする質問のPK
            n番目の質問のPK: n番目の質問に対する回答
        }
        '''
        post_information_dict = {}
        question_num = int(request_post['form-TOTAL_FORMS'])
        question_pk = int(request_post['question_pk'])
        post_information_dict['question_num'] = question_num
        post_information_dict['question_pk'] = question_pk
        for i, question in enumerate(questions):
            answer_text = request_post['form-{}-answer'.format(i)]
            post_information_dict[question.pk] = answer_text
        return post_information_dict

    # formsetの初期値のための辞書をリストに変換
    def _convert_initial_dict_to_list(self, initial_dict):
        '''
        initialは辞書のリスト
        '''
        question_pk_key = 'question_pk'
        answer_key = 'answer'
        initial_list = []
        for question_pk, answer_and_char_num in initial_dict.items():
            initial_list.append({
                question_pk_key: question_pk,
                answer_key: answer_and_char_num,
                })
        return initial_list

    # formsetの初期値のための辞書を作成、回答の文字数のリストも作成
    def _make_initial_dict(self, questions):
        initial = {}
        char_num_list = []
        all_answers = AnswerModel.objects.filter(question__in=questions)
        for question in questions:
            version = question.selected_version
            answer_record = all_answers.get(question=question, version=version)
            initial[question.pk] = answer_record.answer
            char_num_list.append(answer_record.char_num)
        return initial, char_num_list

    def _get_char_num_list(self, questions):
        char_num_list = []
        all_answers = AnswerModel.objects.filter(question__in=questions)
        for question in questions:
            char_num_list.append(
                all_answers.get(question=question, version=question.selected_version).char_num
            )
        return char_num_list

    def get(self, request, es_id):
        template_name = 'esuits/es_edit.html'
        if EntrySheetesModel.objects.filter(pk=es_id).exists():
            # ESの存在を確認
            es_info = EntrySheetesModel.objects.get(pk=es_id)

            if (es_info.author == request.user):
                # 指定されたESが存在し，それが自分のESの場合
                questions = QuestionModel.objects.filter(entry_sheet=es_id).order_by('pk')
                formset_initial_dict, char_num_list = self._make_initial_dict(questions)

                # 編集→履歴→編集の場合
                post_information_key = 'post_information'
                if post_information_key in request.session:
                    post_information = request.session[post_information_key]
                    del request.session[post_information_key]
                    for i, question in enumerate(questions):
                        question_pk = question.pk
                        answer_text = post_information[str(question_pk)]
                        if question_pk != post_information['question_pk']:
                            formset_initial_dict[question_pk] = answer_text
                            char_num_list[i] = len(answer_text)
                            
                formset_initial = self._convert_initial_dict_to_list(formset_initial_dict)
                formset = AnswerFormSet(initial=formset_initial)

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
                    'zipped_posts_info': zip(questions, formset, char_num_list, related_posts_list),
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
                    formset = AnswerFormSet(request.POST)
                    if formset.is_valid():
                        for form in formset:
                            question = questions.get(pk=form.cleaned_data['question_pk'])
                            # 更新する回答レコードを作成
                            upd_answer_record = AnswerModel.objects.get(
                                question=question, version=question.selected_version)
                            answer_text = form.cleaned_data['answer']
                            upd_answer_record.answer = answer_text
                            upd_answer_record.char_num = len(answer_text)

                            upd_answer_record.save()
                        return redirect('esuits:home')
                
                    # formsetのvalidationがFalseのとき
                    # 関連したポスト一覧
                    related_posts_list = self._get_related_posts_list(request, es_id)
                    # ニュース関連
                    news_list = newsapi.get_news(es_info.company)
                    # 企業の情報(ワードクラウドなど)
                    company_info = self._get_company_info(request, es_id)
                    # 文字数を取得
                    char_num_list = self._get_char_num_list(questions)

                    context = {
                        'message': 'OK',
                        'es_info': es_info,
                        'formset_management_form': formset.management_form,
                        'zipped_posts_info': zip(
                            questions, formset, char_num_list, related_posts_list),
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
            questions = QuestionModel.objects.filter(entry_sheet__pk=es_id).order_by('pk')
            question_id = int(request.POST[question_pk_message])

            # リクエストから現状の回答を取り出してセッションに保存
            request.session['post_information'] = self._make_post_information(
                request.POST, questions)

            # 履歴管理画面に遷移
            return redirect('esuits:answer_history', question_id=question_id)
        else:
            return redirect('esuits:home')


def get_related_post(request):
    question_pk = request.GET.get('pk', '')
    question = QuestionModel.objects.get(pk=question_pk)
    answer = AnswerModel.objects.get(question=question, version=question.selected_version)
    return JsonResponse({'question': question.question, 'answer': answer.answer})


def get_wordcloud_path(request):
    image_path_key = 'image_path'
    failed_image_path = '/static/esuits/images/wordcloud_failed.png'
    preparing_image_path = '/static/esuits/images/kanban_jyunbi.png'
    es_id = request.GET.get('es_group_id', '')
    es_record = EntrySheetesModel.objects.get(pk=es_id)
    company_url_record = CompanyHomepageURLModel.objects.get(pk=es_record.homepage_url.pk)
    homepage_url = company_url_record.homepage_url

    # 現状デプロイ時にワードクラウドは使用しない
    if not settings.DEBUG:
        return JsonResponse({image_path_key: preparing_image_path})

    # 以下開発環境
    # CompanyHomepageURLModelにwordcloud_pathが存在している場合はその画像のパスを取り出す
    try:
        homepage_url_record = CompanyHomepageURLModel.objects.get(homepage_url=homepage_url)
        word_cloud_path = homepage_url_record.word_cloud_path

    # URLが存在しない場合
    except:
        return JsonResponse({image_path_key: failed_image_path})

    if word_cloud_path is None:
        try:
            word_cloud_path = get_wordcloud(homepage_url)[1:]
            # CompanyHomepageURLModelを更新
            homepage_url_record.word_cloud_path = word_cloud_path
            homepage_url_record.save()
        except:
            return JsonResponse({image_path_key: failed_image_path})
    return JsonResponse({image_path_key: word_cloud_path})
