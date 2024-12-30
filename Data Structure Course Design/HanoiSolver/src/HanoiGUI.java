import javax.swing.*;
import javax.swing.plaf.FontUIResource;
import java.awt.*;
import java.awt.event.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Enumeration;

/**
 * 类名称：HanoiGUI
 * 类描述：此类提供了一个图形用户界面，用于展示汉诺塔游戏的动画和操作。
 * 它包含了用于显示汉诺塔动画的中间区域、左右两侧的文本显示区以及底部的功能菜单。
 * 用户可以通过界面选择不同的算法（递归或非递归）、圆盘数量、动画速度，并控制动画的开始、停止和重置。
 * 该类还负责初始化界面组件和设置全局字体样式。
 */
public class HanoiGUI extends JFrame {
    private static final String TITLE = "汉诺塔求解器";
    private static final int GAP = 40;  // 边距
    private static final int INIT_COUNT = 3; // 默认圆盘数量为3
//    private boolean isRunning = false; // 运行状态标志
    private int animationSpeed = 50; // 动画速度，默认为50
    private boolean useRecursion=true; //默认选择递归算法
    private Timer timer;
    private HanoiShow hanoiShow;
    JTextArea leftTextArea = new JTextArea(5, 10); // 创建左侧文本框
    JTextArea rightTextArea = new JTextArea(5, 10); // 创建右侧文本框
    private int stepCounts = 1;
    private final String start = "开始";
    private final String stop = "停止";
    private final String end = "结束";
    private final String rightText="         移动指令           步骤数\n";
    JButton animateButton = new JButton(start); // 动画控制按钮
    JButton nextButton = new JButton("下一步"); //下一步按钮
    JComboBox<Integer> diskNumberSelection = new JComboBox<>(new Integer[] {1, 2, 3, 4, 5, 6, 7, 8, 9}); //创建下拉列表
    JRadioButton recursiveButton = new JRadioButton("递归", true); // 创建递归算法选项，默认选中
    JRadioButton nonRecursiveButton = new JRadioButton("非递归"); // 创建非递归算法选项


    //构造函数
    public HanoiGUI() {
        // 设置全局字体
        setUIFont(new FontUIResource(new Font("Microsoft YaHei", Font.PLAIN, 15)));
        //初始化窗口
        initComponent();
    }

