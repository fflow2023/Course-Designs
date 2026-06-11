"""
ID3 决策树核心算法
本文件只实现算法本身，不依赖 sklearn 的现有决策树模型
输入数据格式为 pandas.DataFrame
特征列和目标列已完成缺失值处理和离散化。
"""

from __future__ import annotations

import math
from typing import Any


def _safe_len(data: Any) -> int:
    return 0 if data is None else len(data)


def _majority_class(values: Any, default: Any = None) -> Any:
    """返回多数类；平票时按字符串顺序保证结果稳定"""
    if values is None or len(values) == 0:
        return default

    counts = values.astype(str).value_counts(dropna=False)
    if counts.empty:
        return default

    max_count = counts.max()
    candidates = [str(label) for label, count in counts.items() if count == max_count]
    return sorted(candidates)[0]


def entropy(data: Any, target_col: str) -> float:
    """计算类别集合 U 的信息熵 H(U)"""
    if _safe_len(data) == 0 or target_col not in data.columns:
        return 0.0

    # U：当前节点上的类别集合；u_i：第 i 个类别。
    # counts[u_i] 表示类别 u_i 的样本数。
    counts = data[target_col].astype(str).value_counts(dropna=False)
    # total 表示当前节点样本总数 |U|。
    total = counts.sum()
    if total == 0:
        return 0.0

    result = 0.0
    for count in counts:
        # P(u_i)=类别 u_i 的样本数 / 当前节点样本总数。
        probability = count / total
        if probability > 0:
            # H(U) = - Σ P(u_i) * log2(P(u_i))。
            result -= probability * math.log2(probability)
    return float(result)


def conditional_entropy(data: Any, feature: str, target_col: str) -> float:
    """计算按属性 V 划分后的条件熵 H(U|V)"""
    if _safe_len(data) == 0 or feature not in data.columns or target_col not in data.columns:
        return 0.0

    # V：当前候选划分属性 feature；v_j：属性 V 的第 j 个取值。
    total = len(data)
    result = 0.0
    for _, subset in data.groupby(feature, dropna=False, sort=False):
        # subset 表示 V=v_j 时对应的子数据集。
        # P(v_j)=子数据集样本数 / 当前节点样本总数。
        weight = len(subset) / total
        # entropy(subset, target_col) 计算 H(U|V=v_j)，
        # 即已知属性取值 v_j 后类别 U 的不确定性。
        result += weight * entropy(subset, target_col)
        # H(U|V) = Σ P(v_j) * H(U|V=v_j)。
    return float(result)


def information_gain(data: Any, feature: str, target_col: str) -> float:
    """计算互信息/信息增益 I(U,V)=H(U)-H(U|V)"""
    return float(entropy(data, target_col) - conditional_entropy(data, feature, target_col))


def choose_best_feature(data: Any, features: list[str], target_col: str) -> tuple[str | None, list[dict[str, Any]]]:
    """计算候选属性的信息增益，并返回最优属性和过程表。

    平票时保留 features 中更靠前的属性，方便课堂演示时结果稳定。
    """
    if _safe_len(data) == 0 or not features:
        return None, []

    base_entropy = entropy(data, target_col)
    gain_rows: list[dict[str, Any]] = []
    best_feature: str | None = None
    best_gain = -math.inf

    for feature in features:
        cond_entropy = conditional_entropy(data, feature, target_col)
        gain = base_entropy - cond_entropy
        row = {
            "feature": feature,
            "base_entropy": float(base_entropy),
            "conditional_entropy": float(cond_entropy),
            "information_gain": float(gain),
            "value_count": int(data[feature].astype(str).nunique(dropna=False)),
        }
        gain_rows.append(row)

        if gain > best_gain:
            best_gain = gain
            best_feature = feature

    for row in gain_rows:
        row["selected"] = row["feature"] == best_feature

    return best_feature, gain_rows


def _leaf_node(
    prediction: Any,
    sample_count: int,
    node_entropy: float,
    reason: str,
) -> dict[str, Any]:
    label = None if prediction is None else str(prediction)
    return {
        "is_leaf": True,
        "prediction": label,
        "majority_class": label,
        "split_feature": None,
        "sample_count": int(sample_count),
        "entropy": float(node_entropy),
        "gain": 0.0,
        "reason": reason,
        "children": {},
    }


