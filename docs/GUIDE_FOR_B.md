# 成员B指引 - Agent工程师

> **角色**：大模型核心开发工程师
> **职责**：LangChain Agent引擎、Multi-Agent协作

---

## 一、你的任务

### 1.1 核心任务

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 实现面试官Agent | 生成问题、生成追问 |
| P0 | 实现评估Agent | 多维度评分、生成反馈 |
| P1 | 实现Agent协调器 | 管理多个Agent协作 |
| P2 | 实现知识检索Agent | 检索相关知识（可选） |
| P2 | 实现学习规划Agent | 生成学习路径（可选） |

### 1.2 交付物

| 文件 | 说明 | 必须 |
|------|------|------|
| `agents/__init__.py` | 导出Agent类 | ✅ |
| `agents/base.py` | Agent基类 | ✅ |
| `agents/interviewer.py` | 面试官Agent | ✅ |
| `agents/evaluator.py` | 评估Agent | ✅ |
| `agents/orchestrator.py` | Agent协调器 | ✅ |
| `agents/knowledge.py` | 知识检索Agent | ❌ |
| `agents/planner.py` | 学习规划Agent | ❌ |

---

## 二、接口规范

### 2.1 面试官Agent

```python
from typing import List, Dict, Optional

class InterviewerAgent:
    """面试官Agent - 负责生成问题和追问"""
    
    def __init__(self):
        """初始化LLM和Prompt"""
        pass
    
    def generate_question(
        self,
        target_company: str,
        target_position: str,
        tech_stack: List[str],
        question_index: int,
        previous_qa: List[Dict]
    ) -> str:
        """
        生成面试问题
        
        参数：
            target_company: 目标公司，如"字节跳动"
            target_position: 目标职位，如"后端工程师"
            tech_stack: 技术栈，如["Python", "Redis", "MySQL"]
            question_index: 当前是第几题（从0开始）
            previous_qa: 之前的问答历史
            
        返回：
            面试问题文本
            
        示例：
            >>> agent = InterviewerAgent()
            >>> question = agent.generate_question(
            ...     target_company="字节跳动",
            ...     target_position="后端工程师",
            ...     tech_stack=["Python", "Redis"],
            ...     question_index=0,
            ...     previous_qa=[]
            ... )
            >>> print(question)
            "请介绍一下Redis的持久化机制"
        """
        pass
    
    def generate_followup(
        self,
        original_question: str,
        user_answer: str,
        evaluation_result: Dict,
        followup_count: int
    ) -> str:
        """
        生成追问问题
        
        参数：
            original_question: 原始问题
            user_answer: 用户的回答
            evaluation_result: 评估结果
            followup_count: 已经追问了几次
            
        返回：
            追问问题文本
            
        示例：
            >>> followup = agent.generate_followup(
            ...     original_question="请介绍一下Redis的持久化",
            ...     user_answer="Redis有RDB和AOF两种方式...",
            ...     evaluation_result={"score": 75, ...},
            ...     followup_count=0
            ... )
            >>> print(followup)
            "你提到了RDB，能详细说说RDB的触发条件吗？"
        """
        pass
```

### 2.2 评估Agent

```python
class EvaluatorAgent:
    """评估Agent - 负责评估用户回答"""
    
    def __init__(self):
        """初始化LLM和Prompt"""
        pass
    
    def evaluate(
        self,
        question: str,
        user_answer: str,
        question_type: str,
        category: str
    ) -> Dict:
        """
        评估用户回答
        
        参数：
            question: 面试问题
            user_answer: 用户回答
            question_type: 问题类型，如"technical"/"behavioral"
            category: 问题分类，如"Redis"/"MySQL"/"Python"
            
        返回：
            评估结果字典（必须包含以下字段）：
            {
                "score": 78.5,              # 总分，0-100
                "dimensions": {
                    "accuracy": 82,         # 准确性，0-100
                    "completeness": 75,     # 完整性，0-100
                    "logic": 80,            # 逻辑性，0-100
                    "expression": 70        # 表达能力，0-100
                },
                "strengths": [              # 优点列表
                    "技术概念准确",
                    "有实际项目经验"
                ],
                "improvements": [           # 改进建议
                    "可以补充更多细节",
                    "逻辑可以更清晰"
                ],
                "feedback": "整体回答不错..."  # 详细反馈
            }
        """
        pass
```

### 2.3 Agent协调器

```python
class AgentOrchestrator:
    """Agent协调器 - 管理多个Agent协作"""
    
    def __init__(self):
        """初始化所有Agent"""
        self.interviewer = InterviewerAgent()
        self.evaluator = EvaluatorAgent()
        # self.knowledge = KnowledgeAgent()  # 可选
        # self.planner = PlannerAgent()      # 可选
    
    def run_interview_round(
        self,
        state: Dict
    ) -> Dict:
        """
        执行一轮面试（生成问题 + 评估回答 + 决定下一步）
        
        参数：
            state: 当前面试状态，格式见下方
            
        返回：
            {
                "action": "followup"/"next"/"end",
                "message": "追问内容"或"新问题",
                "evaluation": {...}  # 评估结果
            }
        """
        pass
```

