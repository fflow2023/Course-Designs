import java.awt.*;
/**
 * 类名称：Disk
 * 类描述：Disk类代表汉诺塔游戏中的一个圆盘。每个圆盘都有一个编号和顺序，编号表示圆盘的大小，
 * 顺序表示圆盘在塔上的位置。该类提供了获取圆盘厚度、设置圆盘顺序和绘制圆盘的方法。
 */
public class Disk {
    public static final int UNIT_SIZE = 15; // 单位大小，厚度设两层

    private int number; // 磁盘编号，从小到大0到n
    private int order; // 在柱上的顺序，从下到上0到n

    //获取圆盘厚度
    public static int getThickness() {
        return UNIT_SIZE * 2;
    }

    //创建圆盘对象
    public Disk(int number, int order) {
        this.number = number;
        this.order = order;
    }

    // 设置圆盘顺序
    public void setOrder(int order) {
        this.order = order;
    }

    // 绘制圆盘
    public void paint(Graphics g) {
        // 从预配颜色中设置颜色
        g.setColor(Colors.diskColors[number % Colors.diskColors.length]); // 轮询使用颜色
        // 绘制圆盘形状
        g.fillRect(getThickness() / 2 * (Tower.DISK_CAPACITY - number), getThickness() * (Tower.DISK_CAPACITY - order),
                getThickness() * (number + 1) + Tower.ROD_THICKNESS,  getThickness());
        // 绘制圆盘中间的数字
        g.setColor(Color.BLACK); // 设置数字颜色为黑色
        Font currentFont = g.getFont(); // 获取当前字体
        Font newFont = currentFont.deriveFont((float)(getThickness() * 0.65)); // 根据圆盘厚度调整字体大小
        g.setFont(newFont); // 设置新的字体
        FontMetrics metrics = g.getFontMetrics(newFont); // 获取字体度量
        String numberStr = String.valueOf(number + 1); // 获取圆盘编号的字符串表示
        // 计算数字绘制的位置，使其居中
        int numberX = getThickness() / 2 * (Tower.DISK_CAPACITY - number) + (getThickness() * (number + 1) + Tower.ROD_THICKNESS - metrics.stringWidth(numberStr)) / 2;
        int numberY = getThickness() * (Tower.DISK_CAPACITY - order) + (getThickness() - metrics.getHeight()) / 2 + metrics.getAscent();
        g.drawString(numberStr, numberX, numberY); // 绘制数字
    }

    // 添加 toString 方法
    @Override
    public String toString() {
        // 返回格式为 "--" + 圆盘编号+1 + "-->"
        return " --圆盘" + (number + 1) + "--> ";
    }
}
