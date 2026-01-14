# judge/services.py

from .judge_core.adapter import GoJudgeAdapter
from django.conf import settings
from .judge_core.files import FileManager
import asyncio
import os

STD_MAP = {
    11: "c++11",
    14: "c++14",
    17: "c++17",
    20: "c++20",
}


class CppRunnerService:

    @staticmethod
    async def compile(code: str,
                      use_o2: bool = True,
                      std: int = 14,
                      memory_limit_mb: int = 256,
                            proc_limit: int = 10
        ):
        compile_args = ["/usr/bin/g++", "main.cpp", "-o", "main"]

        if use_o2:
            compile_args.append("-O2")

        compile_args.append(f"-std={STD_MAP.get(std, 'c++14')}")
        compile_args.append("-pipe")

        return await GoJudgeAdapter.run({
            "cmd": [{
                "args": compile_args,
                "env": ["PATH=/usr/bin:/bin"],

                "files": [
                    {"name": "stdin", "content": ""},
                    {"name": "stdout", "max": 1024},
                    {"name": "stderr", "max": 10240}
                ],

                "cpuLimit": 5_000_000_000,
                "memoryLimit": memory_limit_mb * 1024 * 1024,
                "procLimit": proc_limit,

                "copyIn": {"main.cpp": {"content": code}},

                "copyOutCached": ["main"]
            }]
        })

    @staticmethod
    async def run(
        file_id: str,
        input_data: str,
        time_limit_s: int,
        memory_limit_mb: int,
    ):
        return await GoJudgeAdapter.run({
            "cmd": [{
                "args": ["./main"],
                "env": ["PATH=/usr/bin:/bin"],

                "files": [
                    {"name": "stdin", "content": input_data},
                    {"name": "stdout", "max": 256 * 1024 * 1024},
                    {"name": "stderr", "max": 64 * 1024 * 1024}
                ],

                # ✅ 对齐 Codeforces 运行模型
                "cpuLimit": time_limit_s * 1_000_000_000,
                "memoryLimit": memory_limit_mb * 1024 * 1024,
                "procLimit": 1,

                "copyIn": {
                    "main": {"fileId": file_id}
                }
            }]
        })

    @staticmethod
    async def compile_and_run(code: str, input_data: str, use_o2: bool = True, std: int = 14):
        # 1. 编译
        compile_res = await CppRunnerService.compile(code, use_o2=use_o2, std=std)
        print(compile_res)
        if compile_res['status'] != 'Accepted':
            return {
                "status": "Compile Error",
                "output": compile_res['files'].get('stderr', 'Unknown Error')
            }

        file_id = compile_res.get('fileIds', {}).get('main')

        # 2. 运行
        run_res = await CppRunnerService.run(file_id,input_data, 1, 512)

        # 3. 清理
        await GoJudgeAdapter.cleanup(file_id)

        return {
            "status": run_res['status'],
            "time": run_res.get('time', 0) // 1000000,
            "memory": run_res.get('memory', 0) // 1024,
            "output": run_res['files'].get('stdout', '') + run_res['files'].get('stderr', '')
        }



