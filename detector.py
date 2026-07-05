import os
import cv2
import numpy as np
from ultralytics import YOLO

TOY_CLASSES = {
    "teddy bear", "bear", "sports ball", "frisbee", "kite",
    "baseball bat", "baseball glove", "skateboard", "tennis racket",
    "skis", "snowboard", "surfboard",
}

CONF_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5

WEIGHTS = {
    "detect":  "yolov8n.pt",
    "segment": "yolov8n-seg.pt",
}

COLOR_BOX = (0, 200, 0)
COLOR_TEXT = (255, 255, 255)
COLOR_COUNT = (0, 0, 255)

_models = {}


def load_model(mode: str = "detect") -> YOLO:
    weights = WEIGHTS.get(mode, WEIGHTS["detect"])
    if weights not in _models:
        _models[weights] = YOLO(weights)
    return _models[weights]


def _annotate_frame(model: YOLO, image, mode: str):
    results = model(image, conf=CONF_THRESHOLD, iou=IOU_THRESHOLD, verbose=False)
    result = results[0]
    names = model.names


    toy_items = []
    for i, box in enumerate(result.boxes):
        cls_name = names[int(box.cls[0])]
        if cls_name not in TOY_CLASSES:
            continue
        confidence = float(box.conf[0])
        coords = tuple(map(int, box.xyxy[0]))
        toy_items.append((i, cls_name, confidence, coords))

    has_masks = (mode == "segment") and (result.masks is not None)


    if has_masks:
        overlay = image.copy()
        for i, _, _, _ in toy_items:
            if i < len(result.masks.xy):
                pts = np.int32([result.masks.xy[i]])
                cv2.fillPoly(overlay, pts, COLOR_BOX)
        image = cv2.addWeighted(overlay, 0.4, image, 0.6, 0)

    count = 0
    by_class = {}
    detections = []
    for i, cls_name, confidence, (x1, y1, x2, y2) in toy_items:
        if has_masks and i < len(result.masks.xy):
            pts = np.int32([result.masks.xy[i]])
            cv2.polylines(image, pts, True, COLOR_BOX, 2)
        else:
            cv2.rectangle(image, (x1, y1), (x2, y2), COLOR_BOX, 2)

        label = f"{cls_name} {confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(image, (x1, y1 - th - 6), (x1 + tw, y1), COLOR_BOX, -1)
        cv2.putText(image, label, (x1, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1)

        count += 1
        by_class[cls_name] = by_class.get(cls_name, 0) + 1
        detections.append({"class": cls_name, "confidence": round(confidence, 3)})

    cv2.putText(image, f"Toys: {count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, COLOR_COUNT, 2)

    return image, count, by_class, detections


def detect_toys(image_path: str, result_path: str, mode: str = "detect") -> dict:
    if mode not in WEIGHTS:
        mode = "detect"
    model = load_model(mode)

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Не удалось прочитать изображение: {image_path}")

    annotated, count, by_class, detections = _annotate_frame(model, image, mode)

    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    cv2.imwrite(result_path, annotated)

    return {"mode": mode, "media_type": "image", "count": count,
            "by_class": by_class, "detections": detections}


def process_video(video_path: str, result_path: str, mode: str = "detect") -> dict:
    if mode not in WEIGHTS:
        mode = "detect"
    model = load_model(mode)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Не удалось открыть видео: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    os.makedirs(os.path.dirname(result_path), exist_ok=True)

    writer = None
    for codec in ("avc1", "mp4v"):
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(result_path, fourcc, fps, (width, height))
        if writer.isOpened():
            break
        writer.release()
    if writer is None or not writer.isOpened():
        cap.release()
        raise RuntimeError("Не удалось создать выходной видеофайл")

    frames = 0
    peak_count = 0
    peak_by_class = {}

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames += 1
        annotated, count, by_class, _ = _annotate_frame(model, frame, mode)
        if count > peak_count:
            peak_count = count
            peak_by_class = by_class
        writer.write(annotated)

    cap.release()
    writer.release()

    return {"mode": mode, "media_type": "video", "frames": frames,
            "count": peak_count, "by_class": peak_by_class, "detections": []}
