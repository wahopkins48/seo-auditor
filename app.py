import os
import asyncio
from io import BytesIO

from flask import Flask, request, render_template, send_file, jsonify
from weasyprint import HTML

# Must match build.sh so Render build/runtime use the same browser location
_root = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH",
    os.path.join(_root, ".playwright-browsers"),
)

from analyzer import audit_website

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


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

    result = asyncio.run(audit_website(url))

    if result.get("status") == "Error":
        return jsonify({
            "status": "Error",
            "message": result.get("message", "Unknown error")
        }), 500

    rendered_html = render_template("report.html", **result)

    pdf_buf = BytesIO()
    HTML(string=rendered_html, base_url=request.url_root).write_pdf(pdf_buf)
    pdf_buf.seek(0)

    return send_file(
        pdf_buf,
        as_attachment=True,
        download_name="seo_report.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
