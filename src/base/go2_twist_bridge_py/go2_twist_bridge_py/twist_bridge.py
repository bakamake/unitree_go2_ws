#!/usr/bin/env python3
"""
Twist → Go2 Request 桥接节点
带死区 + 限幅保护
"""

import json
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from unitree_api.msg import Request
from .sport_model import ROBOT_SPORT_API_IDS


# ==================== 保护参数（教程保守值） ====================
MAX_LINEAR_VEL   = 0.30   # m/s
MAX_ANGULAR_VEL  = 0.50   # rad/s
LINEAR_DEADBAND  = 0.02   # m/s
ANGULAR_DEADBAND = 0.05   # rad/s

DEFAULT_CMD_VEL_TOPIC = "cmd_vel"
DEFAULT_REQUEST_TOPIC = "/api/sport/request"


def apply_deadband(value: float, threshold: float) -> float:
    return 0.0 if abs(value) < threshold else value


def clamp(value: float, limit: float) -> float:
    return max(-limit, min(value, limit))


class TwistBridge(Node):
    def __init__(self):
        super().__init__("twist_bridge")

        self.request_pub = self.create_publisher(
            Request, DEFAULT_REQUEST_TOPIC, 10
        )
        self.twist_sub = self.create_subscription(
            Twist, DEFAULT_CMD_VEL_TOPIC, self.twist_callback, 10
        )

        self.get_logger().info("Twist 桥接节点已启动：/cmd_vel -> /api/sport/request")

    def sanitize_twist(self, msg: Twist):
        x = clamp(apply_deadband(msg.linear.x, LINEAR_DEADBAND), MAX_LINEAR_VEL)
        y = clamp(apply_deadband(msg.linear.y, LINEAR_DEADBAND), MAX_LINEAR_VEL)
        z = clamp(apply_deadband(msg.angular.z, ANGULAR_DEADBAND), MAX_ANGULAR_VEL)
        return x, y, z

    def twist_callback(self, msg: Twist):
        x, y, z = self.sanitize_twist(msg)

        request = Request()

        if x == 0.0 and y == 0.0 and z == 0.0:
            request.header.identity.api_id = ROBOT_SPORT_API_IDS["BALANCESTAND"]
        else:
            request.header.identity.api_id = ROBOT_SPORT_API_IDS["MOVE"]
            request.parameter = json.dumps({"x": x, "y": y, "z": z})

        self.request_pub.publish(request)


def main():
    rclpy.init()
    rclpy.spin(TwistBridge())
    rclpy.shutdown()


if __name__ == "__main__":
    main()