from flask import Flask, request, render_template, send_file
import asyncio
from analyzer import audit_website
from weasyprint import HTML

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html') # We will create a pretty home page next

@app.route('/audit')
def do_audit():
    url = request.args.get('url')
    result = asyncio.run(audit_website(url))
    
    if result.get("status") == "Error":
        return f"<h1>Audit Failed</h1><p>{result.get('message')}</p>"

    rendered_html = render_template('report.html', **result)
    
    pdf_path = "seo_report.pdf"
    HTML(string=rendered_html).write_pdf(pdf_path)
    
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)