# 成员C指引 - RAG与数据工程工程师

> **角色**：RAG与数据工程工程师
> **职责**：知识库构建、向量检索、数据处理

---

## 一、你的任务

### 1.1 核心任务

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 收集面试题数据 | 爬取/整理面试题 |
| P0 | 数据清洗去重 | 处理原始数据 |
| P0 | 构建ChromaDB向量库 | 向量化并存储 |
| P0 | 实现检索接口 | 供后端调用 |
| P1 | 调优检索策略 | MMR重排序 |
| P2 | 构建标准答案库 | 供评估使用 |

### 1.2 交付物

| 文件 | 说明 | 必须 |
|------|------|------|
| `rag/__init__.py` | 导出RAG类 | ✅ |
| `rag/engine.py` | RAG检索引擎 | ✅ |
| `rag/loader.py` | 文档加载器 | ✅ |
| `rag/splitter.py` | 文本分块 | ✅ |
| `rag/standard_answers.py` | 标准答案库 | ❌ |
| `data/questions/` | 原始面试题数据 | ✅ |
| `data/chroma/` | 向量数据库 | ✅ |
| `scripts/load_questions.py` | 数据导入脚本 | ✅ |

---

## 二、接口规范

### 2.1 RAG引擎

```python
from typing import List, Dict, Optional

class RAGEngine:
    """RAG检索引擎"""
    
    def __init__(self, persist_directory: str = "./data/chroma"):
        """
        初始化RAG引擎
        
        参数：
            persist_directory: ChromaDB持久化目录
        """
        pass
    
    def load_documents(self, file_path: str) -> int:
        """
        加载文档到向量库
        
        参数：
            file_path: 文档文件路径（JSON/CSV）
            
        返回：
            加载的文档数量
            
        示例：
            >>> engine = RAGEngine()
            >>> count = engine.load_documents("./data/questions/redis.json")
            >>> print(f"加载了 {count} 个文档")
        """
        pass
    
    def search(
        self,
        query: str,
        tech_stack: Optional[List[str]] = None,
        category: Optional[str] = None,
        difficulty_min: Optional[int] = None,
        difficulty_max: Optional[int] = None,
        k: int = 5
    ) -> List[Dict]:
        """
        语义检索面试题
        
        参数：
            query: 查询文本，如"Redis缓存穿透"
            tech_stack: 技术栈过滤，如["Redis"]
            category: 分类过滤，如"Redis"
            difficulty_min: 最低难度
            difficulty_max: 最高难度
            k: 返回数量
            
        返回：
            检索结果列表，格式见下方
            
        示例：
            >>> results = engine.search(
            ...     query="Redis缓存穿透解决方案",
            ...     tech_stack=["Redis"],
            ...     k=3
            ... )
            >>> for r in results:
            ...     print(r["question"])
        """
        pass
    
    def search_with_mmr(
        self,
        query: str,
        k: int = 5,
        lambda_mult: float = 0.7
    ) -> List[Dict]:
        """
        MMR重排序检索（增加多样性）
        
        参数：
            query: 查询文本
            k: 返回数量
            lambda_mult: 相关性权重（0-1，越大越注重相关性）
            
        返回：
            检索结果列表
        """
        pass
```

### 2.2 标准答案库（可选）

```python
class StandardAnswerDB:
    """标准答案库"""
    
    def __init__(self, db_path: str = "./data/standard_answers.json"):
        """初始化标准答案库"""
        pass
    
    def get_standard_answer(self, question_id: str) -> Optional[Dict]:
        """
        获取标准答案
        
        参数：
            question_id: 问题ID
            
        返回：
            标准答案，格式见下方
        """
        pass
    
    def get_by_category(self, category: str) -> List[Dict]:
        """
        获取某分类的所有标准答案
        
        参数：
            category: 分类，如"Redis"
            
        返回：
            标准答案列表
        """
        pass
```

---

## 三、数据格式

### 3.1 检索结果格式

```python
{
    "id": "question_001",
    "question": "请介绍一下Redis的持久化机制",
    "category": "Redis",
    "difficulty": 6,
    "tech_stack": ["Redis"],
    "score": 0.85,  # 相似度分数
    "metadata": {
        "source": "牛客网",
        "company": "字节跳动"
    }
}
```

### 3.2 面试题数据格式（JSON）

```python
[
    {
        "id": "redis_001",
        "question": "请介绍一下Redis的持久化机制",
        "category": "Redis",
        "difficulty": 6,
        "tech_stack": ["Redis"],
        "type": "technical",
        "key_points": [           # 关键点（用于评估）
            "RDB快照",
            "AOF日志追加",
            "RDB和AOF的区别",
            "混合持久化"
        ],
        "reference_answer": "Redis有两种持久化方式...",  # 参考答案
        "source": "牛客网",
        "company": "字节跳动"
    }
]
```

### 3.3 标准答案格式

```python
{
    "question_id": "redis_001",
    "question": "请介绍一下Redis的持久化机制",
    "key_points": [
        "RDB快照：fork子进程，生成二进制文件",
        "AOF日志追加：记录写命令",
        "RDB适合备份，AOF适合数据安全",
        "混合持久化：Redis 4.0+支持"
    ],
    "reference_answer": "Redis有两种持久化方式...",
    "scoring_criteria": {
        "accuracy": "是否正确描述RDB和AOF",
        "completeness": "是否覆盖所有关键点",
        "logic": "是否有条理地组织答案"
    }
}
```

