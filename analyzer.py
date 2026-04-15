import json
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


def _safe_json_loads(raw):
    try:
        return json.loads(raw)
    except Exception:
        return None


def _collect_schema_types(node, types_out):
    if isinstance(node, dict):
        node_type = node.get('@type')
        if isinstance(node_type, list):
            for t in node_type:
                if t:
                    types_out.append(str(t))
        elif node_type:
            types_out.append(str(node_type))

        graph = node.get('@graph')
        if isinstance(graph, list):
            for item in graph:
                _collect_schema_types(item, types_out)

        for value in node.values():
            if isinstance(value, (dict, list)):
                _collect_schema_types(value, types_out)

    elif isinstance(node, list):
        for item in node:
            _collect_schema_types(item, types_out)


def _extract_schema_data(soup):
    schema_types = []
    schema_errors = []
    jsonld_blocks = soup.find_all('script', attrs={'type': 'application/ld+json'})

    for i, block in enumerate(jsonld_blocks, start=1):
        raw = (block.string or block.get_text() or '').strip()
        if not raw:
            schema_errors.append(f'Empty JSON-LD block #{i}')
            continue

        parsed = _safe_json_loads(raw)
        if parsed is None:
            schema_errors.append(f'Invalid JSON-LD block #{i}')
            continue

        _collect_schema_types(parsed, schema_types)

    microdata_items = soup.select('[itemscope][itemtype]')
    rdfa_items = soup.select('[typeof]')

    for item in microdata_items:
        itemtype = item.get('itemtype', '')
        if itemtype:
            schema_types.append(itemtype.split('/')[-1])

    for item in rdfa_items:
        typeof = item.get('typeof', '')
        if typeof:
            schema_types.extend([t.strip() for t in typeof.split() if t.strip()])

    schema_types = sorted(set(filter(None, schema_types)))
    schema_found = len(schema_types) > 0

    return {
        'schema_found': schema_found,
        'schema_types': schema_types,
        'schema_jsonld_blocks': len(jsonld_blocks),
        'schema_microdata_items': len(microdata_items),
        'schema_rdfa_items': len(rdfa_items),
        'schema_errors': schema_errors,
    }


async def audit_website(url):
    async with async_playwright() as p:
        browser = None
        context = None
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
                viewport={'width': 375, 'height': 812},
                ignore_https_errors=True,
            )

            page = await context.new_page()

            start_time = time.time()
            response = await page.goto(url, timeout=60000, wait_until='networkidle')
            load_time = round(time.time() - start_time, 2)

            initial_html = ''
            if response:
                try:
                    initial_html = await response.text()
                except Exception:
                    initial_html = ''

            rendered_content = await page.content()
            js_reliance = 'High' if initial_html and len(rendered_content) > len(initial_html) * 1.5 else 'Low'

            soup = BeautifulSoup(rendered_content, 'html.parser')

            title_tag = soup.title.string.strip() if soup.title and soup.title.string else 'Missing Title'
            h1_tag = soup.find('h1')
            h1 = h1_tag.get_text(strip=True) if h1_tag else 'Missing H1'

            meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
            description = (
                meta_desc_tag.get('content', '').strip()
                if meta_desc_tag and meta_desc_tag.get('content')
                else 'Missing Description'
            )

            images = soup.find_all('img')
            missing_alt = [img for img in images if not img.get('alt') or not img.get('alt').strip()]

            schema_data = _extract_schema_data(soup)

            headers = response.headers if response else {}
            lower_headers = {k.lower(): v for k, v in headers.items()}
            hsts = 'Active' if 'strict-transport-security' in lower_headers else 'Missing'
            csp = 'Active' if 'content-security-policy' in lower_headers else 'Missing'

            word_count = len(soup.get_text(' ', strip=True).split())

            recommendations = []

            if not schema_data['schema_found']:
                recommendations.append(
                    'Add JSON-LD structured data that matches the page type, such as Organization, LocalBusiness, Article, Product, FAQPage, or BreadcrumbList.'
                )
            else:
                recommendations.append(
                    'Structured data was found. Make sure the markup matches the visible content and includes the most relevant entity type.'
                )

            if schema_data['schema_errors']:
                recommendations.append(
                    'Fix invalid JSON-LD blocks so search engines can parse your structured data cleanly.'
                )

            if schema_data['schema_found'] and schema_data['schema_jsonld_blocks'] == 0:
                recommendations.append(
                    'Consider using JSON-LD for schema markup because it is easier to maintain and less error-prone.'
                )

            if description == 'Missing Description':
                recommendations.append('Add a meta description.')
            if h1 == 'Missing H1':
                recommendations.append('Add a clear H1 heading.')
            if len(missing_alt) > 0:
                recommendations.append('Add descriptive alt text to images missing it.')
            if csp == 'Missing':
                recommendations.append('Add a Content-Security-Policy header for stronger security.')
            if hsts == 'Missing':
                recommendations.append('Enable HSTS to improve HTTPS enforcement.')
            if word_count < 500:
                recommendations.append('Expand copy to 500+ words to improve semantic relevance.')

            score = 100
            if load_time > 2.5:
                score -= 20
            if word_count < 500:
                score -= 15
            if hsts == 'Missing':
                score -= 10
            if csp == 'Missing':
                score -= 5
            if not schema_data['schema_found']:
                score -= 15
            if schema_data['schema_errors']:
                score -= 5
            if description == 'Missing Description':
                score -= 10
            if h1 == 'Missing H1':
                score -= 10
            if len(missing_alt) > 0:
                score -= min(len(missing_alt) * 2, 10)

            report = {
                'url': url,
                'score': max(score, 0),
                'load_time': load_time,
                'js_reliance': js_reliance,
                'word_count': word_count,
                'hsts': hsts,
                'csp': csp,
                'title': title_tag,
                'h1': h1,
                'description': description,
                'img_count': len(images),
                'img_issues': len(missing_alt),
                'schema_found': schema_data['schema_found'],
                'schema_types': ', '.join(schema_data['schema_types']) if schema_data['schema_types'] else 'None detected',
                'schema_jsonld_blocks': schema_data['schema_jsonld_blocks'],
                'schema_microdata_items': schema_data['schema_microdata_items'],
                'schema_rdfa_items': schema_data['schema_rdfa_items'],
                'schema_errors': schema_data['schema_errors'],
                'recommendations': recommendations,
                'status': 'Success',
            }
        except Exception as e:
            report = {'status': 'Error', 'message': str(e)}
        finally:
            if context is not None:
                await context.close()
            if browser is not None:
                await browser.close()

        return report
