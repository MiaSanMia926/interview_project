# 成员D指引 - 前端工程师

> **角色**：前端与可视化开发工程师
> **职责**：Streamlit界面、交互设计、数据可视化

---

## 一、你的任务

### 1.1 核心任务

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 搭建Streamlit基础框架 | 页面结构、路由 |
| P0 | 实现面试配置页 | 输入公司、职位、技术栈 |
| P0 | 实现面试对话页 | 显示问题、输入回答、显示评估 |
| P1 | 实现面试报告页 | 统计图表、雷达图 |
| P1 | 实现用户画像页 | 历史记录、强弱项分析 |
| P2 | 导出功能 | 导出PDF/Word |

### 1.2 交付物

| 文件 | 说明 | 必须 |
|------|------|------|
| `frontend/app.py` | Streamlit主应用 | ✅ |
| `frontend/pages/home.py` | 首页 | ✅ |
| `frontend/pages/interview.py` | 面试页 | ✅ |
| `frontend/pages/report.py` | 报告页 | ✅ |
| `frontend/pages/profile.py` | 用户画像页 | ❌ |
| `frontend/components/sidebar.py` | 侧边栏组件 | ✅ |
| `frontend/components/chat.py` | 对话组件 | ✅ |
| `frontend/components/charts.py` | 图表组件 | ✅ |

---

## 二、后端接口

### 2.1 接口列表

| 方法 | 路径 | 说明 | 你需要用 |
|------|------|------|----------|
| POST | `/api/users` | 创建用户 | ✅ |
| GET | `/api/users/{id}` | 获取用户 | ✅ |
| GET | `/api/users/{id}/profile` | 用户画像 | ✅ |
| POST | `/api/interviews` | 创建面试 | ✅ |
| POST | `/api/interviews/{id}/start` | 开始面试 | ✅ |
| POST | `/api/interviews/{id}/answer` | 提交回答 | ✅ |
| POST | `/api/interviews/{id}/skip` | 跳过问题 | ✅ |
| GET | `/api/interviews/{id}/state` | 面试状态 | ✅ |
| GET | `/api/interviews/{id}/summary` | 面试总结 | ✅ |
| GET | `/api/interviews` | 面试列表 | ✅ |
| GET | `/health` | 健康检查 | ✅ |

### 2.2 核心接口详细

#### 创建用户

```python
import requests

response = requests.post("http://localhost:8000/api/users", json={
    "username": "test_user"
})
# 返回: {"id": "uuid", "username": "test_user", "created_at": "..."}
```

#### 创建面试

```python
response = requests.post("http://localhost:8000/api/interviews", json={
    "user_id": "uuid",
    "target_company": "字节跳动",
    "target_position": "后端工程师",
    "tech_stack": ["Python", "Redis", "MySQL"],
    "interview_mode": "technical"
})
# 返回: {"id": "uuid", "status": "created", ...}
```

#### 开始面试

```python
response = requests.post(f"http://localhost:8000/api/interviews/{interview_id}/start")
# 返回: {
#     "interview_id": "uuid",
#     "current_phase": "TECHNICAL",
#     "question_index": 0,
#     "evaluation": null,
#     "next_action": "answer",
#     "next_message": "请介绍一下Redis的持久化机制",
#     "is_finished": false
# }
```

#### 提交回答

```python
response = requests.post(f"http://localhost:8000/api/interviews/{interview_id}/answer", json={
    "user_answer": "Redis有两种持久化方式..."
})
# 返回: {
#     "interview_id": "uuid",
#     "current_phase": "EVALUATION",
#     "question_index": 0,
#     "evaluation": {
#         "score": 78.5,
#         "dimensions": {"accuracy": 82, "completeness": 75, "logic": 80, "expression": 70},
#         "strengths": ["技术概念准确"],
#         "improvements": ["可以补充更多细节"],
#         "feedback": "整体回答不错..."
#     },
#     "next_action": "followup",  # followup/next_question/end
#     "next_message": "你提到了RDB，能详细说说吗？",
#     "is_finished": false
# }
```

#### 面试总结

```python
response = requests.get(f"http://localhost:8000/api/interviews/{interview_id}/summary")
# 返回: {
#     "interview_id": "uuid",
#     "overall_score": 76.8,
#     "total_questions": 5,
#     "answered_questions": 5,
#     "duration_minutes": 30,
#     "category_scores": {"Redis": 82, "MySQL": 75, "Python": 80},
#     "dimension_summary": {"accuracy": 78, "completeness": 72, "logic": 80, "expression": 75},
#     "strengths": ["Redis理解深入"],
#     "weaknesses": ["MySQL索引优化"],
#     "recommendations": ["建议深入学习MySQL索引原理"]
# }
```

