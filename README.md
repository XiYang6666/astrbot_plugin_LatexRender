# astrbot-plugin-LatexRender

渲染 LLM 输出的 Latex

## 目的

在 QQ 中无法渲染 Bot 输出的 Latex, 导致难以阅读输出内容, 此插件可以将 Latex 渲染为图片方便阅读

## 配置

| 配置项           | 描述                                                       |
| ---------------- | ---------------------------------------------------------- |
| platform_filter  | 是否开启平台过滤,开启后仅规定的平台启用Latex渲染           |
| allowed_platform | 启用 Latex 渲染的平台, 应填写 astrbot 中的 `机器人名称` 项 |
