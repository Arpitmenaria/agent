import os
import random
from datetime import datetime
from dotenv import load_dotenv
import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

NICHES = [
    ('AI prompts for Indian small business owners', 5),
    ('ChatGPT prompts for Etsy sellers', 7),
    ('AI prompts for freelancers', 6),
    ('Social media caption prompts for restaurants', 4),
    ('ChatGPT prompts for YouTube creators', 8),
]

PRODUCTS_DIR = os.path.dirname(__file__)


def generate_product():
    niche, price = random.choice(NICHES)
    groq_key = os.getenv('GROQ_API_KEY')

    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {groq_key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': 'llama-3.1-8b-instant',
            'max_tokens': 2048,
            'messages': [
                {
                    'role': 'user',
                    'content': (
                        f'Create a digital product for {niche}. '
                        'Write 25 powerful specific ready-to-use AI prompts for this audience. '
                        'Include a catchy product title, a 2 sentence sales description, '
                        'and then number the 25 prompts. '
                        'Make them genuinely useful and specific.'
                    ),
                }
            ],
        },
    )
    response.raise_for_status()
    content = response.json()['choices'][0]['message']['content']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = niche.replace(' ', '_').replace('/', '_')
    txt_filename = f'{safe_name}_{timestamp}.txt'
    txt_path = os.path.join(PRODUCTS_DIR, txt_filename)

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f'NICHE: {niche}\n')
        f.write(f'PRICE: ${price}\n')
        f.write(f'GENERATED: {datetime.now().isoformat()}\n')
        f.write('=' * 60 + '\n\n')
        f.write(content)

    print(f'  Text saved: {txt_filename}')
    return txt_path, price


def create_pdf(txt_file_path):
    with open(txt_file_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    lines = raw.splitlines()
    pdf_path = txt_file_path.replace('.txt', '.pdf')
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ProductTitle',
        parent=styles['Title'],
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#888888',
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    prompt_style = ParagraphStyle(
        'Prompt',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        leftIndent=14,
        spaceAfter=10,
    )

    story = []
    title_found = False
    meta_lines = []

    for line in lines:
        if line.startswith('NICHE:') or line.startswith('PRICE:') or line.startswith('GENERATED:'):
            meta_lines.append(line.strip())
        elif line.startswith('='):
            continue
        elif line.strip() == '':
            story.append(Spacer(1, 6))
        else:
            if not title_found:
                story.append(Paragraph(line.strip(), title_style))
                title_found = True
            elif line.strip()[0].isdigit() and '.' in line[:4]:
                story.append(Paragraph(line.strip(), prompt_style))
            else:
                story.append(Paragraph(line.strip(), body_style))

    if meta_lines:
        story.insert(1, Paragraph('  |  '.join(meta_lines), meta_style))

    doc.build(story)
    print(f'  PDF saved:  {os.path.basename(pdf_path)}')
    return pdf_path


if __name__ == '__main__':
    print('Generating product...')
    txt_path, price = generate_product()
    print('Converting to PDF...')
    create_pdf(txt_path)
    print('Product created successfully')
