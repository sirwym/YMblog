from django.shortcuts import render,get_object_or_404,redirect
from django.core.paginator import Paginator
from .models import Post, Category, Tag
from django.db.models import Count,F
import markdown


def post_list(request):

    # 一次性查出分类和标签 避免N+1
    posts = Post.objects.filter(status='published').select_related('category').prefetch_related('tags').order_by('-published_at')

    # 筛选通过URL参数筛选分类和标签
    category_slug = request.GET.get('category')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    tag_slug = request.GET.get('tag')
    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)

    # 分页逻辑
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {
        'posts': page_obj,
        'categories': Category.objects.annotate(post_count=Count('post')),  #  侧边栏分类列表
        'tags': Tag.objects.all(),             #  侧边栏标签列表
    }

    if request.htmx:
        return render(request, 'blog/partials/post_rows.html', context)

    return render(request, 'blog/list.html', context)

def post_detail(request, slug):
    # 获取公开的文章
    post = get_object_or_404(Post, slug=slug, status='published')

    view_session_key = f'has_viewed_post_{post.id}' # 阅读量key
    if not request.session.get(view_session_key, False):
        Post.objects.filter(pk=post.pk).update(views=F('views') + 1)
        # 必须刷新！否则 post.views 在内存中还是个 F() 表达式，传给模板会显示不正常
        post.refresh_from_db()
        # 在 Session 中标记已读，防止刷新页面重复计数
        request.session[view_session_key] = True


    unlock_session_key = f'post_unlocked_{post.id}'
    # 如果文章有密码(is_encrypted) 且 Session里没有记录True，则视为锁定
    is_locked = post.is_encrypted and not request.session.get(unlock_session_key, False)
    error_message = None
    if request.method == 'POST':
        input_password = request.POST.get('password')
        if input_password == post.password:
            request.session[unlock_session_key] = True
            request.session.set_expiry(60 * 60 * 24)
            return redirect('blog:post_detail', slug=slug)
        else:
            error_message = "访问密码错误，请重新输入"
            is_locked = True  # 保持锁定状态

    post_content = ""
    post_toc = ""
    if not is_locked:  # 解锁才渲染markdown
        # markdown渲染配置
        md = markdown.Markdown(
            extensions=[
                'toc',
                'tables',
                'pymdownx.highlight',  # 替代 codehilite，代码高亮
                'pymdownx.superfences',  # 替代 fenced_code，支持更好看的代码块
                'pymdownx.arithmatex',  # 替代 mdx_math，修复数学公式渲染问题!!!
            ],
            extension_configs={
                # 1. 修复数学公式的关键配置
                'pymdownx.arithmatex': {
                    'generic': True,  # 开启通用模式，它会输出 \( ... \) 而不是 script 标签
                },
                # 2. 代码高亮配置
                'pymdownx.highlight': {
                    'css_class': 'mockup-code w-full highlight',
                    'linenums': False,
                    'use_pygments': True,
                },
                # 3. 允许代码块嵌套
                'pymdownx.superfences': {
                    "disable_indented_code_blocks": True
                }
            }
        )
        # 转换内容
        post_content = md.convert(post.content)

        # 获取目录 (TOC) - 稍后在模板里用
        post_toc = md.toc

    prev_post = Post.objects.filter(status='published', published_at__lt=post.published_at).order_by(
        '-published_at').first()
    next_post = Post.objects.filter(status='published', published_at__gt=post.published_at).order_by(
        'published_at').first()

    context = {
        'post': post,
        'content': post_content,
        'toc': post_toc,
        'prev_post': prev_post,
        'next_post': next_post,
        'is_locked': is_locked,  # 传给模板：是否锁定
        'error_message': error_message,  # 传给模板：错误提示
    }
    return render(request, 'blog/detail.html', context)