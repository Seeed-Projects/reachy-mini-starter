"""优化版本：降低捕获分辨率以提升显示流畅度

当您点击图像时，Reachy Mini 会看向您点击的点。
使用 OpenCV 捕获视频并显示，通过降低捕获分辨率优化性能。

注意：执行此脚本前必须先运行守护进程。
"""

import argparse

import cv2

from reachy_mini import ReachyMini


def click(event, x, y, flags, param):
    """处理鼠标点击事件以获取点击坐标。"""
    if event == cv2.EVENT_LBUTTONDOWN:
        param["just_clicked"] = True
        param["x"] = x
        param["y"] = y


def main(backend: str, width: int, height: int, window_scale: float = 0.5) -> None:
    """显示 Reachy Mini 的摄像头画面并使其看向点击的点。

    Args:
        backend: 媒体后端类型 (default, gstreamer, webrtc)
        width: 捕获分辨率宽度
        height: 捕获分辨率高度
        window_scale: 窗口缩放比例 (默认 0.5，即原大小的 50%)
    """
    state = {"x": 0, "y": 0, "just_clicked": False}

    cv2.namedWindow("Reachy Mini Camera (Optimized)", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Reachy Mini Camera (Optimized)",
                     int(width * window_scale),
                     int(height * window_scale))
    cv2.setMouseCallback("Reachy Mini Camera (Optimized)", click, param=state)

    print(f"优化模式：捕获分辨率设置为 {width}x{height}")
    print("点击图像使 ReachyMini 看向该点。")
    print("按 'q' 退出摄像头画面。")

    with ReachyMini(media_backend=backend) as reachy_mini:
        # 设置捕获分辨率以优化性能
        reachy_mini.media.camera.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        reachy_mini.media.camera.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # 验证分辨率设置是否成功
        actual_width = reachy_mini.media.camera.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = reachy_mini.media.camera.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"实际捕获分辨率: {int(actual_width)}x{int(actual_height)}")

        try:
            while True:
                frame = reachy_mini.media.get_frame()

                if frame is None:
                    print("Failed to grab frame.")
                    continue

                cv2.imshow("Reachy Mini Camera (Optimized)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("Exiting...")
                    break

                if state["just_clicked"]:
                    reachy_mini.look_at_image(state["x"], state["y"], duration=0.3)
                    state["just_clicked"] = False
        except KeyboardInterrupt:
            print("Interrupted. Closing viewer...")
        finally:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="显示 Reachy Mini 的摄像头画面（优化分辨率）并使其看向点击的点。"
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["default", "gstreamer", "webrtc"],
        default="default",
        help="媒体后端类型。",
    )
    parser.add_argument(
        "--resolution",
        type=str,
        choices=["640x480", "800x600", "1280x720"],
        default="640x480",
        help="捕获分辨率（默认: 640x480 以获得最佳性能）。",
    )
    parser.add_argument(
        "--window-scale",
        type=float,
        default=0.5,
        help="窗口缩放比例（默认: 0.5，即原大小的 50%%）。",
    )

    args = parser.parse_args()

    # 解析分辨率
    width, height = map(int, args.resolution.split("x"))

    main(backend=args.backend, width=width, height=height, window_scale=args.window_scale)
