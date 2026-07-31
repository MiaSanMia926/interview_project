from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


ROOT = Path(r"C:\Users\Lenovo\Documents\暑期实训项目")
TEMPLATE = Path(r"C:\Users\Lenovo\Downloads\问题记录模版.docx")
OUTPUT = ROOT / "第一周问题记录.docx"


def set_cell_text(cell, text, bold=False, size=10.5, align=None):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)
    for paragraph in cell.paragraphs:
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.15


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_width(cell, width_dxa):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width_dxa))
    tc_w.set(qn("w:type"), "dxa")


def set_margins(cell, top=120, start=120, bottom=120, end=120):
    tc_pr = cell._tc.get_or_add_tcPr()
    mar = tc_pr.find(qn("w:tcMar"))
    if mar is None:
        mar = OxmlElement("w:tcMar")
        tc_pr.append(mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def main():
    doc = Document(str(TEMPLATE))
    section = doc.sections[0]
    section.top_margin = Pt(72)
    section.bottom_margin = Pt(72)
    section.left_margin = Pt(72)
    section.right_margin = Pt(72)

    table = doc.tables[0]
    headers = ["学号", "姓名", "班级", "项目名称/角色", "日期", "问题记录"]
    values = ["待填写", "待填写", "待填写", "智能面试突破助手 / 后端与RAG集成", "第一周", ""]
    issues = (
        "1. 项目初期需求范围较大，涉及 FastAPI、SQLite、Multi-Agent、RAG 检索、题库数据等多个模块，"
        "模块边界和调用关系不够清晰。\n"
        "解决方法：先梳理 PROJECT_STRUCTURE.md 和主文档，明确 backend、agents、rag、data、tests 的目录职责；"
        "将后端接口、业务服务、Agent 协作和检索能力拆分为相对独立的模块，降低集成复杂度。\n\n"
        "2. 面试题数据来源和字段格式不统一，直接用于检索时容易出现重复、缺字段或类别不一致的问题。\n"
        "解决方法：编写 QuestionLoader 与 load_questions.py，对 JSON 数据进行字段规范化、清洗和去重；"
        "生成 clean_questions.json 和 question_index.json，为后续检索与标准答案匹配提供稳定数据基础。\n\n"
        "3. ChromaDB 或 embedding 环境不一定完整可用，若完全依赖外部向量库会影响第一周演示进度。\n"
        "解决方法：在 RAGEngine 中实现本地 JSON 索引 fallback，采用文本相似度、关键词重合度和 MMR 多样性检索，"
        "保证离线环境下也能完成检索演示，并预留后续替换为真实 ChromaDB 的接口。\n\n"
        "4. API 层需要同时对接用户、面试流程、问题生成、回答提交和总结查询，接口参数与状态流转容易混乱。\n"
        "解决方法：使用 Pydantic Schema 统一请求和响应结构，在 interview_service.py 中集中处理面试状态、"
        "评分结果和下一步动作，路由层只负责参数接收与结果返回。\n\n"
        "5. 第一周集成后需要确认核心链路可运行，但手工测试效率较低，也不便于复现问题。\n"
        "解决方法：补充 test_api.py 与 tests/test_rag.py，覆盖健康检查、用户创建、面试创建、RAG 检索、"
        "缓存统计等关键路径，便于后续迭代时快速发现回归问题。"
    )
    summary = (
        "本周主要完成项目基础结构搭建、后端接口雏形、Agent 协作模块、RAG 数据加载与本地检索能力。"
        "遗留风险集中在真实大模型/向量库接入、前后端字段联调和展示效果验证，计划在第二周继续完善。"
    )

    col_widths = [1200, 1200, 1300, 2300, 1200, 3560]
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_margins(cell)
            if idx < len(col_widths):
                set_width(cell, col_widths[idx])

    for idx, cell in enumerate(table.rows[0].cells):
        set_cell_text(cell, headers[idx], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
        shade_cell(cell, "D9EAF7")

    for idx, cell in enumerate(table.rows[1].cells):
        set_cell_text(cell, values[idx], align=WD_ALIGN_PARAGRAPH.CENTER if idx != 3 else WD_ALIGN_PARAGRAPH.LEFT)

    issue_content_cell = table.rows[2].cells[1].merge(table.rows[2].cells[5])
    note_content_cell = table.rows[3].cells[1].merge(table.rows[3].cells[5])

    set_cell_text(table.rows[2].cells[0], "问题及解决情况", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    shade_cell(table.rows[2].cells[0], "EEF5FB")
    set_cell_text(issue_content_cell, issues, size=10)

    set_cell_text(table.rows[3].cells[0], "图示/说明", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    shade_cell(table.rows[3].cells[0], "EEF5FB")
    set_cell_text(note_content_cell, summary, size=10)

    doc.save(str(OUTPUT))
    print(OUTPUT)


if __name__ == "__main__":
    main()
