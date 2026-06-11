"""
streamlit 页面使用的工具函数和辅助函数
数据处理、评估和可视化
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_ROOT / "datasets"
CSV_ENCODINGS = ("utf-8-sig", "utf-8", "gbk", "gb18030")
ID_COLUMN_NAMES = {"id", "index", "序号", "编号"}


def ensure_dataset_dir() -> Path:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    return DATASET_DIR


def list_datasets() -> dict[str, Path]:
    """扫描 datasets 目录中的 CSV 文件"""
    ensure_dataset_dir()
    files = sorted(DATASET_DIR.glob("*.csv"), key=lambda path: path.name.lower())
    return {path.stem: path for path in files}


def read_csv_flexible(source: str | Path | bytes) -> pd.DataFrame:
    """按中文编码读取 CSV"""
    last_error: Exception | None = None
    for encoding in CSV_ENCODINGS:
        try:
            if isinstance(source, bytes):
                return pd.read_csv(io.BytesIO(source), encoding=encoding)
            return pd.read_csv(source, encoding=encoding)
        except Exception as exc:
            last_error = exc
    raise ValueError(f"无法读取 CSV 文件，请确认文件编码和格式正确。最后错误：{last_error}")


def clean_columns(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result.columns = [str(column).strip() for column in result.columns]

    columns_to_drop: list[str] = []
    for column in result.columns:
        column_text = str(column).strip()
        if column_text == "" or re.fullmatch(r"Unnamed:\s*\d+(\.\d+)?", column_text):
            columns_to_drop.append(column)
            continue
        if column_text.lower() in ID_COLUMN_NAMES:
            columns_to_drop.append(column)
            continue

        values = result[column].astype(str).str.strip()
        zero_based_index = pd.Series([str(index) for index in range(len(result))], index=result.index)
        one_based_index = pd.Series([str(index) for index in range(1, len(result) + 1)], index=result.index)
        if values.equals(zero_based_index) or values.equals(one_based_index):
            columns_to_drop.append(column)

    if columns_to_drop:
        result = result.drop(columns=columns_to_drop)

    deduped_columns: list[str] = []
    seen: dict[str, int] = {}
    for column in result.columns:
        base_name = str(column).strip() or "字段"
        count = seen.get(base_name, 0)
        if count == 0:
            deduped_columns.append(base_name)
        else:
            deduped_columns.append(f"{base_name}_{count + 1}")
        seen[base_name] = count + 1

    result.columns = deduped_columns
    return result


def sanitize_dataset_name(name: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", name.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "uploaded_dataset"


def save_uploaded_dataset(file_bytes: bytes, dataset_name: str) -> Path:
    """把上传的 CSV 保存到 datasets 目录，供后续启动继续选择 """
    ensure_dataset_dir()
    safe_name = sanitize_dataset_name(dataset_name)
    if not safe_name.lower().endswith(".csv"):
        safe_name = f"{safe_name}.csv"
    target = DATASET_DIR / safe_name
    target.write_bytes(file_bytes)
    return target


def validate_dataset(data: pd.DataFrame, target_col: str | None) -> tuple[list[str], list[str]]:
    """返回数据集错误和警告信息"""
    errors: list[str] = []
    warnings: list[str] = []

    if data is None or data.empty:
        errors.append("CSV 数据为空，无法训练 ID3 决策树。")
        return errors, warnings

    if len(data.columns) == 0:
        errors.append("CSV 文件没有字段名，请确认第一行为表头。")
        return errors, warnings

    if target_col is None:
        errors.append("请先选择目标分类列。")
        return errors, warnings

    if target_col not in data.columns:
        errors.append(f"目标列 `{target_col}` 不存在。")

    if len(data.columns) < 2:
        errors.append("数据集至少需要 1 个特征列和 1 个目标分类列。")

    if target_col in data.columns:
        non_missing_targets = data[target_col].dropna()
        if non_missing_targets.empty:
            errors.append("目标分类列全部为空，无法训练。")
        elif non_missing_targets.astype(str).nunique() == 1:
            warnings.append("目标分类列只有一个类别，ID3 会直接生成单一叶节点。")
        else:
            class_counts = non_missing_targets.astype(str).value_counts()
            rare_classes = class_counts[class_counts < 3]
            if not rare_classes.empty:
                rare_text = "、".join([f"{label}({count}条)" for label, count in rare_classes.items()])
                warnings.append(f"以下类别样本过少，评估结果可能不稳定：{rare_text}。")

    if len(data) < 20:
        warnings.append("数据集样本过少（不足 20 条），结果可能不稳定，已默认开启5折交叉验证")

    if target_col in data.columns:
        feature_count = len([column for column in data.columns if column != target_col])
        if feature_count < 2:
            warnings.append("特征列过少，决策树可能过于简单。")

    missing_count = int(data.isna().sum().sum())
    if missing_count > 0:
        warnings.append(f"数据中总共存在 {missing_count} 个缺失值，请在侧边栏选择处理方式。")

    return errors, warnings


def get_numeric_feature_columns(
    data: pd.DataFrame,
    target_col: str,
    min_unique: int = 10,
    min_ratio: float = 0.25,
) -> list[str]:
    """识别更像连续变量的数值字段，低基数数字编码仍按离散类别处理"""
    numeric_columns: list[str] = []
    for column in data.columns:
        if column == target_col or not pd.api.types.is_numeric_dtype(data[column]):
            continue

        numeric_values = pd.to_numeric(data[column], errors="coerce").dropna()
        if numeric_values.empty:
            continue

        unique_count = numeric_values.nunique(dropna=True)
        unique_ratio = unique_count / len(numeric_values)
        if unique_count > min_unique or (unique_count > 5 and unique_ratio >= min_ratio):
            numeric_columns.append(column)

    return numeric_columns


def handle_missing_values(
    data: pd.DataFrame,
    strategy: str,
    target_col: str,
) -> tuple[pd.DataFrame, list[str], dict[int, dict[str, Any]]]:
    """缺失值处理：无论何种策略，优先删除目标列缺失行；特征列可选择删除或众数填充"""
    result = data.copy()
    messages: list[str] = []
    imputed_cells: dict[int, dict[str, Any]] = {}

    # 1. 目标分类列（结果类）存在缺失值的行必须删除，因为无法进行监督学习
    if target_col in result.columns and result[target_col].isna().any():
        before = len(result)
        result = result.dropna(subset=[target_col]).reset_index(drop=True)
        messages.append(f"目标列 `{target_col}` 的缺失样本（{before - len(result)} 行）已直接删除。")

    if not result.isna().any().any():
        return result, messages, imputed_cells

    # 2. 处理特征列的缺失值
    if strategy == "删除缺失行":
        before = len(result)
        result = result.dropna(axis=0).reset_index(drop=True)
        messages.append(f"其余含缺失值的样本 {before - len(result)} 行已按策略删除。")
        return result, messages, imputed_cells

    for column in result.columns:
        if column == target_col:
            continue
        if result[column].isna().any():
            missing_mask = result[column].isna()
            mode_values = result[column].mode(dropna=True)
            fill_value = mode_values.iloc[0] if not mode_values.empty else "缺失"
            for row_index in result.index[missing_mask]:
                imputed_cells.setdefault(int(row_index), {})[column] = fill_value
            result.loc[missing_mask, column] = fill_value
            messages.append(f"特征字段 `{column}` 的缺失值已用众数 `{fill_value}` 填充。")

    return result.reset_index(drop=True), messages, imputed_cells


def _make_tracking_column(columns: list[str]) -> str:
    base_name = "__ID3_ROW_ID__"
    column_name = base_name
    while column_name in columns:
        column_name = f"_{column_name}"
    return column_name


def build_processed_preview(
    train: pd.DataFrame,
    test: pd.DataFrame,
    row_id_col: str,
    imputed_cells: dict[int, dict[str, Any]],
) -> tuple[pd.DataFrame, list[tuple[int, str]]]:
    """生成数据概览页使用的处理后数据，并标记训练/测试划分和众数填充单元格"""

    preview_parts: list[pd.DataFrame] = []
    if not train.empty:
        train_preview = train.copy()
        train_preview.insert(0, "数据划分", "训练集")
        preview_parts.append(train_preview)
    if not test.empty:
        test_preview = test.copy()
        test_preview.insert(0, "数据划分", "测试集")
        preview_parts.append(test_preview)

    if not preview_parts:
        return pd.DataFrame(), []

    preview = pd.concat(preview_parts, ignore_index=True)
    preview = preview.sort_values(row_id_col).reset_index(drop=True)
    row_ids = preview[row_id_col].astype(int).tolist()
    preview = preview.drop(columns=[row_id_col]).astype(object)

    imputed_positions: list[tuple[int, str]] = []
    for display_index, row_id in enumerate(row_ids):
        for column, fill_value in imputed_cells.get(row_id, {}).items():
            if column in preview.columns:
                preview.at[display_index, column] = f"None({fill_value})"
                imputed_positions.append((display_index, column))

    return preview, imputed_positions


def split_train_test(
    data: pd.DataFrame,
    train_ratio: float,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """随机划分训练集和测试集"""
    if train_ratio >= 0.999:
        return data.copy().reset_index(drop=True), data.iloc[0:0].copy()

    if len(data) < 2:
        return data.copy().reset_index(drop=True), data.iloc[0:0].copy()

    shuffled = data.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    train_size = int(round(len(shuffled) * train_ratio))
    train_size = max(1, min(len(shuffled) - 1, train_size))
    train = shuffled.iloc[:train_size].copy().reset_index(drop=True)
    test = shuffled.iloc[train_size:].copy().reset_index(drop=True)
    return train, test


def _format_bin_label(column: str, index: int, left: float, right: float) -> str:
    def fmt(value: float) -> str:
        if np.isneginf(value):
            return "-∞"
        if np.isposinf(value):
            return "+∞"
        return f"{value:.3g}"

    return f"{column}_{index}({fmt(left)}, {fmt(right)}]"


def discretize_numeric_columns(
    train: pd.DataFrame,
    test: pd.DataFrame,
    columns: list[str],
    bins: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, Any]], list[str]]:
    """使用训练集分位数对数值列分箱，并把同样边界应用到测试集"""
    train_result = train.copy()
    test_result = test.copy()
    specs: dict[str, dict[str, Any]] = {}
    messages: list[str] = []

    for column in columns:
        train_numeric = pd.to_numeric(train_result[column], errors="coerce")
        unique_count = train_numeric.nunique(dropna=True)

        if unique_count <= 1:
            value_text = "缺失" if train_numeric.dropna().empty else f"{train_numeric.dropna().iloc[0]:.3g}"
            label = f"{column}_单一值({value_text})"
            train_result[column] = label
            if not test_result.empty:
                test_result[column] = label
            specs[column] = {"type": "single", "label": label}
            messages.append(f"字段 `{column}` 只有一个有效数值，已作为单一离散取值处理。")
            continue

        quantile_count = min(max(2, bins), unique_count)
        try:
            _, raw_edges = pd.qcut(
                train_numeric,
                q=quantile_count,
                retbins=True,
                duplicates="drop",
            )
        except ValueError:
            raw_edges = np.linspace(train_numeric.min(), train_numeric.max(), quantile_count + 1)

        internal_edges = sorted(set(float(edge) for edge in raw_edges[1:-1]))
        cut_edges = [-np.inf] + internal_edges + [np.inf]
        labels = [
            _format_bin_label(column, idx + 1, cut_edges[idx], cut_edges[idx + 1])
            for idx in range(len(cut_edges) - 1)
        ]

        train_result[column] = pd.cut(
            train_numeric,
            bins=cut_edges,
            labels=labels,
            include_lowest=True,
            duplicates="drop",
        ).astype(object)
        train_result[column] = train_result[column].fillna(f"{column}_缺失")

        if not test_result.empty:
            test_numeric = pd.to_numeric(test_result[column], errors="coerce")
            test_result[column] = pd.cut(
                test_numeric,
                bins=cut_edges,
                labels=labels,
                include_lowest=True,
                duplicates="drop",
            ).astype(object)
            test_result[column] = test_result[column].fillna(f"{column}_缺失")

        specs[column] = {
            "type": "quantile",
            "edges": cut_edges,
            "labels": labels,
        }
        messages.append(f"字段 `{column}` 已按训练集分位数离散化为 {len(labels)} 箱。")

    return train_result, test_result, specs, messages


def apply_discretization_specs(sample: dict[str, Any], specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """对单条预测样本应用训练阶段的分箱规则"""
    result = dict(sample)
    for column, spec in specs.items():
        if column not in result:
            continue
        if spec["type"] == "single":
            result[column] = spec["label"]
            continue

        try:
            value = float(result[column])
        except (TypeError, ValueError):
            result[column] = f"{column}_缺失"
            continue

        edges = spec["edges"]
        labels = spec["labels"]
        assigned = labels[-1]
        for index in range(len(labels)):
            left, right = edges[index], edges[index + 1]
            if value > left and value <= right:
                assigned = labels[index]
                break
        result[column] = assigned
    return result


def prepare_model_data(
    data: pd.DataFrame,
    target_col: str,
    missing_strategy: str,
    discretize_numeric: bool,
    bins: int,
    train_ratio: float,
    random_state: int = 42,
) -> dict[str, Any]:
    """完成校验、缺失值处理、划分和离散化"""
    cleaned = clean_columns(data)
    errors, warnings = validate_dataset(cleaned, target_col)
    if errors:
        return {"errors": errors, "warnings": warnings}

    processed, missing_messages, imputed_cells = handle_missing_values(cleaned, missing_strategy, target_col)
    if processed.empty:
        return {
            "errors": ["缺失值处理后数据为空，无法训练。"],
            "warnings": warnings,
            "messages": missing_messages,
        }

    numeric_columns = get_numeric_feature_columns(processed, target_col)
    row_id_col = _make_tracking_column(list(processed.columns))
    processed_with_row_id = processed.copy()
    processed_with_row_id[row_id_col] = range(len(processed_with_row_id))
    train, test = split_train_test(processed_with_row_id, train_ratio, random_state=random_state)

    bin_specs: dict[str, dict[str, Any]] = {}
    bin_messages: list[str] = []
    if numeric_columns and discretize_numeric:
        train, test, bin_specs, bin_messages = discretize_numeric_columns(train, test, numeric_columns, bins=bins)
    elif numeric_columns:
        warnings.append(
            "检测到连续数值型字段。原始 ID3 更适合离散属性；当前将数值按字符串取值处理，建议启用分箱。"
        )

    preview_data, preview_imputed_positions = build_processed_preview(train, test, row_id_col, imputed_cells)
    train = train.drop(columns=[row_id_col])
    test = test.drop(columns=[row_id_col])

    for frame in (train, test):
        for column in frame.columns:
            frame[column] = frame[column].astype(str)

    return {
        "errors": [],
        "warnings": warnings,
        "messages": missing_messages + bin_messages,
        "train": train,
        "test": test,
        "numeric_columns": numeric_columns,
        "bin_specs": bin_specs,
        "preview_data": preview_data,
        "preview_imputed_positions": preview_imputed_positions,
    }


def classification_summary(y_true: list[Any], y_pred: list[Any]) -> dict[str, Any]:
    if not y_true:
        return {"accuracy": None, "correct": 0, "wrong": 0, "total": 0}
    true_text = [str(value) for value in y_true]
    pred_text = [str(value) for value in y_pred]
    correct = sum(actual == predicted for actual, predicted in zip(true_text, pred_text))
    total = len(true_text)
    return {
        "accuracy": correct / total if total else None,
        "correct": correct,
        "wrong": total - correct,
        "total": total,
    }


def confusion_matrix_df(y_true: list[Any], y_pred: list[Any]) -> pd.DataFrame:
    labels = sorted({str(value) for value in y_true} | {str(value) for value in y_pred})
    matrix = pd.DataFrame(0, index=labels, columns=labels, dtype=int)
    matrix.index.name = "真实类别"
    matrix.columns.name = "预测类别"
    for actual, predicted in zip(y_true, y_pred):
        matrix.loc[str(actual), str(predicted)] += 1
    return matrix


def dataframe_to_csv_bytes(data: pd.DataFrame) -> bytes:
    return data.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def tree_to_text(tree: dict[str, Any]) -> str:
    """生成适合报告截图的文本决策树"""
    lines: list[str] = []

    def walk(node: dict[str, Any], prefix: str = "", branch: str = "根") -> None:
        if node.get("is_leaf", False):
            lines.append(
                f"{prefix}{branch}: [叶] 类别={node.get('prediction')} "
                f"(样本={node.get('sample_count')}, H={node.get('entropy'):.4f})"
            )
            return

        lines.append(
            f"{prefix}{branch}: [属性] {node.get('split_feature')} "
            f"(样本={node.get('sample_count')}, H={node.get('entropy'):.4f}, "
            f"Gain={node.get('gain'):.4f})"
        )
        for value, child in node.get("children", {}).items():
            walk(child, prefix + "    ", f"{node.get('split_feature')}={value}")

    walk(tree)
    return "\n".join(lines)


def _dot_escape(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def tree_to_dot(tree: dict[str, Any], detailed: bool = False) -> str:
    """生成 Graphviz DOT 字符串"""
    lines = [
        "digraph ID3Tree {",
        "  graph [rankdir=TB, bgcolor=\"transparent\", nodesep=0.45, ranksep=0.55, margin=0.08];",
        "  node [fontname=\"Microsoft YaHei\", fontsize=16, shape=box, style=\"rounded,filled\", color=\"#3f4a5a\", fillcolor=\"#f7f9fc\"];",
        "  edge [fontname=\"Microsoft YaHei\", fontsize=13, color=\"#596579\"];",
    ]
    counter = {"value": 0}

    def next_id() -> str:
        counter["value"] += 1
        return f"node_{counter['value']}"

    def walk(node: dict[str, Any]) -> str:
        node_id = next_id()
        if node.get("is_leaf", False):
            if detailed:
                label = (
                    f"类别 = {_dot_escape(node.get('prediction'))}\\n"
                    f"样本 = {node.get('sample_count')}\\nH = {node.get('entropy'):.4f}"
                )
            else:
                label = f"类别 = {_dot_escape(node.get('prediction'))}"
            lines.append(
                f"  {node_id} [label=\"{label}\", shape=ellipse, fillcolor=\"#e9f7ef\", color=\"#2e7d32\"];"
            )
            return node_id

        if detailed:
            label = (
                f"{_dot_escape(node.get('split_feature'))}\\n"
                f"样本 = {node.get('sample_count')}\\n"
                f"H = {node.get('entropy'):.4f}\\nGain = {node.get('gain'):.4f}"
            )
        else:
            label = _dot_escape(node.get("split_feature"))
        lines.append(f"  {node_id} [label=\"{label}\", fillcolor=\"#eef4ff\", color=\"#2454a6\"];")
        for value, child in node.get("children", {}).items():
            child_id = walk(child)
            lines.append(f"  {node_id} -> {child_id} [label=\"{_dot_escape(value)}\"];")
        return node_id

    walk(tree)
    lines.append("}")
    return "\n".join(lines)


def render_tree_svg(dot_source: str) -> tuple[bytes | None, str | None]:
    """把 DOT 渲染为 SVG 图片"""
    try:
        import graphviz

        svg_bytes = graphviz.Source(dot_source).pipe(format="svg")
        return svg_bytes, None
    except Exception as exc:
        return None, (
            "静态 Graphviz 渲染失败。请确认已安装 graphviz Python 包和 Graphviz 可执行文件 "
            f"`dot`。错误信息：{exc}"
        )
