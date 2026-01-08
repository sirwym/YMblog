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

# ======================================================
# 模块化 Prompt 组件 (v6.1)
# ======================================================

Tick3 = "```"

# 1. 通用头部
COMMON_HEADER = r"""
你是一个专业的算法竞赛出题专家。请根据【题目描述】和【标程】，生成 `gen.py` 和 `val.py`。

====================
一、全局核心规范 (Global Standards)
====================
1. **输出格式**：必须 **仅返回一个 JSON 对象**。严禁包含 Markdown 代码块标记，严禁输出多余文本。
2. **环境**：仅允许 Python 3 标准库 (`sys`, `random`)。禁止第三方库。
3. **输入**：必须从命令行读取 `seed = int(sys.argv[1])`, `scale = int(sys.argv[2])`。
4. **初始化**：必须执行 `random.seed(seed)`。

5. **【关键】流式输出标准模板 (Stream Output)**：
   为防止 OOM (内存溢出)，**必须**使用以下 `out/flush` 模式输出大规模数据：
   """ + Tick3 + r"""python
   import sys
   BATCH = 1000
   buffer = []
   def out(x):
       buffer.append(str(x))
       if len(buffer) >= BATCH:
           sys.stdout.write(" ".join(buffer) + " ")
           sys.stdout.flush(); del buffer[:]
   # 结束时务必刷新:
   # if buffer: sys.stdout.write(" ".join(buffer)); sys.stdout.flush()
   """ + Tick3 + r"""
"""

# 2. 差异化策略模块
STRATEGIES = {
    # ------------------------------------------------------------------
    # 模式 A: 基础/入门题
    # ------------------------------------------------------------------
    "basic": r"""
====================
二、生成策略 (Basic Mode)
====================
1. **Scale 定义**：
   - `scale=0` (边界)：**必须**包含题目允许的**最小 N** (如 $N=1,2$)、零值、负数、空行等边界。
   - `scale=2` (极限)：题目允许的最大 N/M。
2. **逻辑降级**：
   - 若题目稍显复杂但处于 Basic 模式，**请放弃复杂构造**，转为生成大量边界值和纯随机数据，优先保证代码不报错。
""",

    # ------------------------------------------------------------------
    # 模式 B: 常用算法
    # ------------------------------------------------------------------
    "algo": r"""
====================
二、生成策略 (Algo Mode)
====================
1. **Scale 定义**：
   - `scale=0` (特殊)：**必须**构造全相同值、单调序列、回文串、二分值(0/1)等能卡掉贪心/暴力的分布。
   - `scale=2` (极限)：**必须**取到题目允许的绝对最大值。
   - **数值自洽**：生成去重序列时，确保 `max_val >= needed_count`。

2. **非平凡性**：
   - 检查数据是否“天然”导致答案为 0 或无解。如果是，**必须强制破坏**（如交换元素）以产生有效测试。

3. **系统安全**：
   - **递归保护**：若涉及 DFS/DP，必须执行 `sys.setrecursionlimit(300000)`。
   - **OOM 防护**：严格使用前文提到的流式输出模板。
""",

    # ------------------------------------------------------------------
    # 模式 C: 图论/树 (核心增强)
    # ------------------------------------------------------------------
    "graph": r"""
====================
二、生成策略 (Graph Expert Mode)
====================
1. **【核心】Killer Template Router (必须从下表中选择)**：
   - 当 `scale=2` 时，**必须**混合使用以下至少一种高强度模板，严禁仅使用纯随机图。
   - **强制要求**：在 `gen.py` 源码注释中明确写出使用了哪个模板（如 `# Template: Caterpillar`）。
     [Tree]
     - T1. Deep Chain (深链，卡递归爆栈)
     - T2. Star/Broom (菊花/扫帚，卡重心/度数暴力)
     - T3. Caterpillar (毛毛虫，卡树形DP/直径)
     [Graph]
     - G1. Grid/Lattice (网格图，卡搜索队列)
     - G2. Cycle + Chord (环+弦，卡最短路)
     - G3. Dense Block (局部稠密，卡边枚举)
     - G4. Disconnected -> Connected (先生成森林再连通，卡连通性假设)
     [DAG]
     - D1. Layered DAG (分层图，卡DP顺序)
     - D2. Reverse Topological (反直觉输入序)

2. **构造规范**：
   - **树**：必须使用 "Random Parent" ($p \in [1, i-1]$) + Shuffle。
   - **连通图**：先生成树骨架 (Backbone)，再加随机边。
   - **DAG**：先生成 Permutation，只允许小标号连向大标号。

3. **架构要求 (G-V-R Pattern)**：
   - 主循环 `while True` + `max_retries=20`。
   - **保底策略**：若重试耗尽，回退到 T1 (Chain) 模板，**保证必须输出**。

4. **val.py 特殊要求**：
   - **连通性**：**严禁**递归 DFS。**必须**使用 **迭代式并查集 (Iterative DSU)** 或迭代 BFS。
"""
}


