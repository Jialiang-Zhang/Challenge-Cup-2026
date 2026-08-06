# 赛题简介

本仓库是挑战杯人工智能赛道初赛的 baseline 仓库。赛题围绕 Intern-S 系列模型的数学智能体设计与推理创新展开，选手需要设计一个能够解决数学问题的推理智能体。智能体接收一道数学题文本，结合题目元信息进行推理，并输出最终答案。

选手的核心任务是实现：

```python
agent.solve(problem: str, metadata: dict) -> dict
```

平台会在正式评测时读取实际测试题，调用选手提交代码中的该入口函数，取得 `final_response`，并结合官方 judger 与标准答案进行判分。

本赛题鼓励选手探索不同的智能体设计方式，包括但不限于：

- 提示词设计与多轮推理
- 多候选生成、验证与选择
- 规划、反思、纠错、答案格式化
- 工具调用、检索、记忆或其它推理策略
- 面向数学题的专门解析、符号计算或后处理

最终评分主要依据 `final_response` 的答案正确性。`trace` 可用于记录不含敏感正文的结构化运行摘要，便于内部异常排查和设计分析；它不是获取隐藏评测信息的通道。

## Baseline 仓库说明

本仓库提供一个 naive agent baseline，作用是帮助选手理解：

- 赛题内容与本地调试方式
- 输入数据格式
- 智能体入口函数
- 智能体输出格式
- 平台 runner 与选手代码之间的调用关系

Baseline 只是一个最小可运行示例，不限制选手的具体实现。选手可以保留、修改或替换其中的智能体逻辑，也可以新增模块、工具和依赖。但正式提交的仓库必须满足平台约定的入口规范。

### 必须包含的文件

选手提交的仓库根目录必须包含：

```text
user_agent.py
```

平台 runner 会从该文件中加载选手实现。其它文件可以根据需要添加，例如：

```text
requirements.txt
tools/
prompts/
utils/
```

但所有新增文件都应使用相对路径读取，不要依赖本地机器上的绝对路径。

### `user_agent.py` 必须遵守的规范

`user_agent.py` 中必须提供类：

```python
class ReasoningAgent:
    ...
```

平台会使用官方 client 初始化该类：

```python
from user_agent import ReasoningAgent

agent = ReasoningAgent(client=official_client)
```

因此 `ReasoningAgent` 至少需要支持如下构造方式：

```python
def __init__(self, client, *args, **kwargs):
    ...
```

其中 `client` 由平台提供。选手不要在代码中写死 API key，也不要假设本地存在固定的 API 配置文件。正式评测时，模型访问、限流、token 统计、超时控制等由官方 client 和平台 runner 统一管理。

评测时平台提供的 client 与 baseline 中 `llm_client.py` 的 `InternChatClient` 结构一致，可作为本地实现参考。选手可以参考其中的 `chat(messages, temperature, max_tokens)` 调用方式组织模型请求：

```python
response = client.chat(
    messages=[
        {"role": "user", "content": problem},
    ],
    temperature=0.2,
    max_tokens=4096,
)
```

正式评测 client 可能包含额外的资源统计、限流和安全控制逻辑。选手代码只应依赖公开约定的调用接口，不要依赖 client 内部私有字段。正式评测只保证非流式、单候选响应，因此不要传入 `stream=True` 或 `n != 1`；平台会锁定 `model` 和当前调用的 `messages`，并可能限制 `max_tokens` 和模型调用次数。

`ReasoningAgent` 必须提供推理函数：

```python
def solve(self, problem: str, metadata: dict) -> dict:
    ...
```

输入参数含义如下：

- `problem`: 数学题题面文本。
- `metadata`: 题目元信息字典，至少可能包含 `idx`。正式评测时，metadata 的具体字段以平台 runner 为准。选手代码不得依赖 `answer`、标准答案或隐藏评测数据。

返回值必须是 `dict`，且必须包含非空字符串字段：

```python
{
  "final_response": "最终答案"
}
```

也可以返回可选的 `trace`，但只应记录非敏感的结构化摘要：

```python
{
  "final_response": "最终答案",
  "trace": [
    {"step": "policy_call", "content": {"candidate_id": 0, "status": "completed"}},
    {"step": "verify", "content": {"candidate_id": 0, "accepted": True}},
    {"step": "finalize", "content": {"candidate_id": 0}}
  ]
}
```

字段要求：

- `final_response` 必须是可读的最终答案，不能为空。
- `trace` 可选，建议为列表，只记录步骤名称、调用状态、候选编号、耗时或长度等结构化元数据。
- 返回内容必须可以被 JSON 序列化。
- 不要在 `trace` 中重复题面、完整 prompt、模型输入输出、候选解答或最终答案，也不要写入 API key、访问令牌、个人隐私信息或其它敏感内容。

