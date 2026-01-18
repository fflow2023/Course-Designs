// thermometer.c
#include <intrins.h>
#include <reg52.h>
#define uint unsigned int
#define uchar unsigned char
#include "eeprom52.h"
typedef signed int s16;
typedef signed char s8;

/* 引脚定义：按键、蜂鸣器、报警灯、DS18B20 数据线、小数点控制 */
sbit KEY_MODE = P3 ^ 1;
sbit KEY_DEC = P3 ^ 2;     // INT0，阈值减少键
sbit KEY_INC = P3 ^ 3;     // INT1，阈值增加键
sbit BUZZER = P3 ^ 6;      // 低电平有效
sbit ALARM_LED_H = P1 ^ 6; // 低电平点亮（高温报警指示）
sbit ALARM_LED_L = P1 ^ 7; // 低电平点亮（低温报警指示）
sbit DS18B20_DQ = P3 ^ 7;  // DS18B20 单总线数据线
sbit DOT = P0 ^ 7;         // 数码管小数点控制位

/* 常量定义：温度单位为 0.1℃，阈值单位为 ℃ */
#define TEMP_MIN_DECI_C (-550) // -55.0℃
#define TEMP_MAX_DECI_C (1250) // 125.0℃
#define THRESH_MIN_C (-55)
#define THRESH_MAX_C (125)

/* 共阳极：输出0点亮，输出1熄灭 */
unsigned char code SEG_CODE[10] = {0xC0, 0xF9, 0xA4, 0xB0, 0x99, 0x92, 0x82, 0xF8, 0x80, 0x90};

/* 全局变量：显示闪烁、报警翻转、温度有效标志、阈值与温度缓存 */
bit blink = 0;
bit alarmFlip = 0;
bit temp_valid = 0;

s8 thHigh = 28; // 高温阈值（℃）
s8 thLow = 20;  // 低温阈值（℃）

volatile s16 temp = 250;      // 当前温度（0.1℃），上电先给 25.0℃
volatile uint g_tick50ms = 0; // 50ms 节拍计数

uchar mode = 0; // 0=正常显示；1=设置上限；2=设置下限

/* 计算从 start 到当前经过的 tick 数（50ms 为单位） */
static uint TickElapsed(uint start) {
    return (uint)(g_tick50ms - start); // 利用无符号回卷特性
}

/* EEPROM 写入：保存高低阈值与初始化标志 */
void SaveEEPROM(void) {
    SectorErase(0x2000);                // 擦除参数扇区
    byte_write(0x2000, (uchar)thHigh);  // 写入高温阈值
    byte_write(0x2001, (uchar)thLow);   // 写入低温阈值
    byte_write(0x2060, eepromInitFlag); // 写入初始化标志
}

/* EEPROM 读取：加载高低阈值与初始化标志 */
void LoadEEPROM(void) {
    thHigh = (s8)byte_read(0x2000);     // 读高温阈值
    thLow = (s8)byte_read(0x2001);      // 读低温阈值
    eepromInitFlag = byte_read(0x2060); // 读初始化标志
}

/* 修正阈值：用于调整高温阈值后，限制范围并保证 thHigh > thLow */
void FixThAfterHigh(void) {
    if (thHigh > THRESH_MAX_C)
        thHigh = THRESH_MAX_C; // 上限保护
    if (thHigh < THRESH_MIN_C)
        thHigh = THRESH_MIN_C; // 下限保护
    if (thLow > THRESH_MAX_C)
        thLow = THRESH_MAX_C; // 上限保护
    if (thLow < THRESH_MIN_C)
        thLow = THRESH_MIN_C; // 下限保护
    if (thHigh <= thLow) {
        thHigh = thLow + 1; // 保证高阈值比低阈值至少大 1℃
        if (thHigh > THRESH_MAX_C) {
            thHigh = THRESH_MAX_C; // 高阈值顶到最大
            thLow = thHigh - 1;    // 低阈值随动
        }
    }
}

