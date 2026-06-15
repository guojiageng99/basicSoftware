const taskInput = document.querySelector("#taskInput");
const useMemory = document.querySelector("#useMemory");
const runButton = document.querySelector("#runButton");
const agentGrid = document.querySelector("#agentGrid");
const runStatus = document.querySelector("#runStatus");
const memoryLabel = document.querySelector("#memoryLabel");
const memoryHit = document.querySelector("#memoryHit");
const metricsBox = document.querySelector("#metrics");
const messageLog = document.querySelector("#messageLog");
const messageCount = document.querySelector("#messageCount");
const resultBox = document.querySelector("#resultBox");
const memoryList = document.querySelector("#memoryList");
const memoryCount = document.querySelector("#memoryCount");

const defaultAgents = [
  { name: "planner", role: "规划 Agent", status: "idle", detail: "等待任务" },
  { name: "executor", role: "执行 Agent", status: "idle", detail: "等待任务" },
  { name: "reviewer", role: "检查 Agent", status: "idle", detail: "等待任务" },
];

document.querySelectorAll("[data-task]").forEach((button) => {
  button.addEventListener("click", () => {
    taskInput.value = button.dataset.task;
  });
});

runButton.addEventListener("click", async () => {
  const task = taskInput.value.trim();
  if (!task) {
    taskInput.focus();
    return;
  }

  runButton.disabled = true;
  runButton.textContent = "协作中...";
  runStatus.textContent = "正在运行";
  renderAgents(defaultAgents.map((agent) => ({ ...agent, status: "working", detail: "准备协作" })));

  try {
    const response = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task, use_memory: useMemory.checked }),
    });
    const data = await response.json();
    renderRun(data);
    await loadMemory();
  } catch (error) {
    runStatus.textContent = "运行失败";
    resultBox.textContent = `请求失败：${error}`;
  } finally {
    runButton.disabled = false;
    runButton.textContent = "运行协作流程";
  }
});

function renderRun(data) {
  runStatus.textContent = data.memory_hit ? "共享记忆命中" : "首次完整处理";
  renderAgents(data.agents);
  renderMemoryHit(data);
  renderMetrics(data.metrics);
  renderMessages(data.messages);
  resultBox.textContent = data.result;
}

function renderAgents(agents) {
  agentGrid.innerHTML = agents
    .map(
      (agent) => `
        <article class="agent-card">
          <strong>${agent.role}</strong>
          <span class="status ${agent.status}">${agent.status}</span>
          <p>${agent.detail}</p>
        </article>
      `
    )
    .join("");
}

function renderMemoryHit(data) {
  memoryHit.className = `memory-hit ${data.memory_hit ? "hit" : "miss"}`;
  memoryLabel.textContent = data.memory_hit ? "命中" : "未命中";
  if (data.memory_hit) {
    memoryHit.innerHTML = `
      <strong>命中共享记忆 #${data.memory.id}</strong>
      <p>相似任务：${data.memory.task}</p>
      <p>相似度：${data.memory.similarity}，历史命中次数：${data.memory.hit_count}</p>
    `;
  } else {
    memoryHit.innerHTML = `
      <strong>首次处理，已写入共享记忆</strong>
      <p>系统完成任务拆解、执行、检查，并将结果沉淀为可复用经验。</p>
    `;
  }
}

function renderMetrics(metrics) {
  const rows = [
    ["消息数", metrics.actual.message_count, metrics.baseline.message_count],
    ["步骤数", metrics.actual.step_count, metrics.baseline.step_count],
    ["估算耗时", metrics.actual.estimated_seconds, metrics.baseline.estimated_seconds],
  ];

  const summary = `
    <div class="memory-hit ${metrics.speedup_percent > 0 ? "hit" : "empty"}">
      <strong>${metrics.actual.label}</strong>
      <p>节省步骤：${metrics.saved_steps}，节省消息：${metrics.saved_messages}，估算提速：${metrics.speedup_percent}%</p>
    </div>
  `;

  metricsBox.innerHTML =
    summary +
    rows
      .map(([label, actual, baseline]) => {
        const width = Math.max(8, Math.min(100, Math.round((actual / baseline) * 100)));
        return `
          <div class="metric-row">
            <span>${label}</span>
            <div class="bar"><span style="width:${width}%"></span></div>
            <strong>${actual}</strong>
          </div>
        `;
      })
      .join("");
}

function renderMessages(messages) {
  messageCount.textContent = `${messages.length} 条消息`;
  messageLog.innerHTML = messages
    .map(
      (message) => `
        <article class="message">
          <time>${message.time}</time>
          <span class="route">${message.sender} -> ${message.receiver}</span>
          <p>${message.content}</p>
        </article>
      `
    )
    .join("");
}

async function loadMemory() {
  const response = await fetch("/api/memory");
  const data = await response.json();
  memoryCount.textContent = `${data.items.length} 条`;
  if (!data.items.length) {
    memoryList.innerHTML = `<div class="memory-item"><strong>暂无记忆</strong><p>首次运行任务后会自动写入。</p></div>`;
    return;
  }

  memoryList.innerHTML = data.items
    .map(
      (item) => `
        <article class="memory-item">
          <strong>#${item.id} ${item.task}</strong>
          <p>${item.experience}</p>
          <p>命中次数：${item.hit_count}，更新时间：${item.updated_at}</p>
        </article>
      `
    )
    .join("");
}

renderAgents(defaultAgents);
renderMetrics({
  baseline: { message_count: 10, step_count: 6, estimated_seconds: 2.35 },
  actual: { label: "等待运行", message_count: 0, step_count: 0, estimated_seconds: 0 },
  saved_steps: 0,
  saved_messages: 0,
  speedup_percent: 0,
});
loadMemory();