---

## 三、页面设计

### 3.1 页面结构

```
首页 (home)
├── 开始面试按钮
├── 历史记录
└── 用户信息

面试配置页 (interview_config)
├── 目标公司输入
├── 目标职位输入
├── 技术栈选择
├── 面试模式选择
└── 开始面试按钮

面试页 (interview)
├── 问题显示区
├── 回答输入区
├── 评估结果区
├── 进度条
└── 操作按钮（提交/跳过/结束）

报告页 (report)
├── 总分显示
├── 雷达图（4个维度）
├── 分类得分柱状图
├── 强项/弱项列表
└── 改进建议
```

### 3.2 Streamlit布局示例

```python
import streamlit as st

# 页面配置
st.set_page_config(
    page_title="面试突破助手",
    page_icon="🎯",
    layout="wide"
)

# 侧边栏
with st.sidebar:
    st.header("配置")
    company = st.text_input("目标公司")
    position = st.text_input("目标职位")
    tech_stack = st.multiselect("技术栈", ["Python", "Redis", "MySQL", "Go", "Java"])

# 主内容区
tab1, tab2, tab3 = st.tabs(["面试", "报告", "个人中心"])

with tab1:
    st.header("模拟面试")
    # 面试内容...

with tab2:
    st.header("面试报告")
    # 报告内容...

with tab3:
    st.header("个人中心")
    # 用户信息...
```

---

## 四、图表组件

### 4.1 雷达图（评估维度）

```python
import plotly.graph_objects as go

def radar_chart(dimensions: dict):
    """
    绘制评估维度雷达图
    
    参数：
        dimensions: {"accuracy": 82, "completeness": 75, "logic": 80, "expression": 70}
    """
    categories = ["准确性", "完整性", "逻辑性", "表达能力"]
    values = [dimensions["accuracy"], dimensions["completeness"], 
              dimensions["logic"], dimensions["expression"]]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
```

### 4.2 柱状图（分类得分）

```python
import plotly.express as px

def bar_chart(category_scores: dict):
    """
    绘制分类得分柱状图
    
    参数：
        category_scores: {"Redis": 82, "MySQL": 75, "Python": 80}
    """
    df = px.data.tips()  # 示例数据
    fig = px.bar(
        x=list(category_scores.keys()),
        y=list(category_scores.values()),
        labels={"x": "分类", "y": "分数"},
        title="各分类得分"
    )
    st.plotly_chart(fig, use_container_width=True)
```

### 4.3 进度条

```python
def progress_bar(current: int, total: int):
    """显示面试进度"""
    progress = current / total
    st.progress(progress)
    st.write(f"进度：{current}/{total}")
```

---

## 五、对话组件

```python
def chat_message(role: str, content: str):
    """显示对话消息"""
    if role == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.write(content)
    else:
        with st.chat_message("user", avatar="👤"):
            st.write(content)

def chat_input():
    """用户输入"""
    return st.chat_input("请输入你的回答...")
```

---

## 六、项目结构

```
interview-coach/
├── frontend/                    # 你的工作目录
│   ├── __init__.py
│   ├── app.py                   # 主应用
│   ├── api_client.py            # API调用封装
│   ├── pages/                   # 页面
│   │   ├── __init__.py
│   │   ├── home.py              # 首页
│   │   ├── interview.py         # 面试页
│   │   └── report.py            # 报告页
│   └── components/              # 组件
│       ├── __init__.py
│       ├── sidebar.py           # 侧边栏
│       ├── chat.py              # 对话组件
│       └── charts.py            # 图表组件
```

---

## 七、启动方式

```bash
# 安装依赖
pip install streamlit plotly requests

# 启动前端
cd interview-coach
streamlit run frontend/app.py --server.port 8501
```

访问：http://localhost:8501

---

## 八、协作接口

### 8.1 你依赖的

| 来源 | 内容 | 位置 |
|------|------|------|
| 成员A | API接口文档 | `docs/API.md` |

### 8.2 依赖你的

| 来源 | 内容 |
|------|------|
| 成员E | 界面截图用于PPT |

---

## 九、开发顺序

| 步骤 | 任务 | 预计时间 |
|------|------|----------|
| 1 | 搭建Streamlit框架 | 0.5天 |
| 2 | 实现API调用封装 | 0.5天 |
| 3 | 实现面试配置页 | 0.5天 |
| 4 | 实现面试对话页 | 1天 |
| 5 | 实现评估结果展示 | 0.5天 |
| 6 | 实现报告页（图表） | 1天 |
| 7 | 样式美化 | 0.5天 |
| 8 | 测试和调试 | 0.5天 |

**总计**：约5天

---

**文档版本**：v1.0
**后端工程师**：成员A
