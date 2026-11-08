# Maa Pipeline Guide

本目录包含 MaaFramework pipeline 编写与审查指南。

## 包含内容

- `SKILL.md`: guide 说明文档
- `references/field-reference.md`: Pipeline 字段速查表
- `references/coordinate-hygiene.md`: 点击目标怎么来（坐标坏味与推荐写法）
- `adapters/maahub/skills/maa-pipeline-guide.json`: MaaHub 发布元信息

## 作用

本 skill 介绍如何编写高质量 pipeline JSON，包括节点命名、识别算法、动作类型、状态机控制、以及可复用模式。

## 适用场景

- 设计 MaaFramework pipeline 时参考规范
- 审查 pipeline 文件时验证流程和识别策略
- 避免常见的 `next` 死循环、硬延迟、ROI 设计错误
- 让点击目标由识别结果推导，避免 `DirectHit` + 硬编码 `target`、或识别命中后仍写死 `target_offset` 这两种坐标坏味
