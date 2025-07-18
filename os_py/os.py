import os
import random
import time
import heapq
import threading
from collections import deque
import multiprocessing.shared_memory as sm
import streamlit as st
import pandas as pd
import streamlit as st
import plotly.express as px

# 文件控制块（FCB）类，表示文件的基本信息，包括文件名、创建时间、大小、盘块信息等
class FileControlBlock:
    def __init__(self, filename, create_time, blocks, first_block, directory):
        self.filename = filename  # 文件名
        self.create_time = create_time  # 创建时间
        self.blocks = blocks  # 文件占用的盘块
        self.first_block = first_block  # 第一个盘块号
        self.directory = directory  # 文件所在的目录

# 模拟磁盘类，包含磁盘管理（FAT）、目录和文件操作等
class Disk:
    def __init__(self, block_size=64, block_count=1024, shm_name=None):
        self.block_size = block_size
        self.block_count = block_count
        self.disk_size = block_size * block_count

        if shm_name is None:
            # 主进程，创建新的共享内存
            self.shm = sm.SharedMemory(create=True, size=self.disk_size)
            self.shm_name = self.shm.name
        else:
            # 子进程，连接已存在的共享内存
            self.shm = sm.SharedMemory(name=shm_name)
            self.shm_name = shm_name

        self.disk = self.shm.buf
        self.fat = [-2] * block_count  # FAT表，None表示空闲
        self.free_blocks = deque(range(block_count))
        self.files = {}  # 文件目录，按文件名存储FCB
        self.directories = {"c": {}}  # 初始化时创建一个不可撤销的 c 盘目录
        self.lock = threading.Lock()  # 文件系统锁

    def __del__(self):
        self.shm.close()
        if self.shm_name is not None and sm.SharedMemory(name=self.shm_name).size == self.disk_size:
            self.shm.unlink()

    def get_free_block(self):
        """获取一个空闲的磁盘块"""
        if self.free_blocks:
            return self.free_blocks.popleft()
        return None

    def add_file(self, filename, content, directory):
        """创建文件并存入目录，使用FAT组织数据"""
        with self.lock:
            # 检查目录是否存在
            if directory not in self.directories:
                st.error(f"目录 '{directory}' 不存在!")
                return

            # 检查文件是否已存在
            if filename in self.directories[directory]:
                st.error(f"文件 '{filename}' 在目录 '{directory}' 中已存在!")
                return

            blocks = []
            content_bytes = content.encode()
            # 计算需要多少块
            block_count = (len(content_bytes) + self.block_size - 1) // self.block_size
            first_block = 0
            last_block = None
            for i in range(block_count):
                block_num = self.get_free_block()
                if i == 0:
                    first_block = block_num
                if block_num is None:
                    st.error("磁盘空间不足!")
                    return
                blocks.append(block_num)
                # 计算当前块的内容
                start_content = i * self.block_size
                end_content = start_content + self.block_size
                block_content = content_bytes[start_content:end_content].ljust(self.block_size, b'\x00')
                # 写入磁盘
                start = block_num * self.block_size
                end = start + self.block_size
                self.disk[start:end] = block_content
                # 更新FAT表
                if i != 0:
                    self.fat[last_block] = block_num
                if i == block_count - 1:
                    self.fat[block_num] = -1
                last_block = block_num
            create_time = time.ctime()
            fcb = FileControlBlock(filename, create_time, blocks, first_block, directory)
            self.directories[directory][filename] = fcb
            st.success(f"文件 '{filename}' 在目录 '{directory}' 下创建成功! 当前文件数量：{len(self.directories[directory])}")

    def get_file(self, filename, directory):
        """查询文件信息"""
        with self.lock:
            if directory in self.directories and filename in self.directories[directory]:
                fcb = self.directories[directory][filename]
                st.write(f"文件名: {fcb.filename}, 创建时间: {fcb.create_time}, 占用盘块数: {len(fcb.blocks)}, 目录: {fcb.directory}")
            else:
                st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")

    def read_file(self, filename, block_index, memory_manager, is_in_memory, directory):
        """读取文件内容，按盘块读取"""
        with self.lock:
            if directory in self.directories and filename in self.directories[directory]:
                fcb = self.directories[directory][filename]
                if 0 <= block_index < len(fcb.blocks):
                    block_num = fcb.blocks[block_index]
                    start = block_num * self.block_size
                    end = start + self.block_size
                    content_bytes = self.disk[start:end].tobytes()
                    content = content_bytes.decode().rstrip('\x00')
                    st.write(f"文件 '{filename}' 盘块 {block_index} 内容：")
                    st.text(content)

                    if not is_in_memory:
                        # 分配内存给文件，并设置访问位为 True
                        memory_manager.allocate_to_file(filename, 64, block_num)
                        memory_manager.visit_page(filename)  # 设置访问位为 True
                else:
                    st.error("盘块索引超出范围!")
            else:
                st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")

    def write_file(self, filename, block_index, content, is_in_memory, directory):
        """修改文件内容，按盘块修改"""
        with self.lock:
            if directory in self.directories and filename in self.directories[directory]:
                fcb = self.directories[directory][filename]
                if 0 <= block_index < len(fcb.blocks):
                    block_num = fcb.blocks[block_index]
                    start = block_num * self.block_size
                    end = start + self.block_size
                    content_bytes = content.encode().ljust(self.block_size, b'\x00')
                    self.disk[start:end] = content_bytes
                    st.success(f"文件 '{filename}' 盘块 {block_index} 内容已修改!")

                    if not is_in_memory: 
                        # 分配内存给文件，并设置修改位为 True
                        memory_manager.allocate_to_file(filename, 64, block_num)
                        memory_manager.modify_page(filename, block_index)  # 设置修改位为 True
                else:
                    st.error("盘块索引超出范围!")
            else:
                st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")

    def delete_file(self, filename, directory):
        """删除文件并释放占用的盘块"""
        with self.lock:
            if directory in self.directories and filename in self.directories[directory]:
                fcb = self.directories[directory].pop(filename)
                for block in fcb.blocks:
                    self.fat[block] = None
                    self.free_blocks.append(block)
                st.success(f"文件 '{filename}' 在目录 '{directory}' 下删除成功!")
            else:
                st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")

    def create_directory(self, directory_name):
        """创建目录"""
        with self.lock:
            if directory_name in self.directories:
                st.error(f"目录 '{directory_name}' 已存在!")
            else:
                self.directories[directory_name] = {}
                st.success(f"目录 '{directory_name}' 创建成功!")

    def delete_directory(self, directory_name):
        """删除目录"""
        with self.lock:
            if directory_name == "c":
                st.error("不可删除初始化目录 'c'!")
            elif directory_name in self.directories:
                if self.directories[directory_name]:
                    st.error(f"目录 '{directory_name}' 不为空，无法删除!")
                else:
                    self.directories.pop(directory_name)
                    st.success(f"目录 '{directory_name}' 删除成功!")
            else:
                st.error(f"目录 '{directory_name}' 不存在!")

    def show_directory(self):
        """显示文件目录"""
        with self.lock:
            if self.directories:
                st.write("当前文件目录：")
                for directory, files in self.directories.items():
                    st.write(f"目录: {directory}")
                    if files:
                        data = [
                            {
                                "文件名": fcb.filename,
                                "创建时间": fcb.create_time,
                                "占用盘块数": len(fcb.blocks),
                                "第一盘块号": fcb.first_block
                            }
                            for fcb in files.values()
                        ]
                        df = pd.DataFrame(data)
                        st.table(df)
                    else:
                        st.write("当前目录为空!")
            else:
                st.write("当前目录为空!")

    def show_fat(self):
        """显示FAT表"""
        with self.lock:
            if self.fat:
                st.markdown("FAT表项：")
                fat_df = pd.DataFrame({
                    "Block Number": range(len(self.fat)),
                    "Next Block": self.fat
                })
                st.table(fat_df)

    def get_fat(self, filename, block_index, directory):
        with self.lock:
            if directory in self.directories and filename in self.directories[directory]:
                return self.directories[directory][filename].blocks[block_index]
            else:
                st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")
                return None





