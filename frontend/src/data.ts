/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Interview, UserProfile, InterviewSummary } from './types';

export const DEFAULT_COMPANIES = [
  '字节跳动', '微软', '高盛集团', '麦肯锡', '宝洁 (P&G)', '特斯拉', '腾讯', '阿里巴巴', '美团', '小红书'
];

export const DEFAULT_POSITIONS = [
  '后端开发工程师', '产品经理 (PM)', '人工智能算法工程师', '商业咨询顾问', '投资银行分析师', '品牌市场营销经理', '高级人力资源专员'
];

export const DEFAULT_TECH_STACKS = [
  '系统设计与高并发', '数据库与算法设计', '产品规划与全生命周期', '用户需求深挖与体验', '商业分析与竞争策略', '财务报表与企业估值', '品牌营销与用户增长', 'STAR 行为模型', '敏捷项目管理与协同'
];

// 高保真 mock 历史面试
export const MOCK_HISTORIC_INTERVIEWS: Interview[] = [
  {
    id: 'history-interview-1',
    userId: 'default-user',
    targetCompany: '字节跳动',
    targetPosition: '后端开发工程师',
    techStack: ['Golang', 'Redis', 'MySQL', 'System Design'],
    interviewMode: 'technical',
    status: 'completed',
    overallScore: 82.5,
    createdAt: '2026-07-10T14:30:00Z',
    durationMinutes: 45,
    questions: [
      {
        id: 'hq-1',
        interviewId: 'history-interview-1',
        questionText: '请详细描述 Redis 的缓存击穿、缓存穿透和缓存雪崩，并结合实际高并发场景给出生产级别的防范方案。',
        questionType: 'technical',
        category: 'Redis',
        difficulty: 8,
        userAnswer: '缓存穿透是指查询一个根本不存在的数据，缓存和数据库都不会命中。防范方案是使用布隆过滤器，或对空值进行短期缓存。缓存击穿是指一个热点 Key 在过期的瞬间，大量请求涌入直接打到数据库，可以用互斥锁解决，或者设置热点数据永不过期。缓存雪崩是指大量缓存集中过期，或者 Redis 宕机，可以用随机过期时间、主从高可用、以及限流降级来防范。',
        evaluation: {
          score: 85,
          dimensions: {
            accuracy: 90,
            completeness: 85,
            logic: 80,
            expression: 85
          },
          strengths: [
            '对三者的概念定义非常准确清晰，没有发生混淆',
            '提出的布隆过滤器和互斥锁解决方案均属于工业界主流落地方案'
          ],
          improvements: [
            '可以进一步补充热点数据“永不过期”在实际更新时的“逻辑过期”实现细节',
            '可以提及 Redis Cluster 在遭遇缓存雪崩时的集群负载降级策略'
          ],
          feedback: '回答非常扎实。对经典三险（穿透、击穿、雪崩）的定义无懈可击。建议在谈到互斥锁时，顺便提及分布式锁（如 Redisson）的实现和续期机制，会让表现更上一层楼。'
        }
      },
      {
        id: 'hq-2',
        interviewId: 'history-interview-1',
        questionText: 'MySQL 的 InnoDB 引擎中，为什么选择 B+ 树作为索引结构？它与 B 树、红黑树相比有哪些不可替代的绝对优势？',
        questionType: 'technical',
        category: 'MySQL',
        difficulty: 7,
        userAnswer: 'B+ 树的所有叶子节点都相互链接，形成双向链表，非常适合区间范围查询，而 B 树数据分布在各个节点，需要做中序遍历。另外 B+ 树的非叶子节点只存储键值和指针，不存储整行数据，所以一个节点可以容纳更多索引，树的高度更低，能极大地减少磁盘 I/O。红黑树在数据量大时树的高度会太高，导致磁盘 I/O 频繁。',
        evaluation: {
          score: 88,
          dimensions: {
            accuracy: 92,
            completeness: 85,
            logic: 90,
            expression: 85
          },
          strengths: [
            '逻辑主线清晰，牢牢抓住了“减少磁盘 I/O”和“范围查询能力”这两个底层核心痛点',
            '准确地分析了非叶子节点不存 Row Data 的物理存储优势'
          ],
          improvements: [
            '可以进一步引出 B+ 树叶子节点扇出（Fan-out）的物理计算公式，表明理解深度'
          ],
          feedback: '表现相当优异。B+ 树物理结构与磁盘预读、操作系统页对齐的关联回答得很好。建议主动提及索引分裂与合并的动态过程，更能展现资深级别。'
        }
      },
      {
        id: 'hq-3',
        interviewId: 'history-interview-1',
        questionText: 'Go 语言的 GMP 调度模型中，M 遇到系统阻塞（如 syscall）时，P 和 G 是如何流转移动的？抢占式调度又是如何起作用的？',
        questionType: 'technical',
        category: 'Golang',
        difficulty: 9,
        userAnswer: '当 M 阻塞时，它会释放与之绑定的 P。P 会去寻找一个空闲的 M 或者创建新的 M 来接管。而原来的 M 会和阻塞的 G 一起，等待 syscall 返回。抢占式调度在 Go 1.14 之后是基于信号实现的，sysmon 线程会监控运行超时的 G，向对应的 M 发送 SIGURG 信号，强制中断该 G 并让出 CPU。',
        evaluation: {
          score: 75,
          dimensions: {
            accuracy: 80,
            completeness: 70,
            logic: 75,
            expression: 75
          },
          strengths: [
            '准确指出了 Go 1.14 之后基于 SIGURG 异步信号抢占这一底层演进细节',
            '清晰阐述了 M 释放 P 的解耦流转过程'
          ],
          improvements: [
            '需要明确指出阻塞 syscall 返回后，G 和 M 是如何尝试重新夺回 P，或者如何放入全局运行队列（GRQ）的细节',
            '对 work stealing 窃取机制可以作适当铺垫，使 GMP 故事更加完整'
          ],
          feedback: '知识面不错，特别是了解 SIGURG 抢占信号，这已经超出了很多初中级开发者的水平。但对于 syscall 返回后的 M 离职、G 归队的重定位路径表述稍显模糊，这也是面试常考的细节陷阱。'
        }
      }
    ]
  },
  {
    id: 'history-interview-2',
    userId: 'default-user',
    targetCompany: '腾讯',
    targetPosition: '后端开发工程师',
    techStack: ['Golang', 'Computer Networks', 'OS'],
    interviewMode: 'technical',
    status: 'completed',
    overallScore: 75.2,
    createdAt: '2026-07-08T09:15:00Z',
    durationMinutes: 40,
    questions: [
      {
        id: 'hq-4',
        interviewId: 'history-interview-2',
        questionText: '请详述 TCP 的三次握手与四次挥手过程，以及为什么挥手需要四次而握手只需要三次？CLOSE_WAIT 和 TIME_WAIT 状态分别有什么深层作用？',
        questionType: 'technical',
        category: 'Computer Networks',
        difficulty: 6,
        userAnswer: '握手三次是因为要把 ACK 和 SYN 放在一个包发给客户端，挥手四次是因为服务端收到客户端 FIN 时，可能自己还有数据没发完，需要先回一个 ACK，等自己发完数据后再发 FIN。TIME_WAIT 的作用是等待 2MSL，保证旧连接在网络中的报文都消失，并保证最后一个 ACK 送达。',
        evaluation: {
          score: 76,
          dimensions: {
            accuracy: 78,
            completeness: 75,
            logic: 75,
            expression: 76
          },
          strengths: [
            '对三次和四次的不对称原理解释得通俗易懂',
            '准确指出了 TIME_WAIT 规避旧报文混淆以及确保最后确认包送达这两个核心用处'
          ],
          improvements: [
            '未充分解释 CLOSE_WAIT 的产生根源。CLOSE_WAIT 往往是应用层未主动关闭 socket 导致的，需要指出在业务系统连接泄漏排查中的重要意义'
          ],
          feedback: '回答合格，基本功良好。强烈建议把 CLOSE_WAIT 放在高并发微服务调用失败、FD（文件描述符）枯竭等生产血泪史中去讨论，这会在腾讯面试官面前展现极佳的工程素养。'
        }
      }
    ]
  },
  {
    id: 'history-interview-3',
    userId: 'default-user',
    targetCompany: '小红书',
    targetPosition: '产品经理 (PM)',
    techStack: ['产品规划与全生命周期', '用户需求深挖与体验', '品牌营销与用户增长'],
    interviewMode: 'behavioral',
    status: 'completed',
    overallScore: 86.5,
    createdAt: '2026-07-11T16:40:00Z',
    durationMinutes: 35,
    questions: [
      {
        id: 'hq-5',
        interviewId: 'history-interview-3',
        questionText: '如果你是小红书的产品经理，针对“社区低频或沉默用户流失”的问题，你会如何设计全链路的精细化用户触达或增长留存体系？',
        questionType: 'behavioral',
        category: '产品规划与全生命周期',
        difficulty: 8,
        userAnswer: '我会首先对低频用户进行价值与兴趣画像的分群。第一，在内容侧：结合探索（Exploration）算法为流失临界用户推荐高点击率、普适性强的垂类爆款笔记；第二，在促活策略上：设计低干扰、高价值反馈的利益点，比如完成首评奖励社区积分或福利券；第三，在触达渠道上：建立基于用户日常打开时段的精准 Push 机制，针对各画像群组定制专属文案，并在 App 内增加特定主题的内容热卡引导留存。',
        evaluation: {
          score: 88,
          dimensions: {
            accuracy: 85,
            completeness: 88,
            logic: 90,
            expression: 85
          },
          strengths: [
            '用户分群思路清晰，对“低频用户”流失前因的界定（如无偏好、社交孤立）符合社区生态。',
            '手段覆盖内容分发、促活利益和精细触达通道，具有很高的实操落地可能性。'
          ],
          improvements: [
            '缺乏定量数据指标的定义，如果能引入漏斗转化和 A/B 测试留存目标，评估维度会更完美。'
          ],
          feedback: '非常优秀的业务与产品思维。对用户分类与算法推荐的协同阐述非常生动，体现了成熟互联网大厂的产品素养。'
        }
      },
      {
        id: 'hq-6',
        interviewId: 'history-interview-3',
        questionText: '你刚才提到了通过 Push 促活。如果出现“Push 打开率极高，但次日用户留存率却出现了明显下降”的负反馈，你认为根本原因是什么？你会如何排查与解决？',
        questionType: 'behavioral',
        category: '用户需求深挖与体验',
        difficulty: 8,
        userAnswer: '这很可能是“标题党文案”导致了用户欺骗性负反馈。高打开率证明推送标题或福利极具吸引力，等落到 Landing Page 后内容质量低、不符合预期，导致用户瞬间流失甚至直接卸载应用。我的排查方法：首先看点击后停留时间（Dwell Time）和流失漏斗；其次排查系统通知关闭率与卸载率。解决办法是强化内容与标题一致性，并对推送频次设置严格的配额限制（Frequency Cap）。',
        evaluation: {
          score: 85,
          dimensions: {
            accuracy: 84,
            completeness: 85,
            logic: 88,
            expression: 83
          },
          strengths: [
            '敏锐地剖析出了“预期差”带来的用户信任危机，没有被单一的高点击率指标所蒙蔽。',
            '指标体系排查完整（停留时间、通知关闭、卸载），对 Push 频率控制的落地措施得当。'
          ],
          improvements: [
            '可以进一步提出如何通过多重灰度试验或内容召回池（Candidate Pool）在算法端规避不当推荐的长期演进路线。'
          ],
          feedback: '回答非常到位，对于典型的指标异动分析表现出了很强的数据敏感度。能够从用户体验和信任层面去看指标，不唯数据论，是一流产品经理的特质。'
        }
      }
    ]
  }
];

