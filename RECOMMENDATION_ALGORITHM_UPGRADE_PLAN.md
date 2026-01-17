# 鸡尾酒推荐算法升级方案

## 问题诊断

### 当前问题
- 不同故事输入总是推荐相同的鸡尾酒类型（如Cuba Libre）
- 推荐结果缺乏多样性，用户体验单调
- 算法过于依赖需求匹配，导致"通用型"鸡尾酒总是胜出

### 根本原因分析

1. **评分系统问题**
   - `need_weight=2.5` 权重过高，需求匹配占主导
   - Cuba Libre等鸡尾酒的`Need`字段（"nostalgia", "comfort", "casual fun"）太通用，容易匹配各种输入
   - 维度评分采用平方惩罚，但需求匹配的线性奖励过大

2. **多样性机制不足**
   - `diversity_bonus=0.35` 虽然存在，但只对未使用的鸡尾酒有效
   - `enable_randomization=True` 只在相近分数间随机，但大部分情况下分数差异明显
   - 没有基于语义特征的聚类和分组

3. **数据分布问题**
   - 某些鸡尾酒的维度组合（如Energy=4, Tension=2, Control=3）过于"中庸"
   - 部分鸡尾酒的`Need`字段包含通用需求词，导致高匹配率

## 升级方案

### 方案一：多阶段推荐策略（推荐⭐）

**核心思想**：先筛选候选池，再多样化选择

#### 阶段1：语义特征聚类
- 根据`Energy`, `Tension`, `Control`将鸡尾酒分为9个区域（3x3网格）
- 根据`Need`字段的语义相似度进行聚类
- 为每个用户输入生成"情感向量"，映射到对应的聚类区域

#### 阶段2：候选池生成
- 从目标聚类区域选择Top-10候选
- 避免从同一聚类区域选择过多候选
- 确保候选池包含不同类型的基础酒（Rum, Gin, Whiskey等）

#### 阶段3：多样性加权选择
- 对候选池中的鸡尾酒重新评分
- 引入"新颖性分数"：最近推荐频率的倒数
- 引入"聚类多样性分数"：与已推荐鸡尾酒的聚类距离
- 最终分数 = 匹配分数 × (1 - 新颖性衰减) × 聚类多样性

#### 实施步骤
1. 实现鸡尾酒聚类算法
2. 添加推荐历史记录（session-based或global）
3. 改进`find_best_match`方法，支持多阶段筛选
4. 动态调整权重，平衡匹配度和多样性

---

### 方案二：探索-利用平衡策略

**核心思想**：ε-greedy算法，定期探索冷门鸡尾酒

#### 机制设计
- 70%概率选择最佳匹配（exploitation）
- 30%概率从长尾候选中选择（exploration）
- 长尾定义：最近N次推荐中出现频率<10%的鸡尾酒

#### 实施步骤
1. 维护全局推荐频率统计
2. 在`find_best_match`中实现ε-greedy逻辑
3. 长尾候选优先选择Top Bar Cocktail和新颖鸡尾酒

---

### 方案三：基于语义相似度的多样性优化（最推荐⭐⭐⭐）

**核心思想**：将用户输入的情感特征与鸡尾酒的语义特征进行多样化匹配

#### 改进点

1. **需求匹配权重降低**
   - 将`need_weight`从2.5降低到1.5
   - 增加维度匹配的权重（从40%提升到60%）

2. **引入"反通用性惩罚"**
   - 识别"通用型"鸡尾酒（如Need字段包含太多常见词汇）
   - 对通用型鸡尾酒应用0.8-0.9的惩罚系数
   - Cuba Libre等鸡尾酒会被降分

3. **基于历史推荐的去重**
   - 维护用户session的推荐历史（最近10次）
   - 对已推荐的鸡尾酒应用0.3-0.5的降分
   - 优先推荐从未推荐过的鸡尾酒

4. **Top-K随机化改进**
   - 不是只返回Top-1，而是从Top-10中随机选择
   - 使用"多样性加权随机"：分数越高，被选中的概率越大，但Top-10都有机会

