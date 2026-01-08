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
# 模块化 Prompt 组件 (v6.5 - 多样化边界版)
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

6. **【生死攸关】性能约束 (Performance Guard)**：
   - 生成去重数据（如不重复的数、不重边）时，**严禁**使用 `if x in list` 校验（$O(N^2)$ 会导致超时）。
   - **必须**使用 `set()` (哈希表) 来记录已生成元素，确保查重复杂度为 $O(1)$。
   - 示例：`used = set(); ... while True: x = rand(); if x not in used: used.add(x); break`   
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
1. **Scale 定义（多样性修正）**：
   - `scale=0` (小数据与边界)：**严禁**硬编码为单一的最小情况（如 N=1）。
     - **必须**利用 `seed` 随机生成多种情况，例如：
       - 极小值（题目允许的最小 N）。
       - 小规模随机（如 $N \in [2, 10]$）。
       - 特殊值边界（如 0、负数、空字符串，视题目而定）。
   - `scale=2` (极限)：题目允许的最大 N/M。

2. **特殊约束检查**：
   - **必须**检查题目描述中的“数据保证”（如“保证 $N \ge 2$”）。
   - **gen.py** 必须在生成后校验这些条件，若不满足则重试。
   - 若生成的随机数据“天然”不满足题目要求的操作性（如要求至少操作一次但生成了已排序数组），必须强制破坏或重试。

3. **逻辑降级**：
   - 若题目复杂，优先保证代码不报错，生成纯随机数据，但仍需满足上述硬性约束。
""",

    # ------------------------------------------------------------------
    # 模式 B: 常用算法
    # ------------------------------------------------------------------
    "algo": r"""
====================
二、生成策略 (Algo Mode)
====================
1. **Scale 定义（多样性修正）**：
   - `scale=0` (特殊构造与小数据)：**必须**基于 `seed` 随机选择以下策略之一（不要每次都一样）：
     - 策略A：全相同值 / 模 K 同余。
     - 策略B：单调递增 / 递减（需注意题目是否要求“至少操作一次”，若有则需破坏单调性）。
     - 策略C：特殊值分布（如仅包含 0/1，或最大/最小值）。
     - 策略D：小规模 ($N \le 20$) 的随机极端数据。
   - `scale=2` (极限)：**必须**取到题目允许的绝对最大值。
   - **数值自洽**：生成去重序列时，确保 `max_val >= needed_count`。

2. **非平凡性与约束**：
   - **硬性约束**：严格遵守题目中的“数据保证”。如“保证没有自环”、“保证 $A_i \ne A_j$”。
   - **非平凡性**：检查数据是否“天然”导致答案为 0。如果是，**必须强制破坏**。

3. **系统安全**：
   - **递归保护**：`sys.setrecursionlimit(300000)`。
   - **OOM 防护**：严格使用流式输出。
""",

    # ------------------------------------------------------------------
    # 模式 C: 图论/树 (核心增强)
    # ------------------------------------------------------------------
    "graph": r"""
====================
二、生成策略 (Graph Expert Mode)
====================
1. **【核心】Killer Template Router**：
   - `scale=2` 时，**必须**混合使用以下模板，严禁仅使用纯随机图。
   - **强制要求**：在 `gen.py` 注释中写出使用了哪个模板。
     [Tree] T1. Deep Chain, T2. Star, T3. Caterpillar
     [Graph] G1. Grid, G2. Cycle + Chord, G3. Dense Block, G4. Disconnected->Connected
     [DAG] D1. Layered DAG, D2. Reverse Topological

2. **Scale 定义（多样性修正）**：
   - `scale=0` (退化与小图)：**必须**基于 `seed` 随机选择以下之一：
     - 极小图 ($N=1, 2$)。
     - 特殊退化结构（纯链、纯菊花、完全图）。
     - 小规模随机图 ($N \in [5, 20]$)。
     - **严禁**每次都生成完全一样的图。

3. **构造规范**：
   - **树**："Random Parent" + Shuffle。
   - **连通图**：Tree Backbone + Random Edges。
   - **DAG**：Permutation (small -> large)。

4. **约束与安全**：
   - **数据保证**：若题目保证“图连通”，必须用 G-V-R 模式确保连通。
   - **OOM**：必须使用流式输出。
   - **性能**：必须使用 `set()` 查重。
   - **连通性校验**：**严禁**递归 DFS，必须使用 **迭代式 DSU/BFS**。
"""
}

# 3. 通用尾部
# 注意：这里直接定义字符串，不使用 .format() 填充，所以 JSON 的花括号不需要转义
COMMON_FOOTER = r"""
====================
三、通用校验 (val.py)
====================
1. **读取**：推荐 `data = sys.stdin.read().split()`。
2. **校验**：
   - 格式、范围 ($Min \le x \le Max$)。
   - **重要**：必须校验题目中的 **“特殊保证”** (Data Guarantees)。例如“保证至少操作一次”（即输入不能已经是目标状态）、“保证图连通”。如果不满足，`sys.exit(1)`。
3. **一致性**：val.py 的校验逻辑必须在 gen.py 的 `validate()` 中自检。
4. **退出码**：合法 exit(0)，非法 exit(1)。

====================
四、思维链与输出规范 (CoT & Output)
====================
请严格按照以下步骤思考：

1. **Phase 1: 题型识别与约束提取**
   - 识别题目类型。
   - **【关键】** 仔细阅读题目描述，提取 **“数据保证”**。
     - 例如："保证至少操作一次" -> 生成后检测 `is_sorted`，如果是则 `shuffle`。
     - 例如："保证不含重边" -> 使用 `set` 查重。

2. **Phase 2: 模板选择**
   - `scale=0` 时，确保基于 seed 实现了多样性（不要硬编码单一情况）。
   - `scale=2` 时，从 Killer Template Router 中选择模板。

3. **Phase 3: 代码实现**
   - 编写 gen.py (包含 `validate` 函数，`validate` 必须检查上述提取的特殊约束；包含 G-V-R 重试逻辑；遵守性能约束)。
   - 编写 val.py (严格校验所有约束)。

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

# 4. 题目描述部分 (单独定义，用于 format)
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

    # 关键点：只对 DES_SOL 进行 format，避免污染 COMMON_FOOTER 里的 JSON 花括号
    task_context = DES_SOL.format(description=description, solution=solution)

    # 拼接最终 Prompt
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