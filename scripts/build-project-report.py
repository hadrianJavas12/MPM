#!/usr/bin/env python3
"""Typeset the project Markdown report as an evidence-linked professional PDF."""
import argparse
from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Preformatted, KeepTogether

NAVY, TEAL = colors.HexColor('#102b46'), colors.HexColor('#087e8b')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--subtitle', default='CL-MPM | Windows native | 15 Oktober 2026')
    parser.add_argument('--repository-base-url', default='https://github.com/hadrianJavas12/MPM/blob/codex/triaxial-clay-calibration/')
    args = parser.parse_args()
    fonts = Path('C:/Windows/Fonts')
    for name, filename in [('Arial', 'arial.ttf'), ('Arial-Bold', 'arialbd.ttf'),
                           ('Arial-Italic', 'ariali.ttf'), ('Arial-BoldItalic', 'arialbi.ttf'), ('Consolas', 'consola.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(fonts/filename)))
    pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold', italic='Arial-Italic', boldItalic='Arial-BoldItalic')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('BodyReport', fontName='Arial', fontSize=9.3, leading=14, textColor=NAVY, spaceAfter=7, allowWidows=0, allowOrphans=0))
    styles.add(ParagraphStyle('H1Report', parent=styles['BodyReport'], fontName='Arial-Bold', fontSize=15, leading=19, spaceBefore=16, spaceAfter=8, keepWithNext=True))
    styles.add(ParagraphStyle('H2Report', parent=styles['H1Report'], fontSize=11.5, leading=16, spaceBefore=12))
    styles.add(ParagraphStyle('H3Report', parent=styles['H2Report'], fontSize=10, leading=14))
    styles.add(ParagraphStyle('CellReport', parent=styles['BodyReport'], fontSize=8.1, leading=11, spaceAfter=0))
    styles.add(ParagraphStyle('SmallReport', parent=styles['BodyReport'], fontSize=8, leading=11, textColor=colors.HexColor('#61738a')))
    styles.add(ParagraphStyle('BulletReport', parent=styles['BodyReport'], leftIndent=11, firstLineIndent=-8))
    styles.add(ParagraphStyle('CodeReport', fontName='Consolas', fontSize=7, leading=10, textColor=NAVY, backColor=colors.HexColor('#edf2f7'), borderPadding=8, spaceAfter=10))
    def link_markup(match):
        label, href = match.group(1), match.group(2)
        if not href.startswith('http'):
            try:
                relative = (args.source.resolve().parent / href).resolve().relative_to(Path.cwd().resolve())
                href = args.repository_base_url.rstrip('/') + '/' + relative.as_posix()
            except ValueError:
                return label
        return '<link href="'+href+'" color="#087e8b">'+label+'</link>'
    def inline(raw):
        text = escape(raw.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-'))
        text = re.sub(r'`([^`]+)`', lambda m:'<font name="Consolas" size="8">'+m.group(1)+'</font>', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_markup, text)
        return text
    width = A4[0]-36*mm
    story = [Paragraph('ENGINEERING REPORT', ParagraphStyle('Eyebrow', fontName='Arial-Bold', fontSize=9, textColor=TEAL, spaceAfter=9)),
             Paragraph(escape(args.title), ParagraphStyle('Cover', fontName='Arial-Bold', fontSize=24, leading=30, textColor=NAVY, spaceAfter=12)),
             Paragraph(escape(args.subtitle), styles['SmallReport']), Spacer(1, 8*mm)]
    lines = args.source.read_text(encoding='utf-8-sig').splitlines()
    paragraph, table_rows, code = [], [], []
    in_code = False
    def flush_paragraph():
        if paragraph:
            story.append(KeepTogether([Paragraph(inline(' '.join(paragraph)), styles['BodyReport'])]))
            paragraph.clear()
    def flush_table():
        if not table_rows:
            return
        rows = [[Paragraph(inline(cell), styles['CellReport']) for cell in row] for row in table_rows]
        count = max(map(len, rows))
        weights = [max(12, min(52, max(len(re.sub(r'\[[^]]+\]\([^)]+\)', 'source', r[i])) if i<len(r) else 0 for r in table_rows))) for i in range(count)]
        cols = [width*w/sum(weights) for w in weights]
        table = Table(rows, colWidths=cols, repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dceaf1')),
                                  ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7fa')]),
                                  ('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.4,colors.HexColor('#d7e0e8')),
                                  ('LINEBELOW',(0,0),(-1,0),.7,TEAL),('LEFTPADDING',(0,0),(-1,-1),7),
                                  ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        story.extend([KeepTogether([table]) if len(rows) <= 10 else table, Spacer(1, 4*mm)])
        table_rows.clear()
    for number, line in enumerate(lines):
        if line.startswith('```'):
            flush_paragraph(); flush_table()
            if in_code:
                wrapped=[]
                for original in code:
                    while len(original)>100:
                        split=original.rfind(' ',0,100)
                        split=split if split>30 else 100
                        wrapped.append(original[:split]);original='    '+original[split:].lstrip()
                    wrapped.append(original)
                story.append(Preformatted('\n'.join(wrapped), styles['CodeReport']))
                code.clear()
            in_code=not in_code
            continue
        if in_code:
            code.append(line);continue
        if line.startswith('|'):
            flush_paragraph()
            row=[c.strip() for c in line.strip().strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?',c) for c in row):
                continue
            table_rows.append(row);continue
        flush_table()
        image=re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)', line.strip())
        if image:
            flush_paragraph()
            path=(args.source.parent/image.group(2)).resolve()
            if not path.is_file():
                raise FileNotFoundError(path)
            element=Image(str(path))
            ratio=min(width/element.imageWidth, 100*mm/element.imageHeight)
            element.drawWidth=element.imageWidth*ratio; element.drawHeight=element.imageHeight*ratio
            story.append(KeepTogether([element, Spacer(1,2*mm), Paragraph(escape(image.group(1)),styles['SmallReport'])]))
        elif line.startswith('#'):
            flush_paragraph()
            level=len(line)-len(line.lstrip('#'))
            if level==1 and number<3:
                continue
            story.append(Paragraph(inline(line.lstrip('#').strip()),styles['H1Report' if level<=2 else 'H2Report' if level==3 else 'H3Report']))
        elif not line.strip():
            flush_paragraph()
        elif re.match(r'^\s*[-*] ',line) or re.match(r'^\d+\. ',line):
            flush_paragraph()
            story.append(Paragraph(inline(line.strip()), styles['BulletReport']))
        elif line.startswith('> '):
            flush_paragraph(); story.append(Paragraph(inline(line[2:]), styles['SmallReport']))
        elif line.strip()=='---':
            flush_paragraph()
        else:
            paragraph.append(line.strip())
    flush_paragraph();flush_table()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def page(canvas,doc):
        canvas.setStrokeColor(TEAL);canvas.setLineWidth(2)
        canvas.line(18*mm,A4[1]-15*mm,A4[0]-18*mm,A4[1]-15*mm)
        canvas.setFont('Arial',7);canvas.setFillColor(colors.HexColor('#61738a'))
        canvas.drawString(18*mm,12*mm,'CL-MPM | Audit trail and reproducible evidence | 15 October 2026')
        canvas.drawRightString(A4[0]-18*mm,12*mm,str(doc.page))
    doc=SimpleDocTemplate(str(args.output),pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=23*mm,bottomMargin=22*mm,
                          title=args.title,author='MPM Project',subject='Native Windows MPM engineering documentation')
    # Keep each heading with its first real block, including wrapped tables.
    # Explicit grouping also avoids a heading stranded by nested KeepTogether.
    grouped=[]
    index=0
    while index<len(story):
        item=story[index]
        if isinstance(item,Paragraph) and item.style.name in ('H1Report','H2Report','H3Report') and index+1<len(story):
            item.keepWithNext=0
            following=story[index+1]
            content=following._content if isinstance(following,KeepTogether) else [following]
            grouped.append(KeepTogether([item]+list(content)))
            index+=2
        else:
            grouped.append(item)
            index+=1
    doc.build(grouped,onFirstPage=page,onLaterPages=page)
    print(args.output.resolve())

if __name__=='__main__':
    main()
