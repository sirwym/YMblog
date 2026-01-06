# tools/ai_utils.py
import json
from openai import AsyncOpenAI
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_API_URL
)

# 修改 Prompt：请求 JSON 格式，包含 gen 和 val
GEN_SCRIPT_PROMPT = r"""
你是一个专业的算法竞赛出题人和数据设计专家。
请根据【题目描述】和【标程】，生成两份 Python 3 代码：

1. gen.py：测试数据生成器  
2. val.py：测试数据校验器（Validator）

====================
【gen.py 强制要求】
====================
1. 必须使用 Python 3，仅允许使用标准库。
2. 必须 `import sys` 和 `import random`。
3. 必须从命令行读取：
   - sys.argv[1]：随机种子 seed（int）
   - sys.argv[2]：数据规模 scale（int，0=小数据，1=大数据，2=极限数据）
4. 必须使用 `random.seed(int(sys.argv[1]))` 初始化随机数。
5. 必须输出 **符合题目输入格式** 的完整测试数据到 stdout。
6. **【关键】Scale 定义**：
   - `scale=0`：**边界与特殊情况**。包含题目允许的**最小 N**（注意：若题目要求“至少操作一次”，则 $N$ 不能太小导致天然有序）、最大/最小边界值、以及特殊构造（如完全相同、完全不同、交错等）。
   - `scale=1`：随机中等规模数据。
   - `scale=2`：极限规模数据（贴近题目最大限制）。
7. 输出数据必须 **100% 符合** 题目格式。
8. 禁止使用任何第三方库（如 numpy、networkx 等）。
9. 避免使用可能导致递归深度错误的递归写法。
10. 生成的数据应尽量覆盖容易导致错误算法失败的情况，例如：边界值、极端分布、退化结构、特殊顺序。
11. 禁止无法保证终止的无限循环。
    - Generate-Validate-Retry 模式允许使用 `while True`，
    - 但必须在逻辑上保证有限次内成功（如规模受限、可修正构造）。
12. **【关键逻辑】数值范围自洽**：
    - 在生成“不重复”或“去重”序列时，必须保证随机数的取值范围 (`max_val`) **大于等于** 需要生成的数量。
    - 示例防御代码：`max_val = max(needed_count, target_max_val)`，防止 `ValueError` 或生成重复值。
13. **【关键逻辑】非平凡数据与约束自检**：
    - **题目约束**：仔细阅读题目中的“数据保证”。例如，如果题目隐含 $N \ge 4$ 或“至少需要操作一次”，那么 `scale=0` 时绝不能生成 $N=2$。
    - **强制破坏**：生成数据后，必须检查数据是否“天然”满足了题目目标（导致答案为0）。如果是，必须通过代码（如交换元素）来破坏这种完美状态。
14. **【关键架构】生成-验证-重试模式 (Generate-Validate-Retry)**：
    - 随机生成的数据很难一次性满足所有复杂约束（如连通性、非平凡性）。
    - **必须**编写一个 `validate(data)` 函数，检查数据是否满足所有约束（包括第13点）。
    - 在主逻辑中使用 `while True:` 循环：生成 -> 验证 -> 如果失败则 `continue` 重试 -> 如果成功则 `break` 并输出。
15. **【关键输出】大数据安全输出**：
    - ❌ **严禁**使用 `print(' '.join(map(str, huge_list)))`，这会导致内存溢出或IO截断。
    - ✅ **必须**使用分批输出策略。
    - 示例模板：
      ```python
      BATCH_SIZE = 1000
      buffer = []
      for x in sequence:
          buffer.append(str(x))
          if len(buffer) >= BATCH_SIZE:
              sys.stdout.write(" ".join(buffer) + " ")
              sys.stdout.flush() # 记得 flush
              buffer = []
      if buffer: sys.stdout.write(" ".join(buffer))
      sys.stdout.write("\\n")
      ```
16. **【代码规范】中文注释**：
    - 关键逻辑（如：数据构造思路、反向检查逻辑、特殊情况处理）**必须包含简练的中文注释**，以便人类理解生成思路。

====================
【val.py 强制要求】
====================
1. 必须使用 Python 3，仅允许使用标准库。
2. 必须从 **stdin** 读取 gen.py 生成的数据。推荐使用 `sys.stdin.read().split()` 一次性读取所有 token。
3. 必须严格按照【题目描述】检查：
   - 输入格式是否正确
   - 所有数值是否在合法范围内
   - 题目要求的结构性约束（如：图是否连通、无重边、树结构等）
   - **特殊约束**：检查题目中提到的特殊保证（如“保证至少操作一次”）。
4. **禁止**直接 return / pass / 打印提示信息。
5. 如果数据合法：什么都不输出，正常结束 (exit 0)。
6. 如果发现任何非法情况：
   - 使用 `assert False` 或 `sys.exit(1)` 直接报错。
7. 禁止使用任何第三方库。
8. **【代码规范】中文注释**：关键校验步骤需添加中文注释。


====================
 强制一致性要求
====================
- val.py 中校验的所有约束，必须都能在 gen.py 的 validate() 中被验证。
- 禁止出现 val.py 检查了，但 gen.py 永远不会生成的分支。

====================
【输出格式（非常重要）】
====================
必须 **仅返回一个合法 JSON 对象**，不要包含任何 markdown 或多余文本，格式如下：

{{
    "gen_code": "完整的 gen.py 代码（字符串）",
    "val_code": "完整的 val.py 代码（字符串）"
}}

====================
【题目描述】
{description}

====================
【标程 (C++)】
{solution}
"""


async def generate_gen_script(description, solution):
    """
    生成 gen.py 和 val.py
    """
    user_content = GEN_SCRIPT_PROMPT.format(description=description, solution=solution)

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",  # 建议用 chat 模型输出 JSON，reasoner 容易输出废话
            messages=[
                {"role": "system", "content": "你是一个严谨的算法专家，只输出 JSON。"},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},  # 强制 JSON 模式 (如果模型支持)
            temperature=0.7
        )
        content = response.choices[0].message.content
        # 清洗可能存在的 markdown
        content = content.replace("```json", "").replace("```", "").strip()
        logger.error(content)
        data = json.loads(content)
        return data.get('gen_code', ''), data.get('val_code', '')

    except Exception as e:
        logger.exception(f"AI 生成失败: {e}")
        # 保底代码
        fallback_gen = "import sys, random\nrandom.seed(int(sys.argv[1]) if len(sys.argv)>1 else 0)\nprint(10)"
        fallback_val = "import sys\n# 默认校验通过\npass"
        return fallback_gen, fallback_val