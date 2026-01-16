import asyncio
import os
import django
import sys

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from judge.services import PythonRunnerService, CppRunnerService


async def test_python_simple():
    print(">>> 测试 1: Python 基础运行 (Hello World)")
    code = "print('Hello Python Runner')"
    # 参数: code, input, time(s), mem(mb), proc
    res = await PythonRunnerService.run(code, "", 1, 128, 5)
    print(res)
    status = res['status']
    # 注意：run 返回的是 Go-Judge 原始 JSON，输出在 files.stdout
    output = res['files'].get('stdout', '').strip()

    print(f"   Status: {status}")
    print(f"   Output: {output}")

    assert status == 'Accepted'
    assert output == 'Hello Python Runner'
    print("✅ Python 基础运行测试通过\n")


async def test_python_library_penetration():
    print(">>> 测试 2: 环境穿透 (Cyaron 库检查)")
    # 这段代码将在沙箱里运行，试图引用宿主机的库
    code = """
import sys
try:
    import cyaron
    print(cyaron.__doc__)
except ImportError:
    print("IMPORT_ERROR: Cyaron not found")
except Exception as e:
    print(f"ERROR: {e}")
    """

    res = await PythonRunnerService.run(code, "", 2, 256, 10)
    output = res['files'].get('stdout', '').strip()
    stderr = res['files'].get('stderr', '').strip()
    if "IMPORT_ERROR" in output:
        print("⚠️  警告: Cyaron 未找到。请确认宿主机已安装 cyaron 且 settings.JUDGE_PYTHON_LIBS 路径正确。")
        print(f"   Stderr: {stderr}")
    else:
        print(f"   {output}")
        print("✅ 环境穿透测试通过 (成功加载 Cyaron)")
    print("\n")


async def test_gen_pipeline():
    print(">>> 测试 3: AI 生成流水线集成测试 (Gen + Sol)")

    # 1. 准备一个 C++ 标程 (A + B)
    print("   [Step 1] 编译 C++ 标程...")
    sol_code = """
    #include <iostream>
    using namespace std;
    int main() {
        long long a, b;
        if (cin >> a >> b) cout << (a + b) << endl;
        return 0;
    }
    """


    # 2. 准备 Python 生成器 (随机生成 A B)
    # 这里我们不用 cyaron，先用 random 确保基本流程通畅
    gen_code = """
import random
import sys
# 模拟 driver 传入的 seed
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
random.seed(seed)
print(f"{random.randint(1, 100)} {random.randint(1, 100)}")
    """

    # 3. 准备校验器
    val_code = "pass"

    # 4. 运行流水线 (并发生成 3 组)
    print("   [Step 2] 运行生成流水线 (Count=3)...")
    try:
        results = await PythonRunnerService.run_gen_pipeline(
            gen_code, val_code, sol_code, count=3
        )
        print(results)

        print("   [Step 3] 检查结果:")
        success_cnt = 0
        for res in results:
            print(f"    - Case #{res['id']}: {res['status']}")
            if res['status'] == 'Accepted':
                success_cnt += 1
                # 检查预览字段 (确保 files.py 里的 read_head 工作正常)
                print(f"      [Preview In]:  {res.get('input_preview', '').strip()}")
                print(f"      [Preview Out]: {res.get('output_preview', '').strip()}")
                print(f"      [Path]: {res.get('output_path')}")
            else:
                print(f"      Error: {res.get('error')}")

        if success_cnt == 3:
            print("✅ 流水线测试全部通过")
        else:
            print(f"⚠️ 流水线部分失败 ({success_cnt}/3 成功)")

    except Exception as e:
        print(f"❌ 流水线运行异常: {e}")
        import traceback
        traceback.print_exc()


def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_python_simple())
        loop.run_until_complete(test_python_library_penetration())
        loop.run_until_complete(test_gen_pipeline())
    finally:
        loop.close()


if __name__ == "__main__":
    run()