def build_tree(
    data: Any,
    features: list[str],
    target_col: str,
    parent_majority: Any = None,
    depth: int = 0,
    path: str = "根",
    trace: list[dict[str, Any]] | None = None,
    min_gain: float = 1e-12,
    max_depth: int | None = 12,
) -> dict[str, Any]:
    """递归构建 ID3 决策树。

    trace 会被原地追加每个节点的候选属性信息增益记录，供界面展示。
    """
    if trace is None:
        trace = []

    sample_count = _safe_len(data)
    if sample_count == 0:
        return _leaf_node(parent_majority, 0, 0.0, "子数据集为空，返回父节点多数类")

    current_majority = _majority_class(data[target_col], parent_majority)
    node_entropy = entropy(data, target_col)
    labels = data[target_col].astype(str).unique()

    if len(labels) == 1:
        return _leaf_node(labels[0], sample_count, node_entropy, "当前样本全部属于同一类别")

    if max_depth is not None and depth >= max_depth:
        return _leaf_node(current_majority, sample_count, node_entropy, "达到最大树深度，返回当前节点多数类")

    if not features:
        return _leaf_node(current_majority, sample_count, node_entropy, "候选属性为空，返回当前节点多数类")

    best_feature, gain_rows = choose_best_feature(data, features, target_col)
    for row in gain_rows:
        trace.append(
            {
                "node_path": path,
                "depth": int(depth),
                "feature": row["feature"],
                "base_entropy": row["base_entropy"],
                "conditional_entropy": row["conditional_entropy"],
                "information_gain": row["information_gain"],
                "value_count": row["value_count"],
                "selected": bool(row["selected"]),
            }
        )

    if best_feature is None:
        return _leaf_node(current_majority, sample_count, node_entropy, "没有可用候选属性")

    best_gain = max(row["information_gain"] for row in gain_rows) if gain_rows else 0.0
    if best_gain <= min_gain:
        return _leaf_node(current_majority, sample_count, node_entropy, "信息增益为 0 或无法有效降低熵")

    remaining_features = [feature for feature in features if feature != best_feature]
    node = {
        "is_leaf": False,
        "prediction": str(current_majority),
        "majority_class": str(current_majority),
        "split_feature": best_feature,
        "sample_count": int(sample_count),
        "entropy": float(node_entropy),
        "gain": float(best_gain),
        "reason": "选择信息增益最大的属性作为决策节点",
        "children": {},
    }

    values = sorted(data[best_feature].astype(str).unique(), key=str)
    for value in values:
        subset = data[data[best_feature].astype(str) == value]
        child_path = f"{path} -> {best_feature}={value}"
        node["children"][str(value)] = build_tree(
            subset,
            remaining_features,
            target_col,
            parent_majority=current_majority,
            depth=depth + 1,
            path=child_path,
            trace=trace,
            min_gain=min_gain,
            max_depth=max_depth,
        )

    return node


def predict_one(tree: dict[str, Any], sample: Any, default_class: Any = None) -> Any:
    """预测单条样本；遇到未知属性取值时使用当前节点多数类回退"""
    node = tree
    fallback = default_class

    while node and not node.get("is_leaf", False):
        fallback = node.get("majority_class", fallback)
        feature = node.get("split_feature")
        if feature is None:
            return fallback

        try:
            raw_value = sample[feature]
        except Exception:
            return fallback

        value = str(raw_value)
        children = node.get("children", {})
        if value not in children:
            return fallback
        node = children[value]

    if node:
        return node.get("prediction", fallback)
    return fallback


def predict_one_with_trace(tree: dict[str, Any], sample: Any, default_class: Any = None) -> tuple[Any, list[dict[str, Any]]]:
    """预测单条样本，并返回经过的决策路径，展示用"""
    node = tree
    fallback = default_class
    trace: list[dict[str, Any]] = []

    while node and not node.get("is_leaf", False):
        fallback = node.get("majority_class", fallback)
        feature = node.get("split_feature")
        if feature is None:
            trace.append({"节点": "", "输入取值": "", "处理": "无可用划分属性，返回当前回退类别", "输出": fallback})
            return fallback, trace

        try:
            raw_value = sample[feature]
        except Exception:
            trace.append({"节点": feature, "输入取值": "", "处理": "样本缺少该属性，返回当前节点多数类", "输出": fallback})
            return fallback, trace

        value = "" if raw_value is None else str(raw_value).strip()
        display_value = "未见过的取值" if value == "__UNKNOWN_VALUE__" else value
        children = node.get("children", {})
        if value not in children:
            trace.append({"节点": feature, "输入取值": display_value, "处理": "未匹配到分支，返回当前节点多数类", "输出": fallback})
            return fallback, trace

        trace.append({"节点": feature, "输入取值": display_value, "处理": "匹配分支，继续向下", "输出": ""})
        node = children[value]

    prediction = node.get("prediction", fallback) if node else fallback
    trace.append({"节点": "叶节点", "输入取值": "", "处理": "到达叶节点", "输出": prediction})
    return prediction, trace


def predict_batch(tree: dict[str, Any], data: Any, default_class: Any = None) -> list[Any]:
    """批量预测 DataFrame 中的样本"""
    return [predict_one(tree, row, default_class=default_class) for _, row in data.iterrows()]


def tree_to_rules(tree: dict[str, Any]) -> list[str]:
    """将决策树转换为 IF-THEN 分类规则"""
    rules: list[str] = []

    def walk(node: dict[str, Any], conditions: list[str]) -> None:
        if node.get("is_leaf", False):
            condition_text = " AND ".join(conditions) if conditions else "TRUE"
            rules.append(f"IF {condition_text} THEN 类别 = {node.get('prediction')}")
            return

        feature = node.get("split_feature")
        for value, child in node.get("children", {}).items():
            walk(child, conditions + [f"{feature} = {value}"])

    walk(tree, [])
    return rules


def fit_id3(
    data: Any,
    target_col: str,
    min_gain: float = 1e-12,
    max_depth: int | None = 12,
) -> dict[str, Any]:
    """训练 ID3 模型，返回树结构和可展示的训练过程"""
    features = [column for column in data.columns if column != target_col]
    global_majority = _majority_class(data[target_col])
    gain_history: list[dict[str, Any]] = []
    tree = build_tree(
        data,
        features,
        target_col,
        parent_majority=global_majority,
        trace=gain_history,
        min_gain=min_gain,
        max_depth=max_depth,
    )
    feature_values = {
        feature: sorted(data[feature].astype(str).unique(), key=str)
        for feature in features
    }
    return {
        "tree": tree,
        "gain_history": gain_history,
        "global_majority": global_majority,
        "feature_values": feature_values,
        "features": features,
        "target_col": target_col,
    }
