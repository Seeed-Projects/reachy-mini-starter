"""
Tracking manager - Manages the tracking state and execution
"""

import time
import threading
import cv2
import numpy as np
import sys
import os
import math

# Add parent directory to path to import from object_tracking_yolo
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
object_tracking_dir = os.path.join(parent_dir, 'object_tracking_yolo')
if object_tracking_dir not in sys.path:
    sys.path.insert(0, object_tracking_dir)

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
from .tracker_core import HeadPitchController, HeadYawController, PositionFilter
from .yolo_wrapper import YoloDetector


class TrackingManager:
    """Manages the tracking process with thread-safe state"""

    def __init__(self, backend='default', resolution='1280x960'):
        # Initialization state
        self.is_initialized = False
        self.init_error = None

        # Initialize Reachy Mini
        self.backend = backend
        self.mini = ReachyMini(media_backend=backend)

        # Set camera resolution
        try:
            width, height = map(int, resolution.split('x'))
            self.mini.media.camera.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.mini.media.camera.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.resolution = (width, height)
            print(f"Camera resolution set to: {width}x{height}")
        except Exception as e:
            print(f"Warning: Could not set resolution: {e}")
            self.resolution = (1280, 960)

        # YOLO detector
        self.detector = YoloDetector(
            model_name='yolov8n.pt',
            target_class='bottle',
            conf_threshold=0.3,
            iou_threshold=0.45
        )

        # Controllers
        self.pitch_controller = HeadPitchController(
            pid_p=0.5, pid_i=0.0, pid_d=0.0
        )
        self.yaw_controller = HeadYawController(
            pid_p=0.5, pid_i=0.0, pid_d=0.0
        )

        # Filter
        self.filter = PositionFilter(window_size=5, jump_threshold=30)

        # Tracking state
        self.is_running = False
        self.is_tracking = False
        self.last_detection_time = 0
        self.detection_timeout = 1.0

        # Threading
        self.lock = threading.Lock()
        self.thread = None

        # Latest frame for streaming
        self.latest_frame = None
        self.latest_info = {}

        # Timing
        self.last_time = time.time()

        # Mark as initialized
        self.is_initialized = True
        print("TrackingManager initialized successfully")

    def start(self):
        """Start tracking in background thread"""
        with self.lock:
            if self.is_running:
                return False
            self.is_running = True

        self.thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        """Stop tracking"""
        with self.lock:
            self.is_running = False

        if self.thread:
            self.thread.join(timeout=2.0)

    def _tracking_loop(self):
        """Main tracking loop running in background thread"""
        print("Tracking loop started")
        while True:
            with self.lock:
                if not self.is_running:
                    print("Tracking loop stopping")
                    break

            # Get frame from camera using ReachyMini SDK
            frame = self.mini.media.get_frame()

            if frame is None:
                time.sleep(0.01)
                continue

            current_time = time.time()
            dt = current_time - self.last_time
            self.last_time = current_time

            height, width = frame.shape[:2]

            # Detect objects
            detections = self.detector.detect(frame)

            if detections:
                print(f"Detected {len(detections)} objects")
                self.last_detection_time = current_time
                self.is_tracking = True

                # Find best target
                center, detection, area = self.detector.find_target_center(
                    detections, width, height
                )

                if center is not None:
                    target_x, target_y = center
                    print(f"Target center: ({target_x:.1f}, {target_y:.1f})")

                    # Apply filter
                    filtered_x, filtered_y = self.filter.filter(target_x, target_y)

                    # Compute control
                    new_pitch = self.pitch_controller.compute(filtered_y, height, dt)
                    self.pitch_controller.update(new_pitch)

                    new_yaw = self.yaw_controller.compute(filtered_x, width, dt)
                    self.yaw_controller.update(new_yaw)

                    print(f"Control - Pitch: {new_pitch:.3f}, Yaw: {new_yaw:.3f}")

                    # Send control
                    self._send_control(new_pitch, new_yaw)

                    # Update info with complete detection data for frontend
                    self.latest_info = {
                        'is_tracking': True,
                        'target_center': center,
                        'filtered_center': (filtered_x, filtered_y),
                        'pitch': float(self.pitch_controller.current_pitch),
                        'yaw': float(self.yaw_controller.current_yaw),
                        'target_class': self.detector.target_class,
                        'detection_count': len(detections),
                        'detection_box': [float(detection[0]), float(detection[1]), float(detection[2]), float(detection[3])],
                        'confidence': float(detection[4])
                    }
                else:
                    self.latest_info = {'is_tracking': False}
            else:
                # Check timeout
                if current_time - self.last_detection_time > self.detection_timeout:
                    self.is_tracking = False
                    self.pitch_controller.reset()
                    self.yaw_controller.reset()
                    self.filter.reset()

                self.latest_info = {'is_tracking': False}

            # Store latest frame
            self.latest_frame = frame

    def _send_control(self, head_pitch, head_yaw):
        """Send control to robot"""
        try:
            # 将弧度转换为度（create_head_pose 的 degrees=True 期望输入是度）
            head_pose = create_head_pose(
                x=0, y=0, z=0,
                roll=0,
                pitch=float(math.degrees(head_pitch)),
                yaw=float(math.degrees(head_yaw)),
                degrees=True,
                mm=True
            )
            self.mini.set_target(
                head=head_pose,
                antennas=None,
                body_yaw=None
            )
        except Exception as e:
            print(f"Error sending control: {e}")

    def get_frame_jpeg(self):
        """Get current frame as JPEG bytes (always fresh, raw video)"""
        frame = self.mini.media.get_frame()
        if frame is not None:
            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes()
        else:
            # Return blank frame if camera not ready
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank, "Waiting for camera...", (140, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            ret, jpeg = cv2.imencode('.jpg', blank)
            return jpeg.tobytes()

    def get_info(self):
        """Get current tracking info"""
        with self.lock:
            info = self.latest_info.copy()
            info['is_running'] = self.is_running

            # Convert numpy types to Python native types for JSON serialization
            if 'target_center' in info and info['target_center']:
                info['target_center'] = [float(x) for x in info['target_center']]
            if 'filtered_center' in info and info['filtered_center']:
                info['filtered_center'] = [float(x) for x in info['filtered_center']]
            if 'pitch' in info:
                info['pitch'] = float(info['pitch'])
            if 'yaw' in info:
                info['yaw'] = float(info['yaw'])
            if 'detection_box' in info:
                info['detection_box'] = [float(x) for x in info['detection_box']]
            if 'confidence' in info:
                info['confidence'] = float(info['confidence'])

            return info

    def update_pitch_params(self, p=None, i=None, d=None, gain=None):
        """Update pitch controller parameters"""
        with self.lock:
            if p is not None:
                self.pitch_controller.pid_p = p
            if i is not None:
                self.pitch_controller.pid_i = i
            if d is not None:
                self.pitch_controller.pid_d = d
            if gain is not None:
                self.pitch_controller.gain = gain

    def update_yaw_params(self, p=None, i=None, d=None, gain=None):
        """Update yaw controller parameters"""
        with self.lock:
            if p is not None:
                self.yaw_controller.pid_p = p
            if i is not None:
                self.yaw_controller.pid_i = i
            if d is not None:
                self.yaw_controller.pid_d = d
            if gain is not None:
                self.yaw_controller.gain = gain

    def update_detector_settings(self, target_class=None, conf_threshold=None):
        """Update detector settings"""
        with self.lock:
            self.detector.update_settings(
                target_class=target_class,
                conf_threshold=conf_threshold
            )

    def update_filter_settings(self, window_size=None, jump_threshold=None):
        """Update filter settings"""
        with self.lock:
            if window_size is not None:
                self.filter = PositionFilter(
                    window_size=window_size,
                    jump_threshold=self.filter.jump_threshold
                )
            if jump_threshold is not None:
                self.filter.jump_threshold = jump_threshold

    def reset_tracking(self):
        """Reset tracking state"""
        with self.lock:
            self.pitch_controller.reset()
            self.yaw_controller.reset()
            self.filter.reset()

    def get_available_classes(self):
        """Get available YOLO classes"""
        return self.detector.get_available_classes()

    def get_params(self):
        """Get current parameters"""
        with self.lock:
            return {
                'pitch': {
                    'p': self.pitch_controller.pid_p,
                    'i': self.pitch_controller.pid_i,
                    'd': self.pitch_controller.pid_d,
                    'gain': self.pitch_controller.gain
                },
                'yaw': {
                    'p': self.yaw_controller.pid_p,
                    'i': self.yaw_controller.pid_i,
                    'd': self.yaw_controller.pid_d,
                    'gain': self.yaw_controller.gain
                },
                'detector': {
                    'target_class': self.detector.target_class,
                    'conf_threshold': self.detector.conf_threshold
                },
                'filter': {
                    'window_size': self.filter.window_size,
                    'jump_threshold': self.filter.jump_threshold
                }
            }

    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        # ReachyMini cleanup is handled automatically