### 日志与评测报告

正式评测会在隔离环境中处理 `trace`，并可能直接丢弃选手进程的标准输出和标准错误。在线平台提供下载的评测日志与评测报告会经过脱敏，只包含允许公开的汇总分数、运行状态和聚合统计，不包含逐题题面、标准答案、候选解答、原始模型交互、Judge prompt/响应或其它判分细节。

`trace`、标准输出和标准错误都不是向选手回传隐藏评测信息的通道。选手代码不要打印或记录完整题面、模型请求/响应、`final_response`、环境变量、密钥、文件内容或异常堆栈中的敏感正文；平台也不保证这些内容会原样出现在可下载产物中。

### 实现自由度

选手可以使用 baseline 中的 lagent 示例，也可以完全不用 lagent。平台只要求 `user_agent.py` 暴露符合规范的 `ReasoningAgent` 和 `solve` 方法。

选手可以新增辅助函数、类和模块，也可以在单道题的 `ReasoningAgent` 内部维护状态。但需要注意：

- 正式评测的每道题都会在独立进程中重新加载选手模块、构造 Agent，并只调用一次 `solve`；不要依赖内存、模块全局变量、文件或外部服务保存跨题状态。
- 平台最多同时运行 3 个相互独立的题目进程；这不是对同一个 Agent 实例并发调用 3 次。
- 不要依赖评测题之间的固定顺序。
- 不要依赖本地绝对路径。
- 不要读取或构造隐藏测试集、标准答案或 judger 信息。
- 不要在代码中硬编码 API key。
- 不要输出恶意内容、执行破坏性操作或规避平台资源限制。

### 正式评测的并发、时限与计分

- Agent 阶段的总硬时限为 6 小时，不包含后续 Judge 阶段的耗时。到达时限后，平台可以终止仍在运行的 Agent 代码。
- 每道题的独立进程组有 1200 秒硬时限，包含选手模块加载、Agent 初始化和 `solve` 执行。超时后平台会终止整个进程组，不保证执行 `finally`、退出钩子或其它清理逻辑。
- 截止时只接受已由平台 runner 原子落盘且状态为成功的逐题结果。选手只需从 `solve` 返回规定的字典，不要自行写评测输出文件。
- Agent 异常、无效输出、到达截止时间仍未完成或缺失的题目均计为 `C`。最终成绩的分母固定为完整正式评测题集，不会因为只完成部分题目而缩小。

## 输入数据与输出样例

本地调试输入为 JSONL 文件，每行是一道题。每行至少包含：

```json
{"idx": 0, "problem": "题目文本"}
```

样例：

```json
{"idx": 0, "problem": "设$\\mathbb{F}_{81}$为$81$元的有限域。$T=\\{\\alpha\\in\\mathbb{F}_{81}|\\mathbb{F}_{81}=\\mathbb{F}_3(\\alpha)\\}$。求$T$中元素的个数。", "answer": "72", "subject": "抽象代数", "source": "sample"}
```

其中 `answer` 只会出现在样例数据中，用于选手本地对照调试。正式评测不会向 `solve` 传入标准答案。

本地 runner 会将每道题的结果保存为独立 JSON 文件：

```text
outputs/
  0.json
  1.json
  2.json
```

成功输出样例：

```json
{
  "idx": 0,
  "status": "success",
  "final_response": "72",
  "trace": [
    {
      "step": "select_final_response",
      "content": {
        "candidate_id": 0,
        "confidence_score": 1.0
      }
    }
  ]
}
```

异常输出样例：

```json
{
  "idx": 0,
  "status": "error",
  "final_response": "",
  "error": {
    "type": "RuntimeError",
    "message": "错误信息"
  },
  "trace": []
}
```

本地调试时，如果某个 `idx.json` 已经存在且文件非空，runner 会跳过该题，便于中断后继续运行。

## 本地调试

安装依赖：

```bash
pip install -r requirements.txt
```

设置 API key：

```bash
export INTERN_API_KEY="sk-..."
```

运行样例：

```bash
python main.py --input_file sample_data/dev.jsonl --output_dir sample_outputs
```

本地 runner 默认并发数为 3。如需调整：

```bash
export LOCAL_MAX_CONCURRENCY=2
```

本地 runner 只近似模拟正式评测的最多 3 题并发与逐题原子写入行为。为便于快速调试，它会在一个进程中复用同一个 Agent 实例；正式评测则为每道题重新加载独立 Agent 进程。因此，本地运行不能用于验证跨题状态，也不会完整复现平台的单题 1200 秒进程组硬时限、Agent 阶段 6 小时总硬时限、失败补 `C` 和 Judge 流程。本地调试结果只用于选手自测，不代表正式评测分数。正式评测会使用隐藏测试集、官方 client、平台 runner 和官方 judger。