/* 修正阈值：用于调整低温阈值后，限制范围并保证 thLow < thHigh */
void FixThAfterLow(void) {
    if (thHigh > THRESH_MAX_C)
        thHigh = THRESH_MAX_C; // 上限保护
    if (thHigh < THRESH_MIN_C)
        thHigh = THRESH_MIN_C; // 下限保护
    if (thLow > THRESH_MAX_C)
        thLow = THRESH_MAX_C; // 上限保护
    if (thLow < THRESH_MIN_C)
        thLow = THRESH_MIN_C; // 下限保护

    if (thLow >= thHigh) {
        thLow = thHigh - 1; // 保证低阈值比高阈值至少小 1℃
        if (thLow < THRESH_MIN_C) {
            thLow = THRESH_MIN_C; // 低阈值顶到最小
            thHigh = thLow + 1;   // 高阈值随动
        }
    }
}

/* 参数初始化：从 EEPROM 读取阈值，若无效则写入默认值并保存 */
void InitParam(void) {
    LoadEEPROM(); // 读取历史参数

    if (eepromInitFlag != 1) { // 未初始化或数据无效
        thHigh = 28;           // 默认高温阈值
        thLow = 20;            // 默认低温阈值
        eepromInitFlag = 1;    // 写入初始化标志
        FixThAfterHigh();      // 合法性修正
        SaveEEPROM();          // 保存默认参数
    } else {
        FixThAfterHigh(); // 已初始化也修正，避免越界
    }
}

/* DS18B20 粗延时：用于单总线读写时序 */
static void DelayDs18b20(uint t) {
    while (t--)
        ; // 空循环延时
}

/* DS18B20 复位：拉低复位脉冲并等待存在脉冲 */
static void Ds18b20Reset(void) {
    DS18B20_DQ = 1;
    DelayDs18b20(8); // 释放总线

    DS18B20_DQ = 0;
    DelayDs18b20(80); // 复位脉冲

    DS18B20_DQ = 1;
    DelayDs18b20(34); // 等待存在响应
}

/* DS18B20 写字节：低位先行写入 */
static void Ds18b20WriteByte(uchar dat) {
    uchar i;
    for (i = 0; i < 8; i++) {
        DS18B20_DQ = 0;            // 开始写时隙
        DS18B20_DQ = (dat & 0x01); // 写当前位
        DelayDs18b20(5);           // 保持
        DS18B20_DQ = 1;            // 释放总线
        dat >>= 1;                 // 下一位
    }
}

/* DS18B20 读字节：低位先行读取 */
static uchar Ds18b20ReadByte(void) {
    uchar i;
    uchar dat = 0;
    for (i = 0; i < 8; i++) {
        DS18B20_DQ = 0; // 产生读时隙
        dat >>= 1;      // 为新位腾位置
        DS18B20_DQ = 1; // 释放总线
        if (DS18B20_DQ)
            dat |= 0x80; // 读到 1 则置位
        DelayDs18b20(4); // 时隙补足
    }
    return dat;
}

/* DS18B20 读 1bit：用于轮询转换完成（完成为 1） */
static bit Ds18b20ReadBit(void) {
    bit b;
    EA = 0; // 关总中断，保证时序
    DS18B20_DQ = 0;
    _nop_(); // 短延时
    DS18B20_DQ = 1;
    DelayDs18b20(2); // 读窗口
    b = DS18B20_DQ;  // 采样数据
    EA = 1;          // 开总中断
    DelayDs18b20(6); // 补足时隙
    return b;
}

/* 启动一次 DS18B20 温度转换 */
static void DS18B20_StartConvert(void) {
    EA = 0;                 // 关总中断
    Ds18b20Reset();         // 复位
    Ds18b20WriteByte(0xCC); // Skip ROM (跳过寻址)
    Ds18b20WriteByte(0x44); // Convert T (启动温度转换)
    EA = 1;                 // 开总中断
}

