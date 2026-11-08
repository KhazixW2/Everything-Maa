# Maa Wiki

将 MaaFramework 相关问题和其它 Maa skill 路由到权威官方材料。它覆盖官方文档、schema、API、binding、版本、语义变化和兼容性证据。

- 实现：`skills/maa-wiki/SKILL.md`
- MaaHub 发布元信息：`adapters/maahub/skills/maa-wiki.json`
- 上游 skill：`https://raw.githubusercontent.com/Windsland52/MaaLLMWiki/main/skills/maallmwiki/SKILL.md`

使用原则：先读取上游 `maallmwiki` skill 并按其流程定位版本化索引；最终引用必须回到 MaaFramework 或 binding 的 pinned 原始来源；URL 不可达时按披露的 fallback 顺序处理，仍无法核实则标记未验证。