class Process:
    def __init__(self, priority, memory_required, pid, name):
        self.name = name
        self.pid = pid  # 进程 ID
        self.priority = priority  # 优先级（数值越小，优先级越高）
        self.memory_required = memory_required  # 所需内存大小
        self.use_files = []
        self.message_queue = []

    def __lt__(self, other):
        # 定义优先级比较，便于在优先队列中排序
        return self.priority < other.priority

    @st.dialog("信息传递", width="large")
    def send_message(self, scheduler, memory_manager):
        pid = st.number_input("请输入进程PID")
        message = st.text_area("请输入数据")
        if st.button("传送数据"):
            if pid and message:
                for target in scheduler.ready_queue:
                    if target.pid == pid:
                        # 将消息格式化为 [发送进程PID, 消息内容]
                        target.message_queue.append([self.pid, message])  # 添加发送进程的 PID
                        st.success("传输完成")
                        st.session_state["Mem"] = memory_manager
                        st.session_state["Sdr"] = scheduler
                        return True
                for target in scheduler.running_process:
                    if target.pid == pid:
                        # 将消息格式化为 [发送进程PID, 消息内容]
                        target.message_queue.append([self.pid, message])  # 添加发送进程的 PID
                        st.success("传输完成")
                        st.session_state["Mem"] = memory_manager
                        st.session_state["Sdr"] = scheduler
                        return True
            else:
                st.error("信息不完整！")


    @st.dialog("信息传递", width="large")
    def re_message(self):
        # 如果 message_queue 是空的
        if not self.message_queue:
            st.write("当前没有消息。")  # 提示用户没有数据
            return

        # 确保队列中所有元素是长度为 2 的列表
        formatted_queue = [
            item if isinstance(item, list) and len(item) == 2 else ["未知", item]
            for item in self.message_queue
        ]

        # 将消息队列转换为 DataFrame
        df = pd.DataFrame(formatted_queue, columns=["PID", "Message"])

        # 使用 Streamlit 表格展示数据
        st.table(df)


