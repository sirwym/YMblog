import httpx
from django.conf import settings
import asyncio
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

LARGE_FILE_THRESHOLD = 1024 * 1024  # 1MB 阈值
PREVIEW_SIZE = 4096  # 4KB

# ==========================================
# 核心：Python 驱动脚本
# ==========================================
DRIVER_SCRIPT = r"""
import sys
import subprocess
import os

def main():
    # --- Step 1: 运行生成器 ---
    cmd_gen = [sys.executable, "gen.py"] + sys.argv[1:]

    try:
        with open("case.in", "wb") as f_out:
            # check=True 会在进程返回非0时抛出 CalledProcessError
            subprocess.run(cmd_gen, stdout=f_out, stderr=sys.stderr, check=True)

    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"\n[Driver] Generator Exit: {e.returncode}\n")
        sys.exit(e.returncode)
    except Exception as e:
        sys.stderr.write(f"\n[Driver] Error: {e}\n")
        sys.exit(1)

    # --- Step 2: 运行校验器 ---
    if os.path.exists("val.py"):
        # 校验器需要读文件，这里用 rb 打开传给 stdin
        with open("case.in", "rb") as f_in:
            cmd_val = [sys.executable, "val.py"]
            ret_val = subprocess.run(cmd_val, stdin=f_in, stderr=sys.stderr)

        if ret_val.returncode != 0:
            sys.stderr.write(f"\n[Driver] Validator Failed with exit code {ret_val.returncode}\n")
            sys.exit(ret_val.returncode)

    print("Pipeline Success")

if __name__ == "__main__":
    main()
"""


def pick_scale(total_cases, idx):
    """
    根据总数和当前索引智能选择规模
    """
    if total_cases == 5:
        thresholds = [2, 4, 5]
    elif total_cases == 10:
        thresholds = [4, 7, 10]
    else:
        thresholds = [6, 13, 20]  # 20组时：前6个小，中7个，后7个大

    if idx < thresholds[0]:
        return 0  # 基础/边界
    elif idx < thresholds[1]:
        return 1  # 中等
    else:
        return 2  # 极限 (注意：Scale=2 时不会下载完整数据)


async def compile_solution_cached(code):
    """Step 1: 编译标程并缓存"""
    # 🌟 修改点1：增加 timeout，防止编译超时导致系统错误
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "cmd": [{
                "args": ["/usr/bin/g++", "sol.cpp", "-O2", "-std=c++14", "-o", "sol"],
                "env": ["PATH=/usr/bin:/bin"],
                "files": [
                    {"content": ""},
                    {"name": "stdout", "max": 1024},
                    {"name": "stderr", "max": 10240}
                ],
                "cpuLimit": 10000000000,
                "memoryLimit": settings.MEMORY_LIMIT_BYTES,
                "copyIn": {"sol.cpp": {"content": code}},
                "procLimit": 10,
                "copyOutCached": ["sol"]
            }]
        }
        try:
            res = await client.post(f"{settings.GO_JUDGE_BASE_URL}/run", json=payload)
            if res.status_code != 200: return None, f"Judge Server Error: {res.text}"
            result = res.json()[0]
            if result['status'] != 'Accepted': return None, result['files'].get('stderr', 'Compile Error')
            return result['fileIds']['sol'], None
        except Exception as e:
            logger.exception(f"Compile Error: {e}")
            return None, str(e)


async def _run_pipeline_with_sem(sem, *args, **kwargs):
    """
    包装器：在运行前获取信号量锁
    """
    async with sem:
        return await _run_pipeline(*args, **kwargs)


async def batch_generate_and_run(gen_code, val_code, sol_file_id, count=5):
    # 🌟 核心修复：在当前事件循环中创建信号量，避免 EventLoop 绑定错误
    sem = asyncio.Semaphore(5)

    tasks = []
    for i in range(count):
        seed = i + 1000
        scale = pick_scale(count, i)
        tasks.append(_run_pipeline_with_sem(sem, gen_code, val_code, sol_file_id, seed, scale, i + 1))
    return await asyncio.gather(*tasks)


