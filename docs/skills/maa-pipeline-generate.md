# Maa Pipeline Generate

本目录包含 MaaFramework pipeline OCR 节点生成工具。

## 包含内容

- `scripts/generate_node.py`: 生成单个 OCR 节点并合并到目标 pipeline 文件
- `scripts/generate_sweep.py`: 批量生成不同 expand 值的 sweep pipeline，辅助选择最佳 ROI
- `SKILL.md`: skill 说明文档
- `adapters/maahub/skills/maa-pipeline-generate.json`: MaaHub 发布元信息

## 使用方法

### 生成单个节点

```bash
python "<skill-dir>/scripts/generate_node.py" "目标文字" NodeName resource/base/pipeline/main.json --expand 20 --overwrite
```

### 扫描 expand 值

```bash
python "<skill-dir>/scripts/generate_sweep.py" "目标文字" "x,y,w,h" 0,5,10,15,20,25,30
```

## 说明

- `generate_node.py` 将根据 OCR 识别结果生成节点并将其写入 pipeline。
- `generate_sweep.py` 生成一个 sweep pipeline，用于通过 run_pipeline 验证不同 expand 值的效果。
- 生成的 Click 节点不写死 `target`，由 MaaFramework 点击识别框中心；非文字元素用截图裁剪 + TemplateMatch。
- UI 流程尚未探明时先回到 `maa-workflow-build` 的 EXPLORE 阶段实测，再据此生成节点。
- 目标 pipeline 支持相对路径和绝对路径；实际资源根应以主 Interface 的 `resource[].path` 为准，`assets/resource/base` 是 boilerplate-family 项目示例。
