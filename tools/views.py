from django.shortcuts import render,get_object_or_404
import json
import httpx
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .judge_utils import compile_solution_cached, batch_generate_and_run
import uuid
import zipfile
import os
import io
from celery.result import AsyncResult
from django.core.cache import cache
from django.http import HttpResponse
from .models import Tool
import logging
from django.conf import settings
from .tasks import task_ai_generate

logger = logging.getLogger(__name__)

######################################################################
# 在线C++工具
######################################################################
def check_tool_permission(request, tool_url_name):
    """
    检查工具是否需要密码，以及用户是否已解锁
    返回: (Tool对象, 是否允许访问)
    """
    # 根据 url_name 找到对应的工具 (注意：cpp_runner 对应的数据库 url_name 必须是 'cpp_runner')
    # 如果找不到工具，我们默认它不需要密码（或者你可以抛出404）
    tool = Tool.objects.filter(url_name=tool_url_name).first()

    if not tool:
        return None, True  # 工具没入库，默认允许访问

    if not tool.password:
        return tool, True  # 没有设置密码，直接允许

    # 检查 Session
    unlocked_list = request.session.get('unlocked_tools', [])
    if tool.id in unlocked_list:
        return tool, True  # 已经解锁过

    return tool, False  # 需要密码且未解锁

def tool_dashboard(request):
    """工具箱显示页"""
    tools = Tool.objects.filter(is_active=True)

    return render(request, "tools/dashboard.html", {"tools": tools})

def cpp_runner(request):
    """C++工具运行页面"""

    # 1. 检查权限
    tool, allowed = check_tool_permission(request, 'cpp_runner')

    # 2. 如果被锁住，渲染锁屏页面
    if tool and not allowed:
        return render(request, "tools/lock_screen.html", {"tool": tool})

    return render(request, "tools/cpp_runner.html")

