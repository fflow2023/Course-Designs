import heapq
import threading
import streamlit as st
import random
from modules.process import Process


class Scheduler:
    def __init__(self, memory_manager, disk):
        self.ready_queue = []  # 就绪队列（优先队列）
        self.running_process = []  # 当前运行的进程
        self.memory_manager = memory_manager
        self.disk = disk
        self.lock = threading.Lock()  # 保证线程安全

    def add_process(self, process):
        """向就绪队列中添加进程"""
        with self.lock:
            heapq.heappush(self.ready_queue, process)
            st.success(f"进程 {process.pid} 添加到就绪队列，优先级 {process.priority}")

    def run(self, memory_manager):
        """启动调度器，确保 running_process 最多容纳两个进程，并支持优先级抢占"""
        with self.lock:
            # 如果运行队列未满（最多两个进程），从就绪队列中取出优先级最高的进程并放入运行队列
            while len(self.running_process) < 2 and self.ready_queue:
                selected_process = heapq.heappop(self.ready_queue)
                self.running_process.append(selected_process)
                st.write(f"切换到进程 {selected_process.pid}，优先级 {selected_process.priority}")

            # 检查是否有更高优先级的进程在就绪队列中
            if self.ready_queue:
                # 获取就绪队列中优先级最高的进程
                highest_priority_ready = self.ready_queue[0]
                # 检查 running_process 中是否有比 highest_priority_ready 优先级更低的进程
                for i, running_process in enumerate(self.running_process):
                    if highest_priority_ready.priority < running_process.priority:
                        # 将当前运行的进程放回就绪队列
                        heapq.heappush(self.ready_queue, running_process)
                        # 从 running_process 中移除该进程
                        self.running_process.pop(i)
                        # 将更高优先级的进程放入 running_process
                        self.running_process.append(heapq.heappop(self.ready_queue))
                        st.write(
                            f"抢占切换到进程 {self.running_process[-1].pid}，优先级 {self.running_process[-1].priority}")
                        break

            # 显示内存使用情况的图表
            st.subheader("🔄 内存运行情况")
            memory_manager.show_mem()  # 显示内存使用情况的图表

            # 显示运行队列
            st.subheader("🏃‍♂️ 运行队列")
            if self.running_process:
                running_data = [
                    {
                        "名称": process.name,
                        "PID": process.pid,
                        "优先权": process.priority,
                        "所占空间": process.memory_required,
                    }
                    for process in self.running_process
                ]
                st.table(running_data)
            else:
                st.write("当前没有运行的任务。")

            # 显示就绪队列
            st.subheader("📥 就绪队列")
            if len(self.ready_queue) > 0:
                process_data = [
                    {
                        "名称": process.name,
                        "PID": process.pid,
                        "优先权": process.priority,
                        "所占空间": process.memory_required,
                    }
                    for process in self.ready_queue
                ]
                st.table(process_data)
            else:
                st.write("当前没有就绪的任务。")

            # 更新 session_state
            st.session_state["Sdr"] = self
            st.session_state["Mem"] = memory_manager

    def new_process(self, memory_manager):
        """在主界面添加进程"""
        # 使用 st.form 封装输入框和按钮
        with st.form(key="add_process_form"):
            filename = st.text_input("请输入进程名", key="process_name_input")
            # 使用下拉栏选择优先级，范围为 1-20，数字越小优先级越高
            priority = st.selectbox("请选择优先级（1-20，数字越小优先级越高）", options=range(1, 21), index=9)  # 默认选择 10
            if st.form_submit_button("添加任务"):
                if filename:
                    pid = random.randint(0, 65535)
                    while pid in [process.pid for process in self.ready_queue] or (
                            self.running_process and pid in [process.pid for process in self.running_process]
                    ):
                        # 如果 `pid` 在 ready_queue 或 running_process 中，重新生成
                        pid = random.randint(1, 1000)

                    if memory_manager.allocate_to_process(pid, 64):
                        pcb = Process(priority, 64, pid, filename)
                        self.add_process(pcb)
                        st.success(f"进程 {filename} (PID: {pid}) 添加成功！")
                    else:
                        st.error(f"进程 {pid} 内存不足，无法创建进程")

                    # 更新 session_state
                    st.session_state["Sdr"] = self
                    st.session_state["Mem"] = memory_manager
                else:
                    st.warning("请填写进程名!")

    # 修改 file_op 方法，增加目录选择
    @st.dialog("文件操作")
    def file_op(self, choice, pcb=None):
        # 目录选择下拉栏
        directory = st.selectbox("选择目录", options=list(self.disk.directories.keys()))

        if choice == "添加文件":
            filename = st.text_input("请输入文件名")
            content = st.text_area("请输入文件内容")
            if st.button("添加文件"):
                if filename and content:
                    self.disk.add_file(filename, content, directory)  # 传递 directory 参数
                    st.session_state["Disk"] = self.disk
                else:
                    st.warning("请填写完整信息!")

        elif choice == "查看文件内容":
            filename = st.text_input("请输入查看内容的文件名")
            block_index = st.number_input("请输入查看的盘块索引", min_value=0, step=1)
            if st.button("查看内容"):
                if filename:
                    if filename not in self.disk.directories[directory]:
                        st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")
                        return

                    fcb = self.disk.directories[directory][filename]
                    if block_index >= len(fcb.blocks):
                        st.error(f"盘块索引 {block_index} 超出范围，文件 '{filename}' 只有 {len(fcb.blocks)} 个盘块。")
                        return

                    tem_flag = False
                    for page, page_info in self.memory_manager.page_table.items():
                        if page_info is not None and "Disk_address" in page_info:
                            if page_info["Disk_address"] == self.disk.get_physical_block(filename, block_index, directory):
                                tem_flag = True
                                break

                    if filename in pcb.use_files:
                        self.disk.read_file(filename, block_index, self.memory_manager, self.memory_manager.get_file_memory(filename),
                                    directory)
                    elif tem_flag:
                        if self.memory_manager.visit_page(filename):
                            self.disk.read_file(filename, block_index, self.memory_manager,
                                        self.memory_manager.get_file_memory(filename), directory)
                            pcb.use_files.append(filename)
                        else:
                            st.error(f"文件 '{filename}' 已被其他进程占用")
                    else:
                        self.disk.read_file(filename, block_index, self.memory_manager, self.memory_manager.get_file_memory(filename),
                                    directory)
                        pcb.use_files.append(filename)
                    st.session_state["Disk"] = self.disk
                else:
                    st.warning("请输入文件名!")

        elif choice == "修改文件内容":
            filename = st.text_input("请输入修改内容的文件名")
            block_index = st.number_input("请输入修改的盘块索引", min_value=0, step=1)
            content = st.text_area("请输入新的内容")
            if st.button("修改内容"):
                if filename and content:
                    if filename not in self.disk.directories[directory]:
                        st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")
                        return

                    fcb = self.disk.directories[directory][filename]
                    if block_index >= len(fcb.blocks):
                        st.error(f"盘块索引 {block_index} 超出范围，文件 '{filename}' 只有 {len(fcb.blocks)} 个盘块。")
                        return

                    tem_flag = False
                    for page, page_info in self.memory_manager.page_table.items():
                        if page_info is not None and "Disk_address" in page_info:
                            if page_info["Disk_address"] == self.disk.get_physical_block(filename, block_index, directory):
                                tem_flag = True
                                break

                    if filename in pcb.use_files:
                        self.disk.write_file(filename, block_index, content, self.memory_manager.get_file_memory(filename),
                                        directory)
                        self.memory_manager.modify_page(filename, block_index)
                    elif tem_flag:
                        if self.memory_manager.visit_page(filename):
                            self.disk.write_file(filename, block_index, content, self.memory_manager.get_file_memory(filename),
                                            directory)
                            self.memory_manager.modify_page(filename, block_index)
                            pcb.use_files.append(filename)
                        else:
                            st.error(f"文件 '{filename}' 已被其他进程占用")
                    else:
                        self.disk.write_file(filename, block_index, content, self.memory_manager.get_file_memory(filename),
                                        directory)
                        self.memory_manager.modify_page(filename, block_index)
                        pcb.use_files.append(filename)
                    st.session_state["Disk"] = self.disk
                else:
                    st.warning("请输入文件名和内容!")

        elif choice == "删除文件":
            filename = st.text_input("请输入删除的文件名")
            if st.button("删除文件"):
                if filename:
                    if filename not in self.disk.directories[directory]:
                        st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")
                        return

                    tem_flag = False
                    for page, page_info in self.memory_manager.page_table.items():
                        if page_info is not None and "Disk_address" in page_info:
                            if page_info["info"] == filename:
                                tem_flag = True
                                break

                    if filename in pcb.use_files:
                        self.disk.delete_file(filename, directory)
                        self.memory_manager.dele(filename)
                    elif tem_flag:
                        if self.memory_manager.visit_page(filename):
                            self.disk.delete_file(filename, directory)
                            self.memory_manager.dele(filename)
                            pcb.use_files.append(filename)
                        else:
                            st.error(f"文件 '{filename}' 已被其他进程占用")
                    else:
                        self.disk.delete_file(filename, directory)
                        self.memory_manager.dele(filename)
                        pcb.use_files.append(filename)
                    st.session_state["Disk"] = self.disk
                else:
                    st.warning("请输入文件名!")