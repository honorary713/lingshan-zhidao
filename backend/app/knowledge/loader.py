from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

import re


# 中文区间（含标点），用于判断“两个中文字之间的空格”应被删除
_CJK = r"\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"

# 抽取噪声：学生手册 PDF 中常见的间隔符 / 乱码字符（直接删除）
_BAD_CHARS = (
    "\u668b"  # 暋：夹在汉字间的间隔符
    "\u66eb"  # 曫：出现在“二曫二四年”这类位置
    "\u683a"  # 栺：零散乱码（如“栺学校概况”）
    "\u200b"  # 零宽空格
    "\ufeff"  # BOM
    "\u00a0"  # 不换行空格
)

# 需要替换（而非删除）的字符：PDF 误把右引号渲染成 暠
_REPLACE_MAP = {
    "\u66a0": "\u201d",  # 暠 -> ”
}

_BAD_RE = re.compile("[" + re.escape(_BAD_CHARS) + "]")
_REPLACE_RE = re.compile("|".join(re.escape(k) for k in _REPLACE_MAP))
# 删除“两个 CJK 字符之间”的空格（解决“勤 奋 严 谨”型噪声）
_SPACE_BETWEEN_CJK = re.compile(r"(?<=[" + _CJK + r"])\s+(?=[" + _CJK + r"])")
# 删除 ASCII 括号/方括号与相邻汉字之间的空格（如“( 华东)” -> “(华东)”）
_BRACKET_SPACE = re.compile(r"([\(\[])\s+(?=[" + _CJK + r"])|(?<=[" + _CJK + r"])\s+([\)\]])")
# 纯数字页码行（如单独一行的 “12” 或 “— 13 —”）
_PAGE_RE = re.compile(r"^\s*[-—~]?\s*\d+\s*[-—~]?\s*$")
# 常见页眉/页脚固定串（按需增删）
_HEADER_FOOTER = re.compile(r"中国石油大学（华东）学生手册\s*")  # 每页重复的页眉


def clean_text(text: str) -> str:
    """清洗从 PDF/文档抽取出的文本噪声。"""
    if not text:
        return ""

    text = _BAD_RE.sub("", text)
    text = _REPLACE_RE.sub(lambda m: _REPLACE_MAP[m.group(0)], text)
    text = _HEADER_FOOTER.sub("", text)
    # 全角空格统一为半角
    text = text.replace("\u3000", " ")
    # 删除 CJK 之间的空格、括号与汉字之间的空格
    text = _SPACE_BETWEEN_CJK.sub("", text)
    text = _BRACKET_SPACE.sub(lambda m: m.group(1) or m.group(2), text)
    # 折叠多余空白
    text = re.sub(r"[ \t]+", " ", text)
    # 逐行去掉纯页码行 + 行首尾空白
    lines = []
    for line in text.splitlines():
        if _PAGE_RE.match(line):
            continue
        line = line.strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _iter_block_items(parent):
    for child in parent.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def _extract_pdf_text(file_path: Path) -> str:
    """优先用 PyMuPDF（对中文 PDF 更友好），失败回退 pypdf。"""
    try:
        import fitz

        doc = fitz.open(str(file_path))
        pages = [page.get_text() for page in doc]
        return "\n".join(pages)
    except Exception:
        pass

    try:
        import pypdf

        reader = pypdf.PdfReader(str(file_path))
        return "\n".join((pg.extract_text() or "") for pg in reader.pages)
    except Exception:
        return ""


def load_documents(docs_dir: Path) -> list[dict]:
    documents = []

    for file_path in sorted(docs_dir.glob("*.docx")):
        document = Document(str(file_path))
        parts = []

        for block in _iter_block_items(document):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if text:
                    parts.append(text)
            else:
                for row in block.rows:
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            parts.append(cell_text)

        text = clean_text("\n".join(parts))

        if text:
            documents.append({
                "source": file_path.name,
                "text": text,
            })

    for file_path in sorted(docs_dir.glob("*.pdf")):
        raw = _extract_pdf_text(file_path)
        text = clean_text(raw)

        if text:
            documents.append({
                "source": file_path.name,
                "text": text,
            })

    return documents


def extract_text(filename: str, data: bytes) -> str:
    """从上传文件中提取纯文本（.docx / .pdf / 其余按文本解码）。"""
    lower = filename.lower()

    if lower.endswith(".docx"):
        import io

        document = Document(io.BytesIO(data))
        parts = []
        for block in _iter_block_items(document):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if text:
                    parts.append(text)
            else:
                for row in block.rows:
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            parts.append(cell_text)
        return clean_text("\n".join(parts))

    if lower.endswith(".pdf"):
        import io

        try:
            import fitz

            doc = fitz.open(stream=data, filetype="pdf")
            return clean_text("\n".join(p.get_text() for p in doc))
        except Exception:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(data))
            return clean_text("\n".join((pg.extract_text() or "") for pg in reader.pages))

    for encoding in ("utf-8", "gbk", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


if __name__ == "__main__":
    docs_dir = Path(__file__).resolve().parent.parent.parent / "knowledge_docs"
    result = load_documents(docs_dir)

    print(f"加载文档数：{len(result)}")

    for item in result:
        print(f"文档：{item['source']}")
        print(f"字符数：{len(item['text'])}")
        print(item["text"][:200])
        print("---")
