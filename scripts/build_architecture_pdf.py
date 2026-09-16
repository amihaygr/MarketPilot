"""Build the final MarketPilot architecture PDF from the Markdown source of truth."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "architecture" / "architecture.md"
OUTPUT = ROOT / "docs" / "architecture" / "output" / "MarketPilot.pdf"

PAGE = landscape(A4)
PAGE_WIDTH, PAGE_HEIGHT = PAGE

NAVY = colors.HexColor("#071523")
PANEL = colors.HexColor("#10283C")
MINT = colors.HexColor("#35D4B5")
BLUE = colors.HexColor("#5B91FF")
AMBER = colors.HexColor("#F4B94F")
CORAL = colors.HexColor("#EF7484")
INK = colors.HexColor("#102030")
MUTED = colors.HexColor("#5B6B78")
LINE = colors.HexColor("#D7E0E7")
PAPER = colors.HexColor("#F7F9FB")


def register_fonts() -> tuple[str, str, str]:
    regular = Path("C:/Windows/Fonts/arial.ttf")
    bold = Path("C:/Windows/Fonts/arialbd.ttf")
    mono = Path("C:/Windows/Fonts/consola.ttf")
    if regular.exists() and bold.exists() and mono.exists():
        pdfmetrics.registerFont(TTFont("MPArial", str(regular)))
        pdfmetrics.registerFont(TTFont("MPArialBold", str(bold)))
        pdfmetrics.registerFont(TTFont("MPMono", str(mono)))
        return "MPArial", "MPArialBold", "MPMono"
    return "Helvetica", "Helvetica-Bold", "Courier"


FONT, FONT_BOLD, FONT_MONO = register_fonts()


def inline_markdown(value: str) -> str:
    escaped = html.escape(value.strip())
    escaped = re.sub(r"`([^`]+)`", rf'<font name="{FONT_MONO}" color="#117C70">\1</font>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    return escaped


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="MPTitle",
        parent=styles["Title"],
        fontName=FONT_BOLD,
        fontSize=28,
        leading=32,
        textColor=INK,
        spaceAfter=10,
    )
)
styles.add(
    ParagraphStyle(
        name="MPH1",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=19,
        leading=23,
        textColor=INK,
        spaceBefore=8,
        spaceAfter=8,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="MPH2",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#117C70"),
        spaceBefore=7,
        spaceAfter=5,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="MPBody",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=9.6,
        leading=14,
        textColor=INK,
        spaceAfter=6,
    )
)
styles.add(
    ParagraphStyle(
        name="MPCode",
        parent=styles["Code"],
        fontName=FONT_MONO,
        fontSize=8.3,
        leading=12,
        leftIndent=8,
        rightIndent=8,
        borderColor=colors.HexColor("#B9D8D2"),
        borderWidth=0.7,
        borderPadding=7,
        backColor=colors.HexColor("#EEF8F6"),
        textColor=INK,
        spaceBefore=3,
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="MPSmall",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=7.5,
        leading=10,
        textColor=MUTED,
    )
)


class ArchitectureOverview(Flowable):
    """Compact vector overview used on the cover page."""

    def __init__(self, width: float, height: float = 80 * mm) -> None:
        super().__init__()
        self.width = width
        self.height = height

    def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]:
        return min(self.width, avail_width), self.height

    def draw(self) -> None:
        canvas = self.canv
        width = self.width
        height = self.height
        canvas.setFillColor(NAVY)
        canvas.roundRect(0, 0, width, height, 9, fill=1, stroke=0)
        canvas.setFont(FONT_BOLD, 11)
        canvas.setFillColor(colors.white)
        canvas.drawString(16, height - 22, "FOUR GOVERNED PATHS, ONE EXPLAINABLE PRODUCT")

        rows = [
            ("LIVE", MINT, ["Alpaca", "Kafka", "Spark Streaming", "Gold PROVISIONAL"]),
            ("CERTIFIED", BLUE, ["Bronze", "Spark Batch + DQ", "Silver", "Gold CERTIFIED"]),
            ("RAW ARCHIVE", AMBER, ["Kafka", "Archive Sink", "MinIO Bronze", "Replay evidence"]),
            ("DECISION", CORAL, ["v1 rules", "Hybrid v2 gate", "Backend API", "Web App"]),
        ]
        top = height - 48
        label_width = 78
        gap = 10
        node_width = (width - 36 - label_width - (3 * gap)) / 4
        for index, (label, accent, nodes) in enumerate(rows):
            y = top - index * 52
            canvas.setFillColor(accent)
            canvas.setFont(FONT_BOLD, 8)
            canvas.drawString(16, y + 8, label)
            for node_index, node in enumerate(nodes):
                x = 16 + label_width + node_index * (node_width + gap)
                canvas.setFillColor(PANEL)
                canvas.setStrokeColor(accent)
                canvas.setLineWidth(0.8)
                canvas.roundRect(x, y, node_width, 27, 5, fill=1, stroke=1)
                canvas.setFillColor(colors.white)
                canvas.setFont(FONT_BOLD if node_index in (0, 3) else FONT, 7.2)
                canvas.drawCentredString(x + node_width / 2, y + 10, node)
                if node_index < 3:
                    canvas.setStrokeColor(accent)
                    canvas.line(x + node_width, y + 13.5, x + node_width + gap - 2, y + 13.5)
                    canvas.line(
                        x + node_width + gap - 5,
                        y + 16,
                        x + node_width + gap - 2,
                        y + 13.5,
                    )
                    canvas.line(
                        x + node_width + gap - 5,
                        y + 11,
                        x + node_width + gap - 2,
                        y + 13.5,
                    )


def cover_story() -> list[object]:
    return [
        Spacer(1, 2 * mm),
        Paragraph(
            "MARKETPILOT / ARCHITECTURE",
            ParagraphStyle(
                "CoverKicker", fontName=FONT_MONO, fontSize=9, textColor=MINT, leading=12
            ),
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "Technical Architecture",
            ParagraphStyle(
                "CoverTitle",
                fontName=FONT_BOLD,
                fontSize=34,
                leading=38,
                textColor=colors.white,
            ),
        ),
        Paragraph(
            "A local, reproducible and governed market-data platform",
            ParagraphStyle(
                "CoverSub",
                fontName=FONT,
                fontSize=16,
                leading=21,
                textColor=colors.HexColor("#B9CCDC"),
            ),
        ),
        Spacer(1, 5 * mm),
        ArchitectureOverview(PAGE_WIDTH - 44 * mm),
        Spacer(1, 4 * mm),
        Table(
            [["VERSION", "2.0"], ["VERIFIED", "2026-09-17"], ["STATUS", "Final project baseline"]],
            colWidths=[28 * mm, 70 * mm],
            style=TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), FONT_MONO),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 0), (0, -1), MINT),
                    ("TEXTCOLOR", (1, 0), (1, -1), colors.white),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#294157")),
                ]
            ),
        ),
        PageBreak(),
    ]


def parse_table(lines: list[str]) -> Table:
    rows: list[list[Paragraph]] = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append([Paragraph(inline_markdown(cell), styles["MPSmall"]) for cell in cells])
    count = max(len(row) for row in rows)
    available = PAGE_WIDTH - 38 * mm
    if count == 2:
        widths = [available * 0.28, available * 0.72]
    elif count == 3:
        widths = [available * 0.22, available * 0.32, available * 0.46]
    else:
        widths = [available / count] * count
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PANEL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("GRID", (0, 0), (-1, -1), 0.45, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPER]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def markdown_story(source: str) -> list[object]:
    lines = source.splitlines()
    story: list[object] = []
    index = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            value = " ".join(part.strip() for part in paragraph)
            story.append(Paragraph(inline_markdown(value), styles["MPBody"]))
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            code: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code.append(lines[index])
                index += 1
            value = "<br/>".join(
                html.escape(code_line).replace(" ", "&nbsp;") for code_line in code
            )
            story.append(Paragraph(value, styles["MPCode"]))
            index += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(inline_markdown(stripped[3:]), styles["MPH1"]))
            index += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markdown(stripped[4:]), styles["MPH2"]))
            index += 1
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(parse_table(table_lines))
            story.append(Spacer(1, 3 * mm))
            continue
        if re.match(r"^[-*] ", stripped):
            flush_paragraph()
            items: list[ListItem] = []
            while index < len(lines) and re.match(r"^[-*] ", lines[index].strip()):
                value = re.sub(r"^[-*] ", "", lines[index].strip())
                items.append(
                    ListItem(Paragraph(inline_markdown(value), styles["MPBody"]), leftIndent=10)
                )
                index += 1
            story.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    bulletColor=MINT,
                    leftIndent=17,
                    bulletFontName=FONT_BOLD,
                )
            )
            story.append(Spacer(1, 2 * mm))
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if numbered:
            flush_paragraph()
            items = []
            while index < len(lines):
                match = re.match(r"^(\d+)\.\s+(.*)", lines[index].strip())
                if not match:
                    break
                items.append(
                    ListItem(
                        Paragraph(inline_markdown(match.group(2)), styles["MPBody"]),
                        leftIndent=10,
                    )
                )
                index += 1
            story.append(
                ListFlowable(items, bulletType="1", leftIndent=17, bulletFontName=FONT_BOLD)
            )
            story.append(Spacer(1, 2 * mm))
            continue
        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    return story


def draw_page(canvas, doc) -> None:  # type: ignore[no-untyped-def]
    page_number = canvas.getPageNumber()
    if page_number == 1:
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
        canvas.setFillColor(MINT)
        canvas.rect(0, 0, 7 * mm, PAGE_HEIGHT, fill=1, stroke=0)
        canvas.restoreState()
        return
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_HEIGHT - 14 * mm, PAGE_WIDTH, 14 * mm, fill=1, stroke=0)
    canvas.setFont(FONT_MONO, 7.5)
    canvas.setFillColor(MINT)
    canvas.drawString(18 * mm, PAGE_HEIGHT - 9 * mm, "MARKETPILOT / TECHNICAL ARCHITECTURE")
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_WIDTH - 18 * mm, 10 * mm, f"{page_number - 1:02d}")
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 14 * mm, PAGE_WIDTH - 18 * mm, 14 * mm)
    canvas.restoreState()


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    source = SOURCE.read_text(encoding="utf-8")
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=PAGE,
        leftMargin=19 * mm,
        rightMargin=19 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="MarketPilot Technical Architecture",
        author="MarketPilot",
        subject="Final project architecture",
    )
    story = cover_story() + markdown_story(source)
    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(f"Built {OUTPUT}")


if __name__ == "__main__":
    main()