---

## 三、数据格式

### 3.1 问答历史格式（previous_qa）

```python
[
    {
        "question": "请介绍一下Python的GIL",
        "answer": "GIL是全局解释器锁，它确保同一时刻只有一个线程执行Python字节码...",
        "score": 78.5
    },
    {
        "question": "GIL对多线程有什么影响？",
        "answer": "GIL会导致CPU密集型任务无法利用多核...",
        "score": 82.0
    }
]
```

### 3.2 面试状态格式（state）

```python
{
    "interview_id": "uuid",
    "target_company": "字节跳动",
    "target_position": "后端工程师",
    "tech_stack": ["Python", "Redis", "MySQL"],
    "interview_mode": "technical",
    "current_question_index": 2,
    "max_questions": 5,
    "max_followups": 2,
    "previous_qa": [...]  # 问答历史
}
```

---

## 四、MiMo配置

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# MiMo LLM配置
llm = ChatOpenAI(
    model="mimo-v2.5-pro",
    openai_api_key="your_api_key",  # 从环境变量读取
    openai_api_base="https://api.mimo.xiaomi.com/v1",
    temperature=0.7
)

# 评估时用低温度，保证稳定性
eval_llm = ChatOpenAI(
    model="mimo-v2.5-pro",
    openai_api_key="your_api_key",
    openai_api_base="https://api.mimo.xiaomi.com/v1",
    temperature=0.3
)
```

---

## 五、Prompt模板参考

### 5.1 生成问题的Prompt

```python
generate_question_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一位资深面试官，正在面试{target_position}岗位的候选人。

目标公司：{target_company}
技术栈：{tech_stack}

要求：
1. 生成一个高质量的面试问题
2. 问题应该考察候选人的实际能力和理解深度
3. 避免过于基础或过于偏门的问题

当前是第{question_index}题。
"""),
    ("human", "请生成一个面试问题。")
])
```

### 5.2 评估回答的Prompt

```python
evaluate_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是面试评估专家。请对候选人的回答进行评估。

评估维度（每项0-100分）：
1. accuracy - 准确性：技术概念是否正确
2. completeness - 完整性：是否覆盖关键点
3. logic - 逻辑性：表达是否有条理
4. expression - 表达能力：语言是否流畅

请以JSON格式输出评估结果。
"""),
    ("human", """问题：{question}
候选人回答：{answer}

请评估这个回答。""")
])
```

---

## 六、测试方法

创建 `test_agent.py` 测试你的Agent：

```python
from agents.interviewer import InterviewerAgent
from agents.evaluator import EvaluatorAgent

def test_interviewer():
    """测试面试官Agent"""
    agent = InterviewerAgent()
    
    # 测试生成问题
    question = agent.generate_question(
        target_company="字节跳动",
        target_position="后端工程师",
        tech_stack=["Python", "Redis", "MySQL"],
        question_index=0,
        previous_qa=[]
    )
    print(f"生成的问题: {question}")
    assert isinstance(question, str)
    assert len(question) > 0
    
    # 测试生成追问
    followup = agent.generate_followup(
        original_question="请介绍一下Redis的持久化",
        user_answer="Redis有RDB和AOF两种方式",
        evaluation_result={"score": 75},
        followup_count=0
    )
    print(f"生成的追问: {followup}")
    assert isinstance(followup, str)

def test_evaluator():
    """测试评估Agent"""
    agent = EvaluatorAgent()
    
    result = agent.evaluate(
        question="请介绍一下Redis的持久化机制",
        user_answer="Redis有两种持久化方式：RDB和AOF。RDB是快照，AOF是日志追加。",
        question_type="technical",
        category="Redis"
    )
    print(f"评估结果: {result}")
    
    # 验证返回格式
    assert "score" in result
    assert "dimensions" in result
    assert "strengths" in result
    assert "improvements" in result
    assert "feedback" in result
    assert "accuracy" in result["dimensions"]

if __name__ == "__main__":
    test_interviewer()
    test_evaluator()
    print("✅ 测试通过！")
```

---

## 七、协作接口

### 7.1 你依赖的

| 来源 | 内容 | 位置 |
|------|------|------|
| 成员C | RAG检索结果 | `rag/engine.py` |

### 7.2 依赖你的

| 来源 | 内容 | 调用方式 |
|------|------|----------|
| 成员A | 生成问题、评估回答 | `from agents.interviewer import InterviewerAgent` |

---

## 八、开发顺序

| 步骤 | 任务 | 预计时间 |
|------|------|----------|
| 1 | 创建Agent基类 | 0.5天 |
| 2 | 实现面试官Agent（生成问题） | 1天 |
| 3 | 实现评估Agent | 1天 |
| 4 | 实现追问生成 | 0.5天 |
| 5 | 实现协调器 | 0.5天 |
| 6 | 测试和调试 | 0.5天 |

**总计**：约4天

---

**文档版本**：v1.0
**后端工程师**：成员A
