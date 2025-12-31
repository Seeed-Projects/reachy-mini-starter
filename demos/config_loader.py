#!/usr/bin/env python3
"""配置文件加载器

统一管理机器人配置，所有 demo 共用此配置模块。
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class RobotConfig:
    """机器人配置类"""

    def __init__(self, config_path: str = None):
        """初始化配置

        Args:
            config_path: 配置文件路径，默认为 demos/robot_config.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            script_dir = Path(__file__).parent
            config_path = script_dir / "robot_config.yaml"

        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件

        如果配置文件不存在，使用默认值并提示用户
        """
        if not self.config_path.exists():
            print(f"⚠️  配置文件不存在: {self.config_path}")
            print(f"提示: 请复制配置模板并修改:")
            template_path = self.config_path.parent / "robot_config.yaml.template"
            print(f"      cp {template_path} {self.config_path}")
            print(f"使用默认配置: robot_ip=10.42.0.75, port=8000")
            return {
                "robot": {"ip": "10.42.0.75", "port": 8000},
                "logging": {"level": "INFO"}
            }

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            print(f"使用默认配置: robot_ip=10.42.0.75, port=8000")
            return {
                "robot": {"ip": "10.42.0.75", "port": 8000},
                "logging": {"level": "INFO"}
            }

    @property
    def robot_ip(self) -> str:
        """获取机器人 IP 地址"""
        return self._config.get("robot", {}).get("ip", "10.42.0.75")

    @property
    def robot_port(self) -> int:
        """获取机器人端口"""
        return self._config.get("robot", {}).get("port", 8000)

    @property
    def base_url(self) -> str:
        """获取完整的 API 基础 URL"""
        return f"http://{self.robot_ip}:{self.robot_port}/api"

    @property
    def log_level(self) -> str:
        """获取日志级别"""
        return self._config.get("logging", {}).get("level", "INFO")

    def get(self, key: str, default=None):
        """获取配置值（支持嵌套路径，用 . 分隔）

        Args:
            key: 配置键，如 "robot.ip" 或 "log_level"
            default: 默认值

        Returns:
            配置值或默认值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def __repr__(self) -> str:
        """字符串表示"""
        return f"RobotConfig(ip={self.robot_ip}, port={self.robot_port})"


# 全局配置实例（延迟加载）
_config_instance = None


def get_config(config_path: str = None) -> RobotConfig:
    """获取全局配置实例（单例模式）

    Args:
        config_path: 可选的配置文件路径

    Returns:
        RobotConfig 实例
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = RobotConfig(config_path)

    return _config_instance


if __name__ == "__main__":
    # 测试配置加载
    print("测试配置加载器...")
    config = get_config()
    print(f"配置信息: {config}")
    print(f"机器人 IP: {config.robot_ip}")
    print(f"机器人端口: {config.robot_port}")
    print(f"API URL: {config.base_url}")
    print(f"日志级别: {config.log_level}")
