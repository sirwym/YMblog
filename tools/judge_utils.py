import httpx
from django.conf import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

# ==========================================
# 核心：Python 驱动脚本 (全内存接管版)
# ==========================================
# 变更点：
# 1. 移除 stdout=f_out，改为 stdout=subprocess.PIPE
# 2. 使用 communicate() 强制读取所有输出直到 EOF
# 3. 移除 "-u" 参数，使用 Python 默认缓冲机制以提高性能
# 4. 手动写入文件并 flush/fsync
DRIVER_SCRIPT = r"""
import sys
import subprocess
import os

def main():
    # --- Step 1: 运行生成器 (内存接管) ---
    # 不再直接重定向到文件，而是读到内存，确保数据完整
    cmd_gen = [sys.executable, "gen.py"] + sys.argv[1:]

    try:
        # 使用 PIPE 捕获输出
        proc = subprocess.Popen(cmd_gen, stdout=subprocess.PIPE, stderr=sys.stderr)
        # communicate() 会阻塞直到进程结束并读取所有数据
        stdout_data, _ = proc.communicate()

        if proc.returncode != 0:
            sys.stderr.write(f"\n[Driver] Generator failed with exit code {proc.returncode}\n")
            sys.exit(proc.returncode)

    except Exception as e:
        sys.stderr.write(f"\n[Driver] Execution error: {e}\n")
        sys.exit(1)

    # --- Step 2: 显式写入磁盘 ---
    try:
        with open("case.in", "wb") as f:
            f.write(stdout_data)
            f.flush()
            os.fsync(f.fileno()) # 强制落盘

        # 调试日志：确认写入字节数
        sys.stderr.write(f"[Driver] Successfully wrote {len(stdout_data)} bytes to case.in\n")

    except Exception as e:
        sys.stderr.write(f"\n[Driver] Disk write error: {e}\n")
        sys.exit(1)

    # --- Step 3: 运行校验器 ---
    if os.path.exists("val.py"):
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


def pick_scale_10(i):
    if i <= 3:
        return 0
    elif i <= 6:
        return 1
    else:
        return 2


async def compile_solution_cached(code):
    """Step 1: 编译标程并缓存"""
    async with httpx.AsyncClient() as client:
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
            logger.exception("Compile Error")
            return None, str(e)


async def batch_generate_and_run(gen_code, val_code, sol_file_id, count=5):
    tasks = []
    for i in range(count):
        seed = i + 1000
        scale = pick_scale_10(i)
        tasks.append(_run_pipeline(gen_code, val_code, sol_file_id, seed, scale, i + 1))
    return await asyncio.gather(*tasks)


async def _run_pipeline(gen_code, val_code, sol_file_id, seed, scale, index):
    async with httpx.AsyncClient() as client:
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
                    {"name": "stderr", "max": 4096}
                ],
                "cpuLimit": 5000000000,
                "memoryLimit": settings.MEMORY_LIMIT_BYTES,  # 确保内存足够容纳生成的数据
                "procLimit": 20,
                "copyIn": copy_in,
                "copyOutCached": ["case.in"]
            }]
        }

        try:
            gen_res = await client.post(f"{settings.GO_JUDGE_BASE_URL}/run", json=gen_payload)

            if gen_res.status_code != 200:
                return _make_error_result(index, seed, "Judge Error", f"HTTP {gen_res.status_code}: {gen_res.text}")

            gen_results = gen_res.json()
            if not gen_results:
                return _make_error_result(index, seed, "Judge Error", "Empty response")
            gen_data = gen_results[0]

            if gen_data['status'] != 'Accepted' or gen_data['exitStatus'] != 0:
                err_msg = gen_data['files'].get('stderr', '')
                if not err_msg: err_msg = f"Exit Code: {gen_data.get('exitStatus')}"
                if len(err_msg) > 800: err_msg = err_msg[:800] + "..."
                return _make_error_result(index, seed, "Data Error", err_msg)

            input_file_id = gen_data.get('fileIds', {}).get('case.in')
            if not input_file_id:
                return _make_error_result(index, seed, "Gen Error", "case.in missing")

            input_preview = "Data OK"
            input_full_str = ""

            file_res = await client.get(f"{settings.GO_JUDGE_BASE_URL}/file/{input_file_id}")
            if file_res.status_code == 200:
                input_bytes = file_res.content
                input_full_str = input_bytes.decode('utf-8', errors='replace')
                input_preview = input_full_str[:200] + "..." if len(input_full_str) > 200 else input_full_str

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
                    {"fileId": input_file_id, "max": 100 * 1024 * 1024},
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


def _make_error_result(idx, seed, status, msg):
    msg_str = str(msg) if msg is not None else ""
    return {
        "id": idx, "seed": seed, "status": status,
        "time": 0, "memory": 0,
        "input_preview": "N/A", "output_preview": msg_str,
        "full_input": "", "full_output": ""
    }