/* 读取一次温度并转换为 0.1℃，再量化到 0.5℃ */
static s16 DS18B20_ReadTempOnce(void) {
    uchar lowByte, highByte;
    s16 raw;
    long tmp;
    s16 result;

    EA = 0;                       // 关总中断
    Ds18b20Reset();               // 复位
    Ds18b20WriteByte(0xCC);       // Skip ROM (跳过寻址)
    Ds18b20WriteByte(0xBE);       // Read Scratchpad (读暂存器温度)
    lowByte = Ds18b20ReadByte();  // 温度低字节
    highByte = Ds18b20ReadByte(); // 温度高字节
    EA = 1;                       // 开总中断

    raw = (s16)((highByte << 8) | lowByte); // 原始温度（1/16℃）

    if (raw >= 0) {
        tmp = (long)raw * 10 + 8; // 转 0.1℃并做四舍五入补偿
        result = (s16)(tmp / 16); // 得到 0.1℃
    } else {
        tmp = (long)raw * 10 - 8; // 负数同样补偿
        result = (s16)(tmp / 16);
    }

    if (result >= 0)
        result = ((result + 2) / 5) * 5; // 量化到 0.5℃
    else
        result = ((result - 2) / 5) * 5; // 量化到 0.5℃

    if (result > TEMP_MAX_DECI_C)
        result = TEMP_MAX_DECI_C; // 上限
    if (result < TEMP_MIN_DECI_C)
        result = TEMP_MIN_DECI_C; // 下限

    return result;
}

/* DS18B20 状态机变量：0=空闲启动转换；1=等待完成后读取 */
static uchar ds_state = 0;
static uint ds_startTick = 0;

/* DS18B20 后台任务：非阻塞采样温度 */
static void DS18B20_Task(void) {
    if (ds_state == 0) {
        DS18B20_StartConvert();    // 启动转换
        ds_startTick = g_tick50ms; // 记录起始 tick
        ds_state = 1;              // 进入等待状态
        return;
    }

    if (Ds18b20ReadBit() || TickElapsed(ds_startTick) >= 16) { // 完成或超时 800 ms
        s16 t = DS18B20_ReadTempOnce();                        // 读取温度
        if (!temp_valid && t == 850) {                         // 丢弃上电默认 85.0℃
            ds_state = 0;
            return;
        }
        temp = t;       // 更新温度缓存
        temp_valid = 1; // 置有效标志
        ds_state = 0;   // 回到空闲
    }
}

/* 软件延时：用于消抖与显示扫描 */
static void Delay(uint t) {
    while (--t)
        ; // 空循环延时
}

/* 初始化定时器0：产生约 50ms 的节拍，并配置外部中断触发方式 */
static void InitTimer0(void) {
    TMOD = 0x01; // 定时器0方式1
    TH0 = 0x3C;  // 重装初值
    TL0 = 0xB0;

    EA = 1;  // 开总中断
    ET0 = 1; // 开定时器0中断
    TR0 = 1; // 启动定时器0

    IT0 = 1; // INT0 下降沿触发
    IT1 = 1; // INT1 下降沿触发
}

/* 开机动画：依次选通数码管各位 */
static void DisplayBoot(void) {
    P0 = 0xBF; // 显示“-”的段码

    P2 = 0xBF; // 第1位
    Delay(200);
    P2 = 0xEF; // 第2位
    Delay(200);
    P2 = 0xFB; // 第3位
    Delay(200);
    P2 = 0xFE; // 第4位
    Delay(200);

    P2 = 0xFF; // 全部关闭
}