COMMON_FOOTER = r"""
====================
三、通用校验 (val.py)
====================
1. **读取**：推荐 `data = sys.stdin.read().split()`。
2. **校验**：格式、范围、结构性约束、特殊保证。
3. **一致性**：val.py 的校验逻辑必须在 gen.py 的 `validate()` 中自检。
4. **退出码**：合法 exit(0)，非法 exit(1)。

====================
四、思维链与输出规范 (CoT & Output)
====================
请严格按照以下步骤思考：

1. **Phase 1: 题型识别**
   - 识别题目类型及标程复杂度。

2. **Phase 2: 模板选择**
   - `scale=2` 时，从 Killer Template Router 中选择最具杀伤力的模板。

3. **Phase 3: 代码实现**
   - 编写 gen.py (包含 G-V-R 重试逻辑，流式输出)。
   - 编写 val.py (使用 **迭代式** DSU/BFS)。

====================
【最终 JSON 返回结构】
仅返回一个 JSON 对象，必须包含以下 Key：
{
    "analysis": "题目核心逻辑与边界分析 (100字内)",
    "plan": "针对 scale 0/1/2 的生成策略简述",
    "gen_code": "完整的 gen.py 代码字符串",
    "val_code": "完整的 val.py 代码字符串"
}

"""

DES_SOL = r"""
====================
【题目描述】
{description}

====================
【标程 (C++)】
{solution}
"""


async def generate_gen_script(description, solution, mode="algo"):
    """
    根据 mode 组装 Prompt，并调用 AI 生成代码
    """
    # 1. 默认兜底
    if mode not in STRATEGIES:
        mode = "algo"

    # 2. 动态组装 Prompt
    strategy_content = STRATEGIES[mode]
    task_context = DES_SOL.format(description=description, solution=solution)
    full_prompt = COMMON_HEADER + strategy_content + COMMON_FOOTER + task_context

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个严谨的算法专家，只输出 JSON。"},
                {"role": "user", "content": full_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        logger.info(f"AI Code Generated (Mode: {mode})")

        # 解析返回的 JSON
        data = json.loads(content)

        # 返回完整数据字典
        return {
            "gen_code": data.get('gen_code', ''),
            "val_code": data.get('val_code', ''),
            "analysis": data.get('analysis', 'AI 未提供分析'),
            "plan": data.get('plan', 'AI 未提供计划')
        }

    except Exception as e:
        logger.exception(f"AI 生成失败: {e}")
        # 保底返回
        fallback_gen = "import sys, random\nrandom.seed(int(sys.argv[1]) if len(sys.argv)>1 else 0)\nprint(10)\nimport sys; sys.stdout.flush()"
        fallback_val = "import sys\n# 默认校验通过\npass"
        return {
            "gen_code": fallback_gen,
            "val_code": fallback_val,
            "analysis": "生成发生错误，已回退到保底模式。",
            "plan": "Error Fallback"
        }