class PythonRunnerService:

    @staticmethod
    async def run(code: str, input_data: str, time_limit_s: int, memory_limit_mb: int, proc_limit: int):
        """
        简单运行 Python 代码 (用于在线运行器)
        模式: 纯内存流 (小数据) 或 文件挂载 (大数据)
        这里演示最简单的内存流模式，支持引用宿主机库
        """
        return await GoJudgeAdapter.run({
            "cmd": [{
                "args": ["python3", "main.py"],
                "env": ["PATH=/usr/bin:/bin"],
                "files": [
                    {"name": "stdin", "content": input_data},
                    {"name": "stdout", "max": 1024 * 1024},
                    {"name": "stderr", "max": 1024 * 1024}
                ],
                "cpuLimit": time_limit_s * 1_000_000_000,
                "copyIn": {"main.py": {"content": code}},
                "memoryLimit": memory_limit_mb * 1024 * 1024,
                "procLimit": proc_limit,
            }]
        })

    @staticmethod
    async def run_gen_pipeline(gen_code: str, val_code: str, sol_code: str, count: int = 5):
        """
        AI 测试点生成流水线
        """
        # 1. 创建任务 ID (仅创建目录，返回 ID 字符串)
        run_id = FileManager.create_run_dir()
        container_run_path = f"/judge_run_data/{run_id}"
        sol_file_id = None

        try:
            # 1. 写入 Python 脚本到宿主机目录
            FileManager.write_file(run_id, "gen.py", gen_code)
            FileManager.write_file(run_id, "val.py", val_code)
            FileManager.write_file(run_id, "sol.cpp", sol_code)

            # 2. 编译标程 (结果存在内存 fileId 中，非常快)
            compile_res = await CppRunnerService.compile(sol_code)
            if compile_res['status'] != 'Accepted':
                return [{"id": 0, "status": "Compile Error", "error": compile_res['files'].get('stderr')}]

            sol_file_id = compile_res['fileIds']['main']

            # 3. 并发执行
            sem = asyncio.Semaphore(4)
            tasks = []
            for i in range(count):
                tasks.append(PythonRunnerService._execute_single_case(
                    sem,
                    i + 1,
                    run_id,  # 传入 ID
                    container_run_path,
                    sol_file_id,
                    count
                ))

            results = await asyncio.gather(*tasks)

            # 4. ✅ 新增步骤：打包整个文件夹为 ZIP
            # 只有当全部成功或者部分成功时才打包，根据你的需求调整
            zip_path = FileManager.pack_run_data(run_id, f"problem_data_{run_id}.zip")

            # 你可以将 zip_path 返回给前端，或者只返回 run_id 让前端去拼下载链接
            print(f"Data package created at: {zip_path}")

            return results
        finally:
            if sol_file_id:
                await GoJudgeAdapter.cleanup(sol_file_id)

    @staticmethod
    async def _execute_single_case(sem, idx, run_id, work_dir, sol_file_id, total_count):
        """
        """
        async with sem:
            seed = idx + 1000
            scale = 0 if idx <= 2 else (2 if idx > total_count - 2 else 1)

            case_in = f"{work_dir}/{idx}.in"  # 容器内绝对路径
            case_out = f"{work_dir}/{idx}.out"  # 容器内绝对路径
            print(f"work_dir: {work_dir}")

            # === Step 1: 运行生成器 ===
            gen_res = await GoJudgeAdapter.run({
                "cmd": [{
                    "args": [
                        "python3",
                        "/assets/bin/driver.py",  # driver 在全局 assets 目录
                        work_dir,
                        str(seed),
                        str(scale),
                        case_in
                    ],
                    "env": [
                        "PATH=/usr/bin:/bin",
                    ],
                    # 不需要 mounts 参数，因为我们依靠 docker-compose 的全局挂载
                    "files": [
                        {"name": "stdin", "content": ""},
                        {"name": "stdout", "max": 1024},
                        {"name": "stderr", "max": 4096}
                    ],
                    "memoryLimit": 128 * 1024 * 1024,
                    "cpuLimit": 15_000_000_000,
                    "procLimit": 10
                }]
            })

            # 错误检查
            if gen_res['status'] != 'Accepted' or gen_res['exitStatus'] != 0:
                err_msg = gen_res['files'].get('stderr', '')
                if not err_msg:
                    err_msg = f"Exit Code {gen_res.get('exitStatus')} (No stderr)"
                return {
                    "id": idx, "status": "Gen Error",
                    "error": err_msg
                }

            # === Step 2: 运行 C++ 标程 (零拷贝流) ===
            sol_res = await GoJudgeAdapter.run({
                "cmd": [{
                    # 逻辑：./sol < 输入文件 > 输出文件
                    # 因为 cwd 已经是 work_dir，直接用文件名即可
                    "args": ["sh", "-c", f"./sol < {case_in} > {case_out}"],
                    "files": [
                        {"name": "stdout", "max": 1024},
                        {"name": "stderr", "max": 1024}
                    ],
                    "env": ["PATH=/usr/bin:/bin",],
                    # sol 文件会被复制到 work_dir 下
                    "copyIn": {"sol": {"fileId": sol_file_id}},
                    "memoryLimit": 128 * 1024 * 1024,
                    "cpuLimit": 2_000_000_000,
                    "procLimit": 10,
                }]
            })
            print(sol_res)
            if sol_res['status'] != 'Accepted':
                return {"id": idx, "status": sol_res['status'], "error": "Solution Error"}

            # 构造宿主机路径用于预览读取 (Django 侧)
            host_class_in = FileManager.BASE_DIR / run_id / os.path.basename(case_in)
            host_class_out = FileManager.BASE_DIR / run_id / os.path.basename(case_out)
            input_prev = FileManager.read_head(host_class_in, 100)
            output_prev = FileManager.read_head(host_class_out, 100)

            return {
                "id": idx,
                "status": "Accepted",
                "input_path": host_class_in,
                "output_path": host_class_out,
                "input_preview": input_prev,
                "output_preview": output_prev
            }