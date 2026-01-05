from django.shortcuts import render, get_object_or_404
from django.db.models import F
from .models import GameCategory
from django.core.paginator import Paginator
from .models import Game
import logging

logger = logging.getLogger(__name__)

def game_list(request):
    latest_games = Game.objects.filter(is_public=True).select_related('category').prefetch_related('tags')

    category_slug = request.GET.get('category')
    if category_slug:
        latest_games = latest_games.filter(category__slug=category_slug)

    sort_param = request.GET.get('sort', 'newest')
    sort_options = {
        'newest': '-created_at',  # 最新发布 (时间降序)
        'oldest': 'created_at',  # 最早发布 (时间升序)
        'hot': '-likes_count',  # 点赞最多
        'cold': 'likes_count',  # 点赞最少
    }
    order_by_field = sort_options.get(sort_param, '-created_at')
    latest_games = latest_games.order_by(order_by_field)

    paginator = Paginator(latest_games, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # 生成智能页码范围
    custom_page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1)

    context = {
        'categories': GameCategory.objects.all(),
        'latest_games': page_obj,
        'custom_page_range': custom_page_range,  # 传给模板用于生成按钮
        'current_category': category_slug,  # 传回当前分类，用于翻页时保持筛选状态
        'current_sort': sort_param
    }
    return render(request, 'game/list.html', context)


def game_detail(request, slug):
    game  = get_object_or_404(Game.objects.select_related('category'), slug=slug, is_public=True)
    like_session_key = f'has_liked_game_{game.id}'
    is_liked = request.session.get(like_session_key, False)


    context = {
        'game': game,
        'is_liked': is_liked
    }
    return render(request, 'game/detail.html', context)


def like_game(request, slug):
    game = get_object_or_404(Game, slug=slug, is_public=True)
    like_session_key = f'has_liked_game_{game.id}'
    is_liked = request.session.get(like_session_key, False)

    if request.method == "POST":
        if is_liked:
            if game.likes_count > 0:
                Game.objects.filter(pk=game.pk).update(likes_count=F('likes_count') - 1)

            del request.session[like_session_key]
            is_liked = False
        else:
            Game.objects.filter(pk=game.pk).update(likes_count=F('likes_count') + 1)

            request.session[like_session_key] = True
            is_liked = True

        game.refresh_from_db()
    return render(request, 'game/partials/like_button.html', {
        'game': game,
        'is_liked': is_liked
    })
