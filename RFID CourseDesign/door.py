import paho.mqtt.client as mqtt
from queue import Queue, Empty
import json
import time
import datetime
import csv
import os
import logging
from typing import Dict, Any

# =========================
# 配置区域
# =========================
BROKER_IP = "127.0.0.1"
BROKER_PORT = 1883

TOPIC_SUB = "1766474118996/AIOTSIM2APP"
TOPIC_PUB = "1766474118996/APP2AIOTSIM"

# 权限库 JSON 文件路径
CARD_DB_PATH = "card.json"

# 门禁策略参数
CARD_DEBOUNCE_SEC = 3          # 同一张卡 3 秒内重复刷卡视为抖动/误触发
DOOR_OPEN_HOLD_SEC = 5         # 开门后保持 N 秒，然后自动落锁
ALARM_AFTER_ERROR_COUNT = 3    # 连续非法/异常刷卡次数达到阈值触发报警
ALARM_BEEP_SEC = 3           # 报警持续时间（蜂鸣器/红灯）

# 工作时间策略（仅 staff/visitor 生效；admin 不受限）
WORKDAY_START_HOUR = 8
WORKDAY_END_HOUR = 18

# =========================
# 日志（工程化logging ，便于以后落盘/分级）
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("door_access")

# =========================
# 权限库加载与校验
# =========================
def _write_default_card_db(path: str) -> None:
    """
    当 card.json 不存在时，写一个模板文件，避免用户不知道格式。
    """
    template = {
        "0D00072100": {"name": "老王", "role": "admin", "status": "ok"},
        "0D00072101": {"name": "张三", "role": "staff", "status": "ok"},
        "0D00072102": {"name": "李四", "role": "staff", "status": "lost"},
        "0D00072103": {"name": "赵六", "role": "staff", "status": "black"},
        "0D00072104": {"name": "Tony", "role": "visitor", "status": "ok"},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)


