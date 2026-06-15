from __future__ import annotations

import json
import math
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "agent_memory.db"


class TaskRequest(BaseModel):
    task: str = Field(..., min_length=2, max_length=200)
    use_memory: bool = True


class MemoryCreateRequest(BaseModel):
    task: str
    subtasks: list[str]
    result: str
    experience: str


@dataclass
class AgentState:
    name: str
    role: str
    status: str = "idle"
    detail: str = "Waiting"


class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    task_tokens TEXT NOT NULL,
                    subtasks TEXT NOT NULL,
                    result TEXT NOT NULL,
                    experience TEXT NOT NULL,
                    hit_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    memory_hit INTEGER NOT NULL,
                    memory_id INTEGER,
                    message_count INTEGER NOT NULL,
                    step_count INTEGER NOT NULL,
                    estimated_seconds REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add_memory(
        self, task: str, subtasks: list[str], result: str, experience: str
    ) -> dict[str, Any]:
        now = utc_now()
        tokens = sorted(tokenize(task))
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO memories
                (task, task_tokens, subtasks, result, experience, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.strip(),
                    json.dumps(tokens, ensure_ascii=False),
                    json.dumps(subtasks, ensure_ascii=False),
                    result,
                    experience,
                    now,
                    now,
                ),
            )
            memory_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            return row_to_memory(row) if row else {}

    def find_similar(self, task: str, threshold: float = 0.25) -> dict[str, Any] | None:
        query_tokens = tokenize(task)
        if not query_tokens:
            return None

        best: tuple[float, sqlite3.Row] | None = None
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM memories ORDER BY updated_at DESC").fetchall()

        for row in rows:
            row_tokens = set(json.loads(row["task_tokens"]))
            score = jaccard(query_tokens, row_tokens)
            if best is None or score > best[0]:
                best = (score, row)

        if best is None or best[0] < threshold:
            return None

        score, row = best
        with self._connect() as conn:
            conn.execute(
                "UPDATE memories SET hit_count = hit_count + 1, updated_at = ? WHERE id = ?",
                (utc_now(), row["id"]),
            )
        memory = row_to_memory(row)
        memory["similarity"] = round(score, 3)
        memory["hit_count"] += 1
        return memory

    def list_memories(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY updated_at DESC, id DESC LIMIT 30"
            ).fetchall()
        return [row_to_memory(row) for row in rows]

    def get_memory(self, memory_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        return row_to_memory(row) if row else None

    def log_run(
        self,
        task: str,
        memory_hit: bool,
        memory_id: int | None,
        message_count: int,
        step_count: int,
        estimated_seconds: float,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs
                (task, memory_hit, memory_id, message_count, step_count, estimated_seconds, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task,
                    1 if memory_hit else 0,
                    memory_id,
                    message_count,
                    step_count,
                    estimated_seconds,
                    utc_now(),
                ),
            )

    def recent_runs(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 20").fetchall()
        return [dict(row) for row in rows]


class AgentRuntime:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store
        self.states = [
            AgentState("planner", "规划 Agent"),
            AgentState("executor", "执行 Agent"),
            AgentState("reviewer", "检查 Agent"),
        ]
        self.messages: list[dict[str, Any]] = []

    def run(self, task: str, use_memory: bool = True) -> dict[str, Any]:
        start = time.perf_counter()
        self._reset()
        clean_task = task.strip()
        memory = self.store.find_similar(clean_task) if use_memory else None

        self._message("user", "planner", f"提交任务：{clean_task}", "task")

        if memory:
            self._set_state("planner", "working", "Found reusable shared memory")
            self._message(
                "memory",
                "planner",
                f"命中共享记忆 #{memory['id']}，相似度 {memory['similarity']}",
                "memory_hit",
            )
            subtasks = memory["subtasks"]
            result = build_reused_result(clean_task, memory)
            self._message("planner", "executor", "复用历史子任务，跳过重复拆解", "plan")
            self._set_state("planner", "done", "Reused previous plan")
            self._set_state("executor", "working", "Reusing stored execution result")
            self._message("executor", "reviewer", "基于共享记忆生成复用结果", "execute")
            self._set_state("executor", "done", "Result reused")
            self._set_state("reviewer", "working", "Checking reused result")
            passed, advice = review_result(result, subtasks)
            self._message("reviewer", "user", advice, "review")
            self._set_state("reviewer", "done" if passed else "failed", advice)
            memory_id = memory["id"]
        else:
            self._set_state("planner", "working", "Splitting task")
            subtasks = plan_subtasks(clean_task)
            self._message(
                "planner",
                "executor",
                "任务拆解完成：" + "；".join(subtasks),
                "plan",
            )
            self._set_state("planner", "done", f"{len(subtasks)} subtasks generated")

            self._set_state("executor", "working", "Executing subtasks")
            result = execute_subtasks(clean_task, subtasks)
            self._message("executor", "reviewer", "子任务执行完成，提交检查", "execute")
            self._set_state("executor", "done", "Execution finished")

            self._set_state("reviewer", "working", "Checking result")
            passed, advice = review_result(result, subtasks)
            self._message("reviewer", "memory", advice, "review")
            self._set_state("reviewer", "done" if passed else "failed", advice)

            memory_record = self.store.add_memory(
                clean_task,
                subtasks,
                result,
                build_experience(clean_task, subtasks, passed),
            )
            memory_id = int(memory_record["id"])
            self._message("memory", "all", f"任务经验已写入共享记忆 #{memory_id}", "memory_write")

        elapsed = time.perf_counter() - start
        metrics = build_metrics(memory_hit=bool(memory), message_count=len(self.messages), elapsed=elapsed)
        self.store.log_run(
            clean_task,
            bool(memory),
            memory_id,
            metrics["actual"]["message_count"],
            metrics["actual"]["step_count"],
            metrics["actual"]["estimated_seconds"],
        )

        return {
            "task": clean_task,
            "memory_hit": bool(memory),
            "memory": memory,
            "subtasks": subtasks,
            "result": result,
            "agents": [state.__dict__ for state in self.states],
            "messages": self.messages,
            "metrics": metrics,
        }

    def _reset(self) -> None:
        self.messages = []
        for state in self.states:
            state.status = "idle"
            state.detail = "Waiting"

    def _set_state(self, name: str, status: str, detail: str) -> None:
        state = next(item for item in self.states if item.name == name)
        state.status = status
        state.detail = detail
        self._message("system", name, f"{state.role} 状态变更为 {status}: {detail}", "state")

    def _message(self, sender: str, receiver: str, content: str, kind: str) -> None:
        self.messages.append(
            {
                "id": len(self.messages) + 1,
                "time": datetime.now().strftime("%H:%M:%S"),
                "sender": sender,
                "receiver": receiver,
                "kind": kind,
                "content": content,
            }
        )


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def tokenize(text: str) -> set[str]:
    lowered = text.lower()
    words = set(re.findall(r"[a-z0-9]+", lowered))
    chinese_terms = [
        "微服务",
        "架构",
        "设计文档",
        "分工",
        "前后端",
        "开发",
        "课程",
        "大作业",
        "报告",
        "提纲",
        "目录",
        "小组",
        "成员",
        "安排",
        "方案",
        "答辩",
        "ppt",
        "多智能体",
        "共享记忆",
        "通信",
        "系统",
        "演示",
        "测试",
    ]
    for term in chinese_terms:
        if term in lowered:
            words.add(term)
    for char in re.findall(r"[\u4e00-\u9fff]", text):
        words.add(char)
    return words


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def row_to_memory(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "task": row["task"],
        "task_tokens": json.loads(row["task_tokens"]),
        "subtasks": json.loads(row["subtasks"]),
        "result": row["result"],
        "experience": row["experience"],
        "hit_count": row["hit_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def plan_subtasks(task: str) -> list[str]:
    if "ppt" in task.lower() or "答辩" in task:
        return ["确定答辩结构", "整理系统亮点", "生成页面演示顺序", "总结测试指标"]
    if "分工" in task:
        return ["识别成员角色", "拆分后端与前端任务", "明确交付物", "安排答辩讲解"]
    if "报告" in task or "提纲" in task or "目录" in task:
        return ["分析背景问题", "描述系统功能", "说明关键技术", "整理测试结果", "撰写总结"]
    return ["理解任务目标", "拆分执行步骤", "生成初步结果", "检查完整性"]


def execute_subtasks(task: str, subtasks: list[str]) -> str:
    lines = [f"任务：{task}", "协作结果："]
    for index, item in enumerate(subtasks, start=1):
        lines.append(f"{index}. {item}：已完成，产出可用于报告或答辩材料。")
    lines.append("系统建议：将本次任务、子任务和检查结论写入共享记忆，供相似任务复用。")
    return "\n".join(lines)


def build_reused_result(task: str, memory: dict[str, Any]) -> str:
    return (
        f"任务：{task}\n"
        f"协作结果：检测到与历史任务“{memory['task']}”相似，已复用共享记忆。\n"
        f"复用经验：{memory['experience']}\n"
        "系统建议：保留原有任务结构，只根据当前表达微调标题和输出顺序。"
    )


def review_result(result: str, subtasks: list[str]) -> tuple[bool, str]:
    missing = [item for item in subtasks if item[:2] not in result]
    if missing:
        return False, "检查未通过：部分子任务缺少可追踪结果，需要重新执行。"
    return True, "检查通过：结果覆盖任务拆解、执行过程和可复用经验。"


def build_experience(task: str, subtasks: list[str], passed: bool) -> str:
    status = "通过检查" if passed else "需要复核"
    return f"该类任务适合按 {len(subtasks)} 个步骤处理；关键经验：先拆解、再执行、最后检查，状态为{status}。"


def build_metrics(memory_hit: bool, message_count: int, elapsed: float) -> dict[str, Any]:
    baseline_steps = 6
    baseline_messages = 10
    actual_steps = 3 if memory_hit else 6
    estimated_seconds = round((0.35 * actual_steps) + elapsed, 2)
    baseline_seconds = round(0.35 * baseline_steps + 0.25, 2)
    saved_messages = max(0, baseline_messages - message_count)
    saved_steps = max(0, baseline_steps - actual_steps)
    speedup = 0 if not memory_hit else round((baseline_seconds - estimated_seconds) / baseline_seconds * 100, 1)
    return {
        "baseline": {
            "label": "无共享记忆",
            "message_count": baseline_messages,
            "step_count": baseline_steps,
            "estimated_seconds": baseline_seconds,
        },
        "actual": {
            "label": "启用共享记忆" if memory_hit else "首次处理",
            "message_count": message_count,
            "step_count": actual_steps,
            "estimated_seconds": estimated_seconds,
        },
        "saved_messages": saved_messages,
        "saved_steps": saved_steps,
        "speedup_percent": speedup,
    }


store = MemoryStore(DB_PATH)
runtime = AgentRuntime(store)
app = FastAPI(title="Multi-Agent Shared Memory Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/tasks")
def run_task(payload: TaskRequest) -> dict[str, Any]:
    return runtime.run(payload.task, payload.use_memory)


@app.get("/api/memory")
def list_memory() -> dict[str, Any]:
    return {"items": store.list_memories()}


@app.post("/api/memory")
def create_memory(payload: MemoryCreateRequest) -> dict[str, Any]:
    memory = store.add_memory(payload.task, payload.subtasks, payload.result, payload.experience)
    return {"item": memory}


@app.get("/api/runs")
def list_runs() -> dict[str, Any]:
    return {"items": store.recent_runs()}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