5. **语义聚类分组**
   - 将鸡尾酒按`Energy`, `Tension`, `Control`组合分组
   - 确保连续推荐不来自同一组
   - 增加"组间多样性"奖励

#### 实施优先级
1. **优先级1（立即实施）**
   - 降低need_weight到1.5
   - 实现推荐历史记录（session-based）
   - Top-10随机选择机制

2. **优先级2（短期实施）**
   - 反通用性惩罚机制
   - 语义聚类分组

3. **优先级3（长期优化）**
   - 用户偏好学习
   - 动态权重调整

---

### 方案四：混合策略（综合最优）

结合方案一、二、三的优点：

1. **第一阶段**：基于语义特征筛选Top-20候选
2. **第二阶段**：应用多样性加权（历史去重 + 聚类多样性 + 反通用性惩罚）
3. **第三阶段**：从最终Top-10中使用加权随机选择

## 技术实现细节

### 1. 推荐历史管理

```python
# 在CocktailAgent中添加
self._recommendation_history = {}  # {user_session_id: [cocktail_names]}

def _get_recent_recommendations(self, session_id: str, limit: int = 10) -> List[str]:
    """获取最近的推荐历史"""
    return self._recommendation_history.get(session_id, [])[-limit:]
```

### 2. 反通用性惩罚

```python
# 识别通用型鸡尾酒的Need字段
COMMON_NEEDS = ["comfort", "relaxation", "casual fun", "ease", "approachability"]

def calculate_universality_penalty(self, cocktail: Dict) -> float:
    """计算通用性惩罚系数（0.7-1.0）"""
    needs = cocktail.get('Need', [])
    common_count = sum(1 for need in needs if need.lower() in COMMON_NEEDS)
    if common_count >= 2:
        return 0.75  # 25%降分
    elif common_count == 1:
        return 0.9   # 10%降分
    return 1.0  # 无惩罚
```

### 3. Top-K随机化

```python
def _diversity_weighted_random_select(self, top_k_candidates: List[Dict], k: int = 1) -> List[Dict]:
    """从Top-K候选中进行多样性加权随机选择"""
    if len(top_k_candidates) <= k:
        return top_k_candidates
    
    # 计算每个候选的选择概率（分数越高概率越大，但Top-10都有基础概率）
    max_score = top_k_candidates[0]['score']
    min_score = top_k_candidates[-1]['score']
    score_range = max_score - min_score if max_score > min_score else 1.0
    
    probabilities = []
    for i, candidate in enumerate(top_k_candidates):
        # 基础概率 + 分数加成
        base_prob = 0.1 / len(top_k_candidates)  # 均匀分布基础
        score_bonus = 0.9 * ((candidate['score'] - min_score) / score_range) / len(top_k_candidates)
        probabilities.append(base_prob + score_bonus)
    
    # 归一化
    total_prob = sum(probabilities)
    probabilities = [p / total_prob for p in probabilities]
    
    # 加权随机选择
    import random
    selected = random.choices(top_k_candidates, weights=probabilities, k=k)
    return selected
```

## 推荐实施方案

**推荐采用方案三（基于语义相似度的多样性优化）**，原因：
1. 实现相对简单，风险低
2. 能快速解决推荐单一的问题
3. 可以逐步迭代优化

## 实施步骤

### Phase 1: 快速修复（1-2小时）
1. 降低`need_weight`从2.5到1.5
2. 提高维度匹配权重（从40%到60%）
3. 实现Top-10随机选择（从Top-10中随机选择Top-1）

### Phase 2: 历史记录（2-3小时）
1. 添加session-based推荐历史记录
2. 对已推荐鸡尾酒应用降分

### Phase 3: 反通用性惩罚（2-3小时）
1. 识别通用型鸡尾酒
2. 实现通用性惩罚机制

### Phase 4: 聚类优化（4-5小时）
1. 实现语义聚类分组
2. 组间多样性奖励

## 预期效果

- **多样性提升**：推荐结果覆盖至少60%以上的鸡尾酒类型
- **用户体验**：相同输入不再总是得到相同推荐
- **平衡性**：匹配度和多样性达到良好平衡
