import os
import random
import glob
import urllib.parse
from dotenv import load_dotenv
import requests

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

PRODUCTS_DIR = os.path.dirname(__file__)
PRICES = [400, 500, 600, 700, 800]


def _extract_title_and_description(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    # Skip the header block (NICHE/PRICE/GENERATED/=== lines) to reach LLM content
    lines_raw = raw.splitlines()
    start = 0
    for i, line in enumerate(lines_raw):
        stripped = line.strip()
        if stripped and (line.startswith('NICHE:') or line.startswith('PRICE:') or
                         line.startswith('GENERATED:') or set(stripped) == {'='}):
            start = i + 1
    content = '\n'.join(lines_raw[start:]).strip()
    lines = content.splitlines()

    # Find title: locate "Product Title:" label or first bold/plain heading line
    title = ''
    for line in lines:
        clean = line.strip().strip('*').strip()
        if not clean:
            continue
        if 'product title' in clean.lower():
            title = clean.split(':', 1)[1].strip().strip('"').strip("'").strip('*').strip()
        elif not clean[0].isdigit():
            # First non-numbered, non-empty line is the title
            title = clean.strip('"').strip("'")
        if title:
            break

    # Find sales description: paragraph after "Sales Description" heading
    description = ''
    in_desc = False
    desc_lines = []
    for line in lines:
        stripped = line.strip()
        if 'sales description' in stripped.lower():
            in_desc = True
            continue
        if in_desc:
            if stripped.startswith('**') and stripped.endswith('**') and len(stripped) > 4:
                # Hit the next section heading — stop
                break
            if stripped:
                desc_lines.append(stripped.strip('*').strip())
            elif desc_lines:
                # Blank line after we have content — paragraph done
                break
    description = ' '.join(desc_lines).strip()

    # Fallback: use first two non-empty, non-heading lines if parsing failed
    if not title or not description:
        candidates = [l.strip().strip('*').strip() for l in lines if l.strip() and not l.strip().startswith('#')]
        if not title and candidates:
            title = candidates[0]
        if not description and len(candidates) > 1:
            description = candidates[1]

    return title, description


def list_on_gumroad(pdf_path, txt_path):
    token = os.getenv('GUMROAD_TOKEN')
    title, description = _extract_title_and_description(txt_path)
    price = random.choice(PRICES)

    print(f'  Title:       {title}')
    print(f'  Description: {description[:80]}...')
    print(f'  Price:       ${price // 100}.{price % 100:02d}')

    # Create product
    create_resp = requests.post(
        'https://api.gumroad.com/v2/products',
        headers={'Authorization': f'Bearer {token}'},
        data={
            'name': title,
            'description': description,
            'price': price,
            'published': 'true',
        },
    )
    create_resp.raise_for_status()
    product = create_resp.json()

    if not product.get('success'):
        raise RuntimeError(f'Gumroad product creation failed: {product}')

    product_id = urllib.parse.quote(product['product']['id'], safe='')
    product_url = product['product']['short_url']

    # Upload PDF (Gumroad v2 API supports file attachment on eligible accounts)
    with open(pdf_path, 'rb') as pdf_file:
        upload_resp = requests.post(
            f'https://api.gumroad.com/v2/products/{product_id}/files',
            headers={'Authorization': f'Bearer {token}'},
            files={'file': (os.path.basename(pdf_path), pdf_file, 'application/pdf')},
        )
    if upload_resp.status_code == 404:
        print(f'  Note: PDF auto-upload not available on this account — upload {os.path.basename(pdf_path)} manually via the Gumroad dashboard.')
    else:
        upload_resp.raise_for_status()
        print(f'  PDF uploaded successfully.')

    print(f'  Product URL: {product_url}')
    return product_url


def find_latest_product():
    pdf_files = glob.glob(os.path.join(PRODUCTS_DIR, '*.pdf'))
    if not pdf_files:
        raise FileNotFoundError('No PDF products found in products/ folder.')

    latest_pdf = max(pdf_files, key=os.path.getmtime)
    latest_txt = latest_pdf.replace('.pdf', '.txt')

    if not os.path.exists(latest_txt):
        raise FileNotFoundError(f'Matching txt file not found for: {latest_pdf}')

    return latest_pdf, latest_txt


if __name__ == '__main__':
    print('Finding latest product...')
    pdf_path, txt_path = find_latest_product()
    print(f'  PDF: {os.path.basename(pdf_path)}')
    print(f'  TXT: {os.path.basename(txt_path)}')

    print('Listing on Gumroad...')
    url = list_on_gumroad(pdf_path, txt_path)
    print(f'Product is now LIVE on Gumroad: {url}')
