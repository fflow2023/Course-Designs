# modules/disk.py
import re
import time
import threading
import multiprocessing.shared_memory as sm
import streamlit as st
import pandas as pd
import plotly.express as px

class Directory:
    """表示文件系统中的一个目录（树节点）"""
    def __init__(self, name, parent=None):
        self.name = name                # 目录名
        self.parent = parent            # 指向父目录的引用
        self.subdirectories = {}        # 子目录: {'name': Directory_object}
        self.files = {}                 # 文件: {'filename': FCB_object}

    def get_full_path(self):
        """返回此目录的完整路径字符串"""
        path_parts = []
        current = self
        while current is not None:
            path_parts.append(current.name)
            current = current.parent
        full_path = "/".join(reversed(path_parts))
        if not full_path.endswith('/'):
            full_path += '/'
        return full_path

class FileControlBlock:
    """
    文件控制块（FCB）类，适配连续分配。
    存储起始盘块和盘块数量。
    """
    def __init__(self, filename, create_time, size, start_block, num_blocks, directory_obj):
        self.filename = filename
        self.create_time = create_time
        self.size = size                # 文件内容的实际字节大小
        self.start_block = start_block  # 文件占用的起始盘块号
        self.num_blocks = num_blocks    # 文件占用的总盘块数
        self.directory = directory_obj  # 指向包含此文件的Directory对象