async def _run_pipeline(gen_code, val_code, sol_file_id, seed, scale, index):
    async with httpx.AsyncClient(timeout=30.0) as client:
        # ==========================================
        # Step 1: 生成 + 校验 + 保存 (Driver 模式)
        # ==========================================
        copy_in = {
            "driver.py": {"content": DRIVER_SCRIPT},
            "gen.py": {"content": gen_code}
        }
        if val_code and val_code.strip():
            copy_in["val.py"] = {"content": val_code}

        gen_payload = {
            "cmd": [{
                "args": ["python3", "driver.py", str(seed), str(scale)],
                "env": ["PATH=/usr/bin:/bin"],
                "files": [
                    {"content": ""},
                    {"name": "stdout", "max": 1024},
                    {"name": "stderr", "max": 4096}  # 捕获 Driver 的报错信息
                ],
                "cpuLimit": 15000000000,
                "memoryLimit": settings.MEMORY_LIMIT_BYTES,
                "procLimit": 20,
                "copyIn": copy_in,
                "copyOutCached": ["case.in"]  # 缓存生成的输入文件
            }]
        }

        input_file_id = None
        try:
            gen_res = await client.post(f"{settings.GO_JUDGE_BASE_URL}/run", json=gen_payload)

            if gen_res.status_code != 200:
                return _make_error_result(index, seed, "Judge Error", f"HTTP {gen_res.status_code}")

            gen_results = gen_res.json()
            if not gen_results: return _make_error_result(index, seed, "Judge Error", "Empty response")
            gen_data = gen_results[0]

            # 🌟 修改点4：处理超时 (Exit Status 137/124) 或其他非0退出
            if gen_data['status'] != 'Accepted' or gen_data['exitStatus'] != 0:
                err_msg = gen_data['files'].get('stderr', '')
                status_label = "Data Error"

                # 细化错误类型
                if gen_data['status'] == 'Time Limit Exceeded':
                    status_label = "Gen TLE"
                    err_msg = "Generator timed out (Python is too slow)"
                elif not err_msg:
                    err_msg = f"Exit Code: {gen_data.get('exitStatus')}"

                if len(err_msg) > 800: err_msg = err_msg[:800] + "..."
                return _make_error_result(index, seed, status_label, err_msg)

            input_file_id = gen_data.get('fileIds', {}).get('case.in')
            if not input_file_id:
                return _make_error_result(index, seed, "Gen Error", "case.in missing")

            input_preview = "Data OK"
            input_full_str = ""
            total_size = 0
            preview_content = b""  # 保存二进制内容，避免重复解码

            # 1. 下载预览
            try:
                preview_res = await client.get(
                    f"{settings.GO_JUDGE_BASE_URL}/file/{input_file_id}",
                    headers={"Range": f"bytes=0-{PREVIEW_SIZE}"}  # 关键：Range Header
                )
                preview_content = preview_res.content

                if preview_res.status_code in [200, 206]:
                    preview_data = preview_res.content.decode('utf-8', errors='replace')
                    input_preview = preview_data[:1000] + ("..." if len(preview_data) >= 1000 else "")

                if preview_res.status_code == 206:
                    # 格式: Content-Range: bytes 0-1024/50000
                    content_range = preview_res.headers.get('content-range', '')
                    if '/' in content_range:
                        total_size = int(content_range.split('/')[-1])
                elif preview_res.status_code == 200:
                    # 小文件，Content-Length 即为总大小
                    total_size = int(preview_res.headers.get('content-length', len(preview_res.content)))

            except Exception:
                input_preview = "Preview Fetch Failed"
                if scale >= 2: total_size = 999999999  # 保底

            if total_size > LARGE_FILE_THRESHOLD:
                # 大数据模式：落盘
                try:
                    fd, temp_path = tempfile.mkstemp(suffix=".in")
                    os.close(fd)
                    # 🌟 修改点5：下载大文件时也使用 stream，避免内存爆炸
                    async with client.stream("GET", f"{settings.GO_JUDGE_BASE_URL}/file/{input_file_id}") as resp:
                        if resp.status_code == 200:
                            with open(temp_path, "wb") as f:
                                async for chunk in resp.aiter_bytes():
                                    f.write(chunk)
                            input_full_str = f"__FILE_PATH__:{temp_path}"
                        else:
                            input_full_str = "Download Failed"
                except Exception as e:
                    input_full_str = f"Save Error: {str(e)}"
            else:
                # 小数据模式：内存
                if 0 < total_size <= (PREVIEW_SIZE + 1) and preview_content:
                    # 直接使用预览请求的数据，0 额外请求！
                    input_full_str = preview_content.decode('utf-8', errors='replace')
                else:
                    # 文件大小在 2KB ~ 1MB 之间，或者之前的预览请求失败了
                    full_res = await client.get(f"{settings.GO_JUDGE_BASE_URL}/file/{input_file_id}")
                    if full_res.status_code == 200:
                        input_full_str = full_res.content.decode('utf-8', errors='replace')
                    else:
                        input_full_str = "Fetch Failed"

        except Exception as e:
            return _make_error_result(index, seed, "Sys Error", str(e))

        # ==========================================
        # Step 2: 运行标程
        # ==========================================
        sol_payload = {
            "cmd": [{
                "args": ["./sol"],
                "env": ["PATH=/usr/bin:/bin"],
                "files": [
                    {"fileId": input_file_id, "max": 100 * 1024 * 1024},  # 直接使用 ID
                    {"name": "stdout", "max": 50 * 1024 * 1024},
                    {"name": "stderr", "max": 1024}
                ],
                "cpuLimit": 2000000000,
                "memoryLimit": settings.MEMORY_LIMIT_BYTES,
                "procLimit": 6,
                "copyIn": {"sol": {"fileId": sol_file_id}}
            }]
        }

        try:
            sol_res = await client.post(f"{settings.GO_JUDGE_BASE_URL}/run", json=sol_payload)
            if sol_res.status_code != 200:
                return _make_error_result(index, seed, "Judge Error", f"Sol HTTP {sol_res.status_code}")

            sol_data = sol_res.json()[0]

            if sol_data['status'] != 'Accepted':
                return _make_error_result(index, seed, sol_data['status'], sol_data['files'].get('stderr', ''))

            output_full = sol_data['files'].get('stdout', '')
            output_preview = output_full[:200] + "..." if len(output_full) > 200 else output_full

            return {
                "id": index,
                "seed": seed,
                "status": sol_data['status'],
                "time": sol_data.get('time', 0) // 1000000,
                "memory": sol_data.get('memory', 0) // 1024,
                "input_preview": input_preview,
                "output_preview": output_preview,
                "full_input": input_full_str,
                "full_output": output_full
            }
        except Exception as e:
            return _make_error_result(index, seed, "Run Error", str(e))

        finally:
            # 清理中间文件
            if input_file_id:
                try:
                    await client.delete(f"{settings.GO_JUDGE_BASE_URL}/file/{input_file_id}")
                except Exception:
                    pass


def _make_error_result(idx, seed, status, msg):
    msg_str = str(msg) if msg is not None else ""
    return {
        "id": idx, "seed": seed, "status": status,
        "time": 0, "memory": 0,
        "input_preview": "N/A", "output_preview": msg_str,
        "full_input": "", "full_output": ""
    }