from threading import Semaphore
import pandas as pd
import streamlit as st
import plotly.express as px

class MemoryManager:
    def __init__(self, total_memory, page_size):
        self.total_memory = total_memory
        self.page_size = page_size
        self.total_pages = total_memory // page_size
        self.free_pages = self.total_pages
        self.page_table = {i: None for i in range(self.total_pages)}
        self.process_pages = {}
        self.file_pages = {}
        self.semaphores = {i: Semaphore(0) for i in range(self.total_pages)}
        # 用于CLOCK算法的指针
        self.clock_pointer = 0
        self.disk = None

    def set_disk(self, disk):
        self.disk = disk

    def allocate_to_process(self, process_id, memory_required):
        pages_required = memory_required // self.page_size
        if memory_required % self.page_size != 0:
            pages_required += 1
        allocated_pages = []
        for _ in range(pages_required):
            if self.free_pages > 0:
                page = self._find_free_page()
                if page is not None:
                    self.page_table[page] = {
                        "type": "process",
                        "info": process_id,
                        "is_modify": False,
                        "reference_bit": 1,  # 新分配的页面设置访问位为1
                        "Disk_address": None
                    }
                    allocated_pages.append(page)
                    self.free_pages -= 1
            else:
                page = self._replace_page()
                if page is not None:
                    self.page_table[page] = {
                        "type": "process",
                        "info": process_id,
                        "is_modify": False,
                        "reference_bit": 1,  # 新分配的页面设置访问位为1
                        "Disk_address": None
                    }
                    allocated_pages.append(page)

        if len(allocated_pages) == pages_required:
            self.process_pages[process_id] = allocated_pages
            return True
        else:
            return False

    def allocate_to_file(self, file_name, memory_required, block_index, directory):
        pages_required = memory_required // self.page_size
        if memory_required % self.page_size != 0:
            pages_required += 1
        allocated_pages = []
        for _ in range(pages_required):
            if self.free_pages > 0:
                page = self._find_free_page()
                if page is not None:
                    self.page_table[page] = {
                        "type": "file",
                        "info": file_name,
                        "is_modify": False,
                        "reference_bit": 1,  # 新分配的页面设置访问位为1
                        "Disk_address": block_index,
                        "Directory": directory
                    }
                    allocated_pages.append(page)
                    self.free_pages -= 1
            else:
                page = self._replace_page()
                if page is not None:
                    self.page_table[page] = {
                        "type": "file",
                        "info": file_name,
                        "is_modify": False,
                        "reference_bit": 1,  # 新分配的页面设置访问位为1
                        "Disk_address": block_index,
                        "Directory": directory
                    }
                    allocated_pages.append(page)

        if len(allocated_pages) == pages_required:
            self.file_pages[file_name] = allocated_pages
            return True
        else:
            return False

    def _find_free_page(self):
        for page, info in self.page_table.items():
            if info is None:
                return page
        return None

    def _replace_page(self):
        """CLOCK页面置换算法"""
        victim_page = None
        # 最多扫描两圈（确保能找到可替换的页面）
        for _ in range(2 * self.total_pages):
            page_info = self.page_table[self.clock_pointer]
            
            # 如果页面空闲，直接使用（理论上不应该发生，因为free_pages=0时才会调用此方法）
            if page_info is None:
                victim_page = self.clock_pointer
                break
                
            # 检查页面的访问位
            if page_info["reference_bit"] == 0:
                # 找到可替换的页面
                victim_page = self.clock_pointer
                break
            else:
                # 给页面第二次机会：清除访问位
                page_info["reference_bit"] = 0
            
            # 移动指针到下一个页面
            self.clock_pointer = (self.clock_pointer + 1) % self.total_pages
        
        if victim_page is None:
            # 如果仍然没有找到，选择当前指针指向的页面
            victim_page = self.clock_pointer
        
        # 处理选中的页面
        if self.page_table[victim_page]["is_modify"]:
            self._write_page_to_disk(victim_page)
        
        # 释放该页面
        self._release_page(victim_page)
        
        # 移动指针到下一个页面
        self.clock_pointer = (self.clock_pointer + 1) % self.total_pages
        
        return victim_page

    def _write_page_to_disk(self, page):
        page_info = self.page_table[page]
        if page_info["type"] == "file" and self.disk:
            file_name = page_info["info"]
            block_index = page_info["Disk_address"]
            directory = page_info["Directory"]
            
            start = page * self.page_size
            end = start + self.page_size
            content_bytes = self.disk.disk[start:end].tobytes()
            content = content_bytes.decode().rstrip('\x00')

            self.disk.write_file(file_name, block_index, content, directory)
            page_info["is_modify"] = False

    def _release_page(self, page):
        if self.page_table[page] is not None:
            if self.page_table[page]["type"] == "process":
                process_id = self.page_table[page]["info"]
                if process_id in self.process_pages:
                    self.process_pages[process_id].remove(page)
            elif self.page_table[page]["type"] == "file":
                file_name = self.page_table[page]["info"]
                if file_name in self.file_pages:
                    self.file_pages[file_name].remove(page)
            self.page_table[page] = None
            self.free_pages += 1

    def release(self, process_id=None, file_name=None):
        if process_id:
            if process_id in self.process_pages:
                allocated_pages = self.process_pages.pop(process_id)
                for page in allocated_pages:
                    if self.page_table[page] and self.page_table[page]["type"] == "file":
                        self.page_table[page]["Is_visiting"] = False
                    self._release_page(page)
                st.session_state["Mem"] = self
                return True
        elif file_name:
            if file_name in self.file_pages:
                allocated_pages = self.file_pages.pop(file_name)
                for page in allocated_pages:
                    if self.page_table[page] and self.page_table[page]["type"] == "file":
                        self.page_table[page]["Is_visiting"] = False
                    self._release_page(page)
                st.session_state["Mem"] = self
                return True
        return False

    def show_mem(self):
        used_memory = (self.total_pages - self.free_pages) * self.page_size
        free_memory = self.free_pages * self.page_size

        data = pd.DataFrame({
            "Category": ["空闲", "已使用"],
            "占用情况": [free_memory, used_memory]
        })

        fig = px.bar(data, x="Category", y="占用情况", color="Category",
                     title="内存使用情况 (3D 柱状图)",
                     labels={"占用情况": "内存大小 (bit)"},
                     text="占用情况",
                     height=400)

        fig.update_traces(marker_line_color='black', marker_line_width=1.5, opacity=0.8)
        st.plotly_chart(fig)
        st.markdown(f"空闲空间为: {free_memory}bit")

    def get_file_memory(self, file_name):
        return file_name in self.file_pages

    def show_page(self):
        page_info = []
        for page, info in self.page_table.items():
            if info:
                owner = str(info["info"])
                page_info.append({
                    "类型": info["type"],
                    "占有者": owner,
                    "是否已修改": info["is_modify"],
                    "访问位": info["reference_bit"],  # 显示访问位
                    "正在被访问": info["Is_visiting"] if "Is_visiting" in info else False,
                })
            else:
                page_info.append({
                    "类型": "Free",
                    "占有者": "None",
                    "是否已修改": False,
                    "访问位": 0,
                    "正在被访问": False,
                })

        df = pd.DataFrame(page_info)
        styled_df = df.style.map(lambda x: 'background-color: red' if x != "Free" else 'background-color: green', subset=['类型'])

        with st.expander("📄📄 查看页表（点击展开）", expanded=False):
            st.table(styled_df)
            
    def visit_page(self, file_name):
        for page, info in self.page_table.items():
            if info and info["info"] == file_name:
                info["Is_visiting"] = True
                info["reference_bit"] = 1  # 访问时设置访问位为1
        return True

    def modify_page(self, file_name, block_index):
        for page, info in self.page_table.items():
            if info and info["info"] == file_name and info["Disk_address"] == block_index:
                info["is_modify"] = True
                info["reference_bit"] = 1  # 修改时设置访问位为1
        return True

    def visit_set_false(self, file_name):
        for page, info in self.page_table.items():
            if info and info["info"] == file_name:
                info["Is_visiting"] = False
        return True

    def dele(self, file_name):
        for page, info in self.page_table.items():
            if info and info["info"] == file_name:
                info["type"] = "Free"
                info["info"] = None
                info["is_modify"] = False
                info["Is_visiting"] = False
                info["Disk_address"] = None
                self.semaphores[page].release()
        return True