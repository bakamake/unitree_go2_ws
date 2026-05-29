"""
一键启动建图:驱动 + 传感器处理 + SLAM + RViz(SLAM 专用视图)
"""

import os
from pathlib import Path                              # 处理 launch 文件内的相对路径
from launch import LaunchDescription                  # ROS2 launch 的顶层描述对象
from launch_ros.actions import Node                   # 启动一个 ROS2 节点
from launch.actions import IncludeLaunchDescription   # 嵌套另一个 launch 文件
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # 本包的 share 目录,用来定位 config 文件
    slam_share = Path(get_package_share_directory("go2_slam"))
    sensors_share = Path(get_package_share_directory("go2_sensors"))

    slam_params = str(slam_share / "config" / "slam_toolbox_params.yaml")
    scan_params = str(sensors_share / "config" / "pointcloud_to_laserscan_params.yaml")
    rviz_cfg = str(slam_share / "config" / "slam.rviz")

    # 1) Go2 驱动 —— 复用第 6 章的包,提供 odom/TF
    #    ⚠ 明确关掉 driver 自带的 rviz,否则会和下面第 5 步的 slam rviz 打架(起两个窗口)
    driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(Path(get_package_share_directory("go2_driver_py"))
                / "launch" / "driver.launch.py")
        ),
        launch_arguments={"use_rviz": "false"}.items(),
    )

    # 2) 时间戳修复 —— 第 11 章新增
    timestamp_fix = Node(
        package="go2_sensors",
        executable="pointcloud_timestamp_fix",
        name="pointcloud_timestamp_fix",
        output="screen",
    )

    # 3) 3D 点云 → 2D 扫描
    pc_to_scan = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        name="pointcloud_to_laserscan_node",
        parameters=[scan_params],
        remappings=[
            ("cloud_in", "/utlidar/cloud_fixed"),     # 订时间戳修复后的点云
            ("scan", "/scan"),                         # 输出标准 /scan 话题
        ],
        output="screen",
    )

    # 4) SLAM Toolbox 本体
    slam = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        parameters=[slam_params],
        output="screen",
    )

    # 5) RViz —— 加载 SLAM 专用配置(Fixed Frame = map)
    #    如果 slam.rviz 还没保存,不带 -d,免得启动失败
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_cfg] if os.path.exists(rviz_cfg) else [],
        output="screen",
    )

    return LaunchDescription([driver, timestamp_fix, pc_to_scan, slam, rviz])
