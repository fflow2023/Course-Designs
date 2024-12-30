import javax.swing.SwingUtilities;
import javax.swing.JFrame;

/**
 * 类名称：Main
 * 类描述：程序的主入口类，负责启动汉诺塔图形用户界面。
 * 该类使用SwingUtilities.invokeLater来确保GUI的创建和更新在事件调度线程上执行，
 * 这是Swing编程中的一个最佳实践，以避免线程安全问题。
 * 创建日期：2024/12/28
 * 作者：ZhangJinghao
 */
public class Main {
    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                HanoiGUI hanoiGUI = new HanoiGUI(); // 创建HanoiGUI类的实例
                hanoiGUI.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE); // 设置默认的关闭操作，当用户关闭窗口时，程序将退出
            }
        });
    }
}
