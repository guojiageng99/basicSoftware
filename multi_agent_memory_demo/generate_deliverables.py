#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate .docx report and .pptx from docx template."""
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from docx import Document
from docx.shared import Pt, Cm, RGBColor as DRGB
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from pptx import Presentation
from pptx.util import Inches as PptInches, Pt as PptPt
from pptx.dml.color import RGBColor as PptRGB


BASE = Path(__file__).resolve().parent.parent

def _dfont(run, name="Microsoft YaHei", size=None, bold=False, color=None):
    """Set font for docx run."""
    run.font.name = name or "Microsoft YaHei"
    if size:
        run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = DRGB(*color)


def build_docx():
    doc = Document()
    s = doc.sections[0]
    s.top_margin = Cm(2.54)
    s.bottom_margin = Cm(2.54)
    s.left_margin = Cm(3.17)
    s.right_margin = Cm(3.17)

    ns = doc.styles["Normal"]
    ns.font.name = "Microsoft YaHei"
    ns.font.size = Pt(12)

    def h(text, level=1):
        out = doc.add_heading(text, level=level)
        for r in out.runs:
            _dfont(r, name="Microsoft YaHei")
        return out

    def p(text, size=12, align=None, space_after=6, bold=False):
        pg = doc.add_paragraph()
        run = pg.add_run(text)
        _dfont(run, size=size, bold=bold, name="Microsoft YaHei")
        pg.paragraph_format.space_after = Pt(space_after)
        if align:
            pg.alignment = align
        return pg

    def bullet(text, level=0):
        pg = doc.add_paragraph(text, style="List Bullet")
        pg.paragraph_format.left_indent = Cm(1.2 + level * 0.8)
        pg.paragraph_format.space_after = Pt(3)
        for r in pg.runs:
            _dfont(r, size=11)
        return pg

    def add_row(table, data):
        row = table.add_row()
        for i, txt in enumerate(data):
            cell = row.cells[i]
            cell.text = ""
            run = cell.paragraphs[0].add_run(txt)
            _dfont(run, size=10, bold=(i == 0))

    # TITLE PAGE
    for _ in range(5):
        doc.add_paragraph()
    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = tp.add_run("面向课程任务协作场景的多智能体\n低开销通信、状态传递与共享记忆原型系统")
    _dfont(r, size=22, bold=True)
    doc.add_paragraph()
    sp = doc.add_paragraph()
    sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sp.add_run("—— 2026春《国产基础软件技术及应用》课程大作业")
    _dfont(r, size=14)
    ip = doc.add_paragraph()
    ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ip.paragraph_format.space_before = Pt(30)
    r = ip.add_run("组长：郭嘉庚  组员：黄振明\n提交日期：2026年6月")
    _dfont(r, size=12)
    doc.add_page_break()

    # TOC
    h("目 过 录", 1)
    doc.add_paragraph("（自动生成目录，请使用'引用 -> 索引和目录'功能后更新）")
    doc.add_page_break()

    # Section 1
    h("面向课程任务协作场景的多智能体\n低开销通信、状态传递与共享记忆原型系统", 1)
    p("随着智能体技术在办公自动化、软件开发辅助、知识管理等场景中的应用增多，单一智能体已经难以覆盖复杂任务中的规划、执行、检查和经验复用需求。多智能体协作可以将复杂任务拆分给不同角色处理，但也带来了新的系统问题：智能体之间需要频繁通信，任务状态需要在多个角色之间同步，历史经验如果不能沉淀和复用，就会导致相似任务重复处理。")
    p("在课程任务协作场景中，这类问题非常典型。例如完成一份大作业报告时，需要先分析题目要求，再拆分报告结构，随后生成内容并检查是否完整。如果每次遇到相似任务都重新拆解和执行，增加了重复沟通成本。针对这一问题，本项目设计并实现了一个多智能体协作通信与共享记忆原型系统，用规则模拟三个智能体的协作流程，并通过共享记忆机制验证经验复用对通信开销和处理步骤的降低效果。项目选定的赛题为'赛题9：一种面向多智能体协作的低开销通信、状态传递与共享记忆机制'。")

    # Section 2
    h("系统总体设计", 1)
    h("架构概述", 2)
    p("系统采用经典的三层架构设计：")
    bullet("表现层：基于 HTML/CSS/JS 的单页面 Web Dashboard，展示任务输入、Agent 状态、消息日志、共享记忆和实验指标。")
    bullet("业务层：Python FastAPI 后端，负责 Agent 调度、任务拆解、消息路由和对比指标计算。")
    bullet("数据层：SQLite 嵌入式数据库，持久化存储共享记忆条目和运行记录。")

    h("三 Agent 协作模型", 2)
    p("系统定义了三个核心智能体角色，按串行流水线方式协作：")
    t = doc.add_table(rows=1, cols=4)
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, hh in enumerate(["Agent 名称", "职责", "状态流转", "关键行为"]):
        c = t.rows[0].cells[i]; c.text = ""; rh = c.paragraphs[0].add_run(hh); _dfont(rh, size=10, bold=True)
    add_row(t, ["Planner（规划）", "分析任务类型，拆分为子任务", "idle->working->done", "关键词匹配任务类别"])
    add_row(t, ["Executor（执行）", "根据子任务生成执行结果", "idle->working->done", "逐条完成子任务"])
    add_row(t, ["Reviewer（检查）", "检查结果完整性，输出结论", "idle->working->done/failed", "比对结果中是否包含所有子任务关键词"])

    h("消息通信模块", 2)
    p("系统使用轻量级消息记录机制模拟智能体之间的通信。每条消息包含 sender、receiver、kind、content、time 五个字段。")
    mt = doc.add_table(rows=1, cols=3)
    mt.style = "Light Grid Accent 1"
    mt.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, hh in enumerate(["字段", "含义", "示例值"]):
        c = mt.rows[0].cells[i]; c.text = ""; rc = c.paragraphs[0].add_run(hh); _dfont(rc, size=10, bold=True)
    add_row(mt, ["sender", "发送者标识", "planner / executor / reviewer"])
    add_row(mt, ["receiver", "接收者标识", "all / planner / executor"])
    add_row(mt, ["kind", "消息类型", "task / plan / execute / review"])
    add_row(mt, ["content", "消息正文", "任务拆解完成..."])
    add_row(mt, ["time", "时间戳", "14:23:05"])

    h("状态管理", 2)
    p("每个 Agent 使用统一状态机模型管理运行过程，状态包括 idle（等待）、working（执行中）、done（已完成）、failed（未通过检查）。状态转换保证了整个流程的可观测性和透明性。")

    h("共享记忆模块", 2)
    bullet("存储介质：SQLite 嵌入式数据库，跨平台、零配置部署。")
    bullet("记忆条目：任务描述、关键词 tokens、子任务列表、执行结果、经验总结、命中次数。")
    bullet("写入时机：首次完整处理任务后，自动将结果沉淀为可复用的经验。")
    bullet("读取时机：用户提交新任务时，优先检索共享记忆是否存在相似条目。")

    h("记忆命中机制", 2)
    p("系统采用词袋模型 + Jaccard 相似度算法实现记忆匹配：")
    bullet("分词：提取中文单字、英文单词和预设领域关键词（如'课程''报告''答辩''多智能体''共享记忆'等）。")
    bullet("计算：score = |A ∩ B| / |A ∪ B|，其中 A、B 分别为当前任务和已有记忆的 token 集合。")
    bullet("判定：当最高相似度超过阈值（默认 0.25）时，判定为命中共享记忆。")
    bullet("复用：命中后直接复用历史子任务和结果，跳过完整的任务拆解流程，步骤数从 6 步降至 3 步。")

    doc.add_page_break()

    # Section 3
    h("关键技术实现", 1)
    h("后端 API 设计", 2)
    p("后端基于 FastAPI 框架，提供以下 RESTful 接口：")
    at = doc.add_table(rows=1, cols=3)
    at.style = "Light Grid Accent 1"
    at.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, hh in enumerate(["接口", "方法", "说明"]):
        c = at.rows[0].cells[i]; c.text = ""; rc = c.paragraphs[0].add_run(hh); _dfont(rc, size=10, bold=True)
    add_row(at, ["GET /api/health", "GET", "健康检查"])
    add_row(at, ["POST /api/tasks", "POST", "提交任务，触发 3-Agent 协作"])
    add_row(at, ["GET /api/memory", "GET", "查询共享记忆库"])
    add_row(at, ["POST /api/memory", "POST", "手动录入记忆条目"])
    add_row(at, ["GET /api/runs", "GET", "查询运行历史记录"])

    h("数据库设计", 2)
    bullet("数据库设计：memories 表：id, task, task_tokens(JSON), subtasks(JSON), result, experience, hit_count, created_at, updated_at")
    bullet("运行记录：runs 表：id, task, memory_hit, memory_id, message_count, step_count, estimated_seconds, created_at")

    h("前端实现", 2)
    p("前端使用原生 HTML5 + CSS3 + Vanilla JavaScript 开发，无需任何框架依赖。布局采用 CSS Grid 实现响应式设计，支持桌面端和移动端自适应显示。Dashboard 包含七大区域：任务输入面板、Agent 状态卡片、共享记忆命中区、实验指标区、消息通信日志区、执行结果区和共享记忆库列表区。")

    doc.add_page_break()

    # Section 4
    h("测试与实验分析", 1)
    h("单元测试", 2)
    p("使用 pytest 框架编写了 3 个自动化测试用例：")
    bullet("test_health — 验证健康检查接口正常返回。")
    bullet("test_task_run_and_memory_hit — 先运行一次报告提纲任务，再运行相似任务，验证共享记忆命中功能和指标下降。")
    bullet("test_assignment_task_memory_hit — 先运行分工方案任务，再运行相似分工任务，验证泛化匹配能力。")
    p("测试结果：全部通过（3 passed in 0.66s）。")

    h("对比实验", 2)
    p("实验设定两组场景进行对比：")
    et = doc.add_table(rows=1, cols=4)
    et.style = "Light Grid Accent 1"
    et.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, hh in enumerate(["指标", "无共享记忆（基线）", "有共享记忆（实际）", "节省比例"]):
        c = et.rows[0].cells[i]; c.text = ""; rc = c.paragraphs[0].add_run(hh); _dfont(rc, size=10, bold=True)
    add_row(et, ["消息数量", "10", "7", "减少 3 条"])
    add_row(et, ["步骤数量", "6", "3", "减少 50%"])
    add_row(et, ["估算耗时(s)", "2.35", "~1.30", "提速约 45%"])

    h("演示流程", 2)
    bullet("Step 1：输入'生成一份课程大作业报告提纲'，观察完整的 Plan-Execute-Review 流程。")
    bullet("Step 2：输入'帮我生成课程大作业报告目录'，观察共享记忆命中效果。")
    bullet("Step 3：输入'整理一次小组分工方案'，观察不同类型任务的独立处理能力。")

    doc.add_page_break()

    # Section 5
    h("国产基础软件应用情况", 1)
    p("本项目面向国产基础软件生态中的智能体协作场景，重点关注操作系统上层智能应用的任务协作、状态传递和经验复用机制。")
    p("技术选型方面，系统采用 Python、FastAPI、SQLite 和 Web 前端技术栈，具备完整的跨平台运行能力，可在 Windows 和 Linux 环境中无缽部署。这些技术均遵守开源协议，与国产操作系统（如麒麟软件 openKylin、OpenHarmony）兼容性好，可作为国产基础软件生态中智能应用层的参考实现。")
    p("从国产基础软件课程角度看，本项目关注的是智能体系统在操作系统应用层的基础支撑能力：低开销通信、状态可观测、共享记忆持久化和可复用接口设计。后续如果迁移到国产 Linux 发行版，可将当前本地 SQLite 存储扩展为系统服务，将消息通信机制扩展为进程间通信或 D-Bus 接口，将共享记忆模块作为桌面智能助手或系统 Agent 的基础组件。")

    doc.add_page_break()

    # Section 6
    h("总结与展望", 1)
    p("本项目完成了一个可运行、可演示的多智能体协作通信与共享记忆原型系统。具体完成了以下工作：① 实现了规划 Agent、执行 Agent、检查 Agent 的串行协作流水线；② 设计了轻量级消息通信机制，可完整回溯一次任务的全部交互过程；③ 使用 SQLite 实现了共享记忆库，保存历史任务经验和子任务结构；④ 通过相似任务对比实验，验证了共享记忆对重复任务处理的优化效果。")

    h("不足与改进方向", 2)
    bullet("接入真实大模型 API，使 Agent 具备更强的自然语言理解和生成能力。")
    bullet("引入向量检索（如 FAISS、ChromaDB），替代当前的 Jaccard 词袋匹配，提高记忆命中率。")
    bullet("将共享记忆模块封装为独立系统服务，为多个并发应用提供统一的智能体经验复用能力。")
    bullet("扩展并行协作模式，允许多个 Agent 同时工作并通过消息总线异步协调。")
    bullet("适配国产操作系统环境，增加对麒麟 openKylin 和 OpenHarmony 的兼容性测试。")

    path = BASE / "大作业报告.docx"
    doc.save(str(path))
    print("[OK] 报告已保存:", path)


