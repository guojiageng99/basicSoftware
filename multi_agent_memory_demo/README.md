# Multi-Agent Shared Memory Demo

面向课程任务协作场景的多智能体低开销通信与共享记忆原型系统。

## 功能

- 输入任务后，由规划 Agent、执行 Agent、检查 Agent 顺序协作。
- 消息通信模块记录每次状态和结果传递。
- 状态管理模块展示三个 Agent 的运行状态。
- 共享记忆模块保存历史任务、子任务、结果和经验。
- 相似任务再次输入时，系统会提示命中共享记忆，并减少重复处理步骤。
- 实验指标展示有共享记忆与无共享记忆的消息数量、步骤数量和耗时估算。

## 启动

```powershell
cd multi_agent_memory_demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

打开浏览器访问：

```text
http://127.0.0.1:8000
```

## 演示任务

- 生成一份课程大作业报告提纲
- 整理一次小组分工方案
- 生成一个答辩 PPT 大纲

先运行一次，再输入相似任务，例如“帮我生成课程大作业报告目录”，可以看到共享记忆命中效果。
