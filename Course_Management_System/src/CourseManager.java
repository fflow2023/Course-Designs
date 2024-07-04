import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class CourseManager {
    // 课程列表
    private final List<Course> courses;
    // 课程信息保存的文件名
    private static final String FILE_NAME = "courses.txt";

    // 在构造函数中读取上一次存储的课程信息
    public CourseManager() {
        courses = loadCourses();
    }

    // 添加课程并保存
    public void addCourse(Course course) {
        courses.add(course);
        saveCourses();
    }

    // 根据课程ID移除课程并保存
    public void removeCourse(String courseId) {
        courses.removeIf(course -> course.courseId().equals(courseId));
        saveCourses();
    }

    // 获取课程列表
    public List<Course> getCourses() {
        return courses;
    }

    // 判断给定的课程编号是否已经被占用
    public boolean isCourseIdDuplicate(String courseId) {
        return courses.stream().anyMatch(course -> course.courseId().equals(courseId));
    }

    // 保存课程信息到文件
    private void saveCourses() {
        try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(FILE_NAME))) {
            oos.writeObject(courses);
        } catch (IOException e) {
            // 抛出异常
            System.err.println("保存异常: " + e.getMessage());
        }
    }

    // 从文件加载课程信息
    @SuppressWarnings("unchecked")
    private List<Course> loadCourses() {
        try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream(FILE_NAME))) {
            return (List<Course>) ois.readObject();
        } catch (IOException | ClassNotFoundException e) {
            return new ArrayList<>();
        }
    }
}
