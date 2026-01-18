#include <iostream>
#include <vector>
#include <stack>
#include <chrono>
#define MAX_N 32

class Hanoi {
    private:
    void hanoi(int n, int one, int two, int three, int a[], int *p1, int b[], int *p2, int c[], int *p3) {
        if (n == 1) {
            c[(*p3)++] = a[--(*p1)];
        } else {
            hanoi(n - 1, one, three, two, a, p1, c, p3, b, p2);
            c[(*p3)++] = a[--(*p1)];
            hanoi(n - 1, two, one, three, b, p2, a, p1, c, p3);
        }
    }
    int move(int a[], int *t1, int b[], int *t2) {
        if (*t1 == 0 && *t2 == 0) return 0;
        else if (*t1 == 0) a[(*t1)++] = b[--(*t2)];
        else if (*t2 == 0 || a[*t1 - 1] < b[*t2 - 1]) b[(*t2)++] = a[--(*t1)];
        else a[(*t1)++] = b[--(*t2)];
        return 1;
    }   

    void solveRecursively(int NUM) {
        int a[NUM], b[NUM] = {0}, c[NUM] = {0};
        int num_a = NUM, num_b = 0, num_c = 0;
        int i, *p1 = &num_a, *p2 = &num_b, *p3 = &num_c;

        for (i = 0; i < NUM; i++) {
            a[i] = NUM - i;
        }
        hanoi(NUM, 1, 2, 3, a, p1, b, p2, c, p3);
    }

    void solveIteratively(int NUM) {
        int i, flag = 1, a[NUM], b[NUM] = {0}, c[NUM] = {0};
        int t1 = NUM, t2 = 0, t3 = 0;
        int *p1 = &t1, *p2 = &t2, *p3 = &t3;

        for (i = 0; i < NUM; i++) {
            a[i] = NUM - i;
        }
        i = 0;
        if (NUM % 2) {
            while (flag) {
                switch (i++ % 3) {
                    case 0:
                        c[(*p3)++] = a[--(*p1)];
                        flag = move(a, p1, b, p2);
                        break;
                    case 1:
                        b[(*p2)++] = c[--(*p3)];
                        flag = move(a, p1, c, p3);
                        break;
                    case 2:
                        a[(*p1)++] = b[--(*p2)];
                        flag = move(b, p2, c, p3);
                        break;
                }
            }
        } else {
            while (flag) {
                switch (i++ % 3) {
                    case 0:
                        b[(*p2)++] = a[--(*p1)];
                        flag = move(a, p1, c, p3);
                        break;
                    case 1:
                        c[(*p3)++] = b[--(*p2)];
                        flag = move(a, p1, b, p2);
                        break;
                    case 2:
                        a[(*p1)++] = c[--(*p3)];
                        flag = move(c, p3, b, p2);
                        break;
                }
            }
        }
    }



public:
    long long getHanoiResult(int n, bool useRecursion) {
        auto startTime = std::chrono::high_resolution_clock::now();
        if (useRecursion) {
            solveRecursively(n);
        } else {
            solveIteratively(n);
        }
        auto endTime = std::chrono::high_resolution_clock::now();
        return std::chrono::duration_cast<std::chrono::nanoseconds>(endTime - startTime).count();
    }
};

int main() {
    int n=15;
    int m=30;
    // std::cout<<"请输入圆盘数量n-m:";
    // std::cin >> n>>m;

    while(n<=m){
        n++;
        Hanoi hanoi;
        long long recursiveTime = hanoi.getHanoiResult(n, true);
        long long iterativeTime = hanoi.getHanoiResult(n, false);

        std::cout << "圆盘数量为" << n <<"时:" << std::endl;
        std::cout << "递归的时间: " << recursiveTime << " ns" << std::endl;
        std::cout << "非递归时间: " << iterativeTime << " ns" << std::endl;
        std::cout << " 非递归时间/递归时间 = " << (double)iterativeTime / recursiveTime <<std::endl;
    }
    return 0;
}

/*
圆盘数量为18时:
递归的时间: 1001200 ns
非递归时间: 1002800 ns
 非递归时间/递归时间 = 1.0016
圆盘数量为19时:
递归的时间: 2514100 ns
非递归时间: 1183400 ns
 非递归时间/递归时间 = 0.470705
圆盘数量为20时:
递归的时间: 4010500 ns
非递归时间: 3598900 ns
 非递归时间/递归时间 = 0.897369
圆盘数量为21时:
递归的时间: 10897800 ns
非递归时间: 8145400 ns
 非递归时间/递归时间 = 0.747435
圆盘数量为22时:
递归的时间: 19317400 ns
非递归时间: 15156900 ns
 非递归时间/递归时间 = 0.784624
圆盘数量为23时:
递归的时间: 35535400 ns
非递归时间: 29841000 ns
 非递归时间/递归时间 = 0.839754
圆盘数量为24时:
递归的时间: 71997300 ns
非递归时间: 60409800 ns
 非递归时间/递归时间 = 0.839056
圆盘数量为25时:
递归的时间: 146136300 ns
非递归时间: 124597300 ns
 非递归时间/递归时间 = 0.85261
圆盘数量为26时:
递归的时间: 284583100 ns
非递归时间: 238614600 ns
 非递归时间/递归时间 = 0.838471
圆盘数量为27时:
递归的时间: 570387300 ns
非递归时间: 486700200 ns
 非递归时间/递归时间 = 0.85328
圆盘数量为28时:
递归的时间: 1130647500 ns
非递归时间: 963118100 ns
 非递归时间/递归时间 = 0.851829
圆盘数量为29时:
递归的时间: 2256920300 ns
非递归时间: 1922041100 ns
 非递归时间/递归时间 = 0.851621
圆盘数量为30时:
递归的时间: 4485644900 ns
非递归时间: 3849187200 ns
 非递归时间/递归时间 = 0.858112
*/

/*
每个底座都使用一个对应的数组表示，为简化输出过程，程序中将移盘操作简化为对应底座移出与移入数据的操作，即简单的赋值操作。
移动盘子采用对应数组元素赋值的方式表示，每个数组元素的下标采用指针变量的形式指向等。
对于类似的操作，采用一致的处理办法表达，这样的处理结果才能体现出不同算法思想在执行效率上的差别。
*/
