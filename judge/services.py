# judge/services.py

from .judge_core.adapter import GoJudgeAdapter
from django.conf import settings

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

                "copyIn": {
                    "main.cpp": {"content": code}
                },

                "copyOutCached": ["main"]
            }]
        })

    @staticmethod
    async def run(
        file_id: str,
        input_data: str,
        time_limit_ms: int,
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
                "cpuLimit": time_limit_ms * 1_000_000_000,
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


