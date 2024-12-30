import java.util.LinkedList;
import java.util.Stack;

/**
 *  类名称：Hanoi
 *  类描述：Hanoi类用于解决汉诺塔问题，并生成移动圆盘的过程。
 *  该类提供了递归和非递归两种算法，以及一个用于获取移动过程的方法。
 */

public class Hanoi {
    private static LinkedList<Integer> movesList; // 汉诺塔移动过程列表

    public Hanoi() {
        movesList = new LinkedList<>();
    }

    public static class HanoiResult {  // 这个类用来封装算法执行结果: 移动过程与运行时间
        private final LinkedList<Integer> movesList;
        private final long runTime;

        public HanoiResult(LinkedList<Integer> movesList, long runTime) {
            this.movesList = movesList;
            this.runTime = runTime;
        }

        public LinkedList<Integer> getMovesList() {
            return movesList;
        }

        public long getRunTime() {
            return runTime;
        }
    }

    // 生成汉诺塔移动过程
    public static HanoiResult getHanoiResult(int n, int from, int spare, int dest, boolean useRecursion) {
        Hanoi runner = new Hanoi();
        long startTime = System.nanoTime();
        if (useRecursion) {
            runner.solveRecursively(n, from, spare, dest);  //递归接口
        } else {
            runner.solveIteratively(n); //非递归接口
        }
        long runTime = System.nanoTime()- startTime;
        return new HanoiResult(movesList, runTime);
    }

    // 递归解决汉诺塔问题
    private void solveRecursively(int num, int from, int spare, int destination) {
        if (num == 1) {
            addMoveLists(from, destination);
        } else {
            solveRecursively(num - 1, from, destination, spare);
            addMoveLists(from, destination);
            solveRecursively(num - 1, spare, from, destination);
        }
    }

    // 非递归解决汉诺塔问题
    private void solveIteratively(int n) {
        Stack<Integer>[] a = new Stack[4];
        for (int i = 0; i < 4; i++) {
            a[i] = new Stack<>();
        }
        int[] s = { 0,0,1,2}; // 将栈的下标转换为 ABC(012)
        for (int i = 0; i < n; i++) {
            a[1].push(n - i); // 把盘子从大到小入栈
        }
        if (n % 2 == 1) { // 如果n为奇数则杆的排列顺序为ACB
            s[2] = 2;
            s[3] = 1;
        }
        while (true) {
            int next = 0; // 用来记录第一步中的下一个杆
            for (int i = 1; i <= 3; i++) { // 将最小圆盘移动到下一个杆上
                if (!a[i].empty()) {
                    if (a[i].peek() == 1) {
                        if (i == 3) next = 1;
                        else next = i + 1;
                        move(i, next, a, s); // 移动
                        break;
                    }
                }
            }
            if (a[2].size() == n || a[3].size() == n) break;

            int other1, other2; // 记录第二步中的另外两个杆
            switch (next) {
                case 1: {
                    other1 = 2;
                    other2 = 3;
                    break;
                }
                case 2: {
                    other1 = 3;
                    other2 = 1;
                    break;
                }
                case 3: {
                    other1 = 1;
                    other2 = 2;
                    break;
                }
                default:
                    other1 = other2 = -1;
                    break;
            }
            if (a[other1].empty()) // 移动到空杆
            {
                move(other2, other1, a, s);
            }
            else if (a[other2].empty()) {
                move(other1, other2, a, s);
            }
            else {
                if (a[other1].peek() < a[other2].peek()) // 把较小的那个圆盘移动到较大的那个圆盘上
                {
                    move(other1, other2, a, s);
                }
                else {
                    move(other2, other1, a, s);
                }
            }
        }
    }

    // 添加移动信息
    private void addMoveLists(int from, int destination) {
        movesList.addLast(from);
        movesList.addLast(destination);
    }

    // 移动圆盘的方法(非递归)
    private void move(int now, int next, Stack<Integer>[] a, int[] s) {
        a[next].push(a[now].peek());
        a[now].pop();
        addMoveLists(s[now],s[next]);
    }
}

