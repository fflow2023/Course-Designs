import javax.swing.*;
import javax.swing.plaf.FontUIResource;
import javax.swing.table.DefaultTableModel;
import javax.swing.table.TableRowSorter;
import java.awt.*;
import java.util.*;
import java.util.List;

public class CourseManagementGUI extends JFrame {
    private final CourseManager courseManager; // 课程管理器对象
    private JTable courseTable; // 课程显示表格
    private DefaultTableModel tableModel; // 表格模型，用于管理表格数据

    public CourseManagementGUI(CourseManager courseManager) {
        this.courseManager = courseManager;
        setUIFont(new FontUIResource(new Font("Microsoft YaHei", Font.PLAIN, 14))); // 设置全局字体

        setTitle("NEUQ课程管理系统"); // 设置窗口标题
        setSize(800, 600); // 设置窗口大小
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE); // 设置关闭操作
        setLocationRelativeTo(null); // 将窗口定位到屏幕中央
        initializeUI(); // 初始化用户界面
        setVisible(true);
    }

    private void  setUIFont(FontUIResource f) { //应用统一的字体到所有组件
        Enumeration<Object> keys = UIManager.getDefaults().keys();
        while (keys.hasMoreElements()) {
            Object key = keys.nextElement();
            Object value = UIManager.get(key);
            if (value instanceof FontUIResource) {
                UIManager.put(key, f);
            }
        }
    }

    private void initializeUI() {
        String[] columnNames = {"课程名", "课程编号", "课程类别", "开课年级", "任课老师"};
        tableModel = new DefaultTableModel(columnNames, 0) {
            @Override
            public boolean isCellEditable(int row, int column) {
                return false; // 禁止直接编辑表格内容
            }
        };
        courseTable = new JTable(tableModel);
        courseTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION); // 设置单选模式
        courseTable.setRowHeight(30); // 设置表格行高度
        courseTable.getTableHeader().setReorderingAllowed(false); // 禁止表头拖动
        courseTable.getTableHeader().setResizingAllowed(false); // 禁止表格列调整大小

        // 设置排序器
        TableRowSorter<DefaultTableModel> sorter = new TableRowSorter<>(tableModel);
        //将前面创建的TableRowSorter实例设置为表格courseTable的行排序器
        courseTable.setRowSorter(sorter);

        // 设置课程编号列默认升序排序
        sorter.setSortKeys(List.of(new RowSorter.SortKey(1, SortOrder.ASCENDING)));
        // 设置开课年级列自定义排序
        Map<String, Integer> gradeOrderMap = new HashMap<>();
        gradeOrderMap.put("大一", 1);
        gradeOrderMap.put("大二", 2);
        gradeOrderMap.put("大三", 3);
        gradeOrderMap.put("大四", 4);
        sorter.setComparator(3, Comparator.comparingInt((String grade) -> gradeOrderMap.getOrDefault(grade, 0)));
        //这段代码设置了表格的第四列（索引为3，开课年级列）的自定义排序。
        //首先，创建了一个HashMap来定义年级的排序顺序，然后使用Comparator.comparingInt来创建一个比较器，
        //该比较器根据年级在gradeOrderMap中的值来比较表格行。如果gradeOrderMap中没有找到对应的年级，则返回0。

        loadCoursesToTable(); // 将课程数据加载到表格中

        JScrollPane scrollPane = new JScrollPane(courseTable); // 创建带滚动条的表格
        add(scrollPane, BorderLayout.CENTER); // 将表格添加到中心区域

        JPanel controlPanel = new JPanel();
        JButton addButton = new JButton("添加课程 (Alt+A)");
        addButton.setMnemonic('A'); // 设置快捷键
        JButton updateButton = new JButton("修改课程 (Alt+E)");
        updateButton.setMnemonic('E'); // 设置快捷键
        JButton deleteButton = new JButton("删除课程 (Alt+D)");
        deleteButton.setMnemonic('D'); // 设置快捷键
        JButton searchButton = new JButton("查询课程 (Alt+S)");
        searchButton.setMnemonic('S'); // 设置快捷键

        controlPanel.add(addButton);
        controlPanel.add(updateButton);
        controlPanel.add(deleteButton);
        controlPanel.add(searchButton);
        add(controlPanel, BorderLayout.SOUTH); // 将控制按钮添加到南部区域

        addButton.addActionListener(e -> showCourseDialog(null)); // 添加课程按钮事件
        updateButton.addActionListener(e -> {
            int selectedRow = courseTable.getSelectedRow();
            if (selectedRow != -1) {
                int modelRow = courseTable.convertRowIndexToModel(selectedRow); // 转换视图索引为模型索引
                Course course = getCourseFromTable(modelRow); // 获取选中的课程
                showCourseDialog(course); // 显示修改课程对话框
            } else {
                JOptionPane.showMessageDialog(this, "请选择要修改的课程");
            }
        });


        deleteButton.addActionListener(e -> {
            int selectedRow = courseTable.getSelectedRow();
            if (selectedRow != -1) {
                int modelRow = courseTable.convertRowIndexToModel(selectedRow);
                String courseId = (String) tableModel.getValueAt(modelRow, 1); // 获取课程编号
                int response = JOptionPane.showConfirmDialog(this,
                        "确定要删除课程 <" + tableModel.getValueAt(modelRow, 0)+ "> 吗？",
                        "确认删除",
                        JOptionPane.YES_NO_OPTION,
                        JOptionPane.WARNING_MESSAGE);
                if (response == JOptionPane.YES_OPTION) {
                    courseManager.removeCourse(courseId); // 删除课程
                    tableModel.removeRow(modelRow); // 从表格中移除课程
                }
            } else {
                JOptionPane.showMessageDialog(this, "请选择要删除的课程");
            }
        });

        searchButton.addActionListener(e -> {
            String searchId = JOptionPane.showInputDialog("输入课程编号查询:"); // 获取查询编号
            if (searchId != null) {
                for (int i = 0; i < tableModel.getRowCount(); i++) {
                    if (tableModel.getValueAt(i, 1).equals(searchId)) {
                        // 将模型行索引转换为视图行索引
                        int viewRowIndex = courseTable.convertRowIndexToView(i);
                        courseTable.setRowSelectionInterval(viewRowIndex, viewRowIndex); // 选中查询到的行
                        courseTable.scrollRectToVisible(new Rectangle(courseTable.getCellRect(i, 0, true))); // 滚动到查询结果
                        JOptionPane.showMessageDialog(this, "<"+tableModel.getValueAt(i, 0)+"> 的详细信息: " + courseManager.getCourses().get(i).toString());
                        return;
                    }
                }
                JOptionPane.showMessageDialog(this, "未找到课程");
            }
        });
    }


    private void showCourseDialog(Course course) {   //添加与编辑课程的窗口
        JDialog dialog = new JDialog(this, "课程信息", true); // 创建模态对话框
        dialog.setSize(400, 360); // 设置对话框大小

        GridBagLayout layout = new GridBagLayout(); // 使用GridBagLayout 网格布局
        GridBagConstraints gbc = new GridBagConstraints(); //GridBagConstraints 类用来配置组件的布局方式
        dialog.setLayout(layout);

        // 创建并设置课程信息输入框
        JTextField courseNameField = new JTextField(course != null ? course.courseName() : "", 20);
        JTextField courseIdField = new JTextField(course != null ? course.courseId() : "", 20);
        JComboBox<String> categoryBox = new JComboBox<>(new String[]{"选修", "必修"});
        categoryBox.setSelectedItem(course != null ? course.courseCategory() : "选修");
        JComboBox<String> gradeBox = new JComboBox<>(new String[]{"大一", "大二", "大三", "大四"});
        gradeBox.setSelectedItem(course != null ? course.courseGrade() : "大一");
        JTextField teacherNameField = new JTextField(course != null ? course.teacherName() : "", 20);

        gbc.insets = new Insets(10, 10, 10, 10); // 设置边距
        gbc.fill = GridBagConstraints.HORIZONTAL; // 设置填充方式

        // 添加组件到对话框
        addComponent(dialog, layout, gbc, new JLabel("课程名:"), 0, 0, 1, 1, GridBagConstraints.EAST);
        addComponent(dialog, layout, gbc, courseNameField, 1, 0, 1, 1, GridBagConstraints.WEST);
        addComponent(dialog, layout, gbc, new JLabel("课程编号:"), 0, 1, 1, 1, GridBagConstraints.EAST);
        addComponent(dialog, layout, gbc, courseIdField, 1, 1, 1, 1, GridBagConstraints.WEST);
        addComponent(dialog, layout, gbc, new JLabel("课程类别:"), 0, 2, 1, 1, GridBagConstraints.EAST);
        addComponent(dialog, layout, gbc, categoryBox, 1, 2, 1, 1, GridBagConstraints.WEST);
        addComponent(dialog, layout, gbc, new JLabel("开课年级:"), 0, 3, 1, 1, GridBagConstraints.EAST);
        addComponent(dialog, layout, gbc, gradeBox, 1, 3, 1, 1, GridBagConstraints.WEST);
        addComponent(dialog, layout, gbc, new JLabel("任课老师:"), 0, 4, 1, 1, GridBagConstraints.EAST);
        addComponent(dialog, layout, gbc, teacherNameField, 1, 4, 1, 1, GridBagConstraints.WEST);

        JButton saveButton = new JButton("保 存");
        saveButton.addActionListener(e -> {
            // 获取用户输入的数据
            String courseName = courseNameField.getText().trim();
            String courseId = courseIdField.getText().trim();
            String category = (String) categoryBox.getSelectedItem();
            String grade = (String) gradeBox.getSelectedItem();
            String teacherName = teacherNameField.getText().trim();

            if (courseName.isEmpty() || courseId.isEmpty() || teacherName.isEmpty()) {
                JOptionPane.showMessageDialog(dialog, "所有字段都必须填写", "错误", JOptionPane.ERROR_MESSAGE);
            } else
                // 此处编号未修改时不弹出错误
                if (courseManager.isCourseIdDuplicate(courseId) && (course == null || !course.courseId().equals(courseId))) {
                JOptionPane.showMessageDialog(dialog, "课程编号已存在", "错误", JOptionPane.ERROR_MESSAGE);}
             else {
                Course newcourse = new Course(courseName, courseId, category, grade, teacherName);
                if (course == null) {
                    courseManager.addCourse(newcourse); // 添加新课程
                } else {
                    courseManager.removeCourse(course.courseId()); // 删除旧课程
                    courseManager.addCourse(newcourse); // 添加修改后的课程
                }
                loadCoursesToTable(); // 重新加载表格数据
                dialog.dispose(); // 关闭对话框
            }
        });

        gbc.gridwidth = 2;
        gbc.ipady = 10;
        gbc.anchor = GridBagConstraints.CENTER;
        addComponent(dialog, layout, gbc, saveButton, 0, 5, 2, 3, GridBagConstraints.CENTER);

        dialog.setLocationRelativeTo(this); // 将对话框定位到窗口中央
        dialog.setVisible(true); // 显示对话框
    }

    // 辅助方法，用于添加组件到对话框并设置GridBagConstraints
    private void addComponent(Container container, GridBagLayout layout, GridBagConstraints gbc, Component component, int gridx, int gridy, int gridwidth, int gridheight, int anchor) {
        // 设置组件的列索引
        gbc.gridx = gridx;
        // 设置组件的行索引
        gbc.gridy = gridy;
        // 设置组件所占据的列数
        gbc.gridwidth = gridwidth;
        // 设置组件所占据的行数
        gbc.gridheight = gridheight;
        // 设置组件的对齐方式
        gbc.anchor = anchor;
        // 使用GridBagLayout设置组件的布局约束
        layout.setConstraints(component, gbc);
        // 将组件添加到容器中
        container.add(component);
    }

    //获取对应行课程信息
    private Course getCourseFromTable(int modelRow) {
        String courseName = (String) tableModel.getValueAt(modelRow, 0);
        String courseId = (String) tableModel.getValueAt(modelRow, 1);
        String courseCategory = (String) tableModel.getValueAt(modelRow, 2);
        String courseGrade = (String) tableModel.getValueAt(modelRow, 3);
        String teacherName = (String) tableModel.getValueAt(modelRow, 4);
        return new Course(courseName, courseId, courseCategory, courseGrade, teacherName);
    }


    //将课程信息加载入表格
    private void loadCoursesToTable() {
        tableModel.setRowCount(0); // 清空表格
        for (Course course : courseManager.getCourses()) {
            tableModel.addRow(new Object[]{
                    course.courseName(),
                    course.courseId(),
                    course.courseCategory(),
                    course.courseGrade(),
                    course.teacherName()
            });
        }
    }
}