export const MOCK_SUMMARY_1: InterviewSummary = {
  interviewId: 'history-interview-1',
  overallScore: 82.5,
  totalQuestions: 3,
  answeredQuestions: 3,
  durationMinutes: 45,
  categoryScores: {
    'Redis': 85,
    'MySQL': 88,
    'Golang': 75
  },
  dimensionSummary: {
    accuracy: 87,
    completeness: 80,
    logic: 82,
    expression: 82
  },
  strengths: [
    '核心技术基本功扎实，对 Redis、MySQL B+ 树等底层底层存储原理有深入的推敲。',
    '具备优秀的逻辑归纳能力，阐述 B+ 树相比红黑树等非关系索引物理读写优势时层次极为清晰。',
    '对 Golang 底层演进（如抢占调度在 1.14 之后基于信号的演进）保持了很高的知识追踪。'
  ],
  weaknesses: [
    'Golang GMP 在外部 Syscall 挂起返回后的重平衡细节把握不够精确。',
    '在高并发架构细节设计上，还缺乏更主动的工程思维（如逻辑过期设计模式、多级缓存一致性保障）。'
  ],
  recommendations: [
    '建议深入阅读 Go Runtime 的 `proc.go` 核心源码，研究 `exitsyscall` 的具体实现步骤，掌握 G 是如何落回到局部/全局队列或被抢占的。',
    '学习分布式缓存的高阶设计：掌握大 Key、热 Key 的动态发现与滑窗过滤机制，在大型互联网公司属于通关秘籍。',
    '提升在白板或架构描述中运用专业指标与算力约束进行系统设计推演的能力。'
  ]
};

