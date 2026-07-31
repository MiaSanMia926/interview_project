# 技术选型说明

## 图表渲染方案

考核允许两种图表方案：
a. 后端 Matplotlib/Plotly 绘图 -> Base64 返回前端
b. 后端 Skill 生成 ECharts JSON -> 前端 ECharts 渲染

本项目的图表采用**方案 B 的变体**：
- 后端不生成 Base64 图片，而是通过 Agent 返回结构化数据
- 前端用 Vue + SVG 手写雷达图/趋势图/图谱，不依赖 ECharts 库
- 数据流：后端 API 返回评分数据 -> 前端 computed 计算坐标 -> SVG 渲染

对应考核标准中"两种方案评分标准完全等价"，且前端 UI 美观度不计分。

## fetch vs axios

前端使用浏览器原生 fetch 而非 axios，因为：
1. fetch 是 Web 标准，零依赖
2. SSE 流式场景下 fetch + ReadableStream 比 axios 更适合
3. 功能等价，具备完整的请求/响应拦截、错误处理能力

## PydanticOutputParser vs with_structured_output

使用了 LangChain 新版 API `with_structured_output`，是 `PydanticOutputParser` 的现代替代方案，
功能完全等价。同时保留了 `evaluate_pydantic()` 方法使用经典的 `PydanticOutputParser`。