## Intern-S API 使用说明

选手可以使用报名挑战杯时填写的手机号注册书生 API 控制台：

```text
https://internlm.intern-ai.org.cn/api/document
```

API 控制台主要用于：

- 查看 API docs 和可用模型列表。
- 获取、创建或管理 API key。
- 申请更高的 RPM / TPM 流控。
- 查看调用量、配额和使用情况。

书生 API 控制台中的 API 均可免费使用。平台会对普通用户执行流控策略：

```text
RPM 30
TPM 150000
```

如果本地调试或实验需要更高流控，可以前往以下页面申请提升：

```text
https://internlm.intern-ai.org.cn/api/strategy
```

申请时请在备注中填写“挑战杯”。通常情况下，200 RPM 以内的流控提升会在 1-2 个工作日内生效。具体生效时间以 API 控制台状态为准。

选手可以使用 API 控制台下的任意可用模型作为智能体 base model，例如：

- `intern-s1`
- `intern-s1-pro`
- `intern-s2-preview`

本地使用 baseline runner 调试时，可以通过环境变量指定模型：

```bash
export INTERN_MODEL="intern-s2-preview"
```

如需调整 API endpoint，请以书生 API 控制台文档中的接口地址为准配置 `INTERN_API_BASE`。

`InternChatClient.chat` 支持书生 Chat API 的 `thinking_mode`、`tools` 等参数，也可以通过额外关键字参数透传其它接口参数：

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"},
                },
                "required": ["expression"],
            },
        },
    }
]

client = InternChatClient(
    default_args={
        "thinking_mode": True,
        "top_p": 0.9,
    }
)
response = client.chat(
    messages=[{"role": "user", "content": "计算 1 + 1"}],
    tools=tools,
    tool_choice="auto",
)
```

`default_args`（或初始化 client 时直接提供的额外关键字参数）会应用于每次请求；`chat` 中提供的参数优先级更高。普通回复仍返回文本字符串；如果模型发起工具调用，则返回完整的 assistant message 字典，其中包含 `tool_calls`。

上述透传约定仅适用于非流式、单候选 Chat API 请求。正式评测 client 会拒绝 `stream=True` 和 `n != 1`，并始终使用平台选定的模型及本次传入的 `messages`；选手传入同名额外参数不能覆盖这些平台字段。

提交仓库至评分系统时，选手可以选择智能体实际使用的模型。正式评测时，平台 runner 会通过官方 client 使用该模型进行调用。

评分系统 client 使用的 API 来自书生 API 控制台：

```text
https://internlm.intern-ai.org.cn/api
```

建议选手本地调试时也使用同一份 API 控制台，避免本地实验环境和正式评分环境之间产生模型行为、接口格式或网关策略差异。

## 提交方式

参赛队伍可以在报名结束后提交作品进行判分，提交开放时间预计为 2026-07-01 起，具体以赛事通知为准。选手需要基于 baseline 仓库准备自己的提交代码，并向判分系统提交仓库地址与 commit SHA。

推荐流程：

1. 获取 baseline 仓库代码。
2. 在自己的仓库中完成实现。
3. 确保仓库根目录包含符合规范的 `user_agent.py`。
4. 将代码推送到 GitHub 或平台指定的代码托管服务。
5. 在判分系统中完成仓库授权。
6. 向判分系统提交仓库地址和 commit SHA。

关于仓库可见性：

- 如果直接 fork 一个公开 baseline 仓库，fork 和提交内容通常也是公开可见的。
- 如果不希望自己的方案公开，建议将 baseline clone 到本地后，推送到自己的 private repository。
- 选手也可以保持仓库公开，但需自行承担方案被其他人看到的风险。

判分系统会以选手提交的 commit SHA 作为评测快照。请务必提交具体 commit SHA，而不是只提交分支名。分支名可能继续变化，commit SHA 才能保证结果可复现。

### 挑战杯官网材料提交

判分系统用于初赛榜单评测，挑战杯官网材料提交用于满足赛事报名与材料归档要求。两者都需要完成。

初赛截止前，请根据挑战杯官网要求，将自己的最终版本代码仓库与赛题要求的其它材料打包成 `.zip` 文件，提交到挑战杯官网，并发送邮件至：

```text
changshuai@pjlab.org.cn
```

建议压缩包内至少包含：

- 最终版本代码。
- `user_agent.py` 及所有运行所需的辅助文件。
- `requirements.txt` 或其它依赖说明。
- 一份说明文件，写明队伍信息、题目名称、最终仓库地址、最终分支名称、最终 commit hash 和选择使用的模型。

提交前建议检查：

- `user_agent.py` 可以被正常 import。
- `ReasoningAgent(client=official_client)` 可以正常初始化。
- `solve(problem, metadata)` 返回包含非空 `final_response` 的字典。
- 所有依赖都已写入 `requirements.txt` 或赛事另行指定的依赖文件。
- 代码中没有硬编码 API key、个人路径、临时文件路径或调试用标准答案。

## 自动判分系统

自动判分系统预计 7 月上线，具体上线日期以赛事通知为准。

判分系统上线前，如果选手需要提交作品并获取评测分数，可以将代码库打包成 `.zip` 文件发送邮件至：

```text
changshuai@pjlab.org.cn
```

邮件模板如下：

```text
邮件主题：[挑战杯初赛评测申请] 队伍名称 - 题目名称 - commit hash

