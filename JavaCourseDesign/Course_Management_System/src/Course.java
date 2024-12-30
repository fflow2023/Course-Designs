import java.io.Serializable;

// 定义记录类Course，实现Serializable接口，以便进行序列化和反序列化操作（以文件的方式存储和读取）
public record Course(String courseName, String courseId, String courseCategory, String courseGrade, String teacherName) implements Serializable {

    // 重载toString方法，便于输出查询结果
    @Override
    public String toString() {
        return    "\n 课程名称: " + courseName
                + "\n 课程编号: " + courseId
                + "\n 课程类别: " + courseCategory
                + "\n 开课年级: " + courseGrade
                + "\n 任课老师: " + teacherName;
    }
    public String getName(){
        return courseName;
    }
}