#模拟内存
from threading import Semaphore
import pandas as pd
import streamlit as st

# 在 MemoryManager 类中增加 FIFO 页面置换逻辑
class MemoryManager:
    def __init__(self, total_memory, page_size):
        self.total_memory = total_memory  # 总内存
        self.page_size = page_size  # 页大小
        self.total_pages = total_memory // page_size  # 总页数
        self.free_pages = self.total_pages  # 初始时所有页面都是空闲的
        self.page_table = {i: None for i in range(self.total_pages)}  # 页表，初始化为字典
        self.process_pages = {}  # 存储进程与页面的映射
        self.file_pages = {}  # 存储文件与页面的映射
        self.semaphores = {i: Semaphore(0) for i in range(self.total_pages)}  # 为每个页面初始化信号量
        self.page_queue = deque()  # 用于 FIFO 页面置换的队列

    def allocate_to_process(self, process_id, memory_required):
        """分配内存给进程"""
        pages_required = memory_required // self.page_size
        if memory_required % self.page_size != 0:
            pages_required += 1  # 如果内存大小不能整除页大小，则多分配一页
        allocated_pages = []
        for _ in range(pages_required):
            if self.free_pages > 0:
                # 如果有空闲页面，直接分配
                page = self._find_free_page()
                if page is not None:
                    self.page_table[page] = {
                        "type": "process",
                        "info": process_id,
                        "is_modify": False,
                        "Is_visiting": False,
                        "Disk_address": None
                    }
                    allocated_pages.append(page)
                    self.free_pages -= 1
                    self.page_queue.append(page)  # 将页面加入队列
            else:
                # 如果没有空闲页面，进行页面置换
                page = self._replace_page()
                if page is not None:
                    self.page_table[page] = {
                        "type": "process",
                        "info": process_id,
                        "is_modify": False,
                        "Is_visiting": False,
                        "Disk_address": None
                    }
                    allocated_pages.append(page)
                    self.page_queue.append(page)  # 将页面加入队列

        if len(allocated_pages) == pages_required:
            self.process_pages[process_id] = allocated_pages
            return True
        else:
            return False  # 如果页面不足，返回 False

    def allocate_to_file(self, file_name, memory_required, FAT_NO):
        """分配内存给文件"""
        pages_required = memory_required // self.page_size
        if memory_required % self.page_size != 0:
            pages_required += 1  # 如果内存大小不能整除页大小，则多分配一页
        allocated_pages = []
        for _ in range(pages_required):
            if self.free_pages > 0:
                # 如果有空闲页面，直接分配
                page = self._find_free_page()
                if page is not None:
                    self.page_table[page] = {
                        "type": "file",
                        "info": file_name,
                        "is_modify": False,
                        "Is_visiting": True,  # 设置为 True，表示正在访问
                        "Disk_address": FAT_NO
                    }
                    allocated_pages.append(page)
                    self.free_pages -= 1
                    self.page_queue.append(page)  # 将页面加入队列
            else:
                # 如果没有空闲页面，进行页面置换
                page = self._replace_page()
                if page is not None:
                    self.page_table[page] = {
                        "type": "file",
                        "info": file_name,
                        "is_modify": False,
                        "Is_visiting": True,  # 设置为 True，表示正在访问
                        "Disk_address": FAT_NO
                    }
                    allocated_pages.append(page)
                    self.page_queue.append(page)  # 将页面加入队列

        if len(allocated_pages) == pages_required:
            self.file_pages[file_name] = allocated_pages
            return True
        else:
            return False  # 如果页面不足，返回 False

    def _find_free_page(self):
        """查找一个空闲页面"""
        for page, info in self.page_table.items():
            if info is None:
                return page
        return None

    def _replace_page(self):
        """FIFO 页面置换算法"""
        if self.page_queue:
            # 从队列头部取出最早加载的页面
            page_to_replace = self.page_queue.popleft()

            # 检查页面是否被修改
            if self.page_table[page_to_replace]["is_modify"]:
                # 如果页面被修改，将其写回磁盘
                self._write_page_to_disk(page_to_replace)

            # 将访问位置为 False
            self.page_table[page_to_replace]["Is_visiting"] = False

            # 释放该页面
            self._release_page(page_to_replace)
            return page_to_replace
        return None

    def _write_page_to_disk(self, page):
        """将修改过的页面写回磁盘"""
        page_info = self.page_table[page]
        if page_info["type"] == "file":
            # 获取文件信息和磁盘块号
            file_name = page_info["info"]
            block_index = page_info["Disk_address"]

            # 获取文件内容
            start = page * self.page_size
            end = start + self.page_size
            content_bytes = self.disk[start:end].tobytes()
            content = content_bytes.decode().rstrip('\x00')

            # 将内容写回磁盘
            self.disk.write_file(file_name, block_index, content, is_in_memory=False, directory="c")

            # 重置 is_modify 标志位
            page_info["is_modify"] = False

    def _release_page(self, page):
        """释放页面"""
        if self.page_table[page] is not None:
            # 如果页面被进程占用，更新进程的页面映射
            if self.page_table[page]["type"] == "process":
                process_id = self.page_table[page]["info"]
                if process_id in self.process_pages:
                    self.process_pages[process_id].remove(page)
            # 如果页面被文件占用，更新文件的页面映射
            elif self.page_table[page]["type"] == "file":
                file_name = self.page_table[page]["info"]
                if file_name in self.file_pages:
                    self.file_pages[file_name].remove(page)
            # 标记页面为空闲
            self.page_table[page] = None
            self.free_pages += 1

    def release(self, process_id=None, file_name=None):
        """释放内存"""
        if process_id:
            if process_id in self.process_pages:
                allocated_pages = self.process_pages.pop(process_id)  # 获取并移除进程的分配页面
                # 标记页面为未分配，并将访问位置为 False
                for page in allocated_pages:
                    if self.page_table[page] and self.page_table[page]["type"] == "file":
                        self.page_table[page]["Is_visiting"] = False  # 将访问位置为 False
                    self._release_page(page)
                st.session_state["Mem"] = self  # 更新状态
                return True
        elif file_name:
            if file_name in self.file_pages:
                allocated_pages = self.file_pages.pop(file_name)  # 获取并移除文件的分配页面
                # 标记页面为未分配，并将访问位置为 False
                for page in allocated_pages:
                    if self.page_table[page] and self.page_table[page]["type"] == "file":
                        self.page_table[page]["Is_visiting"] = False  # 将访问位置为 False
                    self._release_page(page)
                st.session_state["Mem"] = self  # 更新状态
                return True
        return False

    def show_mem(self):
        """显示内存占用情况"""
        used_memory = (self.total_pages - self.free_pages) * self.page_size
        free_memory = self.free_pages * self.page_size

        # 创建数据
        data = pd.DataFrame({
            "Category": ["空闲", "已使用"],
            "占用情况": [free_memory, used_memory]
        })

        # 使用 Plotly 绘制 3D 柱状图
        fig = px.bar(data, x="Category", y="占用情况", color="Category",
                     title="内存使用情况 (3D 柱状图)",
                     labels={"占用情况": "内存大小 (bit)"},
                     text="占用情况",
                     height=400)

        # 增加立体感
        fig.update_traces(marker_line_color='black', marker_line_width=1.5, opacity=0.8)

        # 显示图表
        st.plotly_chart(fig)

        st.markdown(f"空闲空间为: {free_memory}bit")

    def get_file_memory(self, file_name):
        """根据文件名查询文件在内存中的分配情况"""
        if file_name in self.file_pages:
            return True
        else:
            return False

    def show_page(self):
        """显示页表（下拉展开）"""
        page_info = []
        # 遍历页表，获取每个页面的详细信息
        for page, info in self.page_table.items():
            if info:
                # 如果页面被占用，获取详细信息
                page_info.append({
                    "类型": info["type"],  # 类型：进程或文件
                    "占有者": info["info"],  # 进程ID或文件名
                    "是否已修改": info["is_modify"],  # 是否被修改
                    "正在被访问": info["Is_visiting"],
                })
            else:
                # 如果页面为空闲，标记为空闲
                page_info.append({
                    "类型": "Free",  # 标记为空闲
                    "占有者": "None",  # 没有占用者
                    "是否已修改": False,  # 未修改
                    "正在被访问": False,
                })

        # 将列表转换为pandas DataFrame
        df = pd.DataFrame(page_info)

        # 定义颜色函数
        def color_type(val):
            color = 'red' if val != "Free" else 'green'
            return f'background-color: {color}'

        # 应用颜色到表格
        styled_df = df.style.applymap(color_type, subset=['类型'])

        # 使用st.expander输出
        with st.expander("📄 查看页表（点击展开）", expanded=False):
            st.table(styled_df)  # 显示在Streamlit的表格中

    def visit_page(self, file_name):
        """修改页面的 is_visiting 属性为 True"""
        for page, info in self.page_table.items():
            if info and info["info"] == file_name:
                info["Is_visiting"] = True  # 设置访问位为 True
        return True

    def modify_page(self, file_name, block_index):
        """修改页面的 is_modify 属性为 True"""
        for page, info in self.page_table.items():
            if info and info["info"] == file_name and info["Disk_address"] == block_index:
                info["is_modify"] = True  # 设置修改位为 True
        return True

    def visit_set_false(self, file_name):
        """修改页面的 is_visiting 属性为 False"""
        for page, info in self.page_table.items():
            if info and info["info"] == file_name:  # 检查 page 对应的 info 字段中的 file_name
                info["Is_visiting"] = False
        return True

    def dele(self, file_name):
        """删除文件并释放相关页面"""
        for page, info in self.page_table.items():
            if info and info["info"] == file_name:  # 检查 page 对应的 info 字段中的 file_name
                info["type"] = "Free"
                info["info"] = None
                info["is_modify"] = False
                info["Is_visiting"] = False
                info["Disk_address"] = None
                self.semaphores[page].release()  # 释放信号量，表明页面已删除
        return True



    def modify_page(self, file_name, block_index):
        """修改页面的 is_modify 属性并释放信号量"""
        for page, info in self.page_table.items():
            if info and info["info"] == file_name and info["Disk_address"] == block_index:  # 检查 page 对应的 info 字段中的 file_name
                info["is_modify"] = True
                self.semaphores[page].release()  # 页面修改后，释放信号量
        return True

    def visit_page(self, file_name):
        """修改页面的 is_visiting 属性并阻塞，直到页面修改"""
        for page, info in self.page_table.items():
            if info and info["info"] == file_name and not info["Is_visiting"]:  # 检查 page 对应的 info 字段中的 file_name
                info["Is_visiting"] = True
                self.semaphores[page].acquire()  # 阻塞，直到页面修改完成
        return True

    def visit_set_false(self, file_name):
        """修改页面的 is_visiting 属性为 False"""
        for page, info in self.page_table.items():
            if info and info["info"] == file_name:  # 检查 page 对应的 info 字段中的 file_name
                info["Is_visiting"] = False
        return True

    def dele(self, file_name):
        """删除文件并释放相关页面"""
        for page, info in self.page_table.items():
            if info and info["info"] == file_name:  # 检查 page 对应的 info 字段中的 file_name
                info["type"] = "Free"
                info["info"] = None
                info["is_modify"] = False
                info["Is_visiting"] = False
                info["Disk_address"] = None
                self.semaphores[page].release()  # 释放信号量，表明页面已删除
        return True







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
        directory = st.selectbox("选择目录", options=list(disk.directories.keys()))

        if choice == "添加文件":
            filename = st.text_input("请输入文件名")
            content = st.text_area("请输入文件内容")
            if st.button("添加文件"):
                if filename and content:
                    disk.add_file(filename, content, directory)  # 传递 directory 参数
                    st.session_state["Disk"] = disk
                else:
                    st.warning("请填写完整信息!")

        elif choice == "查看文件内容":
            filename = st.text_input("请输入查看内容的文件名")
            block_index = st.number_input("请输入查看的盘块索引", min_value=0, step=1)
            if st.button("查看内容"):
                if filename:
                    if filename not in disk.directories[directory]:
                        st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")
                        return

                    fcb = disk.directories[directory][filename]
                    if block_index >= len(fcb.blocks):
                        st.error(f"盘块索引 {block_index} 超出范围，文件 '{filename}' 只有 {len(fcb.blocks)} 个盘块。")
                        return

                    tem_flag = False
                    for page, page_info in memory_manager.page_table.items():
                        if page_info is not None and "Disk_address" in page_info:
                            if page_info["Disk_address"] == disk.get_fat(filename, block_index, directory):
                                tem_flag = True
                                break

                    if filename in pcb.use_files:
                        disk.read_file(filename, block_index, memory_manager, memory_manager.get_file_memory(filename),
                                       directory)
                    elif tem_flag:
                        if memory_manager.visit_page(filename):
                            disk.read_file(filename, block_index, memory_manager,
                                           memory_manager.get_file_memory(filename), directory)
                            pcb.use_files.append(filename)
                        else:
                            st.error(f"文件 '{filename}' 已被其他进程占用")
                    else:
                        disk.read_file(filename, block_index, memory_manager, memory_manager.get_file_memory(filename),
                                       directory)
                        pcb.use_files.append(filename)
                    st.session_state["Disk"] = disk
                else:
                    st.warning("请输入文件名!")

        elif choice == "修改文件内容":
            filename = st.text_input("请输入修改内容的文件名")
            block_index = st.number_input("请输入修改的盘块索引", min_value=0, step=1)
            content = st.text_area("请输入新的内容")
            if st.button("修改内容"):
                if filename and content:
                    if filename not in disk.directories[directory]:
                        st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")
                        return

                    fcb = disk.directories[directory][filename]
                    if block_index >= len(fcb.blocks):
                        st.error(f"盘块索引 {block_index} 超出范围，文件 '{filename}' 只有 {len(fcb.blocks)} 个盘块。")
                        return

                    tem_flag = False
                    for page, page_info in memory_manager.page_table.items():
                        if page_info is not None and "Disk_address" in page_info:
                            if page_info["Disk_address"] == disk.get_fat(filename, block_index, directory):
                                tem_flag = True
                                break

                    if filename in pcb.use_files:
                        disk.write_file(filename, block_index, content, memory_manager.get_file_memory(filename),
                                        directory)
                        memory_manager.modify_page(filename, block_index)
                    elif tem_flag:
                        if memory_manager.visit_page(filename):
                            disk.write_file(filename, block_index, content, memory_manager.get_file_memory(filename),
                                            directory)
                            memory_manager.modify_page(filename, block_index)
                            pcb.use_files.append(filename)
                        else:
                            st.error(f"文件 '{filename}' 已被其他进程占用")
                    else:
                        disk.write_file(filename, block_index, content, memory_manager.get_file_memory(filename),
                                        directory)
                        memory_manager.modify_page(filename, block_index)
                        pcb.use_files.append(filename)
                    st.session_state["Disk"] = disk
                else:
                    st.warning("请输入文件名和内容!")

        elif choice == "删除文件":
            filename = st.text_input("请输入删除的文件名")
            if st.button("删除文件"):
                if filename:
                    if filename not in disk.directories[directory]:
                        st.error(f"文件 '{filename}' 在目录 '{directory}' 中不存在!")
                        return

                    tem_flag = False
                    for page, page_info in memory_manager.page_table.items():
                        if page_info is not None and "Disk_address" in page_info:
                            if page_info["info"] == filename:
                                tem_flag = True
                                break

                    if filename in pcb.use_files:
                        disk.delete_file(filename, directory)
                        memory_manager.dele(filename)
                    elif tem_flag:
                        if memory_manager.visit_page(filename):
                            disk.delete_file(filename, directory)
                            memory_manager.dele(filename)
                            pcb.use_files.append(filename)
                        else:
                            st.error(f"文件 '{filename}' 已被其他进程占用")
                    else:
                        disk.delete_file(filename, directory)
                        memory_manager.dele(filename)
                        pcb.use_files.append(filename)
                    st.session_state["Disk"] = disk
                else:
                    st.warning("请输入文件名!")