收件人：changshuai@pjlab.org.cn

正文：
队伍名称：

题目名称：基于 Intern-S 系列模型的数学智能体设计与推理创新

报名成员信息（至少填写 1 名挑战杯官网内报名成员）：
- 姓名：
- 学校：
- 报名手机号：

需要评测的代码版本：
- 仓库地址：
- 分支名称：main
- commit hash：
- 选择使用的模型：例如 intern-s2-preview

附件：
- 代码库 zip 文件名：

备注：
- 如有特殊依赖、运行说明或需要说明的异常情况，请在这里填写。
```

邮件评测同样以邮件中写明的分支名称和 commit hash 为准。请确保附件中的代码版本与邮件正文中的 commit hash 对应，避免评测结果无法复现。

判分系统的基本工作流程如下：

1. 选手在系统中提交仓库地址与 commit SHA。
2. 系统检查仓库授权，并拉取对应 commit 的代码。
3. 系统在隔离环境中安装依赖并加载 `user_agent.py`。
4. 系统根据选手提交时选择的模型，使用官方 client 初始化 `ReasoningAgent`。
5. 平台 runner 读取正式评测题，调用 `agent.solve(problem, metadata)`。
6. 系统收集 `final_response`、`trace`、运行耗时、异常信息和资源使用情况。
7. 官方 judger 结合标准答案对结果进行判分。
8. 系统返回最终分数、是否存在异常，以及经过脱敏的汇总日志和评测报告。

正式评测时：

- 平台会使用官方闭源测试集。
- 平台会使用来自书生 API 控制台的官方 client，不使用选手自带 API key。
- 平台会统一控制超时、并发、模型调用预算和资源限制。
- 平台提供的下载产物只包含脱敏后的汇总信息，不会向选手返回逐题题目、标准答案、候选解答、原始模型交互、judger 细节或逐题详细反馈。
- 如果代码无法安装、无法 import、入口函数不符合规范、运行超时、输出格式错误或触发安全策略，系统会标记异常。

## 初赛评分与晋级

初赛完全采取客观评分方式对所有参赛队伍进行排名。排名依据为初赛截止日期时，判分系统榜单上的队伍最终排名。

在初赛截止日期前，组委会会根据整体赛题完成质量、参赛队伍分数分布等情况，公布进入决赛的最低分数线。进入决赛的队伍数量少于 30 支，具体晋级名单以赛事官方通知为准。

## 提交次数限制

从判分系统上线日到初赛截止时间，每支队伍的提交次数限制为：

- 每天最多提交 2 次。
- 每周最多提交 10 次。

判分系统会给出最终分数、是否存在异常以及脱敏后的汇总日志和评测报告。请选手在本地充分调试后再提交正式评测，避免因格式错误、依赖缺失或超时浪费提交次数。

## 常见异常

以下情况可能导致判分异常：

- 仓库授权失败，系统无法拉取提交。
- 提交的是分支名而不是 commit SHA。
- `user_agent.py` 不存在。
- `ReasoningAgent` 类不存在或构造函数不接受 `client`。
- `solve` 方法不存在、签名不符合要求或抛出异常。
- 返回值不是字典。
- `final_response` 缺失、为空或不是字符串。
- 返回值无法 JSON 序列化。
- 依赖无法安装或版本冲突。
- 运行超时或资源使用超过平台限制。
- 代码依赖本地绝对路径、私有文件或未声明资源。
- 代码包含硬编码密钥、恶意行为或规避评测限制的逻辑。

## 实现建议

为了提高提交稳定性，建议选手：

- 保持入口接口简单稳定，把复杂逻辑封装到内部模块。
- 对模型输出做答案抽取和格式化，避免 `final_response` 过长或答案不明确。
- 对异常进行适度处理，保证单题失败不会影响整体运行。
- 控制模型调用次数和 token 使用，避免超时。
- 在本地使用样例数据完整跑通安装、初始化、推理和输出保存流程。
- 如需返回 `trace`，只保留非敏感的结构化摘要，不要记录题面、答案或原始模型交互。

本仓库的 baseline 仅用于说明接口和基本思路。正式比赛欢迎选手提交更强、更稳定、更有创造性的数学智能体实现。