---

## 四、数据收集建议

### 4.1 数据来源

| 来源 | 类型 | 数量目标 |
|------|------|----------|
| 牛客网面经 | 技术题 | 100+ |
| LeetCode讨论区 | 算法题 | 50+ |
| 大厂面试真题 | 综合 | 50+ |
| 技术博客 | 专项 | 50+ |

### 4.2 分类体系

```
Redis
├── 基础数据结构
├── 持久化（RDB/AOF）
├── 缓存策略（穿透/雪崩/击穿）
├── 分布式（Cluster/Sentinel）
└── 性能优化

MySQL
├── 索引（B+树/联合索引）
├── 事务（ACID/隔离级别）
├── 锁（行锁/表锁/死锁）
├── 优化（慢查询/执行计划）
└── 分库分表

Python
├── 基础语法
├── GIL与多线程
├── 内存管理
├── 装饰器/生成器
└── 异步编程

系统设计
├── 短链接系统
├── 秒杀系统
├── 消息队列
└── 分布式系统
```

### 4.3 数据格式示例

**文件位置**：`data/questions/redis.json`

```json
[
    {
        "id": "redis_001",
        "question": "Redis有哪些数据结构？",
        "category": "Redis",
        "difficulty": 3,
        "tech_stack": ["Redis"],
        "type": "technical",
        "key_points": ["String", "List", "Hash", "Set", "ZSet"],
        "source": "牛客网"
    },
    {
        "id": "redis_002",
        "question": "Redis的持久化机制有哪些？各有什么优缺点？",
        "category": "Redis",
        "difficulty": 6,
        "tech_stack": ["Redis"],
        "type": "technical",
        "key_points": ["RDB快照", "AOF日志", "RDB优缺点", "AOF优缺点", "混合持久化"],
        "source": "字节跳动"
    }
]
```

---

## 五、ChromaDB使用

### 5.1 安装

```bash
pip install chromadb langchain-community
```

### 5.2 基本使用

```python
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# 初始化Embedding
embeddings = HuggingFaceEmbeddings(
    model_name="shibing624/text2vec-base-chinese"  # 中文Embedding
)

# 创建向量库
vectorstore = Chroma(
    persist_directory="./data/chroma",
    embedding_function=embeddings
)

# 添加文档
vectorstore.add_texts(
    texts=["Redis的持久化机制", "MySQL索引原理"],
    metadatas=[
        {"category": "Redis", "difficulty": 6},
        {"category": "MySQL", "difficulty": 5}
    ]
)

# 检索
results = vectorstore.similarity_search(
    query="Redis缓存穿透",
    k=5,
    filter={"category": "Redis"}
)
```

### 5.3 MMR检索

```python
# MMR检索（增加多样性）
results = vectorstore.max_marginal_relevance_search(
    query="Redis缓存",
    k=5,
    lambda_mult=0.7  # 0-1，越大越注重相关性
)
```

---

## 六、后端调用方式

后端会这样调用你的代码：

```python
from rag.engine import RAGEngine

# 初始化
engine = RAGEngine()

# 检索面试题
results = engine.search(
    query="Redis缓存穿透解决方案",
    tech_stack=["Redis"],
    category="Redis",
    difficulty_min=5,
    difficulty_max=8,
    k=3
)

# 返回给前端或Agent使用
for result in results:
    print(result["question"])
```

---

## 七、测试方法

创建 `test_rag.py` 测试：

```python
from rag.engine import RAGEngine

def test_rag():
    """测试RAG引擎"""
    engine = RAGEngine()
    
    # 测试加载文档
    count = engine.load_documents("./data/questions/redis.json")
    print(f"加载了 {count} 个文档")
    assert count > 0
    
    # 测试检索
    results = engine.search(
        query="Redis持久化",
        k=3
    )
    print(f"检索到 {len(results)} 个结果")
    assert len(results) > 0
    
    # 验证返回格式
    for r in results:
        assert "question" in r
        assert "category" in r
        assert "difficulty" in r
    
    print("✅ 测试通过！")

if __name__ == "__main__":
    test_rag()
```

---

## 八、协作接口

### 8.1 你依赖的

| 来源 | 内容 | 位置 |
|------|------|------|
| 成员A | 数据库Schema | `docs/DATABASE_SCHEMA.md` |

### 8.2 依赖你的

| 来源 | 内容 | 调用方式 |
|------|------|----------|
| 成员A | 检索面试题 | `from rag.engine import RAGEngine` |
| 成员B | 检索结果用于生成问题 | 通过成员A传递 |

---

## 九、开发顺序

| 步骤 | 任务 | 预计时间 |
|------|------|----------|
| 1 | 收集面试题数据（100+题目） | 1天 |
| 2 | 数据清洗和格式化 | 0.5天 |
| 3 | 实现文档加载器 | 0.5天 |
| 4 | 构建ChromaDB向量库 | 0.5天 |
| 5 | 实现检索接口 | 1天 |
| 6 | 调优MMR策略 | 0.5天 |
| 7 | 测试 | 0.5天 |

**总计**：约4.5天

---

**文档版本**：v1.0
**后端工程师**：成员A
