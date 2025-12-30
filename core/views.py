from django.shortcuts import render
from blog.models import Post
from game.models import Game

def index(request):
    # 1. 获取最新发布的 3 篇文章
    recent_posts = Post.objects.filter(status='published').select_related('category').order_by('-published_at')[:3]
    recent_games = Game.objects.filter(is_public=True).order_by('-created_at')[:3]    # 2. (可选) 获取热门文章或推荐文章

    context = {
        'recent_posts': recent_posts,
        'recent_games': recent_games,
    }
    return render(request, 'home.html', context)


def roadmap_view(request):
    return render(request, 'core/roadmap_gesp_csp.html')