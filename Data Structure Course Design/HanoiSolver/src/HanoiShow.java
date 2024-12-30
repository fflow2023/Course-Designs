import javax.swing.*;
import java.util.LinkedList;

/**
 * 类名称：HanoiShow
 * 类描述：此类用于展示汉诺塔游戏的动画。它继承了JComponent类，以在Swing应用程序中绘制汉诺塔的塔和圆盘。
 * 该类管理三个塔（初始塔、辅助塔和目标塔）以及圆盘的移动,并且能够按顺序执行圆盘的移动操作，直到完成整个汉诺塔的解。
 */
public class HanoiShow extends JComponent {
    //定义塔的索引
    private static final int INIT_Tower = 0;
    private static final int SPARE_Tower = 1;
    private static final int DEST_Tower = 2;
    private static final char[] letter ={'A','B','C'};
    private Tower[] towers; //三座塔
    private LinkedList<Integer> movesList;  //存储汉诺塔运行过程
    private long runtime = 0;
    private LinkedList<Integer>[] stacks = new LinkedList[3]; // 用于模拟栈
    private JTextArea leftTextArea; // 引用左侧文本区

    // 构造函数
    public HanoiShow(int num,boolean useRecursion, JTextArea leftTextArea) {  //添加bool参数 选择是否用递归算法
        this.leftTextArea = leftTextArea;
        setLayout(new BoxLayout(this, BoxLayout.X_AXIS)); // 设置布局方式，横向堆垒
        initComponent(num,useRecursion);
    }

    // 初始化组件
    private void initComponent(int num,boolean useRecursion) {
        Hanoi.HanoiResult hanoiResult = Hanoi.getHanoiResult(num, INIT_Tower, SPARE_Tower, DEST_Tower, useRecursion); // 获取汉诺塔结果
        movesList=hanoiResult.getMovesList();  // 获取移动过程
        runtime=hanoiResult.getRunTime(); // 获取运行时间
        towers = new Tower[3]; // 初始化三个柱
        add(towers[INIT_Tower] = new Tower("初始柱 A", num));
        add(towers[SPARE_Tower] = new Tower("辅助柱 B"));
        add(towers[DEST_Tower] = new Tower("目标柱 C"));

        // 初始化模拟栈
        for (int i = 0; i < stacks.length; i++) {
            stacks[i] = new LinkedList<>();
        }
        // 初始化第一个塔的栈
        for (int i = 1; i <= num; i++) {
            stacks[INIT_Tower].addFirst(i);
        }
        updateStacksStatus();
    }

    // 更新汉诺塔整个页面的显示组件
    public void setDiskNumber(int num , boolean useRecursion) {
        removeAll(); // 移除所有组件（这里指Tower）
        initComponent(num , useRecursion); // 重新初始化组件
        validate(); // 添加的组件重新按照Layout布局好
        repaint(); // 调用paintComponent，重新绘制，并绘制子组件
    }

    String message = "移动指令";
    // 转移圆盘
    public boolean moveNext() {
        if (movesList.isEmpty()) {
            return true;
        }
        // 转移圆盘
        int from = movesList.removeFirst();
        int to = movesList.removeFirst();
        Disk temp = towers[from].popDisk();
        message = " 柱" + letter[from] + temp.toString() + "柱" + letter[to]; // 更新移动指令
        towers[to].pushDisk(temp);
        towers[from].update();
        towers[to].update();
        stacks[to].addLast(stacks[from].getLast());
        stacks[from].removeLast();
        updateStacksStatus();
        return movesList.isEmpty(); // 转移完成返回true，否则false
    }

    public String getMessage(){ // 返回移动指令信息以添加到右侧文本区
        return message;
    }

    private void updateStacksStatus() { // 获取栈的状态
        StringBuilder sb = new StringBuilder("          栈的内容\n    底<----------->顶 ");
        for (int i = 0; i < stacks.length; i++) {
            sb.append("\n\n栈").append(letter[i]).append(": ");
            for (Integer diskSize : stacks[i]) {
                sb.append(diskSize).append(" ");
            }
        }
        sb.append("\n\n执行时间: ").append(runtime).append(" ns \n");
        leftTextArea.setText(sb.toString());
    }



}
