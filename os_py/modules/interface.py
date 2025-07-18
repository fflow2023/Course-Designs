# modules\interface.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from modules.disk import Disk
from modules.memory import MemoryManager
from modules.process import Process
from modules.scheduler import Scheduler
# Streamlit 页面


# 自定义 CSS 样式 (略)
def inject_custom_css():
    st.markdown(
        """
        <style>
        /* 侧边栏整体样式 */
        .css-1d391kg {
            background: linear-gradient(145deg, #6a11cb, #2575fc); /* 蓝紫色渐变背景 */
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3); /* 更强的阴影 */
            border: 1px solid rgba(255, 255, 255, 0.3); /* 边框 */
            backdrop-filter: blur(10px); /* 毛玻璃效果 */
        }

        /* 侧边栏标题样式 */
        .sidebar .sidebar-content .sidebar-title {
            font-size: 28px;
            font-weight: bold;
            color: white; /* 白色文字 */
            margin-bottom: 25px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2); /* 文字阴影 */
        }

        /* 侧边栏按钮样式 */
        .stButton > button {
            width: 100%;
            background: linear-gradient(145deg, #6a11cb, #2575fc); /* 蓝紫色渐变背景 */
            color: white; /* 按钮文字颜色为白色 */
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin-bottom: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2); /* 按钮阴影 */
            transition: all 0.3s ease; /* 平滑过渡 */
        }

        /* 按钮悬停效果 */
        .stButton > button:hover {
            background: linear-gradient(145deg, #2575fc, #6a11cb); /* 悬停时渐变反转 */
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.3); /* 悬停时阴影增强 */
            transform: translateY(-2px); /* 悬停时按钮上移 */
            color: white !important; /* 确保悬停时文字颜色保持为白色 */
        }

        /* 侧边栏分隔线样式 */
        .sidebar-divider {
            border-top: 2px solid rgba(255, 255, 255, 0.2); /* 更柔和的分隔线 */
            margin: 25px 0;
        }

        /* 侧边栏按钮图标样式 */
        .sidebar .stButton > button::before {
            content: "➤"; /* 添加箭头图标 */
            margin-right: 10px;
            font-size: 18px;
            transition: transform 0.3s ease; /* 图标动画 */
        }

        /* 按钮悬停时图标动画 */
        .sidebar .stButton > button:hover::before {
            transform: translateX(5px); /* 悬停时图标右移 */
        }

        /* 侧边栏整体动画 */
        .sidebar {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        /* 侧边栏悬停时整体效果 */
        .sidebar:hover {
            transform: translateX(5px); /* 悬停时侧边栏右移 */
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3); /* 悬停时阴影增强 */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
st.markdown(
    """
    <style>
    /* 自定义正方形按钮样式 */
    .square-button {
        width: 38px !important;  /* 按钮宽度 */
        height: 38px !important; /* 按钮高度，与宽度一致 */
        padding: 0 !important;   /* 去除内边距 */
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;      /* 圆角 */
        font-size: 18px;         /* 图标大小 */
    }
    </style>
    """,
    unsafe_allow_html=True
)
def inject_custm_css():
    st.markdown(
        """
        <style>
        /* 主界面整体样式 */
        .main-container {
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        /* 标题样式 */
        .main-title {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
        }

        /* 图表容器样式 */
        .chart-container {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        /* 表格样式 */
        .data-table {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        /* 侧边栏样式 */
        .sidebar .sidebar-content {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 10px;
        }

        /* 按钮样式 */
        .stButton > button {
            background-color: #3498db;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }

        .stButton > button:hover {
            background-color: #2980b9;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# 主界面
def main_interface(disk, memory_manager, scheduler):
    # 注入自定义 CSS
    inject_custm_css()

    # 主界面标题
    st.markdown('<div class="main-title">🏠 主界面</div>', unsafe_allow_html=True)

    # 磁盘占用和内存占用的图表并排
    st.markdown('<div class="chart-container">📊 磁盘与内存占用情况</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        # 计算空闲块总数（基于空闲盘块表）
        free_blocks = 0
        for start, length in disk.free_block_list:
            free_blocks += length
            
        used_blocks = disk.block_count - free_blocks
        
        disk_usage = {
            "已使用": used_blocks,
            "空闲": free_blocks,
        }
        df_disk = pd.DataFrame({
            "Category": list(disk_usage.keys()),
            "占用情况": list(disk_usage.values()),
        })
        fig_disk = px.pie(df_disk, values="占用情况", names="Category", title="磁盘占用情况 (连续分配)")
        st.plotly_chart(fig_disk, use_container_width=True)

    with col2:
        memory_manager.show_mem()

    # 运行队列
    st.markdown('<div class="chart-container">🏃‍♂️ 运行队列</div>', unsafe_allow_html=True)
    if scheduler.running_process:
        running_data = [
            {
                "名称": process.name,
                "PID": process.pid,
                "优先权": process.priority,
                "所占空间": process.memory_required,
            }
            for process in scheduler.running_process
        ]
        df_running = pd.DataFrame(running_data)
        st.dataframe(df_running, use_container_width=True)
    else:
        st.write("当前没有运行的进程。")

    # 页表显示
    st.markdown('<div class="chart-container">📄 页表情况</div>', unsafe_allow_html=True)
    memory_manager.show_page()
    # 磁盘显示
    st.markdown('<div class="chart-container">🗺️ 磁盘分配图</div>', unsafe_allow_html=True)
    disk.show_disk_allocation_map()

def inject_top_bar_css():
    st.markdown(
        """
        <style>
        /* 上边栏样式 */
        .top-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(145deg, #FFD700, #FFA500) !important; /* 金黄色渐变 */
            padding: 10px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        /* 图标样式 */
        .top-bar-icon {
            font-size: 40px; /* 调整图标大小 */
            margin-right: 10px;
        }

        /* 欢迎文字样式 */
        .top-bar-welcome {
            font-size: 24px;
            font-weight: bold;
            color: black;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }

        /* 时间显示样式 */
        .top-bar-time {
            font-size: 18px;
            font-weight: bold;
            color: black;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        """,
        unsafe_allow_html=True,
    )

def top_bar(icon_path):
    # 注入上边栏样式
    inject_top_bar_css()

    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    windows_icon = '<span class="custom-icon">NEUQ-OS</span>'
    # 使用 st.markdown 包裹上边栏内容
    st.markdown(
        f"""
        <div class="top-bar">
            <div class="col1">
                <span class="top-bar-icon">{windows_icon}</span>
            </div>
            <div class="col2">
                <div class="top-bar-welcome">欢迎使用模拟版操作系统</div>
            </div>
            <div class="col3">
                <div class="top-bar-time">{current_time}<a/div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
from datetime import datetime
# 在 streamlit_interface 函数中调用上边栏
def inject_dialog_css():
    st.markdown(
        """
        <style>
        /* 弹窗整体样式 */
        .stDialog {
            background-color: #ffffff; /* 弹窗背景颜色 */
            border-radius: 10px; /* 圆角 */
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* 阴影效果 */
            padding: 20px; /* 内边距 */
            border: 1px solid #e0e0e0; /* 边框 */
        }

        /* 弹窗标题样式 */
        .stDialog .stDialogTitle {
            font-size: 24px; /* 标题字体大小 */
            font-weight: bold; /* 标题字体加粗 */
            color: #2c3e50; /* 标题颜色 */
            margin-bottom: 15px; /* 标题与内容之间的间距 */
        }

        /* 弹窗内容样式 */
        .stDialog .stDialogContent {
            font-size: 16px; /* 内容字体大小 */
            color: #333333; /* 内容字体颜色 */
            line-height: 1.6; /* 行高 */
        }

        /* 弹窗按钮样式 */
        .stDialog .stButton button {
            background-color: #3498db; /* 按钮背景颜色 */
            color: white; /* 按钮文字颜色 */
            border-radius: 5px; /* 按钮圆角 */
            padding: 10px 20px; /* 按钮内边距 */
            font-size: 16px; /* 按钮字体大小 */
            transition: background-color 0.3s ease; /* 按钮悬停效果 */
        }

        /* 按钮悬停效果 */
        .stDialog .stButton button:hover {
            background-color: #2980b9; /* 按钮悬停时的背景颜色 */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
def streamlit_interface(disk, memory_manager, scheduler):
    inject_dialog_css()  # 注入弹窗样式
    inject_top_bar_css()
    inject_custom_css()

    # 添加上边栏
    icon_path = "wr.png"
    top_bar(icon_path)

    # 检查是否已经添加了初始化进程
    if 'init_process_added' not in st.session_state:
        # 添加两个初始化进程
        init_process1 = Process(priority=20, memory_required=64, pid=9998, name="Init Process 1")
        init_process2 = Process(priority=20, memory_required=64, pid=9999, name="Init Process 2")

        # 分配内存给初始化进程
        memory_manager.allocate_to_process(init_process1.pid, init_process1.memory_required)
        memory_manager.allocate_to_process(init_process2.pid, init_process2.memory_required)

        # 将初始化进程添加到调度器的运行队列
        scheduler.running_process.append(init_process1)
        scheduler.running_process.append(init_process2)

        # 标记初始化进程已添加
        st.session_state["init_process_added"] = True

    # 侧边栏菜单
    st.sidebar.markdown('<div class="sidebar-title">📂 功能模块</div>', unsafe_allow_html=True)

    # 使用按钮切换功能模块
    if st.sidebar.button("🏠 主界面"):
        st.session_state["operation"] = "主界面"
    if st.sidebar.button("📁 文件系统"):
        st.session_state["operation"] = "文件系统"
    if st.sidebar.button("🧠 内存管理"):
        st.session_state["operation"] = "内存管理"
    if st.sidebar.button("⚙️ 进程操作"):
        st.session_state["operation"] = "进程操作"

    # 获取当前选择的功能模块
    operation = st.session_state.get("operation", "主界面")

    if operation == "主界面":
        main_interface(disk, memory_manager, scheduler)
   
    elif operation == "文件系统":
        st.title("💾 文件系统")

        st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.sidebar.markdown('<div class="sidebar-title">📂 文件/目录操作</div>', unsafe_allow_html=True)
        
        file_operations = [
            "🌳 显示目录结构", 
            "➕ 创建目录", 
            "➕ 创建文件", 
            "📄 操作文件",
            "🗑️ 删除目录", 
            "🗑️ 删除文件",
            "🗺️ 查看磁盘分配图"
        ]
        
        file_operation = st.sidebar.radio(
            "选择操作:", 
            file_operations, 
            key="file_op_radio"
        )

        # ==============================================================================
        # UI 全面升级，使用下拉框选择路径
        # ==============================================================================
        
        if file_operation == "🌳 显示目录结构":
            st.subheader("🌳 目录结构 (树形视图)")
            with st.container(border=True):
                # 调用已修复的 disk.show_directory()
                disk.show_directory()

        elif file_operation == "➕ 创建目录":
            st.subheader("📁 创建新目录")
            with st.form("create_dir_form"):
                # 获取所有现有目录路径
                all_dirs = disk.get_all_directory_paths()
                # 使用下拉框选择父目录
                parent_path = st.selectbox("选择父目录", options=all_dirs, help="新目录将在此目录下创建。")
                new_dir_name = st.text_input("新目录名", placeholder="例如: my_new_folder")
                
                submitted = st.form_submit_button("创建目录")
                if submitted:
                    if parent_path and new_dir_name:
                        # 拼接完整路径
                        full_path = f"{parent_path.rstrip('/')}/{new_dir_name}"
                        disk.create_directory(full_path)
                        st.session_state["Disk"] = disk
                        st.rerun()
                    else:
                        st.warning("父目录和新目录名都不能为空!")

        elif file_operation == "🗑️ 删除目录":
            st.subheader("🗑️ 删除空目录")
            
            # 单独获取可删除目录列表
            deletable_dirs = [p for p in disk.get_all_directory_paths() if p not in ['c', 'c/']]
            
            if not deletable_dirs:
                st.info("当前没有可删除的目录。")
            else:
                with st.form("delete_dir_form"):
                    path_to_delete = st.selectbox("选择要删除的空目录", options=deletable_dirs)
                    submitted = st.form_submit_button("确认删除目录", type="primary")
                    if submitted:
                        disk.delete_directory(path_to_delete)
                        # 更新状态
                        st.session_state["Disk"] = disk
                        st.toast(f"目录 '{path_to_delete}' 已删除")
                        st.rerun()

        elif file_operation == "➕ 创建文件":
            st.subheader("➕ 创建新文件")
            with st.form("create_file_form"):
                all_dirs = disk.get_all_directory_paths()
                path = st.selectbox("选择文件所在的目录", options=all_dirs)
                filename = st.text_input("新文件名", placeholder="例如: report.txt")
                content = st.text_area("文件内容")
                submitted = st.form_submit_button("创建文件")
                if submitted:
                    if filename and path:
                        disk.add_file(filename, content, path)
                        st.session_state["Disk"] = disk
                    else:
                        st.warning("目录、文件名不能为空!")

        elif file_operation == "📄 操作文件":
            st.subheader("📄 文件内容操作 (查询/读取/写入)")
            all_dirs = disk.get_all_directory_paths()
            tab1, tab2, tab3 = st.tabs(["🔍 查询信息", "📖 读取内容", "✍️ 写入内容"])

            with tab1:
                with st.form("query_form"):
                    st.info("查询文件的元数据。")
                    q_path = st.selectbox("文件所在目录路径", options=all_dirs, key="q_path_select")
                    q_filename = st.text_input("文件名", key="q_filename")
                    if st.form_submit_button("查询文件"):
                        if q_path and q_filename:
                            disk.get_file(q_filename, q_path)
                        else:
                            st.warning("请选择目录并输入文件名")

            with tab2:
                with st.form("read_form"):
                    st.info("从文件的指定盘块读取内容。")
                    r_path = st.selectbox("文件所在目录路径", options=all_dirs, key="r_path_select")
                    r_filename = st.text_input("文件名", key="r_filename")
                    r_block_idx = st.number_input("盘块索引", min_value=0, step=1, key="r_idx")
                    if st.form_submit_button("读取盘块"):
                        if r_path and r_filename:
                            disk.read_file(r_filename, r_block_idx, r_path)
                        else:
                            st.warning("请选择目录并输入文件名")

            with tab3:
                with st.form("write_form"):
                    st.info("向文件的指定盘块写入新内容。")
                    w_path = st.selectbox("文件所在目录路径", options=all_dirs, key="w_path_select")
                    w_filename = st.text_input("文件名", key="w_filename")
                    w_block_idx = st.number_input("盘块索引", min_value=0, step=1, key="w_idx")
                    w_content = st.text_area("要写入的新内容", key="w_content")
                    if st.form_submit_button("写入盘块"):
                        if w_path and w_filename:
                            if w_content:  # 允许写入空内容
                                disk.write_file(w_filename, w_block_idx, w_content, w_path)
                            else:
                                st.warning("请输入要写入的内容")
                        else:
                            st.warning("请选择目录并输入文件名")
        
        elif file_operation == "🗑️ 删除文件":
            st.subheader("🗑️ 删除文件")
            with st.form("delete_file_form"):
                all_dirs = disk.get_all_directory_paths()
                path = st.selectbox("选择文件所在的目录", options=all_dirs)
                filename = st.text_input("要删除的文件名")
                submitted = st.form_submit_button("确认删除文件", type="primary")
                if submitted:
                    if filename and path:
                        disk.delete_file(filename, path)
                        st.session_state["Disk"] = disk
                    else:
                        st.warning("目录和文件名不能为空!")

        elif file_operation == "🗺️ 查看磁盘分配图": 
            st.subheader("🗺️ 磁盘分配图")
            with st.container(border=True):
                disk.show_disk_allocation_map()


    elif operation == "内存管理":
        st.title("🧠 内存管理")

        # 内存管理操作菜单
        st.sidebar.markdown('<div class="sidebar-title">🧠 内存操作</div>', unsafe_allow_html=True)
        if st.sidebar.button("🔄 查看运行情况"):
            st.session_state["memory_operation"] = "查看运行情况"
        if st.sidebar.button("添加进程"):
            st.session_state["memory_operation"] = "添加进程"
        if st.sidebar.button("📄 显示页表"):
            st.session_state["memory_operation"] = "显示页表"

        # 获取当前选择的内存操作
        memory_operation = st.session_state.get("memory_operation", "查看运行情况")

        if memory_operation == "查看运行情况":
            st.subheader("🔄 内存运行情况")
            with st.container():
                scheduler.run(memory_manager)

        elif memory_operation == "添加进程":
            st.subheader("➕ 添加进程")
            with st.container():
                scheduler.new_process(memory_manager)

        elif memory_operation == "显示页表":
            st.subheader("📄 页表情况")
            memory_manager.show_page()

    elif operation == "进程操作":
        st.title("⚙️ 进程操作")

        # 如果没有运行的进程，显示提示信息
        if not scheduler.running_process:
            st.write("当前没有可操作的进程。")
        else:
            # 显示进程操作的下拉栏和按钮
            st.subheader("⚙️ 进程操作")

            # 进程0的操作按钮
            if len(scheduler.running_process) > 0:
                st.write("**进程0操作**")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    if st.button("添加文件", key="op10"):
                        scheduler.file_op(choice="添加文件")
                with col2:
                    if st.button("查看文件内容", key="op20"):
                        scheduler.file_op(choice="查看文件内容", pcb=scheduler.running_process[0])
                with col3:
                    if st.button("修改文件内容", key="op30"):
                        scheduler.file_op(choice="修改文件内容", pcb=scheduler.running_process[0])
                with col4:
                    if st.button("删除文件", key="op40"):
                        scheduler.file_op(choice="删除文件", pcb=scheduler.running_process[0])
                with col5:
                    if st.button(
                            f"❌",  # 红色叉号图标
                            key="finish0",
                            help="终止进程",  # 鼠标悬停提示
                            # 使用自定义 CSS 类
                            kwargs={"class": "square-button"}
                    ):
                        # 检查是否为初始化进程
                        if scheduler.running_process[0].pid in [9998, 9999]:
                            st.error("不可终止初始化进程！")
                        else:
                            for j in range(len(scheduler.running_process[0].use_files)):
                                memory_manager.visit_set_false(scheduler.running_process[0].use_files[j])
                            scheduler.running_process[0].use_files = []
                            memory_manager.release(process_id=scheduler.running_process.pop(0).pid)
                            st.session_state["Sdr"] = scheduler
                            st.rerun()

            # 进程1的操作按钮
            if len(scheduler.running_process) > 1:
                st.write("**进程1操作**")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    if st.button("添加文件", key="op11"):
                        scheduler.file_op(choice="添加文件")
                with col2:
                    if st.button("查看文件内容", key="op21"):
                        scheduler.file_op(choice="查看文件内容", pcb=scheduler.running_process[1])
                with col3:
                    if st.button("修改文件内容", key="op31"):
                        scheduler.file_op(choice="修改文件内容", pcb=scheduler.running_process[1])
                with col4:
                    if st.button("删除文件", key="op41"):
                        scheduler.file_op(choice="删除文件", pcb=scheduler.running_process[1])
                with col5:
                    if st.button(
                            f"❌",  # 红色叉号图标
                            key="finish1",
                            help="终止进程",  # 鼠标悬停提示
                            # 使用自定义 CSS 类
                            kwargs={"class": "square-button"}
                    ):
                        # 检查是否为初始化进程
                        if scheduler.running_process[1].pid in [9998, 9999]:
                            st.error("不可终止初始化进程！")
                        else:
                            for j in range(len(scheduler.running_process[1].use_files)):
                                memory_manager.visit_set_false(scheduler.running_process[1].use_files[j])
                            scheduler.running_process[1].use_files = []
                            memory_manager.release(process_id=scheduler.running_process.pop(1).pid)
                            st.session_state["Sdr"] = scheduler
                            st.rerun()

            # 在侧边栏添加“发消息”和“收消息”按钮
            st.sidebar.markdown('<div class="sidebar-title">📨 进程通信</div>', unsafe_allow_html=True)
            for i, process in enumerate(scheduler.running_process):
                st.sidebar.markdown(f"**进程 {i} 通信**")
                if st.sidebar.button(f"📤 进程{i}发消息", key=f"send_message_{i}"):
                    process.send_message(scheduler, memory_manager)
                if st.sidebar.button(f"📥 进程{i}收消息", key=f"receive_message_{i}"):
                    process.re_message()