class MessageSender:
    def __init__(self, message_queue):
        self.message_queue = message_queue

    def send_message(self, message):
        """模拟发送消息"""
        print(f"发送消息: {message}")
        self.message_queue.put(message)  # 将消息放入队列

class MessageReceiver:
    def __init__(self, message_queue):
        self.message_queue = message_queue

    def receive_message(self):
        """模拟接收消息"""
        while True:
            if not self.message_queue.empty():
                message = self.message_queue.get()  # 从队列中取出消息
                print(f"接收消息: {message}")
            time.sleep(1)  # 每隔 1 秒检查一次队列

        # Streamlit 页面


# 自定义 CSS 样式
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



# 自定义 CSS 样式
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
        # 磁盘占用饼状图
        disk_usage = {
            "已使用": disk.block_count - len(disk.free_blocks),
            "空闲": len(disk.free_blocks),
        }
        df_disk = pd.DataFrame({
            "Category": list(disk_usage.keys()),
            "占用情况": list(disk_usage.values()),
        })
        fig_disk = px.pie(df_disk, values="占用情况", names="Category", title="磁盘占用情况")
        st.plotly_chart(fig_disk, use_container_width=True)

    with col2:
        # 内存占用柱状图
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

    # FAT 表显示
    st.markdown('<div class="chart-container">📊 FAT 表</div>', unsafe_allow_html=True)
    disk.show_fat()
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

    # 使用 Font Awesome 的 Windows 图标
    windows_icon = '<i class="fab fa-windows"></i>'

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
        # 文件系统操作（保持不变）
        st.title("💾 文件系统")

        # 文件系统操作菜单
        st.sidebar.markdown('<div class="sidebar-title">📂 文件操作</div>', unsafe_allow_html=True)
        if st.sidebar.button("🔍 查询文件"):
            st.session_state["file_operation"] = "查询文件"
        if st.sidebar.button("📁 显示目录"):
            st.session_state["file_operation"] = "显示目录"
        if st.sidebar.button("📊 查看FAT表"):
            st.session_state["file_operation"] = "查看FAT表"
        if st.sidebar.button("📂 创建目录"):
            st.session_state["file_operation"] = "创建目录"
        if st.sidebar.button("🗑️ 删除目录"):
            st.session_state["file_operation"] = "删除目录"

        # 获取当前选择的文件操作
        file_operation = st.session_state.get("file_operation", "查询文件")

        # 目录选择下拉栏
        directory = st.selectbox("选择目录", options=list(disk.directories.keys()))

        if file_operation == "查询文件":
            st.subheader("🔍 查询文件")
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    filename = st.text_input("请输入查询的文件名", key="filename_input")
                with col2:
                    if st.button("查询文件", key="query_file_button"):
                        if filename:
                            disk.get_file(filename, directory)
                            st.session_state["Disk"] = disk
                            st.success("查询成功！")
                        else:
                            st.warning("请输入文件名!")
                # 添加磁盘占用饼状图
                st.subheader("📊 磁盘占用情况")
                disk_usage = {
                    "已使用": disk.block_count - len(disk.free_blocks),
                    "空闲": len(disk.free_blocks),
                }
                df_disk = pd.DataFrame({
                    "Category": list(disk_usage.keys()),
                    "占用情况": list(disk_usage.values()),
                })
                fig_disk = px.pie(df_disk, values="占用情况", names="Category", title="磁盘占用情况")
                st.plotly_chart(fig_disk, use_container_width=True)

        elif file_operation == "显示目录":
            st.subheader("📁 文件目录")
            with st.container():
                disk.show_directory()

        elif file_operation == "查看FAT表":
            st.subheader("📊 FAT 表")
            disk.show_fat()

        elif file_operation == "创建目录":
            st.subheader("📂 创建目录")
            with st.container():
                new_directory = st.text_input("请输入新目录名")
                if st.button("创建目录"):
                    if new_directory:
                        disk.create_directory(new_directory)
                        st.session_state["Disk"] = disk
                    else:
                        st.warning("请输入目录名!")

        elif file_operation == "删除目录":
            st.subheader("🗑️ 删除目录")
            with st.container():
                delete_directory = st.selectbox("选择要删除的目录", options=list(disk.directories.keys()))
                if st.button("删除目录"):
                    if delete_directory:
                        disk.delete_directory(delete_directory)
                        st.session_state["Disk"] = disk
                    else:
                        st.warning("请选择目录!")

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


if __name__ == "__main__":
    if 'Disk' not in st.session_state:
        disk = Disk()
        st.session_state["Disk"] = disk
    else:
        disk = st.session_state["Disk"]

    if 'Mem' not in st.session_state:
        memory_manager = MemoryManager(64 * 64, 64)
        st.session_state["Mem"] = memory_manager
    else:
        memory_manager = st.session_state["Mem"]

    if 'Sdr' not in st.session_state:
        scheduler = Scheduler(memory_manager, disk)
        st.session_state["Sdr"] = scheduler
    else:
        scheduler = st.session_state["Sdr"]

    streamlit_interface(disk, memory_manager, scheduler)