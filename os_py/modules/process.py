import streamlit as st
import pandas as pd
import random
import time


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