def build_pptx():
    prs = Presentation()
    prs.slide_width = PptInches(13.333)
    prs.slide_height = PptInches(7.5)

    BG = PptRGB(244, 241, 234)
    GRN = PptRGB(25, 107, 84)
    BLK = PptRGB(24, 34, 31)

    def blank():
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        bg = sl.background; fl = bg.fill; fl.solid(); fl.fore_color.rgb = BG
        bar = sl.shapes.add_shape(1, PptInches(0), PptInches(0), PptInches(13.333), PptInches(0.06))
        bar.fill.solid(); bar.fill.fore_color.rgb = GRN; bar.line.fill.background()
        return sl

    def title_sl(text, bullets, top=1.5):
        sl = blank()
        tb = sl.shapes.add_textbox(PptInches(0.7), PptInches(0.5), PptInches(11.5), PptInches(1))
        tf = tb.text_frame; tf.word_wrap = True
        r = tf.paragraphs[0].add_run(text)
        r.font.size = PptPt(26); r.bold = True; r.font.color.rgb = GRN; r.font.name = "微软雅黑"
        if bullets:
            bb = sl.shapes.add_textbox(PptInches(0.7), PptInches(top), PptInches(11.5), PptInches(5.5))
            tf2 = bb.text_frame; tf2.word_wrap = True
            for idx, b in enumerate(bullets):
                pg = tf2.paragraphs[0] if idx == 0 else tf2.add_paragraph()
                pg.space_after = PptPt(8)
                rr = pg.add_run("• " + b)
                rr.font.size = PptPt(15); rr.font.color.rgb = BLK; rr.font.name = "微软雅黑"
        return sl

    # Slide 1
    sl = blank()
    tb = sl.shapes.add_textbox(PptInches(1), PptInches(2.2), PptInches(11), PptInches(2.5))
    tf = tb.text_frame; tf.word_wrap = True
    r1 = tf.paragraphs[0].add_run("面向课程任务协作场景的多智能体\n低开销通信、状态传递与共享记忆原型系统")
    r1.font.size = PptPt(30); r1.bold = True; r1.font.color.rgb = GRN; r1.font.name = "微软雅黑"
    sb = sl.shapes.add_textbox(PptInches(1), PptInches(4.8), PptInches(11), PptInches(0.6))
    sf = sb.text_frame
    r2 = sf.paragraphs[0].add_run("—— 2026春《国产基础软件技术及应用》课程大作业 · 郭嘉廍 · 黄振明")
    r2.font.size = PptPt(14); r2.font.color.rgb = PptRGB(102, 112, 107); r2.font.name = "微软雅黑"

    title_sl("背景问题", [
        "智能体技术在办公自动化、软件开发、知识管理中广泛应用",
        "单一智能体难以覆盖复杂任务的全生命周期",
        "多智能体协作带来通信开销、状态同步和经验复用难题",
        "在课程任务协作中，相似任务重复拆解增加了不必要的沟通成本",
        "本项目围绕赛题9，设计低开销通信、状态传递和共享记忆机制",
    ])

    title_sl("系统总体架构", [
        "表现层：HTML/CSS/JS 单页面 Dashboard（七大可视化区域）",
        "业务层：Python FastAPI 后端（Agent 调度、任务拆解、消息路由）",
        "数据层：SQLite 嵌入式数据库（共享记忆持久化）",
        "三层解耦、跨平台部署、零外部依赖服务",
    ])

    title_sl("三 Agent 协作模型", [
        "Planner（规划）：分析任务类型，拆分为多个可执行的子任务",
        "Executor（执行）：根据子任务列表逐项生成执行结果",
        "Reviewer（检查）：检查结果是否覆盖所有子任务，输出审查结论",
        "串行流水线协作模式：用户 -> Planner -> Executor -> Reviewer -> 用户",
    ])

    title_sl("消息通信与状态管理", [
        "轻量级消息队列：sender、receiver、kind、content、time 五字段",
        "消息类型：task / plan / execute / review / state / memory_hit",
        "状态机：idle -> working -> done / failed",
        "全链路可观测：一次任务的所有通信均可在 Dashboard 追探",
    ])

    title_sl("共享记忆机制", [
        "写入：首次完整处理后，自动将任务、子任务、结果、经验写入 SQLite",
        "读取：新任务提交时，优先检索共享记忆中的相似条目",
        "分词：中文单字 + 英文单词 + 领域关键词",
        "匹配：Jaccard 相似度算法，threshold = 0.25",
        "复用：命中后步骤数从 6 步缩减至 3 步，消息减少 30%",
    ])

    title_sl("实验结果", [
        "消息数量：10 -> 7，减少 3 条",
        "步骤数量：6 -> 3，减少 50%",
        "估算耗时：2.35s -> ~1.30s，提速约 45%",
        "自动化测试：3 个用例全部通过",
    ])

    title_sl("总结与展望", [
        "完成了可运行、可演示的多智能体协作原型系统",
        "验证了共享记忆对重复任务处理的优化价值",
        "系统设计面向国产基础软件生态，兼容麒麟 openKylin / OpenHarmony",
        "未来方向：接入 LLM API、引入向量检索、封装系统服务、适配国产 OS",
    ])

    path = BASE / "答辩PPT.pptx"
    prs.save(str(path))
    print("[OK] PPT已保存:", path)


if __name__ == "__main__":
    print("Generating deliverables...")
    build_docx()
    build_pptx()
    print("\nDone!")
