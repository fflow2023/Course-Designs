import java.awt.*;

/**
 * 类名称：Colors
 * 类描述：此类定义了汉诺塔游戏中使用的颜色常量。它包含了一组用于圆盘的颜色数组以及用于塔的颜色数组。
 */
public class Colors {
    private static Color purple = new Color(0x80, 0x00, 0x80); // 紫色
    private static Color indigo = new Color(0x88, 0x33, 0xCC); // 淡靛蓝
    public static final Color[] diskColors = {Color.RED, Color.ORANGE, Color.YELLOW,
            Color.GREEN, Color.BLUE, indigo , purple, Color.MAGENTA, Color.PINK};

    public static final Color[] rodColors = {Color.BLACK, Color.DARK_GRAY};
}
