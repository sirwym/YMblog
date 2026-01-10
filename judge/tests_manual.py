# judge/tests_manual.py
import asyncio
import os
import django

# 设置 Django 环境 (如果在 shell 外运行需要)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from judge.services import CppRunnerService

async def test_hello_world():
    print(">>> 测试 1: Hello World + O2")
    code = """
    #include <iostream>
    using namespace std;
    int main() {
        int a, b;
        if (cin >> a >> b) cout << (a + b) << endl;
        else cout << "Hello World" << endl;
        return 0;
    }
    """
    # Case A: 无输入
    res1 = await CppRunnerService.compile_and_run(code, "", True)
    print(f"Case A Result: {res1['status']}, Output: {res1['output'].strip()}")
    assert res1['output'].strip() == "Hello World"

    # Case B: 有输入
    res2 = await CppRunnerService.compile_and_run(code, "10 20", True)
    print(f"Case B Result: {res2['status']}, Output: {res2['output'].strip()}")
    assert res2['output'].strip() == "30"

    print("✅ Hello World 测试通过\n")

async def test_compile_error():
    print(">>> 测试 2: 编译错误")
    code = "int main() { return a; }" # 变量 a 未定义
    res = await CppRunnerService.compile_and_run(code, "", True)
    print(f"Result: {res['status']}")
    print(f"Error Msg (Prefix): {res['output'][:50]}...")
    assert res['status'] == "Compile Error"
    print("✅ 编译错误测试通过\n")

def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_hello_world())
    loop.run_until_complete(test_compile_error())
    loop.close()

if __name__ == "__main__":
    run()