class Disk:
    def __init__(self, block_size=64, block_count=1024, shm_name=None):
        self.block_size = block_size
        self.block_count = block_count
        self.disk_size = block_size * block_count

        if shm_name is None:
            self.shm = sm.SharedMemory(create=True, size=self.disk_size)
            self.shm_name = self.shm.name
        else:
            self.shm = sm.SharedMemory(name=shm_name)
            self.shm_name = shm_name

        self.disk = self.shm.buf
        
        # 空闲盘块表：存储(start_block, num_blocks)元组
        self.free_block_list = [(0, block_count)]
        
        self.lock = threading.Lock()
        self.root = Directory(name="c")
    
    def __del__(self):
        self.shm.close()
        try:
            sm.SharedMemory(name=self.shm_name).unlink()
        except FileNotFoundError:
            pass

    def _find_free_contiguous_blocks(self, num_blocks):
        """使用首次适应算法在空闲盘块表中查找足够大的连续空间"""
        for i, (start, length) in enumerate(self.free_block_list):
            if length >= num_blocks:
                return start
        return None

    def _allocate_blocks(self, start_block, num_blocks):
        """在空闲盘块表中分配指定的连续盘块"""
        new_free_list = []
        allocated = False
        
        for start, length in self.free_block_list:
            # 空闲区域在分配区域之后
            if start > start_block + num_blocks - 1:
                new_free_list.append((start, length))
            # 空闲区域在分配区域之前
            elif start + length - 1 < start_block:
                new_free_list.append((start, length))
            # 空闲区域包含分配区域
            else:
                allocated = True
                # 空闲区域被分配区域完全包含
                if start < start_block and start + length > start_block + num_blocks:
                    # 拆分成两个空闲区域
                    new_free_list.append((start, start_block - start))
                    new_free_list.append((start_block + num_blocks, length - (start_block - start) - num_blocks))
                # 分配区域在空闲区域的开头
                elif start == start_block:
                    if length > num_blocks:
                        new_free_list.append((start + num_blocks, length - num_blocks))
                # 分配区域在空闲区域的末尾
                elif start + length == start_block + num_blocks:
                    if length > num_blocks:
                        new_free_list.append((start, length - num_blocks))
                # 分配区域覆盖整个空闲区域
                else:
                    # 完全覆盖，不添加回空闲列表
                    pass
        
        if allocated:
            self.free_block_list = new_free_list
        else:
            st.error(f"无法分配块 {start_block} 到 {start_block + num_blocks - 1}")

    def _free_blocks(self, start_block, num_blocks):
        """释放指定的连续盘块，合并相邻区域"""
        # 创建新空闲区域
        new_block = (start_block, num_blocks)
        
        # 插入并合并相邻区域
        merged = False
        new_list = []
        
        # 先添加新区域
        self.free_block_list.append(new_block)
        
        # 按起始块排序
        self.free_block_list.sort(key=lambda x: x[0])
        
        # 合并相邻区域
        merged_list = []
        current_start, current_length = self.free_block_list[0]
        
        for i in range(1, len(self.free_block_list)):
            next_start, next_length = self.free_block_list[i]
            
            # 检查是否相邻或重叠
            if current_start + current_length >= next_start:
                # 合并区域
                end = max(current_start + current_length, next_start + next_length)
                current_length = end - current_start
            else:
                # 添加当前区域并移动到下一个
                merged_list.append((current_start, current_length))
                current_start, current_length = next_start, next_length
        
        # 添加最后一个区域
        merged_list.append((current_start, current_length))
        
        self.free_block_list = merged_list

    def add_file(self, filename, content, path):
        with self.lock:
            target_dir = self._find_directory(path)
            if not target_dir:
                st.error(f"目录路径 '{path}' 不存在!")
                return

            if filename in target_dir.files:
                st.error(f"文件 '{filename}' 在目录 '{path}' 中已存在!")
                return

            content_bytes = content.encode('utf-8')
            file_size = len(content_bytes)
            num_blocks = (file_size + self.block_size - 1) // self.block_size
            
            # 查找连续的空闲块
            start_block = self._find_free_contiguous_blocks(num_blocks)
            
            if start_block is None:
                st.error("磁盘空间不足或没有足够的连续空间!")
                return

            # 分配空间
            self._allocate_blocks(start_block, num_blocks)
            
            # 写入数据到连续的盘块中
            for i in range(num_blocks):
                block_num = start_block + i
                start_content = i * self.block_size
                end_content = start_content + self.block_size
                block_content = content_bytes[start_content:end_content].ljust(self.block_size, b'\x00')
                
                start_disk = block_num * self.block_size
                end_disk = start_disk + self.block_size
                self.disk[start_disk:end_disk] = block_content
                
            create_time = time.ctime()
            # 创建新的FCB
            fcb = FileControlBlock(filename, create_time, file_size, start_block, num_blocks, target_dir)
            target_dir.files[filename] = fcb
            st.success(f"文件 '{filename}' 在目录 '{path}' 下创建成功!")

    def get_file(self, filename, path):
        with self.lock:
            target_dir = self._find_directory(path)
            if target_dir and filename in target_dir.files:
                fcb = target_dir.files[filename]
                st.write(f"文件名: {fcb.filename}, 创建时间: {fcb.create_time}, 大小: {fcb.size} B")
                st.write(f"存储方式: 连续分配, 起始盘块: {fcb.start_block}, 占用盘块数: {fcb.num_blocks}")
                st.write(f"目录: {fcb.directory.get_full_path()}")
            else:
                st.error(f"文件 '{filename}' 在目录 '{path}' 中不存在!")

    def delete_file(self, filename, path):
        with self.lock:
            target_dir = self._find_directory(path)
            if target_dir and filename in target_dir.files:
                fcb = target_dir.files.pop(filename)
                # 释放占用的连续盘块
                self._free_blocks(fcb.start_block, fcb.num_blocks)
                st.success(f"文件 '{filename}' 在目录 '{path}' 下删除成功!")
            else:
                st.error(f"文件 '{filename}' 在目录 '{path}' 中不存在!")
    
    def read_file(self, filename, block_index, path, memory_manager=None, is_in_memory=None):
        if not path or not filename:
            st.error("目录和文件名不能为空!")
            return
        with self.lock:
            target_dir = self._find_directory(path)
            if target_dir and filename in target_dir.files:
                fcb = target_dir.files[filename]
                if 0 <= block_index < fcb.num_blocks:
                    block_num = fcb.start_block + block_index
                    start = block_num * self.block_size
                    end = start + self.block_size
                    content_bytes = self.disk[start:end].tobytes()
                    content = content_bytes.decode('utf-8', errors='ignore').rstrip('\x00')
                    st.write(f"文件 '{filename}' (位于 '{path}') 逻辑盘块 {block_index} (物理盘块 {block_num}) 内容：")
                    st.text_area("Content", content, height=150, key=f"read_{path}_{filename}_{block_index}")
                else:
                    st.error("逻辑盘块索引超出范围!")
            else:
                st.error(f"文件 '{filename}' 在目录 '{path}' 中不存在!")

    def write_file(self, filename, block_index, content, path, memory_manager=None, is_in_memory=None):
        if not path or not filename:
            st.error("目录和文件名不能为空!")
            return
        with self.lock:
            target_dir = self._find_directory(path)
            if target_dir and filename in target_dir.files:
                fcb = target_dir.files[filename]
                if 0 <= block_index < fcb.num_blocks:
                    block_num = fcb.start_block + block_index
                    start = block_num * self.block_size
                    end = start + self.block_size
                    content_bytes = content.encode('utf-8').ljust(self.block_size, b'\x00')
                    if len(content_bytes) > self.block_size:
                        content_bytes = content_bytes[:self.block_size]
                    
                    self.disk[start:end] = content_bytes
                    st.success(f"文件 '{filename}' (位于 '{path}') 逻辑盘块 {block_index} (物理盘块 {block_num}) 内容已修改!")
                else:
                    st.error("逻辑盘块索引超出范围!")
            else:
                st.error(f"文件 '{filename}' 在目录 '{path}' 中不存在!")

    def show_disk_allocation_map(self):
        """显示磁盘分配图，基于空闲盘块表"""
        with self.lock:
            st.markdown("#### 磁盘分配图 (空闲盘块表)")
            
            # 1. 创建一个映射，从盘块号到文件名
            block_to_file_map = {}
            
            # 递归函数来遍历所有目录和文件
            def collect_file_blocks(directory):
                for fcb in directory.files.values():
                    for i in range(fcb.num_blocks):
                        block_num = fcb.start_block + i
                        block_to_file_map[block_num] = fcb.filename
                for subdir in directory.subdirectories.values():
                    collect_file_blocks(subdir)
            
            collect_file_blocks(self.root)

            # 2. 准备要在DataFrame中显示的数据
            map_data = []
            
            # 添加已分配块
            for block_num in range(self.block_count):
                if any(start <= block_num < start + length for start, length in self.free_block_list):
                    state = "空闲"
                    owner = "N/A"
                else:
                    state = "占用"
                    owner = block_to_file_map.get(block_num, "未知")
                map_data.append({"盘块号": block_num, "状态": state, "占用者": owner})
            
            if map_data:
                map_df = pd.DataFrame(map_data)
                st.dataframe(map_df, use_container_width=True, height=400)
                
                # 显示空闲盘块表
                st.markdown("#### 空闲盘块表")
                free_table = []
                for i, (start, length) in enumerate(self.free_block_list):
                    free_table.append({
                        "序号": i+1,
                        "起始盘块": start,
                        "长度": length,
                        "结束盘块": start + length - 1
                    })
                
                if free_table:
                    free_df = pd.DataFrame(free_table)
                    st.dataframe(free_df)
                else:
                    st.info("没有空闲盘块")
            else:
                st.write("磁盘分配图为空。")
                

    def create_directory(self, path):
        with self.lock:
            if not path or path.strip() in ["", "/", "c", "c/"]:
                st.error("无效的目录路径或试图创建根目录！")
                return
            parts = path.strip('/').split('/')
            new_dir_name = parts[-1]
            parent_path = "/".join(parts[:-1])
            if not parent_path:
                parent_path = 'c'
            parent_dir = self._find_directory(parent_path)
            if not parent_dir:
                st.error(f"父目录 '{parent_path}' 不存在!")
                return
            if new_dir_name in parent_dir.subdirectories:
                st.error(f"目录 '{new_dir_name}' 在 '{parent_path}' 中已存在!")
            else:
                new_dir = Directory(name=new_dir_name, parent=parent_dir)
                parent_dir.subdirectories[new_dir_name] = new_dir
                st.success(f"目录 '{path}' 创建成功!")

    def delete_directory(self, path):
        with self.lock:
            if path.lower() in ['c', 'c/']:
                st.error("不可删除根目录 'c'!")
                return
            target_dir = self._find_directory(path)
            if not target_dir:
                st.error(f"目录 '{path}' 不存在!")
                return
            if target_dir.files or target_dir.subdirectories:
                st.error(f"目录 '{path}' 不为空，无法删除!")
            else:
                parent_dir = target_dir.parent
                if parent_dir:
                    del parent_dir.subdirectories[target_dir.name]
                    st.success(f"目录 '{path}' 删除成功!")

    def _find_directory(self, path):
        if not path or not isinstance(path, str): return None
        path = path.strip().lower()
        if path in ['c', 'c/', '/c', '/']: return self.root
        if not path.startswith('c'):
            path = 'c/' + path.lstrip('/')
        path = re.sub(r'/+', '/', path).rstrip('/')
        parts = path.split('/')[1:]
        current_dir = self.root
        for part in parts:
            if not part: continue
            if part in current_dir.subdirectories:
                current_dir = current_dir.subdirectories[part]
            else:
                return None
        return current_dir

    def show_directory(self):
        with st.expander("📁 目录结构", expanded=True):
            tree_lines = ["c:/"]
            self._build_tree_lines(self.root, "", tree_lines)
            st.code("\n".join(tree_lines), language="plaintext")

    def _build_tree_lines(self, directory, prefix, tree_lines):
        files = sorted(list(directory.files.values()), key=lambda x: x.filename)
        subdirectories = sorted(list(directory.subdirectories.values()), key=lambda x: x.name)
        items = subdirectories + files
        for i, item in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = "└└── " if is_last else "├── "
            if isinstance(item, Directory):
                tree_lines.append(f"{prefix}{connector}📁 {item.name}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                self._build_tree_lines(item, new_prefix, tree_lines)
            else:
                file_info = f"{item.filename} (大小: {item.size} B, 起始块: {item.start_block}, 块数: {item.num_blocks})"
                tree_lines.append(f"{prefix}{connector}📄📄 {file_info}")

    def get_all_directory_paths(self):
        paths = ['c/']
        self._get_paths_recursive(self.root, paths)
        return sorted(set(paths))

    def _get_paths_recursive(self, directory, path_list):
        for subdir in directory.subdirectories.values():
            path_list.append(subdir.get_full_path())
            self._get_paths_recursive(subdir, path_list)

    def get_physical_block(self, filename, block_index, path):
        """
        根据文件的逻辑盘块索引，计算并返回其在磁盘上的物理盘块号。
        """
        with self.lock:
            target_dir = self._find_directory(path)
            if not target_dir or filename not in target_dir.files:
                return None
                
            fcb = target_dir.files[filename]
            if not (0 <= block_index < fcb.num_blocks):
                return None
                
            return fcb.start_block + block_index