"""
基于 ID3 算法的可视化决策树分类系统
使用 streamlit 构建可视化展示页面
"""

from __future__ import annotations

import base64
import io

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt

from id3 import fit_id3, predict_batch, predict_one_with_trace, tree_to_rules
from utils import (
    apply_discretization_specs,
    classification_summary,
    clean_columns,
    confusion_matrix_df,
    dataframe_to_csv_bytes,
    get_numeric_feature_columns,
    list_datasets,
    prepare_model_data,
    read_csv_flexible,
    render_tree_svg,
    save_uploaded_dataset,
    tree_to_dot,
    tree_to_text,
)


st.set_page_config(
    page_title="ID3 决策树分类系统",
    layout="wide",
)


st.markdown(
    """
    <style>
    .main .block-container {padding-top: 1.6rem;}
    [data-testid="stTabs"] button[role="tab"] {
        padding: 0.6rem 1.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


DEFAULT_TRAIN_RATIO = 0.8
DEFAULT_MAX_DEPTH = 8
DEFAULT_DISCRETIZE_NUMERIC = True
DEFAULT_RANDOM_STATE = 66
DEFAULTS_VERSION = 3


def figure_to_svg_bytes(fig) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buffer.getvalue()


def show_responsive_svg(svg_bytes: bytes, max_width: int, height: int) -> None:
    encoded_svg = base64.b64encode(svg_bytes).decode("ascii")
    components.html(
        f"""
        <!doctype html>
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                background: transparent;
                overflow: hidden;
            }}
            .chart-wrap {{
                width: 100%;
                max-width: {max_width}px;
                box-sizing: border-box;
            }}
            .chart-wrap img {{
                display: block;
                width: 100%;
                height: auto;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: #ffffff;
                box-sizing: border-box;
            }}
        </style>
        <div class="chart-wrap">
            <img src="data:image/svg+xml;base64,{encoded_svg}" />
        </div>
        """,
        height=height,
        scrolling=False,
    )


def plot_bar_chart(labels: list, values: list, title: str, xlabel: str):
    label_texts = [str(label) for label in labels]
    numeric_values = [float(value) for value in values]
    row_count = max(1, len(label_texts))
    fig_height = min(3.8, max(2.2, 0.42 * row_count + 0.9))
    fig, ax = plt.subplots(figsize=(6.2, fig_height), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    positions = list(range(row_count))
    ax.barh(positions, numeric_values, color="#5b8cc9", edgecolor="#3f6fa9", linewidth=0.6)
    ax.set_yticks(positions)
    ax.set_yticklabels(label_texts, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=8)
    ax.grid(axis="x", linestyle="--", linewidth=0.6, alpha=0.28)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#d1d5db")
    ax.spines["bottom"].set_color("#d1d5db")
    ax.tick_params(axis="x", labelsize=8)

    max_value = max(numeric_values) if numeric_values else 0.0
    right_limit = max_value * 1.16 if max_value > 0 else 1.0
    ax.set_xlim(0, right_limit)
    for position, value in zip(positions, numeric_values):
        label = f"{value:.4f}" if abs(value - round(value)) > 1e-9 else str(int(round(value)))
        ax.text(value + right_limit * 0.018, position, label, va="center", fontsize=8, color="#334155")

    longest_label = max((len(label) for label in label_texts), default=4)
    left_margin = min(0.36, max(0.18, longest_label * 0.012))
    fig.subplots_adjust(left=left_margin, right=0.94, top=0.82, bottom=0.22)
    return fig


def plot_confusion_matrix(matrix: pd.DataFrame):
    label_count = max(1, len(matrix.index), len(matrix.columns))
    fig_size = min(5.4, max(3.4, 0.62 * label_count + 1.7))
    fig, ax = plt.subplots(figsize=(fig_size, fig_size), dpi=130)
    fig.patch.set_facecolor("white")
    image = ax.imshow(matrix.values, cmap="Blues")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_yticks(range(len(matrix.index)))
    ax.set_xticklabels(matrix.columns, rotation=0, fontsize=9)
    ax.set_yticklabels(matrix.index, fontsize=9)
    ax.set_xlabel("预测类别", fontsize=10)
    ax.set_ylabel("真实类别", fontsize=10)
    ax.set_title("混淆矩阵", fontsize=12, fontweight="bold", pad=10)

    max_value = matrix.values.max() if matrix.size else 0
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix.iloc[row, col]
            color = "white" if max_value and value > max_value / 2 else "#1f2937"
            ax.text(col, row, str(value), ha="center", va="center", color=color, fontsize=10)

    for spine in ax.spines.values():
        spine.set_color("#d1d5db")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    return fig


def show_svg_tree_viewer(svg_bytes: bytes) -> None:
    encoded_svg = base64.b64encode(svg_bytes).decode("ascii")
    html = f"""
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            background: #ffffff;
            font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
        }}
        .tree-toolbar {{
            display: flex;
            gap: 8px;
            align-items: center;
            margin-bottom: 8px;
        }}
        .tree-toolbar button {{
            border: 1px solid #cbd5e1;
            background: #f8fafc;
            border-radius: 6px;
            padding: 6px 10px;
            cursor: pointer;
            font-size: 13px;
        }}
        .tree-toolbar span {{
            color: #64748b;
            font-size: 13px;
        }}
        #treeViewport {{
            width: 100%;
            height: 720px;
            overflow: hidden;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background: #ffffff;
            position: relative;
            cursor: grab;
            box-sizing: border-box;
        }}
        #treeViewport.dragging {{
            cursor: grabbing;
        }}
        #treeCanvas {{
            position: absolute;
            left: 0;
            top: 0;
            transform-origin: 0 0;
            will-change: transform;
        }}
        #treeCanvas img {{
            display: block;
            max-width: none;
            user-select: none;
            pointer-events: none;
        }}
        #treeViewport:fullscreen {{
            width: 100vw;
            height: 100vh;
            border-radius: 0;
        }}
    </style>
    <div class="tree-toolbar">
        <button id="zoomIn">放大</button>
        <button id="zoomOut">缩小</button>
        <button id="resetView">重置</button>
        <button id="fitView">适配宽度</button>
        <button id="fullScreen">全屏</button>
        <span>滚轮缩放，按住鼠标拖拽移动</span>
    </div>
    <div id="treeViewport">
        <div id="treeCanvas">
            <img id="treeImage" src="data:image/svg+xml;base64,{encoded_svg}" draggable="false" />
        </div>
    </div>
    <script>
        const viewport = document.getElementById("treeViewport");
        const canvas = document.getElementById("treeCanvas");
        const image = document.getElementById("treeImage");

        let scale = 1;
        let translateX = 16;
        let translateY = 16;
        let dragging = false;
        let lastX = 0;
        let lastY = 0;

        function applyTransform() {{
            canvas.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{scale}})`;
        }}

        function fitToWidth() {{
            if (!image.naturalWidth) return;
            if (viewport.clientWidth < 240) {{
                setTimeout(fitToWidth, 120);
                return;
            }}
            const availableWidth = Math.max(100, viewport.clientWidth - 32);
            scale = Math.min(3, Math.max(0.08, availableWidth / image.naturalWidth));
            translateX = 16;
            translateY = 16;
            applyTransform();
        }}

        function resetView() {{
            scale = 1;
            translateX = 16;
            translateY = 16;
            applyTransform();
        }}

        function zoomAt(clientX, clientY, factor) {{
            const rect = viewport.getBoundingClientRect();
            const x = clientX - rect.left;
            const y = clientY - rect.top;
            const oldScale = scale;
            const newScale = Math.min(5, Math.max(0.08, scale * factor));
            if (newScale === scale) return;

            const imageX = (x - translateX) / oldScale;
            const imageY = (y - translateY) / oldScale;
            scale = newScale;
            translateX = x - imageX * scale;
            translateY = y - imageY * scale;
            applyTransform();
        }}

        viewport.addEventListener("wheel", (event) => {{
            event.preventDefault();
            const factor = event.deltaY < 0 ? 1.12 : 0.88;
            zoomAt(event.clientX, event.clientY, factor);
        }}, {{ passive: false }});

        viewport.addEventListener("mousedown", (event) => {{
            dragging = true;
            lastX = event.clientX;
            lastY = event.clientY;
            viewport.classList.add("dragging");
        }});

        window.addEventListener("mousemove", (event) => {{
            if (!dragging) return;
            translateX += event.clientX - lastX;
            translateY += event.clientY - lastY;
            lastX = event.clientX;
            lastY = event.clientY;
            applyTransform();
        }});

        window.addEventListener("mouseup", () => {{
            dragging = false;
            viewport.classList.remove("dragging");
        }});

        document.getElementById("zoomIn").addEventListener("click", () => {{
            const rect = viewport.getBoundingClientRect();
            zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, 1.2);
        }});
        document.getElementById("zoomOut").addEventListener("click", () => {{
            const rect = viewport.getBoundingClientRect();
            zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, 0.8);
        }});
        document.getElementById("resetView").addEventListener("click", resetView);
        document.getElementById("fitView").addEventListener("click", fitToWidth);
        document.getElementById("fullScreen").addEventListener("click", async () => {{
            try {{
                if (!document.fullscreenElement) {{
                    await viewport.requestFullscreen();
                }} else {{
                    await document.exitFullscreen();
                }}
            }} catch (error) {{
                alert("当前浏览器或页面容器不允许全屏显示。");
            }}
        }});

        image.addEventListener("load", () => {{
            fitToWidth();
            setTimeout(fitToWidth, 100);
            setTimeout(fitToWidth, 500);
        }});
        applyTransform();
    </script>
    """
    components.html(html, height=760, scrolling=False)


def style_imputed_cells(data: pd.DataFrame, imputed_positions: list[tuple[int, str]]):
    position_set = set(imputed_positions)

    def apply_style(_: pd.DataFrame) -> pd.DataFrame:
        styles = pd.DataFrame("", index=data.index, columns=data.columns)
        for row_index, column in position_set:
            if row_index in styles.index and column in styles.columns:
                styles.at[row_index, column] = (
                    "background-color: #fee2e2; color: #991b1b; font-weight: 600;"
                )
        return styles

    return data.style.apply(apply_style, axis=None)


def show_dataset_overview(data: pd.DataFrame, target_col: str | None, result: dict | None = None) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("样本数", len(data))
    col2.metric("字段数", len(data.columns))
    col3.metric("缺失值", int(data.isna().sum().sum()))

    st.write("字段名：", "、".join([f"`{column}`" for column in data.columns]))
    if result:
        for warning in result.get("warnings", []):
            st.warning(warning)
        for message in result.get("messages", []):
            st.info(message)

    preview_data = result.get("preview_data") if result else None
    if isinstance(preview_data, pd.DataFrame) and not preview_data.empty:
        split_text = "第一折训练集或第一折验证集" if result.get("use_cross_validation") else "训练集还是测试集"
        st.caption(f"下表展示缺失值和连续值预处理后的数据；`数据划分` 表示该行进入{split_text}。")
        display_data = preview_data.copy()
        if result.get("use_cross_validation") and "数据划分" in display_data.columns:
            display_data["数据划分"] = display_data["数据划分"].replace(
                {"训练集": "第一折训练集", "测试集": "第一折验证集"}
            )
        imputed_positions = [
            (row_index, column)
            for row_index, column in result.get("preview_imputed_positions", [])
            if row_index < len(display_data)
        ]
        if imputed_positions:
            st.dataframe(style_imputed_cells(display_data, imputed_positions), use_container_width=True)
        else:
            st.dataframe(display_data, use_container_width=True)
    else:
        st.dataframe(data, use_container_width=True)

    if target_col and target_col in data.columns:
        st.subheader("类别分布")
        counts = data[target_col].astype(str).value_counts().rename_axis("类别").reset_index(name="数量")
        chart_col, _ = st.columns([0.55, 0.45])
        with chart_col:
            show_responsive_svg(
                figure_to_svg_bytes(
                    plot_bar_chart(
                        counts["类别"].tolist(),
                        counts["数量"].tolist(),
                        title="类别分布",
                        xlabel="样本数量",
                    )
                ),
                max_width=680,
                height=min(420, max(260, 70 + len(counts) * 42)),
            )


def show_gain_history(gain_history: list[dict]) -> None:
    if not gain_history:
        st.info("当前树没有可展开的信息增益计算过程，可能是数据已经属于同一类别。")
        return

    gain_df = pd.DataFrame(gain_history)
    display_df = gain_df.rename(
        columns={
            "node_path": "节点路径",
            "depth": "深度",
            "feature": "候选属性",
            "base_entropy": "划分前熵 H(U)",
            "conditional_entropy": "条件熵 H(U|V)",
            "information_gain": "信息增益 I(U,V)",
            "value_count": "属性取值数",
            "selected": "是否选中",
        }
    )
    numeric_cols = ["划分前熵 H(U)", "条件熵 H(U|V)", "信息增益 I(U,V)"]
    for column in numeric_cols:
        display_df[column] = display_df[column].map(lambda value: f"{value:.6f}")
    display_df["是否选中"] = display_df["是否选中"].map(lambda value: "是" if value else "否")

    st.dataframe(display_df, use_container_width=True)

    root_rows = gain_df[gain_df["node_path"] == "根"].sort_values("information_gain", ascending=False)
    if not root_rows.empty:
        st.subheader("根节点候选属性信息增益")
        chart_col, _ = st.columns([0.55, 0.45])
        with chart_col:
            show_responsive_svg(
                figure_to_svg_bytes(
                    plot_bar_chart(
                        root_rows["feature"].tolist(),
                        root_rows["information_gain"].tolist(),
                        title="根节点信息增益",
                        xlabel="信息增益",
                    )
                ),
                max_width=680,
                height=min(420, max(260, 80 + len(root_rows) * 42)),
            )


def show_tree_and_rules(model: dict, detailed_tree: bool) -> None:
    tree = model["tree"]
    dot_source = tree_to_dot(tree, detailed=detailed_tree)
    svg_bytes, error = render_tree_svg(dot_source)
    if svg_bytes:
        show_svg_tree_viewer(svg_bytes)
    else:
        st.warning(error)
        with st.expander("查看 DOT 源码"):
            st.code(dot_source, language="dot")

    st.subheader("IF-THEN 分类规则")
    rules = tree_to_rules(tree)
    if rules:
        for index, rule in enumerate(rules, start=1):
            st.code(f"{index}. {rule}", language="text")
    else:
        st.info("当前决策树没有可导出的规则。")

    with st.expander("文本决策树", expanded=False):
        st.code(tree_to_text(tree), language="text")


def run_k_fold_cross_validation(
    first_train: pd.DataFrame,
    first_valid: pd.DataFrame,
    target_col: str,
    min_gain: float,
    max_depth: int,
    random_state: int,
    folds: int = 5,
) -> dict:
    if first_train.empty or first_valid.empty:
        return {"error": "样本数不足 2 条，无法进行交叉验证。"}

    first_train = first_train.copy().reset_index(drop=True)
    first_valid = first_valid.copy().reset_index(drop=True)
    effective_folds = min(folds, len(first_train) + len(first_valid))
    rows = []
    total_correct = 0
    total_count = 0
    accuracies = []

    def evaluate_fold(fold_index: int, train_data: pd.DataFrame, valid_data: pd.DataFrame) -> None:
        nonlocal total_correct, total_count
        model = fit_id3(
            train_data,
            target_col=target_col,
            min_gain=float(min_gain),
            max_depth=int(max_depth),
        )
        predictions = predict_batch(model["tree"], valid_data[model["features"]], default_class=model["global_majority"])
        summary = classification_summary(valid_data[target_col].tolist(), predictions)
        accuracy = summary["accuracy"]
        if accuracy is not None:
            accuracies.append(accuracy)
        total_correct += summary["correct"]
        total_count += summary["total"]
        rows.append(
            {
                "折次": fold_index,
                "训练样本数": len(train_data),
                "验证样本数": len(valid_data),
                "Accuracy": accuracy,
                "预测正确": summary["correct"],
                "预测错误": summary["wrong"],
            }
        )

    evaluate_fold(1, first_train, first_valid)

    remaining_fold_count = effective_folds - 1
    if remaining_fold_count > 0:
        shuffled_train = first_train.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
        fold_sizes = [len(shuffled_train) // remaining_fold_count] * remaining_fold_count
        for index in range(len(shuffled_train) % remaining_fold_count):
            fold_sizes[index] += 1

        start = 0
        for offset, fold_size in enumerate(fold_sizes, start=2):
            end = start + fold_size
            valid_data = shuffled_train.iloc[start:end].copy().reset_index(drop=True)
            train_data = pd.concat(
                [shuffled_train.iloc[:start], shuffled_train.iloc[end:], first_valid],
                ignore_index=True,
            )
            start = end
            if not valid_data.empty and not train_data.empty:
                evaluate_fold(offset, train_data, valid_data)

    return {
        "folds": len(rows),
        "mean_accuracy": sum(accuracies) / len(accuracies) if accuracies else None,
        "overall_accuracy": total_correct / total_count if total_count else None,
        "rows": rows,
    }


def show_cross_validation_result(cv_result: dict | None) -> None:
    if not cv_result:
        return

    st.subheader("五折交叉验证")
    if cv_result.get("error"):
        st.warning(cv_result["error"])
        return

    col_mean, col_overall, col_count = st.columns(3)
    mean_accuracy = cv_result.get("mean_accuracy")
    overall_accuracy = cv_result.get("overall_accuracy")
    col_mean.metric("平均 Accuracy", f"{mean_accuracy:.2%}" if mean_accuracy is not None else "-")
    col_overall.metric("整体 Accuracy", f"{overall_accuracy:.2%}" if overall_accuracy is not None else "-")
    col_count.metric("折数", cv_result.get("folds", 0))
    st.caption("启用五折时，当前页面展示的决策树和测试评估来自第一折；下表用于汇总五折验证结果。")

    cv_df = pd.DataFrame(cv_result.get("rows", []))
    if not cv_df.empty:
        cv_df["Accuracy"] = cv_df["Accuracy"].map(lambda value: f"{value:.2%}" if value is not None else "-")
        st.dataframe(cv_df, use_container_width=True)


def show_prediction_and_evaluation(result: dict) -> None:
    model = result["model"]
    test = result["test"]
    target_col = model["target_col"]
    features = model["features"]

    st.subheader("单条样本预测")
    with st.form("single_prediction_form"):
        input_values = {}
        input_errors = []
        cols = st.columns(2)
        for index, feature in enumerate(features):
            with cols[index % 2]:
                if feature in result["bin_specs"]:
                    input_values[feature] = st.number_input(f"{feature}", value=0.0, key=f"num_{feature}")
                else:
                    options = list(model["feature_values"].get(feature, []))
                    if options:
                        unknown_option = "未见过的取值"
                        selected = st.selectbox(f"{feature}", options + [unknown_option], key=f"sel_{feature}")
                        if selected == unknown_option:
                            input_values[feature] = "__UNKNOWN_VALUE__"
                        else:
                            input_values[feature] = selected
                    else:
                        input_values[feature] = ""
                        input_errors.append(f"`{feature}` 没有可选训练取值。")

        submitted = st.form_submit_button("预测单条样本")
        if submitted:
            if input_errors:
                for error in input_errors:
                    st.warning(error)
            else:
                prepared_sample = apply_discretization_specs(input_values, result["bin_specs"])
                prediction, trace = predict_one_with_trace(
                    model["tree"],
                    prepared_sample,
                    default_class=model["global_majority"],
                )
                st.success(f"预测类别：{prediction}")
                st.dataframe(pd.DataFrame(trace), use_container_width=True)
                st.caption("离散特征选择“未见过的取值”时，会在对应决策节点触发当前节点多数类回退；连续数值特征会先按训练阶段的分箱规则转换后再预测。")

    if result.get("cv_result"):
        st.divider()
        show_cross_validation_result(result["cv_result"])

    st.divider()
    if result.get("use_cross_validation"):
        st.subheader("第一折验证集批量预测与评估")
        st.caption("当前决策树使用第一折训练集训练，本表使用第一折验证集评估。")
    else:
        st.subheader("测试集批量预测与评估")
    if test.empty:
        if result.get("use_cross_validation"):
            st.info("当前没有第一折验证集，无法进行五折验证。")
        else:
            st.info("当前没有测试集。若需要评估，请将训练集比例调低；若用于课件复现，可使用全部数据训练。")
        return

    if len(test) < 20:
        label = "第一折验证集" if result.get("use_cross_validation") else "测试集"
        st.warning(f"{label}样本数不足 20 条，Accuracy 波动可能较大。")

    predictions = predict_batch(model["tree"], test[features], default_class=model["global_majority"])
    result_df = test.copy()
    result_df["预测类别"] = predictions
    result_df["是否正确"] = result_df[target_col].astype(str) == result_df["预测类别"].astype(str)

    summary = classification_summary(result_df[target_col].tolist(), predictions)
    col1, col2, col3 = st.columns(3)
    col1.metric("Accuracy", f"{summary['accuracy']:.2%}" if summary["accuracy"] is not None else "-")
    col2.metric("预测正确", summary["correct"])
    col3.metric("预测错误", summary["wrong"])

    st.dataframe(result_df, use_container_width=True)
    st.download_button(
        "导出预测结果 CSV",
        data=dataframe_to_csv_bytes(result_df),
        file_name="id3_predictions.csv",
        mime="text/csv",
    )

    matrix = confusion_matrix_df(result_df[target_col].tolist(), predictions)
    st.subheader("混淆矩阵")
    show_responsive_svg(
        figure_to_svg_bytes(plot_confusion_matrix(matrix)),
        max_width=560,
        height=520,
    )


def load_sidebar_data() -> tuple[pd.DataFrame | None, str]:
    st.sidebar.header("数据输入")
    datasets = list_datasets()
    data_source = st.sidebar.radio("数据来源", ["选择已有数据集", "上传 CSV 数据集"])
    data: pd.DataFrame | None = None
    dataset_name = ""

    if data_source == "选择已有数据集":
        if not datasets:
            st.sidebar.warning("datasets 目录下还没有 CSV 数据集。")
            return None, dataset_name
        selected_name = st.sidebar.selectbox("已有数据集", list(datasets.keys()))
        dataset_name = selected_name
        try:
            data = clean_columns(read_csv_flexible(datasets[selected_name]))
        except Exception as exc:
            st.sidebar.error(str(exc))
            data = None
    else:
        uploaded = st.sidebar.file_uploader("上传 CSV 文件", type=["csv"])
        if uploaded is not None:
            file_bytes = uploaded.getvalue()
            dataset_name = uploaded.name.rsplit(".", 1)[0]
            try:
                data = clean_columns(read_csv_flexible(file_bytes))
            except Exception as exc:
                st.sidebar.error(str(exc))
                data = None

            st.sidebar.caption("CSV 要求：第一行为字段名，至少包含 1 个特征列和 1 个目标分类列。")
            save_name = st.sidebar.text_input("保存为数据集名称", value=dataset_name)
            if st.sidebar.button("保存到 datasets"):
                try:
                    target = save_uploaded_dataset(file_bytes, save_name)
                    st.sidebar.success(f"已保存：{target.name}")
                except Exception as exc:
                    st.sidebar.error(f"保存失败：{exc}")
        else:
            st.sidebar.info("上传 CSV 后可直接训练，也可保存到 datasets 目录。")

    return data, dataset_name


def train_model_from_data(
    data: pd.DataFrame,
    dataset_name: str,
    target_col: str,
    missing_strategy: str,
    discretize_numeric: bool,
    bins: int,
    train_ratio: float,
    min_gain: float,
    max_depth: int,
    random_state: int,
    use_cross_validation: bool,
) -> tuple[dict | None, list[str]]:
    if use_cross_validation:
        train_ratio = 0.8

    prepared = prepare_model_data(
        data,
        target_col=target_col,
        missing_strategy=missing_strategy,
        discretize_numeric=discretize_numeric,
        bins=bins,
        train_ratio=train_ratio,
        random_state=random_state,
    )
    if prepared.get("errors"):
        return None, prepared["errors"]

    model = fit_id3(
        prepared["train"],
        target_col=target_col,
        min_gain=float(min_gain),
        max_depth=int(max_depth),
    )
    cv_result = None
    if use_cross_validation:
        cv_result = run_k_fold_cross_validation(
            prepared["train"],
            prepared["test"],
            target_col=target_col,
            min_gain=float(min_gain),
            max_depth=int(max_depth),
            random_state=int(random_state),
            folds=5,
        )
    return {
        "dataset_name": dataset_name,
        "target_col": target_col,
        "train": prepared["train"],
        "test": prepared["test"],
        "model": model,
        "warnings": prepared["warnings"],
        "messages": prepared["messages"],
        "numeric_columns": prepared["numeric_columns"],
        "bin_specs": prepared["bin_specs"],
        "preview_data": prepared.get("preview_data"),
        "preview_imputed_positions": prepared.get("preview_imputed_positions", []),
        "max_depth": int(max_depth),
        "use_cross_validation": bool(use_cross_validation),
        "cv_result": cv_result,
    }, []


def init_demo_defaults(force: bool = False) -> None:
    defaults = {
        "train_ratio": DEFAULT_TRAIN_RATIO,
        "max_depth": DEFAULT_MAX_DEPTH,
        "discretize_numeric": DEFAULT_DISCRETIZE_NUMERIC,
        "missing_strategy": "众数填充",
        "bins": 3,
        "min_gain": 1e-12,
        "random_state": DEFAULT_RANDOM_STATE,
    }
    for key, value in defaults.items():
        if force or key not in st.session_state:
            st.session_state[key] = value


def make_training_signature(
    dataset_name: str,
    data: pd.DataFrame,
    target_col: str,
    missing_strategy: str,
    discretize_numeric: bool,
    bins: int,
    train_ratio: float,
    min_gain: float,
    max_depth: int,
    random_state: int,
    use_cross_validation: bool,
) -> tuple:
    return (
        dataset_name,
        tuple(data.columns),
        data.shape,
        target_col,
        missing_strategy,
        bool(discretize_numeric),
        int(bins),
        round(float(train_ratio), 4),
        float(min_gain),
        int(max_depth),
        int(random_state),
        bool(use_cross_validation),
    )


def main() -> None:
    st.title("基于 ID3 算法的可视化决策树分类系统")
    st.caption("从零实现 ID3 决策树：直观展示信息增益计算、树结构、规则和预测结果。")

    if st.session_state.get("_defaults_version") != DEFAULTS_VERSION:
        init_demo_defaults(force=True)
        st.session_state["_defaults_version"] = DEFAULTS_VERSION
        st.session_state.pop("trained_result", None)
        st.session_state.pop("_training_signature", None)

    data, dataset_name = load_sidebar_data()

    target_col = None
    train_clicked = False
    if data is not None and not data.empty:
        dataset_context = (dataset_name, tuple(data.columns))
        if st.session_state.get("_dataset_context") != dataset_context:
            init_demo_defaults(force=True)
            st.session_state["_dataset_context"] = dataset_context
            st.session_state.pop("trained_result", None)
            st.session_state.pop("_training_signature", None)
            st.session_state.pop("target_col_select", None)
            st.session_state["use_cross_validation"] = len(data) < 20
        init_demo_defaults(force=False)
        if "use_cross_validation" not in st.session_state:
            st.session_state["use_cross_validation"] = len(data) < 20

        st.sidebar.header("训练设置")
        columns = list(data.columns)
        target_col = st.sidebar.selectbox(
            "目标分类列",
            columns,
            index=len(columns) - 1,
            key="target_col_select",
        )
        missing_strategy = st.sidebar.selectbox(
            "缺失值处理",
            ["众数填充", "删除缺失行"],
            key="missing_strategy",
        )

        numeric_columns = get_numeric_feature_columns(data, target_col)
        if numeric_columns:
            st.sidebar.warning("检测到连续数值字段：" + "、".join(numeric_columns))
        discretize_numeric = st.sidebar.checkbox(
            "对连续数值字段进行分位数分箱",
            key="discretize_numeric",
        )
        bins = st.sidebar.slider(
            "分箱数量",
            min_value=2,
            max_value=6,
            disabled=not discretize_numeric,
            key="bins",
        )
        use_cross_validation = st.sidebar.checkbox(
            "启用五折交叉验证",
            key="use_cross_validation",
        )
        if use_cross_validation:
            st.session_state["train_ratio"] = 0.8
        train_ratio = st.sidebar.slider(
            "训练集比例",
            min_value=0.5,
            max_value=1.0,
            step=0.05,
            disabled=use_cross_validation,
            key="train_ratio",
        )
        if use_cross_validation:
            train_ratio = 0.8
            st.sidebar.caption("五折交叉验证固定为 80% 训练、20% 验证；当前展示第一折。")

        with st.sidebar.expander("高级参数"):
            max_depth = st.slider(
                "最大树深度",
                min_value=1,
                max_value=20,
                key="max_depth",
            )
            min_gain = st.number_input(
                "最小信息增益阈值",
                min_value=0.0,
                format="%.12f",
                key="min_gain",
            )
            random_state = st.number_input("随机种子", min_value=0, step=1, key="random_state")

        train_clicked = st.sidebar.button("训练 ID3 决策树", type="primary")
    else:
        missing_strategy = "众数填充"
        discretize_numeric = False
        bins = 3
        train_ratio = DEFAULT_TRAIN_RATIO
        min_gain = 1e-12
        max_depth = DEFAULT_MAX_DEPTH
        random_state = DEFAULT_RANDOM_STATE
        use_cross_validation = False

    if data is not None and not data.empty and target_col is not None:
        training_signature = make_training_signature(
            dataset_name,
            data,
            target_col,
            missing_strategy,
            discretize_numeric,
            bins,
            train_ratio,
            min_gain,
            int(max_depth),
            int(random_state),
            bool(use_cross_validation),
        )
    else:
        training_signature = None

    should_train = (
        data is not None
        and not data.empty
        and target_col is not None
        and (train_clicked or st.session_state.get("_training_signature") != training_signature)
    )

    if should_train:
        trained_result, errors = train_model_from_data(
            data,
            dataset_name=dataset_name,
            target_col=target_col,
            missing_strategy=missing_strategy,
            discretize_numeric=discretize_numeric,
            bins=bins,
            train_ratio=train_ratio,
            min_gain=float(min_gain),
            max_depth=int(max_depth),
            random_state=int(random_state),
            use_cross_validation=bool(use_cross_validation),
        )
        if errors:
            st.session_state.pop("trained_result", None)
            st.session_state.pop("_training_signature", None)
            for error in errors:
                st.error(error)
        else:
            st.session_state["trained_result"] = trained_result
            st.session_state["_training_signature"] = training_signature
            if train_clicked:
                st.success("ID3 决策树训练完成。")

    result = st.session_state.get("trained_result")
    if result and training_signature and st.session_state.get("_training_signature") != training_signature:
        st.warning("当前展示的是上一次训练结果。若更换了数据集或目标列，请重新点击训练。")

    page_options = ["数据概览", "算法过程", "决策树", "预测评估"]
    if st.session_state.get("active_page") not in page_options:
        st.session_state["active_page"] = page_options[0]

    page_cols = st.columns(len(page_options))
    for page, column in zip(page_options, page_cols):
        with column:
            is_active = st.session_state["active_page"] == page
            if st.button(
                page,
                key=f"page_{page}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ) and not is_active:
                st.session_state["active_page"] = page
                st.rerun()

    active_page = st.session_state["active_page"]

    if active_page == "数据概览":
        if data is None:
            st.info("请在左侧选择内置数据集或上传 CSV 数据集。")
        else:
            st.header("数据集预览")
            show_dataset_overview(data, target_col, result)

    elif active_page == "算法过程":
        st.header("ID3 算法原理")
        st.latex(r"H(U)=-\sum_i P(u_i)\log_2P(u_i)")
        st.latex(r"H(U|V)=-\sum_j P(v_j)\sum_i P(u_i|v_j)\log_2P(u_i|v_j)")
        st.latex(r"I(U,V)=H(U)-H(U|V)")
        st.markdown(
            """
            ID3 在每个节点计算所有候选属性的信息增益，选择信息增益最大的属性作为当前决策节点，
            然后对各属性取值对应的子集递归建树。
            """
        )
        if result:
            st.subheader("信息增益计算过程")
            if result.get("use_cross_validation"):
                st.caption("该信息增益表来自第一折训练集上的 ID3 建树过程。")
            show_gain_history(result["model"]["gain_history"])
        else:
            st.info("训练后将显示每个节点的候选属性信息增益表。")

    elif active_page == "决策树":
        col_title, col_toggle = st.columns([0.7, 0.3])
        with col_title:
            st.header("决策树可视化")
        with col_toggle:
            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
            detailed_tree = st.checkbox("显示详细节点信息", value=False, key="tree_detailed")

        if result:
            if result.get("use_cross_validation"):
                st.caption("当前决策树来自五折交叉验证第一折的训练集。")
            show_tree_and_rules(result["model"], detailed_tree=detailed_tree)
        else:
            st.info("训练后将显示 Graphviz 决策树、文本树和 IF-THEN 规则。")

    else:
        st.header("预测与评估")
        if result:
            if result.get("use_cross_validation"):
                st.write("第一折训练集样本数：", len(result["train"]), "；第一折验证集样本数：", len(result["test"]))
            else:
                st.write("训练集样本数：", len(result["train"]), "；测试集样本数：", len(result["test"]))
            show_prediction_and_evaluation(result)
        else:
            st.info("训练后可进行单条样本预测和测试集批量评估。")


if __name__ == "__main__":
    main()