    //初始化窗口
    private void initComponent() {
        // 设置窗口的布局管理器为BorderLayout，以便将窗口分为五个区域：北、南、东、西、中
        setLayout(new BorderLayout());

        // 创建上部面板，用于显示动画区和两个文本区
        JPanel topPanel = new JPanel(new BorderLayout()); // 使用BorderLayout布局
        topPanel.setBorder(BorderFactory.createLineBorder(Color.GRAY)); // 添加灰色边框以区分区域

        // 左侧文本显示区 (显示栈的变化)
        JPanel leftPanel = new JPanel(new BorderLayout());  // 左侧文本区
        leftPanel.setBorder(BorderFactory.createLineBorder(Color.GRAY)); // 添加边框
        leftTextArea.setMargin(new Insets(5, 5, 5, 5)); // 设置边距
        leftTextArea.setEditable(false); // 设置文本区域为只读
        leftTextArea.setFont(leftTextArea.getFont().deriveFont((float)17)); // 左侧字体大小17
        JScrollPane leftScrollPane = new JScrollPane(leftTextArea); // 创建滚动面板并添加文本区域
        leftPanel.add(leftScrollPane, BorderLayout.CENTER); // 将滚动面板添加到左侧面板
        topPanel.add(leftPanel, BorderLayout.WEST);

        // 右侧文本显示区  (显示移动记录)
        JPanel rightPanel = new JPanel(new BorderLayout()); // 右侧文本区
        rightPanel.setBorder(BorderFactory.createLineBorder(Color.GRAY)); // 添加边框
        rightTextArea.setMargin(new Insets(5, 5, 5, 5)); // 设置边距
        rightTextArea.setEditable(true); // 设置文本区域为只读
        rightTextArea.setFont(leftTextArea.getFont().deriveFont((float)13)); // 右侧字体大小13
        JScrollPane rightScrollPane = new JScrollPane(rightTextArea); // 创建滚动面板并添加文本区域
        rightPanel.add(rightScrollPane, BorderLayout.CENTER); // 将滚动面板添加到右侧面板
        topPanel.add(rightPanel, BorderLayout.EAST);
        rightTextArea.setText(rightText);
        // 设置文本区固定宽度
        Dimension fixedSize = new Dimension(220, 0); // 宽度为220，高度自适应
        leftPanel.setPreferredSize(fixedSize);
        rightPanel.setPreferredSize(fixedSize);

        // 创建中间动画显示区
        JPanel centerPanel = new JPanel(); // 汉诺塔面板
        hanoiShow = new HanoiShow(INIT_COUNT,useRecursion,leftTextArea); // 添加到Panel时，默认采用左右居中，上面GAP为5的Layout
        centerPanel.setBackground(Color.lightGray); // 设置背景为灰色
        centerPanel.add(hanoiShow);

        // 将centerPanel添加到topPanel的中心区域
        topPanel.add(centerPanel, BorderLayout.CENTER);

        // 将topPanel添加到窗口的中心区域
        add(topPanel, BorderLayout.CENTER);

        // 创建下部面板，用于放置功能菜单
        JPanel bottomPanel = new JPanel();
        bottomPanel.setLayout(new BoxLayout(bottomPanel, BoxLayout.Y_AXIS)); // 使用BoxLayout布局，垂直排列组件
        bottomPanel.setBorder(BorderFactory.createLineBorder(Color.GRAY)); // 添加灰色边框以区分区域

        // bottomPanel 底部功能区菜单设置
        animateButton.addActionListener(event -> {  //  动画控制按钮 添加监听事件
            recursiveButton.setEnabled(false);
            nonRecursiveButton.setEnabled(false);
//            diskNumberSelection.setEnabled(false);
            if (animateButton.getText().equals(start)) {
                timer.start();
                animateButton.setText(stop);
            } else if (animateButton.getText().equals(stop)) {
                timer.stop();
                animateButton.setText(start);
            }
        });
        // 自动控制的计时器
        // 速度animationSpeed 1-100 对应延迟DELAY 1000-10
        timer = new Timer(1010-animationSpeed*10, event -> {
            if (hanoiShow.moveNext()) { //结束时
                timer.stop();
                nextButton.setEnabled(false);
                animateButton.setText(end);
            }
            rightTextArea.append(hanoiShow.getMessage() + "    (" + stepCounts +") \n");
            stepCounts++;
            timer.setDelay(1005 - animationSpeed * 10);
        });

        // 下一步按钮
        nextButton.addActionListener(event -> {
            recursiveButton.setEnabled(false);
            nonRecursiveButton.setEnabled(false);
            timer.stop();
            if(hanoiShow.moveNext()) { // 结束时
                animateButton.setText(end);
                rightTextArea.append(hanoiShow.getMessage() + "    (" + stepCounts +") \n");
                nextButton.setEnabled(false);
                return;
            }
            if (animateButton.getText().equals(stop)) {
                animateButton.setText(start);
            }
                rightTextArea.append(hanoiShow.getMessage() + "    (" + stepCounts +") \n");
                stepCounts++;

        });

        // 重置按钮
        JButton resetButton = new JButton("重置");
        resetButton.addActionListener(event -> reset());

        //帮助按钮
        JButton infoButton = new JButton("?帮助");
        infoButton.addActionListener(e -> {
            try {
                // 读取根目录下的help.html文件内容
                String helpHtml = new String(Files.readAllBytes(Paths.get("help.html")));
                // 使用JEditorPane来显示HTML内容
                JEditorPane editorPane = new JEditorPane("text/html", helpHtml);
                editorPane.setEditable(false); // 设置编辑器为不可编辑
                JScrollPane scrollPane = new JScrollPane(editorPane); // 添加滚动条
                scrollPane.setPreferredSize(new Dimension(800, 500)); // 设置窗口大小
                JOptionPane.showMessageDialog(null, scrollPane, "帮助信息", JOptionPane.PLAIN_MESSAGE);
            } catch (IOException ex) {
                // 如果读取文件出错，显示错误信息
                JOptionPane.showMessageDialog(null, "帮助文件丢失: " + ex.getMessage(), "错误", JOptionPane.ERROR_MESSAGE);
            }
        });
        // 创建Info按钮面板，使用BorderLayout来放置Info按钮在右下角
        JPanel infoPanel = new JPanel(new BorderLayout());
        infoPanel.add(infoButton, BorderLayout.EAST); // 将Info按钮放在面板最右边


        // 创建按钮组面板
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.CENTER)); // 使用FlowLayout布局，居中对齐
        buttonPanel.add(animateButton); // 添加动画控制按钮
        buttonPanel.add(nextButton);  //添加下一步按钮
        buttonPanel.add(resetButton); // 添加重置按钮

        // 创建圆盘数量选择面板
        JPanel diskNumberPanel = new JPanel(new FlowLayout(FlowLayout.CENTER)); // 使用FlowLayout布局，居中对齐
        diskNumberPanel.add(new JLabel("圆盘数量:")); // 添加标签
        diskNumberSelection.setSelectedItem(INIT_COUNT); // 设置初始选择项
        diskNumberSelection.setPreferredSize(new Dimension(50, diskNumberSelection.getPreferredSize().height)); //设置宽度
        diskNumberSelection.addActionListener(event -> {  // 修改圆盘数量时
            reset();
        });
        diskNumberPanel.add(diskNumberSelection); // 添加下拉列表

        // 创建勾选选项面板，用于选择算法类型
        JPanel algorithmPanel = new JPanel(new FlowLayout(FlowLayout.CENTER)); // 使用FlowLayout布局，居中对齐
        algorithmPanel.add(new JLabel("算法选择："));  //添加标签
        ButtonGroup algorithmGroup = new ButtonGroup(); // 创建按钮组，确保只能选择一个选项
        algorithmGroup.add(recursiveButton); // 将递归选项添加到按钮组
        algorithmGroup.add(nonRecursiveButton); // 将非递归选项添加到按钮组
        algorithmPanel.add(recursiveButton); // 将递归选项添加到面板
        algorithmPanel.add(nonRecursiveButton); // 将非递归选项添加到面板
        // 创建一个ItemListener来监听按钮组的变化
        ItemListener itemListener = e -> {
            // 检查是哪个按钮被选中，并更新useRecursion变量
            if (e.getSource() == recursiveButton && e.getStateChange() == ItemEvent.SELECTED) {
                useRecursion = true;
            } else if (e.getSource() == nonRecursiveButton && e.getStateChange() == ItemEvent.SELECTED) {
                useRecursion = false;
            }
            reset(); // 选择算法时自动重置
        };
        // 将ItemListener添加到每个按钮
        recursiveButton.addItemListener(itemListener);
        nonRecursiveButton.addItemListener(itemListener);

        // 创建速度面板
        JPanel sliderPanel = new JPanel(new FlowLayout(FlowLayout.CENTER));// 使用FlowLayout布局，居中对齐
        JSlider speedSlider = new JSlider(1, 100); // 创建滑动条，范围从1到100
        JLabel speedLabel = new JLabel(String.format("动画速度: %02d", speedSlider.getValue())); // 创建标签，显示当前速度，格式化为两位数
        // 为滑动条添加监听器，当滑动条值改变时更新标签和动画速度
        speedSlider.addChangeListener(e -> {
            int newValue = speedSlider.getValue();
            speedLabel.setText(String.format("动画速度: %02d", newValue)); // 更新标签
            animationSpeed = newValue; // 更新动画速度
//            updateTimerDelay(); // 更新计时器延迟
        });
        // 为滑动条添加鼠标监听器，用于点击滑动条时调整动画速度值
        speedSlider.addMouseListener(new MouseAdapter() {
            @Override
            public void mousePressed(MouseEvent e) {
                // 计算点击位置对应的滑动条值
                int value = getValueForXPosition(speedSlider, e.getX());
                // 设置滑动条的值
                speedSlider.setValue(value);
            }
            private int getValueForXPosition(JSlider slider, int xPos) {
                int trackWidth = slider.getWidth() - slider.getInsets().left - slider.getInsets().right;
                double valuePosition = xPos - slider.getInsets().left;
                double valueRatio = valuePosition / (double) trackWidth;
                return (int) Math.round(slider.getMinimum() + valueRatio * (slider.getMaximum() - slider.getMinimum()));
            }
        });
        sliderPanel.add(speedLabel); // 将标签添加到速度面板
        sliderPanel.add(speedSlider); // 将滑动条添加到速度面板

        // 添加组件到底部菜单面板
        bottomPanel.add(diskNumberPanel); // 圆盘数量选择面板
        bottomPanel.add(algorithmPanel);  // 算法选择面板
        bottomPanel.add(sliderPanel);  // 速度面板
        bottomPanel.add(buttonPanel); // 按钮组面板
        bottomPanel.add(infoPanel, BorderLayout.SOUTH); // 信息面板

        // 将底部菜单面板添加到主窗口的南部区域
        add(bottomPanel, BorderLayout.SOUTH);

        // 必须设置大小，使用BoxLayout报错
        setSize(topPanel.getPreferredSize().width + 2*GAP, topPanel.getPreferredSize().height + bottomPanel.getPreferredSize().height + GAP);
        setTitle(TITLE);  // 设置标题
        setVisible(true); // 设置窗口可见
        setLocationRelativeTo(null); // 设置窗口居中显示
    }

    private void reset(){ //重置按钮
        timer.stop();
        animateButton.setText(start);
        // 重置动画显示区
        hanoiShow.setDiskNumber((int)diskNumberSelection.getSelectedItem(),useRecursion);
        // 重置文本区
        rightTextArea.setText(rightText);
        stepCounts =1;
        //启用算法选择按钮
        recursiveButton.setEnabled(true);
        nonRecursiveButton.setEnabled(true);
        nextButton.setEnabled(true);
    }

    //应用统一的字体到所有组件
    private void setUIFont(FontUIResource f) {
        Enumeration<Object> keys = UIManager.getDefaults().keys();
        while (keys.hasMoreElements()) {
            Object key = keys.nextElement();
            Object value = UIManager.get(key);
            if (value instanceof FontUIResource) {
                UIManager.put(key, f);
            }
        }
    }
}