/* 显示温度：输入为 0.1℃，格式为 XXX.X（带符号） */
static void DispTemp(s16 tempDeciC) {
    s16 absTemp;
    bit isNegative;
    uint value;
    if (tempDeciC < 0) {
        isNegative = 1;       // 负号标志
        absTemp = -tempDeciC; // 取绝对值
    } else {
        isNegative = 0;
        absTemp = tempDeciC;
    }
    value = (uint)absTemp; // 转无符号便于拆位
    {
        uchar digitThousand = (uchar)(value / 1000);      // 100.0 位
        uchar digitHundred = (uchar)(value % 1000 / 100); // 10.0 位
        uchar digitTen = (uchar)(value % 100 / 10);       // 1.0 位
        uchar digitOne = (uchar)(value % 10);             // 0.1 位

        P0 = SEG_CODE[digitOne]; // 显示 0.1 位
        P2 = 0xBF;
        Delay(200);
        P2 = 0xFF;

        P0 = SEG_CODE[digitTen]; // 显示 1.0 位
        P2 = 0xEF;
        DOT = 0; // 点亮小数点
        Delay(200);
        P2 = 0xFF;

        if ((digitThousand + digitHundred) != 0)
            P0 = SEG_CODE[digitHundred]; // 显示 10.0 位
        else
            P0 = 0xFF; // 前导零空白
        P2 = 0xFB;
        Delay(200);
        P2 = 0xFF;
        if (isNegative)
            P0 = 0xBF; // 显示负号
        else if (digitThousand != 0)
            P0 = SEG_CODE[digitThousand]; // 显示 100.0 位
        else
            P0 = 0xFF; // 空白
        P2 = 0xFE;
        Delay(200);
        P2 = 0xFF;
    }
}

/* 设置模式显示：三位数字可闪烁，第4位固定显示 H 或 L */
static void DispThBlink(s8 thresholdC, bit showDigits) {
    s8 absC;
    bit isNegative;
    uchar hundred, ten, one;

    if (thresholdC < 0) {
        isNegative = 1;     // 负号标志
        absC = -thresholdC; // 取绝对值
    } else {
        isNegative = 0;
        absC = thresholdC;
    }

    hundred = (uchar)(absC / 100);  // 百位
    ten = (uchar)(absC % 100 / 10); // 十位
    one = (uchar)(absC % 10);       // 个位

    P0 = showDigits ? SEG_CODE[one] : 0xFF; // 个位闪烁控制
    P2 = 0xBF;
    Delay(100);
    P2 = 0xFF;

    P0 = showDigits ? SEG_CODE[ten] : 0xFF; // 十位闪烁控制
    P2 = 0xEF;
    Delay(100);
    P2 = 0xFF;

    if (showDigits) {
        if (isNegative)
            P0 = 0xBF; // 百位显示负号
        else if (hundred != 0)
            P0 = SEG_CODE[hundred]; // 显示百位
        else
            P0 = 0xFF; // 前导零空白
    } else {
        P0 = 0xFF; // 熄灭实现闪烁
    }

    P2 = 0xFB;
    Delay(100);
    P2 = 0xFF;

    if (mode == 1)
        P0 = 0x89; // 显示 H
    else
        P0 = 0xC7; // 显示 L

    P2 = 0xFE;
    Delay(100);
    P2 = 0xFF;
}

/* 报警检测：比较温度与上下阈值，控制灯与蜂鸣器闪烁 */
static void AlarmCheck(s16 tempDeciC) {
    static uint lastFlipTick = 0;

    if (TickElapsed(lastFlipTick) >= 10) { // 500ms 翻转一次节奏
        alarmFlip = ~alarmFlip;            // 翻转相位
        lastFlipTick = g_tick50ms;         // 记录时间
    }

    if (tempDeciC > (s16)thHigh * 10) { // 高温报警
        ALARM_LED_L = 1;                // 低温灯熄灭
        if (alarmFlip) {
            ALARM_LED_H = 0; // 高温灯点亮
            BUZZER = 0;      // 蜂鸣器响
        } else {
            ALARM_LED_H = 1; // 高温灯熄灭
            BUZZER = 1;      // 蜂鸣器停
        }
    } else if (tempDeciC < (s16)thLow * 10) { // 低温报警
        ALARM_LED_H = 1;                      // 高温灯熄灭
        if (alarmFlip) {
            ALARM_LED_L = 0; // 低温灯点亮
            BUZZER = 0;      // 蜂鸣器响
        } else {
            ALARM_LED_L = 1; // 低温灯熄灭
            BUZZER = 1;      // 蜂鸣器停
        }
    } else {
        ALARM_LED_H = 1; // 正常：关闭指示灯
        ALARM_LED_L = 1;
        BUZZER = 1; // 正常：关闭蜂鸣器
    }
}

