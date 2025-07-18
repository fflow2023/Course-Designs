import streamlit as st
from modules.disk import Disk
from modules.memory import MemoryManager
from modules.scheduler import Scheduler
from modules.interface import streamlit_interface

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