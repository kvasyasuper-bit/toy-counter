import os
import uuid
from flask import Flask, request, jsonify, render_template, send_file

from detector import detect_toys, process_video
from database import init_db, save_request, get_history
from report import export_excel, export_pdf

UPLOAD_DIR = "uploads"
RESULT_DIR = "static/results"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
ALLOWED_EXT = IMAGE_EXT | VIDEO_EXT

app = Flask(__name__)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
init_db()


def allowed_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXT


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    if "image" not in request.files:
        return jsonify(error="Файл не был передан"), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify(error="Файл не выбран"), 400
    if not allowed_file(file.filename):
        return jsonify(error="Недопустимый формат файла"), 400


    ext = os.path.splitext(file.filename)[1].lower()
    uid = uuid.uuid4().hex
    src_path = os.path.join(UPLOAD_DIR, uid + ext)
    file.save(src_path)


    mode = request.form.get("mode", "detect")

    is_video = ext in VIDEO_EXT

    try:
        if is_video:
            result_name = uid + "_result.mp4"
            result_path = os.path.join(RESULT_DIR, result_name)
            stats = process_video(src_path, result_path, mode=mode)
        else:
            result_name = uid + "_result.jpg"
            result_path = os.path.join(RESULT_DIR, result_name)
            stats = detect_toys(src_path, result_path, mode=mode)
    except Exception as e:
        return jsonify(error=f"Ошибка обработки: {e}"), 500


    save_request(file.filename, stats)

    return jsonify(
        mode=stats["mode"],
        media_type=stats["media_type"],
        count=stats["count"],
        by_class=stats["by_class"],
        detections=stats.get("detections", []),
        frames=stats.get("frames"),
        result_url="/static/results/" + result_name,
    )


@app.route("/history")
def history():
    """JSON"""
    return jsonify(history=get_history())


@app.route("/report/excel")
def report_excel():
    """Excel"""
    path = export_excel()
    return send_file(path, as_attachment=True, download_name="report.xlsx")


@app.route("/report/pdf")
def report_pdf():
    """PDF"""
    path = export_pdf()
    return send_file(path, as_attachment=True, download_name="report.pdf")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
