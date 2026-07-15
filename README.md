# JX3 JCL Conversion Service

独立 Web 服务，将剑网3 JCL 战斗日志转换为 jx3dps-online 兼容的 JSON 格式。

当前支持心法：**无方 (10627)**

## 功能

- 上传 .jcl / .txt 战斗日志文件
- 自动识别无方玩家
- 解析技能伤害时间轴、DOT、Buff 状态快照
- 导出 jx3dps-online 兼容的 JSON
- 诊断未识别的技能/Buff/奇穴 ID

## 快速启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

浏览器打开 `http://localhost:8080` 使用 Web 界面。

## API

### POST /v1/jcl/convert

上传 JCL 文件进行转换。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | .jcl 或 .txt 文件, 最大 25 MiB |
| target_level | int | 否 | 目标等级 (131-134), 默认 134 |
| max_time | float | 否 | 战斗最大时间(秒), 不填则使用完整时间 |
| player_id | str | 否 | 玩家 ID, 不填则自动选择第一个无方 |

### GET /v1/health

健康检查。

## 项目结构

```
jx3-jcl-service/
├── app/
│   ├── main.py        # FastAPI 应用
│   ├── convert.py     # JCL 转换核心逻辑
│   ├── models.py      # Pydantic 数据模型
│   └── static/        # Web 前端
│       └── index.html
├── tests/
│   ├── test_convert.py   # 转换逻辑测试
│   ├── test_api.py       # HTTP 端点测试
│   └── fixtures/         # 测试用 JCL 文件
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```

## 依赖

- Python >= 3.11
- FastAPI
- [Formulator](https://github.com/kerdevils/Formulator) (JCL 解析引擎)
- 技能数据参考 [Generator](https://github.com/IcyTide/Generator)

## Docker

```bash
docker build -t jx3-jcl-service -f Dockerfile ..
docker run -p 8080:8080 jx3-jcl-service
```

## 开发

```bash
pip install -e ".[dev]"
pytest tests/
```

## JSON 输出格式

```json
{
  "player": {"id": "...", "name": "角色名", "kungfuId": 10627, "kungfuName": "无方"},
  "battle": {"startFrame": 0, "endFrame": 12345},
  "data": {
    "技能名称#技能ID-等级": {
      "Buff1,Buff2|快照Buff1|目标Buff1": {
        "timeline": [[帧, 是否会心, 伤害], ...],
        "hit_damage": 1234,
        "critical_damage": 2345,
        "critical_strike": 0.5,
        "expected_damage": 1800,
        "expected_count": 10
      }
    }
  },
  "diagnostics": {
    "unknownSkillIds": [],
    "unknownBuffIds": [],
    "unknownTalentIds": []
  }
}
```
