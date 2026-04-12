from flask import Flask, request, render_template, send_file
import asyncio
import os
import tempfile
from analyzer import audit_website
from weasyprint import HTML

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/audit')
def do_audit():
    url = (request.args.get('url') or '').strip()
    if not url:
        return {"status": "Error", "message": "Missing required query parameter: url"}, 400

    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    result = asyncio.run(audit_website(url))

    if result.get('status') == 'Error':
        return {"status": "Error", "message": result.get('message', 'Unknown error')}, 500

    rendered_html = render_template('report.html', **result)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf_path = tmp.name

    try:
        HTML(string=rendered_html, base_url=request.url_root).write_pdf(pdf_path)
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name='seo_report.pdf',
            mimetype='application/pdf'
        )
    finally:
        try:
            os.remove(pdf_path)
        except OSError:
            pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
