# 接口契约规范

## 概述

本目录包含YouTube分析工具各模块间的接口契约规范。每个契约定义了模块间的数据交换格式、API规范、事件规范以及错误处理要求。

## 契约文件列表

| 契约文件 | 描述 | 提供方 | 使用方 |
|---------|------|--------|--------|
| `project_config_contract.md` | 项目配置和环境接口 | TASK_01 | TASK_02, TASK_03 |
| `api_framework_contract.md` | API框架和数据库接口 | TASK_02 | TASK_04, TASK_08, TASK_10 |
| `frontend_framework_contract.md` | 前端框架接口 | TASK_03 | TASK_09 |
| `youtube_data_contract.md` | YouTube数据提取接口 | TASK_04 | TASK_05, TASK_07 |
| `transcription_contract.md` | 音频转录接口 | TASK_05 | TASK_06 |
| `content_analysis_contract.md` | 内容分析接口 | TASK_06 | TASK_08 |
| `comment_analysis_contract.md` | 评论分析接口 | TASK_07 | TASK_08 |
| `orchestrator_contract.md` | 分析编排器接口 | TASK_08 | TASK_09 |
| `result_display_contract.md` | 结果展示接口 | TASK_09 | TASK_10 |
| `websocket_events_contract.md` | WebSocket事件规范 | 全局 | 全局 |

## 契约遵循原则

### 1. 向后兼容性
- 所有接口变更必须保持向后兼容
- 新增字段使用可选属性
- 废弃字段保留至少一个版本周期

### 2. 数据验证
- 所有输入数据必须进行格式验证
- 使用Pydantic (Python) 和 Zod (TypeScript) 进行数据验证
- 提供清晰的错误消息

### 3. 错误处理
- 统一的错误响应格式
- 明确的错误代码和消息
- 适当的HTTP状态码

### 4. 文档要求
- 每个接口必须有完整的文档
- 包含示例请求和响应
- 说明错误情况和处理方式

## 版本控制

接口版本遵循语义化版本控制：
- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

当前版本: `v1.0.0`

## 使用指南

1. **实现前**: 仔细阅读相关契约文档
2. **开发中**: 严格按照契约规范实现接口
3. **测试时**: 使用契约中的示例数据进行测试
4. **变更时**: 先更新契约文档，再实现代码变更

## 契约验证

每个契约都包含：
- 数据模型定义
- API端点规范
- 事件格式定义
- 验证规则
- 测试用例

使用以下工具进行契约验证：
- **Python**: Pydantic模型验证
- **TypeScript**: Zod schema验证
- **API**: OpenAPI规范验证
- **WebSocket**: 自定义事件验证器
