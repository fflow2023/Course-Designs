import javax.swing.*;
import java.awt.*;
import java.util.Stack;

/**
 * 类名称：Tower
 * 类描述：Tower类代表汉诺塔游戏中的一个塔，它继承自JComponent，用于在GUI中绘制塔和其上的圆盘。
 */
public class Tower extends JComponent {
    public static final int DISK_CAPACITY = 9; // 塔能容纳的最大圆盘数量
    public static final int ROD_THICKNESS = 8; // 柱子的粗细
    public static final int LABEL_HEIGHT = 35; // 塔标签的高度

    private String name; // 塔的显示名称

    // 所有圆盘对象，使用栈来存储，栈顶为最上面的圆盘
    private Stack<Disk> disks = null;

    // 构建空的塔
    public Tower(String name) {
        this(name, 0); // 调用本类构造方法
    }

    // 构建初始化圆盘数的塔
    public Tower(String name, int numberOfDisk) {
        this.name = name;
        // 初始化圆盘栈
        disks = new Stack<>();
        // 添加圆盘到塔上，编号从0开始，最上面的圆盘编号为0
        for (int i = 0; i < numberOfDisk; i++) {
            disks.push(new Disk(numberOfDisk - i - 1, i));
        }
        initComponent(); // 初始化组件
    }

    // 初始化页面组件
    private void initComponent() {
        JLabel tipLabel = new JLabel(name, JLabel.CENTER); // 创建标签显示塔的名称
        tipLabel.setSize(getLength(), LABEL_HEIGHT); // 设置标签大小
        tipLabel.setLocation(0, getLength()); // 设置标签位置
        add(tipLabel); // 将标签添加到塔组件中

        // 设置塔组件的首选大小
        setPreferredSize(new Dimension(getLength(), getLength() + LABEL_HEIGHT));
    }

    // 计算塔的长度（横塔和竖塔相同）
    public static int getLength() {
        return Disk.getThickness() * (DISK_CAPACITY + 1) + ROD_THICKNESS; //  一个塔高出一个厚度和塔的粗度
    }

    // 添加圆盘操作
    public Disk pushDisk(Disk disk) {
        disk.setOrder(disks.size()); // 设置圆盘的顺序
        return disks.push(disk); // 将圆盘压入栈中,返回添加的圆盘
    }

    // 弹出最上面的圆盘
    public Disk popDisk() {
        return disks.pop(); // 从栈中弹出最上面的圆盘
    }

    // 更新数据和组件
    public void update() {
        repaint(); // 重新绘制，触发paintComponent方法
    }

    // 重写JComponent的paintComponent方法，用于绘制塔和其上的圆盘
    @Override
    public void paintComponent(Graphics g) {
        super.paintComponent(g); // 调用父类的paintComponent方法
        ((Graphics2D)g).setStroke(new BasicStroke(ROD_THICKNESS)); // 设置绘制塔的线条粗细
        g.setColor(Colors.rodColors[1]); // 设置塔的颜色
        g.fillRect(0, getLength() - ROD_THICKNESS, getLength(), 2*ROD_THICKNESS); // 绘制塔的水平部分
        g.fillRect((getLength() - ROD_THICKNESS) / 2, 0, ROD_THICKNESS, getLength()); // 绘制塔的垂直部分
        // 绘制塔上的所有圆盘
        for(Disk disk: disks) {
            disk.paint(g);
        }
    }
}
