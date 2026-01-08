"""
YOLO 检测器 - 使用 YOLO 模型检测物体
"""

import math


class YoloDetector:
    """YOLO 物体检测器"""

    def __init__(self, model_name='yolov8n.pt', target_class='bottle',
                 conf_threshold=0.5, iou_threshold=0.45):
        """
        初始化 YOLO 检测器

        Args:
            model_name: YOLO 模型名称
            target_class: 目标类别名称
            conf_threshold: 置信度阈值
            iou_threshold: IOU 阈值
        """
        self.model_name = model_name
        self.target_class = target_class
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

        # 尝试加载 YOLO
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_name)
            self.class_names = self.model.names
            self.available = True

            print(f"YOLO 模型加载成功: {model_name}")
            print(f"目标类别: {target_class}")

            if target_class not in self.class_names.values():
                print(f"警告: '{target_class}' 不在支持类别中")
                print(f"支持类别: {', '.join(self.class_names.values())}")

        except ImportError:
            self.model = None
            self.class_names = {}
            self.available = False
            print("错误: ultralytics 未安装")
            print("安装命令: pip install ultralytics")

    def detect(self, frame):
        """
        检测图像中的目标物体

        Args:
            frame: 输入图像 (BGR)

        Returns:
            detections: 检测结果列表 [(x1, y1, x2, y2, conf, class_id), ...]
        """
        if not self.available or self.model is None:
            return []

        # 获取目标类别 ID
        target_id = None
        for class_id, class_name in self.class_names.items():
            if class_name == self.target_class:
                target_id = class_id
                break

        # 只检测目标类别
        if target_id is not None:
            results = self.model(
                frame,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                classes=[target_id],
                verbose=False
            )
        else:
            # 如果目标类别不存在，检测所有
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
        """
        从检测结果中选择最佳目标并计算中心

        Args:
            detections: 检测结果列表
            frame_width, frame_height: 帧尺寸

        Returns:
            center: 目标中心 (x, y)，如果没有找到则返回 None
            detection: 最佳检测结果，如果没有找到则返回 None
            area: 检测框面积
        """
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

            # 计算到中心的距离
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