async def get_sys_info(request):
    """获取编译器版本信息"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "cmd": [{
                    "args": ["/usr/bin/g++", "--version"],
                    "env": ["PATH=/usr/bin:/bin"],
                    "files": [{"content": ""}, {"name": "stdout", "max": 1024}, {"name": "stderr", "max": 1024}],
                    "cpuLimit": 1000000000,
                    "memoryLimit": 64 * 1024 * 1024,
                    "procLimit": 50
                }]
            }
            res = await client.post(f"{settings.GO_JUDGE_BASE_URL}/run", json=payload)
            data = res.json()[0]

            # 解析第一行，例如 "g++ (Alpine 12.2.1_git20220924-r10) 12.2.1 ..."
            raw_version = data['files']['stdout'].split('\n')[0]
            # 提取版本号数字 (可选)
            # version_match = re.search(r'g\+\+.*?(\d+\.\d+\.\d+)', raw_version)

            return JsonResponse({
                'compiler': raw_version,
                'memory_limit': settings.MEMORY_LIMIT_MB
            })
    except Exception as e:
        logger.exception(f"获取系统信息失败: {e}")
        return JsonResponse({'compiler': 'G++ (未知版本)', 'memory_limit': settings.MEMORY_LIMIT_MB})


async def run_cpp_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        user_input = data.get('input', '')
        use_o2 = data.get('use_o2', True)

        if not code:
            return JsonResponse({'error': '代码不能为空'}, status=400)

        async with httpx.AsyncClient() as client:

            # ==========================================
            # 第一步：编译请求
            # ==========================================
            # 基础参数
            compiler_args = ["/usr/bin/g++", "main.cpp", "-std=c++14", "-o", "main"]

            # 如果开启了优化，追加 -O2
            if use_o2:
                compiler_args.append("-O2")
            compile_payload = {
                "cmd": [{
                    "args": compiler_args,

                    "env": ["PATH=/usr/bin:/bin"],
                    "files": [
                        {"content": ""},  # 0: stdin
                        {"name": "stdout", "max": 10240},  # 1: stdout
                        {"name": "stderr", "max": 10240}  # 2: stderr (编译错误会在这里)
                    ],
                    "cpuLimit": 10000000000,  # 10秒编译时间
                    "memoryLimit": settings.MEMORY_LIMIT_BYTES,
                    "procLimit": 10,
                    # 关键：把代码写入文件
                    "copyIn": {
                        "main.cpp": {"content": code}
                    },
                    # 关键：缓存编译好的 'main' 文件，供下一步使用
                    "copyOutCached": ["main"]
                }]
            }

            res1 = await client.post(f"{settings.GO_JUDGE_BASE_URL}/run", json=compile_payload)
            result1 = res1.json()[0]  # 拿到第一个命令的结果

            # 1.1 检查编译是否成功
            if result1['status'] != 'Accepted':
                return JsonResponse({
                    'status': 'Compile Error',
                    'output': result1.get('files', {}).get('stderr', '编译失败，未知错误')
                })

            # 1.2 获取缓存的文件 ID
            main_file_id = result1.get('fileIds', {}).get('main')
            if not main_file_id:
                return JsonResponse({'error': '编译成功但未生成可执行文件'}, status=500)

            # ==========================================
            # 第二步：运行请求
            # ==========================================
            run_payload = {
                "cmd": [{
                    "args": ["./main"],
                    "env": ["PATH=/usr/bin:/bin"],
                    "files": [
                        {"content": user_input},  # 0: 用户输入
                        {"name": "stdout", "max": 1024 * 1024},  # 1: 运行结果
                        {"name": "stderr", "max": 1024 * 1024}  # 2: 运行时错误
                    ],
                    "cpuLimit": 2000000000,  # 2秒运行时间
                    "memoryLimit": settings.MEMORY_LIMIT_BYTES,
                    "stackLimit": settings.MEMORY_LIMIT_BYTES,
                    "procLimit": 6,
                    # 关键：使用上一步的 fileId 把可执行文件拷进来
                    "copyIn": {
                        "main": {"fileId": main_file_id}
                    }
                }]
            }

            res2 = await client.post(f"{settings.GO_JUDGE_BASE_URL}/run", json=run_payload)
            result2 = res2.json()[0]

            # ==========================================
            # 第三步：清理缓存 (无论运行成功与否)
            # ==========================================
            await client.delete(f"{settings.GO_JUDGE_BASE_URL}/file/{main_file_id}")

            # 组合输出
            output = result2['files'].get('stdout', '')
            error = result2['files'].get('stderr', '')
            return JsonResponse({
                'status': result2['status'],
                'output': output + error,
                'time': result2.get('time', 0) / 1000000,  # 纳秒 -> 毫秒
                'memory': result2.get('memory', 0) / 1024  # 字节 -> KB
            })
    except Exception as e:
        logger.exception(f"run_cpp_api error:  {e}")
        return JsonResponse({'error': "服务器错误！"}, status=500)


@require_POST
def api_unlock_tool(request):
    """验证密码并记录 Session"""
    try:
        data = json.loads(request.body)
        tool_id = data.get('tool_id')
        password = data.get('password')
        tool = get_object_or_404(Tool, id=tool_id)
        if tool.password == password:
            # 密码正确，写入 Session
            unlocked_list = request.session.get('unlocked_tools', [])
            if tool_id not in unlocked_list:
                unlocked_list.append(tool_id)
                request.session['unlocked_tools'] = unlocked_list
                request.session.modified = True  # 确保 Session 保存
                request.session.set_expiry(3600)   # 60分钟无操作自动过期

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': '密码错误，请重试'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': '服务器错误'})

######################################################################
# AI测试数据生成
######################################################################

def testcase_generator(request):
    """AI生成数据页面"""
    tool, allowed = check_tool_permission(request, 'testcase_generator')

    # 如果被锁住，渲染锁屏页面
    if tool and not allowed:
        return render(request, "tools/lock_screen.html", {"tool": tool})

    return render(request, "tools/testcase_gen.html")


async def api_ai_generate(request):
    """
    前端点击“生成”时调用此接口 使用celery
    """
    if request.method != 'POST':
        return JsonResponse({'error': '405'}, status=405)

    data = json.loads(request.body)
    desc = data.get('description', '')
    sol = data.get('solution', '')

    # 启动异步任务 (非阻塞)
    # 使用 .delay() 方法，这会立刻返回一个 AsyncResult 对象
    task = task_ai_generate.delay(desc, sol)

    # 秒回 task_id 给前端，前端去转圈圈
    return JsonResponse({'task_id': task.id})

def api_check_task(request):
    """
    前端轮询此接口检查任务状态
    """
    task_id = request.GET.get('task_id')
    if not task_id:
        return JsonResponse({'status': 'Error', 'error': 'No task_id'})

    # 查询 Celery 结果
    result = AsyncResult(task_id)

    if result.state == 'PENDING':
        response = {'state': 'PENDING', 'status': '排队中...'}
    elif result.state == 'STARTED':
        response = {'state': 'STARTED', 'status': 'AI 思考中...'}
    elif result.state == 'SUCCESS':
        # 任务成功，result.result 就是 tasks.py 里 return 的字典
        response = {
            'state': 'SUCCESS',
            'result': result.result
        }
    elif result.state == 'FAILURE':
        response = {'state': 'FAILURE', 'error': str(result.info)}
    else:
        response = {'state': result.state}

    return JsonResponse(response)


# API: 运行测试并缓存结果
async def api_run_testgen(request):
    if request.method != 'POST':
        return JsonResponse({'error': '405'}, status=405)

    data = json.loads(request.body)
    sol_code = data.get('solution', '')
    gen_code = data.get('gen_code', '')
    val_code = data.get('val_code', '')
    count = int(data.get('count', 5))
    if count < 1:
        count = 1
    if count > 20:
        count = 20

    file_id, error = await compile_solution_cached(sol_code)
    if not file_id: return JsonResponse({'status': 'Compile Error', 'error': error})

    try:
        results = await batch_generate_and_run(gen_code, val_code, file_id, count)

        # --- ZIP 打包逻辑 ---
        zip_uuid = str(uuid.uuid4())
        test_cases = []
        frontend_results = []

        for res in results:
            if res['status'] == 'Accepted':
                test_cases.append({
                    'id': res['id'],
                    'input': res.pop('full_input'),
                    'output': res.pop('full_output')
                })
            else:
                res.pop('full_input', None)
                res.pop('full_output', None)

            frontend_results.append(res)

        cache_payload = {
            'solution': sol_code,
            'gen_code': gen_code,
            'val_code': val_code,
            'cases': test_cases
        }

        # 存入 Redis/LocMemCache
        await cache.aset(f"testgen_zip_{zip_uuid}", cache_payload, timeout=600)

        return JsonResponse({
            'status': 'OK',
            'results': frontend_results,  # 轻量级结果
            'zip_id': zip_uuid  # 下载凭证
        })

    except Exception as e:
        logger.exception(f"run_cpp_api error:  {e}")
        return JsonResponse({'status': 'Error', 'error': str(e)})

    finally:
        # 删除编译好的标程二进制文件
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(f"{settings.GO_JUDGE_BASE_URL}/file/{file_id}")
        except Exception as cleanup_error:
            pass


def download_testcase_zip(request, zip_id):
    """根据 ID 打包下载"""
    cache_data = cache.get(f"testgen_zip_{zip_id}")

    if not cache_data:
        return HttpResponse("下载链接已过期或无效", status=404)

    # 兼容性处理
    if isinstance(cache_data, list):
        cases = cache_data
        gen_code = ""
        val_code = ""
        sol_code = ""  # 旧缓存可能没有
    else:
        cases = cache_data.get('cases', [])
        gen_code = cache_data.get('gen_code', '')
        val_code = cache_data.get('val_code', '')
        sol_code = cache_data.get('solution', '')  # <--- 获取标程

    # 用于记录需要删除的临时文件路径
    temp_files_to_clean = []

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. 写入代码文件
        if gen_code: zip_file.writestr("gen.py", gen_code)
        if val_code: zip_file.writestr("val.py", val_code)
        if sol_code: zip_file.writestr("sol.cpp", sol_code)

        # 2. 写入测试点
        for item in cases:
            idx = item['id']

            # --- 处理 Input ---
            inp_content = item.get('input', '')
            if inp_content and inp_content.startswith("__FILE_PATH__:"):
                file_path = inp_content.split(":", 1)[1]
                if os.path.exists(file_path):
                    zip_file.write(file_path, arcname=f"{idx}.in")
                    temp_files_to_clean.append(file_path)
                else:
                    zip_file.writestr(f"{idx}.in", "Error: Temp file missing (expired?)")
            else:
                zip_file.writestr(f"{idx}.in", inp_content)

            # --- 处理 Output ---
            # 如果 output 也是文件路径模式，同理处理（目前假设 output 是字符串）
            zip_file.writestr(f"{idx}.out", item.get('output', ''))

    # 3. 打包完成后，删除临时文件
    for f_path in temp_files_to_clean:
        try:
            if os.path.exists(f_path):
                os.remove(f_path)
        except Exception as e:
            pass
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="testcases_{zip_id[:8]}.zip"'
    return response