/* 主程序：初始化后循环执行采样、按键处理、显示与报警 */
void main(void) {
    uint i;
    uint blinkStartTick = 0;
    InitParam();     // 初始化阈值参数
    InitTimer0();    // 初始化定时器与外部中断
    ALARM_LED_H = 1; // 默认不报警
    ALARM_LED_L = 1;
    BUZZER = 1;
    ds_state = 0; // DS18B20 状态机复位
    for (i = 0; i < 300; i++)
        DisplayBoot(); // 开机动画
    while (1) {
        DS18B20_Task(); // 后台温度采样
        if (KEY_MODE == 0) {
            BUZZER = 0;  // 按键提示音
            Delay(2000); // 消抖
            BUZZER = 1;
            while (KEY_MODE == 0)
                ; // 等待释放

            ALARM_LED_H = 1; // 切换模式时先关闭报警
            ALARM_LED_L = 1;
            BUZZER = 1;
            mode++;    // 切换模式
            blink = 1; // 进入设置默认显示
            blinkStartTick = g_tick50ms;
            if (mode > 2) {
                mode = 0;     // 返回正常模式
                SaveEEPROM(); // 保存阈值
            }
        }
        if (mode == 0) {
            EX0 = 0; // 关闭阈值调节中断
            EX1 = 0;
            DispTemp(temp); // 显示温度
            if (temp_valid)
                AlarmCheck(temp); // 温度有效后报警判断
        } else if (mode == 1) {
            BUZZER = 1;
            EX0 = 1; // 开启减/加键中断
            EX1 = 1;
            if (TickElapsed(blinkStartTick) >= 10) {
                blink = ~blink;              // 翻转闪烁状态
                blinkStartTick = g_tick50ms; // 更新节拍
            }
            DispThBlink(thHigh, blink); // 显示高阈值
        } else {
            BUZZER = 1;
            EX0 = 1;
            EX1 = 1;
            if (TickElapsed(blinkStartTick) >= 10) {
                blink = ~blink;              // 翻转闪烁状态
                blinkStartTick = g_tick50ms; // 更新节拍
            }
            DispThBlink(thLow, blink); // 显示低阈值
        }
    }
}

/* 定时器0中断：产生 50ms 节拍，供状态机与闪烁使用 */
void timer0_isr(void) interrupt 1 { // 方式1
    TH0 = 0x3C;                     // 重装初值
    TL0 = 0xB0;
    g_tick50ms++; // 50ms 计数加 1
}

/* 外部中断0：减少键，设置模式下调整阈值 */
void int0_isr(void) interrupt 0 {
    EX0 = 0; // 关闭自身中断，防止抖动重复触发
    if (KEY_DEC == 0) {
        BUZZER = 0;  // 提示音
        Delay(2000); // 消抖
        BUZZER = 1;
        while (KEY_DEC == 0) {
            if (mode == 1)
                DispThBlink(thHigh, 1); // 按住时保持显示
            else if (mode == 2)
                DispThBlink(thLow, 1);
        }
        if (mode == 1) {
            thHigh--;         // 高阈值减 1℃
            FixThAfterHigh(); // 修正合法性
        } else if (mode == 2) {
            thLow--;         // 低阈值减 1℃
            FixThAfterLow(); // 修正合法性
        }
    }
    EX0 = 1; // 恢复外部中断0
}

/* 外部中断1：增加键，设置模式下调整阈值 */
void int1_isr(void) interrupt 2 {
    EX1 = 0; // 关闭自身中断，防止抖动重复触发
    if (KEY_INC == 0) {
        BUZZER = 0;  // 提示音
        Delay(2000); // 消抖
        BUZZER = 1;
        while (KEY_INC == 0) {
            if (mode == 1)
                DispThBlink(thHigh, 1); // 按住时保持显示
            else if (mode == 2)
                DispThBlink(thLow, 1);
        }
        if (mode == 1) {
            thHigh++;         // 高阈值加 1℃
            FixThAfterHigh(); // 修正合法性
        } else if (mode == 2) {
            thLow++;         // 低阈值加 1℃
            FixThAfterLow(); // 修正合法性
        }
    }
    EX1 = 1; // 恢复外部中断1
}
