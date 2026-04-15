import os
import logging
import asyncio
from io import BytesIO

root = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", os.path.join(root, ".playwright-browsers"))

from flask import Flask, request, render_template, send_file, jsonify
from analyzer import audit_website
from weasyprint import HTML

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/audit")
def do_audit():
    url = (request.args.get("url") or "").strip()

    if not url:
        return jsonify({
            "status": "Error",
            "message": "Missing required query parameter: url"
        }), 400

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        app.logger.info("Starting audit for %s", url)
        app.logger.info("PLAYWRIGHT_BROWSERS_PATH=%s", os.environ.get("PLAYWRIGHT_BROWSERS_PATH"))

        result = asyncio.run(audit_website(url))
        app.logger.info("Audit result status: %s", result.get("status"))

        if result.get("status") == "Error":
            app.logger.error("Audit failed: %s", result.get("message"))
            return jsonify({
                "status": "Error",
                "message": result.get("message", "Unknown audit error")
            }), 500

        rendered_html = render_template("report.html", result=result)

        pdf_buf = BytesIO()
        HTML(string=rendered_html, base_url=request.url_root).write_pdf(pdf_buf)
        pdf_buf.seek(0)

        return send_file(
            pdf_buf,
            as_attachment=True,
            download_name="seo-report.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        app.logger.exception("Unhandled /audit error")
        return jsonify({
            "status": "Error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
