from django.test import TestCase
from unittest.mock import patch, AsyncMock, MagicMock
# 假设你的 ai_utils.py 在 tools app 下，如果路径不同请修改 import
from tools.ai_utils import generate_gen_script, GEN_SCRIPT_PROMPT


class AIUtilsTestCase(TestCase):

    async def test_generate_gen_script_success(self):
        """
        测试正常情况下：API 返回带 Markdown 的代码，函数应能正确清洗并返回
        """
        # 1. 准备模拟数据
        description = "输入两个整数 A 和 B"
        solution = "int a, b; cin >> a >> b;"

        # 模拟 OpenAI 返回的原始内容 (包含 ```python 标记)
        raw_ai_response = """```python
import sys
import random
seed = int(sys.argv[1])
random.seed(seed)
print(random.randint(1, 100))
```"""
        # 我们期望清洗后的结果
        expected_code = """import sys
import random
seed = int(sys.argv[1])
random.seed(seed)
print(random.randint(1, 100))"""

        # 2. 构造 Mock 对象结构
        # OpenAI 的 response 结构是 response.choices[0].message.content
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = raw_ai_response
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        # 3. Patch 掉 client.chat.completions.create
        # 注意路径：要 patch 你的 ai_utils.py 里导入的 client 对象的方法
        with patch('tools.ai_utils.client.chat.completions.create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            # 4. 执行函数
            result = await generate_gen_script(description, solution)

            # 5. 验证结果
            self.assertEqual(result, expected_code)

            # 6. 验证是否调用了 API，且参数正确
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs

            # 验证模型是否正确
            self.assertEqual(call_kwargs['model'], "deepseek-reasoner")
            # 验证 Prompt 是否正确拼接
            expected_prompt = GEN_SCRIPT_PROMPT.format(description=description, solution=solution)
            self.assertEqual(call_kwargs['messages'][1]['content'], expected_prompt)

    async def test_generate_gen_script_failure(self):
        """
        测试异常情况下：API 调用失败（如网络错误），应返回保底代码
        """
        description = "测试题目"
        solution = "测试代码"

        # 1. Patch 模拟抛出异常
        with patch('tools.ai_utils.client.chat.completions.create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("网络连接超时")

            # 2. 执行函数
            result = await generate_gen_script(description, solution)

            # 3. 验证结果
            # 应该包含错误提示
            self.assertIn("# AI 调用失败", result)
            # 应该包含具体的错误信息
            self.assertIn("网络连接超时", result)
            # 应该包含保底的 Python 代码逻辑
            self.assertIn("import sys, random", result)