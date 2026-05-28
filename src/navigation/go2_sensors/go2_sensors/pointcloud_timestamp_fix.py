#!/usr/bin/env python3
"""
时间戳修复节点:订阅原始点云,重写时间戳后重新发布。
专治 Go2 UTlidar 点云时间戳早于系统时间的毛病。
"""

import rclpy                                       # ROS2 Python 客户端库,节点的入口
from rclpy.duration import Duration                # 用来构造"回拨 0.05 秒"的时间差
from rclpy.node import Node                        # 所有 ROS2 节点的基类
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy  # QoS 策略,控制通信可靠性
from sensor_msgs.msg import PointCloud2            # 标准点云消息类型


class PointCloudTimestampFix(Node):
    def __init__(self):
        super().__init__("pointcloud_timestamp_fix")

        # 回拨 0.05 秒:保证下游"查 TF"时不会查到未来,否则第 12 章 AMCL
        # 会持续报 "Lookup would require extrapolation into the future"
        self.backdate = Duration(seconds=0.05)

        # 订阅 QoS:BEST_EFFORT(不保证每一帧都收到,但延迟低)
        # 选 BEST_EFFORT 是因为 Go2 驱动发布时兼容这个策略
        sub_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        # 发布 QoS:RELIABLE(保证 SLAM 一帧不漏,必要时重传)
        pub_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        # 订阅原始点云
        self.sub = self.create_subscription(
            PointCloud2,
            "/utlidar/cloud_deskewed",
            self.on_cloud,
            sub_qos,
        )

        # 发布时间戳修复后的点云,下游节点来订这个话题
        self.pub = self.create_publisher(
            PointCloud2,
            "/utlidar/cloud_fixed",
            pub_qos,
        )

        self.get_logger().info("时间戳修复节点已启动(回拨 0.05s)")

    def on_cloud(self, msg: PointCloud2) -> None:
        # 用"当前时间 − 0.05s"覆盖原时间戳,其他字段不动
        msg.header.stamp = (self.get_clock().now() - self.backdate).to_msg()
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = PointCloudTimestampFix()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
