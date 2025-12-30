from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import ImageUpload


@login_required  # 必须登录才能上传 (如果是 PicGo 需要改为 Token 认证，这里先做浏览器端的)
@require_POST
def upload_image_api(request):
    """
    简单的图片上传 API
    接收字段: 'file'
    返回: { "url": "/media/...", "name": "..." }
    """
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    file = request.FILES['file']

    # 创建记录
    image = ImageUpload.objects.create(
        user=request.user,
        file=file,
        name=file.name
    )

    return JsonResponse({
        'location': image.file.url,  # 这是 TinyMCE/CKEditor 等编辑器通用的返回字段
        'url': image.file.url,  # 通用字段
        'name': image.name
    })