def load_user_db(path: str) -> Dict[str, Dict[str, str]]:
    """
    从 card.json 读取权限库，并做最基本的字段校验，避免运行期 KeyError。
    期望格式：
    {
      "卡号": {"name": "...", "role": "admin|staff|visitor", "status": "ok|lost|black"},
      ...
    }
    """
    if not os.path.exists(path):
        _write_default_card_db(path)
        raise SystemExit(
            f"未找到 {path}，已自动生成模板文件。请编辑后重新运行。"
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise SystemExit(f"读取 {path} 失败：{e}")

    if not isinstance(data, dict):
        raise SystemExit(f"{path} 格式错误：根节点必须是 JSON 对象(dict)。")

    allowed_roles = {"admin", "staff", "visitor"}
    allowed_status = {"ok", "lost", "black"}

    user_db: Dict[str, Dict[str, str]] = {}
    for card_id, info in data.items():
        if not isinstance(card_id, str) or not card_id.strip():
            raise SystemExit("card.json 存在非法卡号（空/非字符串）。")

        if not isinstance(info, dict):
            raise SystemExit(f"卡号 {card_id} 的信息必须是对象(dict)。")

        name = str(info.get("name", "")).strip()
        role = str(info.get("role", "")).strip()
        status = str(info.get("status", "")).strip()

        if not name:
            raise SystemExit(f"卡号 {card_id} 缺少 name。")
        if role not in allowed_roles:
            raise SystemExit(f"卡号 {card_id} 的 role 非法：{role}。")
        if status not in allowed_status:
            raise SystemExit(f"卡号 {card_id} 的 status 非法：{status}。")

        user_db[card_id.strip()] = {"name": name, "role": role, "status": status}

    if not user_db:
        raise SystemExit("card.json 为空：至少需要一条卡号记录。")

    logger.info("权限库加载成功：%d 张卡", len(user_db))
    return user_db


# =========================
# 门禁控制器：核心业务逻辑
# =========================
class DoorController:
    """
    DoorController 负责：
    - 权限校验（存在性、挂失/黑名单、工作时间）
    - 反潜回（单读卡器模拟进/出状态切换）
    - 自动落锁（避免门一直保持开锁）
    - 报警输出（蜂鸣器/红灯）
    - CSV 审计日志（便于答辩展示、事后追溯）
    """

    def __init__(self, client: mqtt.Client, user_db: Dict[str, Dict[str, str]]):
        self.client = client
        self.user_db = user_db

        # per-card 状态缓存：inside 表示“是否在门内”，last_ts 用于防抖
        self.last_state_check: Dict[str, Dict[str, Any]] = {}

        # 门的“逻辑开锁”状态
        self.door_open_ts = 0.0
        self.is_door_open = False

        # 连续错误计数：用于检测“多次非法尝试”
        self.error_count = 0

        # CSV 审计日志
        self.log_file = "access_log.csv"
        self._init_csv_log()

    def _init_csv_log(self) -> None:
        """初始化 CSV 文件（不存在则创建并写表头）。"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["时间", "卡号", "姓名", "动作", "结果", "备注"])

    def check_auto_close(self) -> None:
        """
        周期性任务：自动落锁。
        工程化做法：主循环里“短周期轮询”，而不是开线程 sleep，
        避免多线程竞态（尤其是 I/O + 状态机场景）。
        """
        if not self.is_door_open:
            return

        elapsed = time.time() - self.door_open_ts
        if elapsed > DOOR_OPEN_HOLD_SEC:
            logger.info("超时自动落锁（开锁已持续 %.1fs）", elapsed)
            self.send_cmd({"doorLock": False, "id": 0})
            self.is_door_open = False

    def handle_card(self, card_id: str) -> None:
        """
        刷卡入口：对卡号进行校验并执行开门/报警/记录日志。
        """
        now_ts = time.time()
        now_dt = datetime.datetime.now()

        # 1) 卡号是否在权限库内
        user = self.user_db.get(card_id)
        if not user:
            self.log_event(card_id, "未知", "刷卡", False, "查无此人")
            self.error_count += 1
            if self.error_count >= ALARM_AFTER_ERROR_COUNT:
                self.trigger_alarm("非法闯入尝试（多次未知卡）")
            return

        # 取出该卡的历史状态；没有就初始化
        state = self.last_state_check.get(card_id, {"inside": False, "last_ts": 0.0})

        # 2) 物理防抖：短时间内重复刷卡忽略（防误触发/抖动）
        if now_ts - float(state["last_ts"]) < CARD_DEBOUNCE_SEC:
            logger.info("卡号 %s 刷卡过快（<%ds），忽略", card_id, CARD_DEBOUNCE_SEC)
            return

        # 3) 黑名单/挂失检查：直接拒绝并可触发报警
        if user["status"] != "ok":
            reason = "黑名单" if user["status"] == "black" else "挂失卡"
            logger.warning("拒绝通行：%s（%s）", reason, user["name"])
            self.trigger_alarm(reason)
            self.log_event(card_id, user["name"], "刷卡", False, reason)
            return

        # 4) 时间策略：仅员工/访客受限，管理员可随时通行
        if user["role"] != "admin":
            is_workday = now_dt.weekday() < 5  # 0~4 表示周一到周五
            is_worktime = WORKDAY_START_HOUR <= now_dt.hour < WORKDAY_END_HOUR
            if not (is_workday and is_worktime):
                self.log_event(card_id, user["name"], "刷卡", False, "非工作时间")
                logger.info("拒绝通行：非工作时间（%s）", user["name"])
                return

        # 5) 反潜回
        action = "出门" if state["inside"] else "进门"

        # 6) 执行开门（发布 MQTT 指令给执行端）
        logger.info("允许通行：%s (%s) %s", user["name"], user["role"] , action)
        self.send_cmd({"doorLock": True, "id": 0})

        # 更新门状态：用于自动落锁
        self.is_door_open = True
        self.door_open_ts = now_ts

        # 刷对了：清空连续错误计数
        self.error_count = 0

        # 更新该卡状态：切换 inside，并记录本次刷卡时间用于防抖
        state["inside"] = not bool(state["inside"])
        state["last_ts"] = now_ts
        self.last_state_check[card_id] = state

        # 审计日志
        self.log_event(card_id, user["name"], action, True, "正常通行")

    def trigger_alarm(self, reason: str) -> None:
        """
        触发报警输出：蜂鸣器 + 红灯。
        工程注意点：用 try/finally 确保异常时也能关闭报警，避免“卡死一直响”。
        """
        logger.error("报警触发：%s", reason)
        try:
            self.send_cmd({"alarm": True, "id": 0})
            time.sleep(ALARM_BEEP_SEC)
        finally:
            self.send_cmd({"alarm": False, "id": 0})

    def send_cmd(self, cmd_dict: Dict[str, Any]) -> None:
        """
        将控制命令序列化为 JSON 并发布到 MQTT。
        ensure_ascii=False：保证中文字段/内容可读。
        """
        payload = json.dumps(cmd_dict, ensure_ascii=False)
        self.client.publish(TOPIC_PUB, payload)

    def log_event(self, card_id: str, name: str, action: str, success: bool, reason: str) -> None:
        """
        审计日志：
        - 控制台/日志：便于实时观察
        - CSV：便于 Excel 打开、汇报展示、事后追溯
        """
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result_str = "成功" if success else "失败"

        # 日志输出
        if success:
            logger.info("%s(%s) - %s - %s：%s", name, card_id, action, result_str, reason)
        else:
            logger.warning("%s(%s) - %s - %s：%s", name, card_id, action, result_str, reason)

        # CSV 落盘（utf-8-sig）
        with open(self.log_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([now_str, card_id, name, action, result_str, reason])


# =========================
# MQTT 包装：连接、订阅、消息入队
# =========================
class HQYJMqttClient:
    """
    说明：
    - on_message 回调里只做“轻量处理 + 入队”，避免阻塞 MQTT 网络线程
    - 主循环从队列取数据做业务逻辑
    """

    def __init__(self, broker_ip: str, broker_port: int):
        self.mqtt_queue: Queue = Queue(maxsize=255)

        # paho-mqtt 客户端
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect

        # 连接状态码：0 表示成功（paho 定义）
        self.rc = 100

        try:
            self.client.connect(broker_ip, broker_port, keepalive=3)
        except Exception as e:
            logger.error("MQTT 连接失败：%s", e)

    def on_message(self, client, userdata, message) -> None:
        """
        消息回调：
        - 尽量容错：解析失败直接忽略（模拟器/现场数据可能不稳定）
        - 队列过大时丢弃最老的，保留最新的
        """
        try:
            msg = json.loads(message.payload.decode(errors="ignore"))
        except Exception:
            return

        if "RFID_125K" not in msg:
            return

        try:
            if self.mqtt_queue.qsize() > 200:
                self.mqtt_queue.get_nowait()
            self.mqtt_queue.put_nowait(msg)
        except Exception:
            # 队列满/竞争条件下的异常，直接忽略即可
            pass

    def on_connect(self, client, userdata, flags, rc) -> None:
        self.rc = rc
        logger.info("MQTT 连接结果 rc=%s", rc)


# =========================
# 主程序入口
# =========================
def main() -> None:
    # 1) 加载权限库（从 card.json）
    user_db = load_user_db(CARD_DB_PATH)

    # 2) 初始化 MQTT
    hqyj_mqtt = HQYJMqttClient(BROKER_IP, BROKER_PORT)
    hqyj_mqtt.client.loop_start()

    # 3) 等待连接完成（给模拟器/网络一点时间）
    logger.info("正在连接 MQTT Broker...")
    for _ in range(10):
        if hqyj_mqtt.rc == 0:
            break
        time.sleep(0.5)

    if hqyj_mqtt.rc != 0:
        logger.error("MQTT 未连接成功（rc=%s），程序退出", hqyj_mqtt.rc)
        return

    # 4) 订阅刷卡数据主题
    hqyj_mqtt.client.subscribe(TOPIC_SUB, qos=0)
    logger.info("已订阅：%s", TOPIC_SUB)

    # 5) 初始化门禁控制器
    controller = DoorController(hqyj_mqtt.client, user_db)
    logger.info("系统就绪，请刷卡...")

    try:
        while True:
            # (A) 周期性任务：自动落锁等
            controller.check_auto_close()

            # (B) 处理刷卡消息
            try:
                mqtt_data = hqyj_mqtt.mqtt_queue.get(timeout=0.1)
            except Empty:
                continue

            raw_rfid = mqtt_data.get("RFID_125K")
            if not raw_rfid:
                continue

            # 兼容：某些模拟器会把 RFID_125K 发成 list（批量/异常格式）
            rfid_list = raw_rfid if isinstance(raw_rfid, list) else [raw_rfid]

            for card_id in rfid_list:
                clean_id = str(card_id).strip()

                # 过滤明显噪声：长度太短的直接忽略
                if len(clean_id) <= 4:
                    continue

                controller.handle_card(clean_id)

    except KeyboardInterrupt:
        logger.info("收到退出信号，系统关闭中...")

    finally:
        # 工程化收尾：停止网络循环并断开连接
        try:
            hqyj_mqtt.client.loop_stop()
            hqyj_mqtt.client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    main()
