"""
YOLO detector wrapper
"""

import math


class YoloDetector:
    """YOLO 物体检测器"""

    def __init__(self, model_name='yolov8n.pt', target_class='bottle',
                 conf_threshold=0.5, iou_threshold=0.45):
        self.model_name = model_name
        self.target_class = target_class
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

        try:
            from ultralytics import YOLO
            self.model = YOLO(model_name)
            self.class_names = self.model.names
            self.available = True
        except ImportError:
            self.model = None
            self.class_names = {}
            self.available = False

    def update_settings(self, target_class=None, conf_threshold=None, iou_threshold=None):
        """Update detector settings"""
        if target_class is not None:
            self.target_class = target_class
        if conf_threshold is not None:
            self.conf_threshold = conf_threshold
        if iou_threshold is not None:
            self.iou_threshold = iou_threshold

    def detect(self, frame):
        if not self.available or self.model is None:
            return []

        target_id = None
        for class_id, class_name in self.class_names.items():
            if class_name == self.target_class:
                target_id = class_id
                break

        if target_id is not None:
            results = self.model(
                frame,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                classes=[target_id],
                verbose=False
            )
        else:
            results = self.model(
                frame,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False
            )

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    detections.append((x1, y1, x2, y2, conf, class_id))

        return detections

    def find_target_center(self, detections, frame_width, frame_height):
        if not detections:
            return None, None, 0

        center_x = frame_width / 2
        center_y = frame_height / 2

        best_detection = None
        min_distance = float('inf')

        for det in detections:
            x1, y1, x2, y2, conf, class_id = det
            det_center_x = (x1 + x2) / 2
            det_center_y = (y1 + y2) / 2

            distance = math.sqrt((det_center_x - center_x) ** 2 + (det_center_y - center_y) ** 2)

            if distance < min_distance:
                min_distance = distance
                best_detection = det

        if best_detection is not None:
            x1, y1, x2, y2, conf, class_id = best_detection
            center = ((x1 + x2) / 2, (y1 + y2) / 2)
            area = (x2 - x1) * (y2 - y1)
            return center, best_detection, area

        return None, None, 0

    def get_available_classes(self):
        """Get list of available YOLO classes"""
        return list(self.class_names.values()) if self.available else []
