# Reachy Mini Starter Kit

基于官方 API 文档的 Reachy Mini 机器人 Python 开发框架。

## 项目结构

```
reachy-mini-starter/
├── src/                          # 核心库
│   ├── connection.py             # 连接管理
│   ├── config.py                 # 配置管理
│   ├── logger.py                 # 日志系统
│   └── utils.py                  # 工具函数
├── demos/                        # 基础控制演示
│   ├── 01_basic_audio_control/   # Demo 1: 音频控制
│   ├── 02_basic_body_rotation/   # Demo 2: 身体旋转
│   ├── 03_basic_nod_head/        # Demo 3: 点头动作
│   ├── 04_basic_shake_head/      # Demo 4: 摇头动作
│   ├── API_接口开发指南.md       # API 开发文档
│   ├── CN使用修改.md             # 使用修改指南
│   └── CN连接配网.md             # 连接配网指南
├── configs/                      # 配置文件
├── scripts/                      # 工具脚本
└── requirements.txt              # 依赖包
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置机器人 IP
cp demos/robot_config.yaml.template demos/robot_config.yaml
# 编辑 demos/robot_config.yaml 修改机器人 IP 地址

# 3. 运行基础控制 Demo
python demos/01_basic_audio_control/test_audio_control.py
python demos/02_basic_body_rotation/test_body_rotation.py
python demos/03_basic_nod_head/test_nod_head.py
python demos/04_basic_shake_head/test_shake_head.py
```

## 配置说明

所有 Demo 共用同一个配置文件 `demos/robot_config.yaml`，只需配置一次即可：

```yaml
robot:
  ip: "10.42.0.75"    # 修改为你的机器人 IP
  port: 8000
```

配置文件已被 `.gitignore` 忽略，不会提交到仓库。

## 基础控制 Demo

### Demo 1: 音频控制 (test_audio_control.py)
演示如何通过音频信号控制机器人动作响应

### Demo 2: 身体旋转 (test_body_rotation.py)
演示机器人身体左右旋转控制

### Demo 3: 点头动作 (test_nod_head.py)
演示机器人上下点头动作控制

### Demo 4: 摇头动作 (test_shake_head.py)
演示机器人左右摇头动作控制

## 开发路线图

当前版本提供基础控制接口，后续将基于这些基础能力实现复杂应用：

- [ ] Agent 集成 - 结合 AI Agent 实现智能决策
- [ ] LLM 集成 - 集成大语言模型实现自然语言交互
- [ ] 视觉系统 - 添加摄像头视觉识别能力
- [ ] 语音交互 - 集成语音识别和合成
- [ ] 情感表达 - 基于状态的情感化动作表达

## 文档

- [API 接口开发指南](demos/API_接口开发指南.md) - 完整的 API 接口文档
- [使用修改指南](demos/CN使用修改.md) - 使用说明和修改建议
- [连接配网指南](demos/CN连接配网.md) - 网络连接配置说明
