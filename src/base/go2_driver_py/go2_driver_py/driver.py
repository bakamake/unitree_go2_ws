"""
  需求：
      1.发布里程计消息；
      2.广播里程计坐标变换；
      3.发布关节状态消息。
  分析1：
      1.了解里程计消息字段；
      2.从哪获取？机器人已经发布高层消息话题；
      3.实现，先订阅状态话题，然后转换成里程计消息，最后发布。
  分析2：
      1.需要发布机器人基坐标系与odom坐标系的相对关系；
      2.这些相对坐标系与里程计消息类似
      3.发布。
  分析3：
      1.了解关节状态信息；
      2.获取数据
      3.订阅低层状态话题，然后解析转换成关节消息，最后发布。
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from unitree_go.msg import SportModeState,LowState,MotorState
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from sensor_msgs.msg import JointState


class Driver(Node):
    def __init__(self):
        super().__init__('driver_py')

        self.declare_parameter("odom_frame","odom")
        self.declare_parameter("base_frame","base")
        self.declare_parameter("publish_tf", True)

        self.odom_frame = self.get_parameter("odom_frame").value
        self.base_frame = self.get_parameter("base_frame").value
        self.publish_tf = self.get_parameter("publish_tf").value

        # 创建 odom 的发布对象
        self.odom_pub = self.create_publisher(Odometry,"odom",10)
        # 创建 SportState 的订阅对象
        self.mode_sub = self.create_subscription(SportModeState,"/lf/sportmodestate",self.mode_cb,10)
        # 创建坐标变换广播器
        self.tf_bro = TransformBroadcaster(self)

        # 创建关节发布对象
        self.joint_pub = self.create_publisher(JointState,"joint_states",10)
        # 创建低层状态获取对象（回调函数中实现数据转换）
        self.state_sub = self.create_subscription(LowState,"/lf/lowstate",self.state_cb,10)

    def state_cb(self,state : LowState):
        # 获取关节状态并发布
        joint_state = JointState()
        # 数据组织
        joint_state.header.stamp = self.get_clock().now().to_msg()

        # 设置关节名称
        joint_state.name = [
            "FL_hip_joint","FL_thigh_joint","FL_calf_joint",
            "FR_hip_joint","FR_thigh_joint","FR_calf_joint",
            "RL_hip_joint","RL_thigh_joint","RL_calf_joint",
            "RR_hip_joint","RR_thigh_joint","RR_calf_joint",
        ]

        for i in range(12):
            q = float(state.motor_state[i].q)
            joint_state.position.append(q)


        # 发布
        self.joint_pub.publish(joint_state)

    def mode_cb(self,mode : SportModeState):
        #解析生成odom对象
        odom = Odometry()

        # 时间戳
        odom.header.stamp = self.get_clock().now().to_msg()
        # 原点坐标系
        odom.header.frame_id = self.odom_frame
        # 机器狗基坐标系
        odom.child_frame_id = self.base_frame

        # 位置
        odom.pose.pose.position.x = float(mode.position[0])
        odom.pose.pose.position.y = float(mode.position[1])
        odom.pose.pose.position.z = float(mode.position[2])

        # 姿态
        odom.pose.pose.orientation.w = float(mode.imu_state.quaternion[0])
        odom.pose.pose.orientation.x = float(mode.imu_state.quaternion[1])
        odom.pose.pose.orientation.y = float(mode.imu_state.quaternion[2])
        odom.pose.pose.orientation.z = float(mode.imu_state.quaternion[3])

        # 速度
        odom.twist.twist.linear.x = float(mode.velocity[0])
        odom.twist.twist.linear.y = float(mode.velocity[1])
        odom.twist.twist.linear.z = float(mode.velocity[2])

        odom.twist.twist.angular.z = float(mode.yaw_speed)

        # 发布
        self.odom_pub.publish(odom)

        # 广播坐标变换
        if self.publish_tf:
            # 生成坐标变换数据
            trans_form = TransformStamped()

            trans_form.header.stamp = self.get_clock().now().to_msg()
            trans_form.header.frame_id = self.odom_frame

            trans_form.child_frame_id = self.base_frame

            # 设置偏移量
            trans_form.transform.translation.x = odom.pose.pose.position.x
            trans_form.transform.translation.y = odom.pose.pose.position.y
            trans_form.transform.translation.z = odom.pose.pose.position.z

            # 设置旋转角度
            trans_form.transform.rotation = odom.pose.pose.orientation

            # 发布
            self.tf_bro.sendTransform(trans_form)

def main():
    rclpy.init()
    rclpy.spin(Driver())
    rclpy.shutdown()

if __name__ == '__main__':
    main()