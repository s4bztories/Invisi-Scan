from flask import Flask, render_template, jsonify, send_from_directory
import os, json

app = Flask(__name__, static_folder="static", template_folder="templates")

DEFAULT_REPORT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "report.json")
VISUAL_REPORT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "report_visual.json")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/report")
def api_report():
    report_path = VISUAL_REPORT if os.path.exists(VISUAL_REPORT) else DEFAULT_REPORT
    if not os.path.exists(report_path):
        return jsonify({"ok": False, "error": "No report found", "path": report_path}), 404
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"ok": True, "report": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/uploads/<path:filename>")
def uploads(filename):
    base = "/mnt/data"
    full = os.path.join(base, filename)
    if os.path.exists(full):
        return send_from_directory(base, filename)
    return ("Not found", 404)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