// 高保真 用户能力画像
export const MOCK_USER_PROFILE: UserProfile = {
  userId: 'default-user',
  username: 'Cheng Zihan',
  totalInterviews: 2,
  averageScore: 78.9,
  radarData: [
    { name: '技术准确性 (Accuracy)', score: 84, fullMark: 100 },
    { name: '要点完整性 (Completeness)', score: 78, fullMark: 100 },
    { name: '思维逻辑性 (Logic)', score: 81, fullMark: 100 },
    { name: '沟通表达力 (Expression)', score: 79, fullMark: 100 }
  ],
  categoryData: [
    { category: 'MySQL', score: 88 },
    { category: 'Redis', score: 85 },
    { category: '计算机网络', score: 76 },
    { category: 'Golang', score: 75 }
  ],
  trendData: [
    { date: '07-05', score: 68, title: '初次模拟' },
    { date: '07-08', score: 75, title: '腾讯模拟' },
    { date: '07-10', score: 83, title: '字节模拟' }
  ],
  strengths: [
    '对经典数据库（MySQL、Redis）的物理内存和磁盘存储结构掌握十分深刻，对 B+ 树优势、缓存异常防御手段熟悉。',
    '能快速感知并描述较深底层的机制（如 Go 基于信号的异步抢占、Redis 双向叶链表区间查等）。',
    '逻辑框架完整，能够在短时间内构建起多点回答骨架，避免散乱无序。'
  ],
  weaknesses: [
    '复杂网络排障和网络编程机制（如 TCP TIME_WAIT 在生产中遭遇高并发本地端口枯竭时的解法，或 CLOSE_WAIT 泄露修复）深度略微不足。',
    '多并发调度底层临界流转容易漏掉重分配细节（如 Go 协程在阻塞解除后的落队策略）。'
  ],
  recommendations: [
    '针对网络协议核心，研究一下 Linux TCP 套接字的端口复用、SO_REUSEADDR 机制，以及微服务架构中连接池的最佳参数实践。',
    '针对并发编程：建议写几个基于 CSP 模型的真实管道多路复用组件，加深对 GMP 抢占式系统调用的物理运行感知。',
    '在未来面试中：加强“工程背景化”表达。在说出概念的同时，带上一两句真实的生产排障痛点和数据对比（例如磁盘 I/O 减少近 70% 等数字），会让技术说服力大幅倍增。'
  ],
  challenges: [
    { id: 1, text: '深入研究 Linux TCP 端口复用与连接池参数调优', priority: 'high' },
    { id: 2, text: '手写一个基于 CSP 模型的并发管道组件', priority: 'medium' },
    { id: 3, text: '面试表达中补充真实生产排障案例和量化数据', priority: 'low' }
  ],
  knowledgeGraph: {
    nodes: [
      { id: 'redis', label: 'Redis 缓存层', group: 'core' },
      { id: 'redis-strategy', label: '缓存击穿/穿透/雪崩', group: 'sub' },
      { id: 'bloom-filter', label: '布隆过滤器', group: 'sub' },
      { id: 'redis-cluster', label: 'Redis Cluster 分布式', group: 'sub' },
      
      { id: 'mysql', label: 'MySQL 数据库', group: 'core' },
      { id: 'bplus-tree', label: 'B+树索引引擎', group: 'sub' },
      { id: 'mysql-io', label: '磁盘预读与页对齐', group: 'sub' },
      
      { id: 'golang', label: 'Go 语言并发', group: 'core' },
      { id: 'gmp-model', label: 'GMP 协程调度', group: 'sub' },
      { id: 'preemptive', label: '1.14 抢占式调度', group: 'sub' },
      { id: 'syscall-block', label: '系统挂起与回收', group: 'weak' },
      
      { id: 'network', label: '计算机网络', group: 'core' },
      { id: 'tcp-handshake', label: 'TCP 3握手4挥手', group: 'sub' },
      { id: 'time-wait', label: 'TIME_WAIT & CLOSE_WAIT', group: 'weak' },
      { id: 'port-exhaustion', label: '并发套接字端口枯竭', group: 'weak' }
    ],
    links: [
      { source: 'redis', target: 'redis-strategy', label: '核心策略' },
      { source: 'redis-strategy', target: 'bloom-filter', label: '防御工具' },
      { source: 'redis-strategy', target: 'redis-cluster', label: '物理拓扑' },
      
      { source: 'mysql', target: 'bplus-tree', label: '基础物理结构' },
      { source: 'bplus-tree', target: 'mysql-io', label: '磁盘I/O关联' },
      
      { source: 'golang', target: 'gmp-model', label: '调度核心' },
      { source: 'gmp-model', target: 'preemptive', label: '抢占升级' },
      { source: 'gmp-model', target: 'syscall-block', label: '阻塞陷阱' },
      
      { source: 'network', target: 'tcp-handshake', label: '核心传输协议' },
      { source: 'tcp-handshake', target: 'time-wait', label: '连接状态机' },
      { source: 'time-wait', target: 'port-exhaustion', label: '生产故障演进' }
    ]
  }
};
