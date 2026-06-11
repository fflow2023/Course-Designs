# 基于 ID3 算法的可视化决策树分类系统

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行命令

```bash
streamlit run app.py
```

启动后浏览器会打开本地页面。若没有自动打开，可查看终端输出中的 Local URL。

## 项目结构

```text
DM_ID3/
├── app.py                  # Streamlit 主程序
├── id3.py                  # ID3 算法核心实现
├── utils.py                # 数据处理、评估、可视化辅助函数
├── datasets/
│   └── PlayTennis.csv       # 示例数据集
├── requirements.txt
└── README.md
```

## CSV 数据格式要求

- 第一行为字段名。
- 至少包含 1 个特征列和 1 个目标分类列。
- 每一行是一条样本。
- 推荐使用 UTF-8 或 GBK 编码。
- 原始 ID3 更适合离散属性。系统把“所有非缺失值均为数值，且不同取值超过 3 种”的字段识别为连续数值字段，可在界面中手动启用分位数分箱。

示例：
```csv
天气,气温,湿度,风,类别
晴,热,高,无,N
多云,热,高,无,P
雨,适中,高,有,N
```