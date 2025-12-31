# Reachy Mini Starter Kit

基于官方 API 的 Reachy Mini 机器人 Python 开发框架，提供基础控制接口和完整示例代码。

---

**中文** | [English](README_EN.md)

---

## 特性

- 统一的配置管理系统，一处配置全局使用
- 完整的基础控制 Demo，涵盖音频、运动等核心功能
- 详细的 API 开发文档和使用指南
- 为后续 Agent 和 LLM 集成预留扩展接口

## 项目结构

```
reachy-mini-starter/
├── src/                          # 核心库
│   ├── connection.py             # 连接管理
│   ├── config.py                 # 配置管理
│   ├── logger.py                 # 日志系统
│   └── utils.py                  # 工具函数
├── demos/                        # 基础控制演示
│   ├── config_loader.py          # 配置加载器
│   ├── robot_config.yaml.template # 配置模板
│   ├── 01_basic_audio_control/   # 音频控制
│   ├── 02_basic_body_rotation/   # 身体旋转
│   ├── 03_basic_nod_head/        # 点头动作
│   └── 04_basic_shake_head/      # 摇头动作
├── docs/                         # 文档
│   ├── API_REFERENCE_CN.md       # API 参考文档（中文）
│   ├── USAGE_GUIDE_CN.md         # 使用指南（中文）
│   ├── NETWORK_GUIDE_CN.md       # 网络配置（中文）
│   ├── API_REFERENCE.md          # API 参考文档（English）
│   ├── USAGE_GUIDE.md            # 使用指南（English）
│   └── NETWORK_GUIDE.md          # 网络配置（English）
├── configs/                      # 配置文件目录
├── scripts/                      # 工具脚本
└── requirements.txt              # 依赖包
```

## 快速开始

### 前置要求

- Python 3.7+
- Reachy Mini 机器人（已连接同一网络）

### 安装与配置

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 创建配置文件
cp demos/robot_config.yaml.template demos/robot_config.yaml

# 3. 编辑配置文件，修改机器人 IP 地址
vim demos/robot_config.yaml
```

配置文件内容：

```yaml
robot:
  ip: "10.42.0.75"    # 修改为你的机器人实际 IP
  port: 8000
```

### 运行 Demo

```bash
# 音频控制 - 扬声器/麦克风音量调节
python demos/01_basic_audio_control/test_audio_control.py

# 身体旋转 - 底座左右转动
python demos/02_basic_body_rotation/test_body_rotation.py

# 点头动作 - 头部上下运动
python demos/03_basic_nod_head/test_nod_head.py

# 摇头动作 - 头部左右转动
python demos/04_basic_shake_head/test_shake_head.py
```

## 配置说明

所有 Demo 共用 `demos/robot_config.yaml` 配置文件，只需配置一次即可。

配置文件已加入 `.gitignore`，不会被提交到仓库，保护隐私信息。

## Demo 说明

| Demo | 功能 | API 接口 |
|------|------|----------|
| 音频控制 | 扬声器/麦克风音量调节与测试 | `/api/volume/*` |
| 身体旋转 | 底座左右旋转控制 (±160°) | `/api/move/goto` |
| 点头动作 | 头部俯仰运动 | `/api/move/goto` |
| 摇头动作 | 头部偏航运动 | `/api/move/goto` |

## 文档

### 中文文档

- [API 接口开发指南](docs/API_REFERENCE_CN.md) - 完整的 REST API 参考文档
- [使用修改指南](docs/USAGE_GUIDE_CN.md) - 详细的使用说明和修改建议
- [连接配网指南](docs/NETWORK_GUIDE_CN.md) - 网络连接配置步骤

### English Documentation

- [API Reference Guide](docs/API_REFERENCE.md) - Complete REST API reference
- [Usage and Debugging Guide](docs/USAGE_GUIDE.md) - Detailed usage instructions
- [Network Configuration Guide](docs/NETWORK_GUIDE.md) - Network setup steps

## 开发路线

当前版本为基础控制接口，后续计划：

- [ ] **Agent 集成** - 结合 AI Agent 实现智能决策和行为规划
- [ ] **LLM 集成** - 接入大语言模型实现自然语言交互
- [ ] **视觉系统** - 添加摄像头视觉识别能力
- [ ] **语音交互** - 集成语音识别和语音合成
- [ ] **情感表达** - 基于内部状态的情感化动作表达

## 许可证

参见 [LICENSE](LICENSE) 文件
