"""
实机 Nav2 2D 基线:
驱动 + 点云转 LaserScan + AMCL + Nav2 + twist_mux + RViz
"""

from pathlib import Path                                      # 处理 share 目录里的配置文件路径

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription                          # ROS2 launch 的顶层描述对象
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition                     # 条件启动 RViz
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node                           # 启动 ROS2 节点


def generate_launch_description() -> LaunchDescription:
    map_yaml = LaunchConfiguration("map")
    use_rviz = LaunchConfiguration("use_rviz")

    nav_share = Path(get_package_share_directory("go2_navigation"))
    sensors_share = Path(get_package_share_directory("go2_sensors"))
    driver_share = Path(get_package_share_directory("go2_driver_py"))

    nav2_params = str(nav_share / "config" / "nav2_params.yaml")
    twist_mux_params = str(nav_share / "config" / "twist_mux.yaml")
    scan_params = str(sensors_share / "config" / "pointcloud_to_laserscan_params.yaml")
    driver_launch = str(driver_share / "launch" / "driver.launch.py")

    rviz_config = str(nav_share / "rviz" / "navigation.rviz")

    # 1) 底层驱动:提供 /odom、TF、/joint_states 和最终的 /cmd_vel 桥接
    driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(driver_launch),
        launch_arguments={"use_rviz": "false"}.items(),
    )

    # 2) 复用第 11 章的时间戳修复节点,并给 TF 查询留 0.10s 缓冲
    timestamp_fix = Node(
        package="go2_sensors",
        executable="pointcloud_timestamp_fix",
        name="pointcloud_timestamp_fix",
        parameters=[
            {
                "input_topic": "/utlidar/cloud_deskewed",
                "output_topic": "/utlidar/cloud_fixed",
                # /odom 只有 20 Hz,scan 时间戳回退 0.10s,AMCL 查 odom→base 才追得上
                "backdate_sec": 0.10,
            }
        ],
        output="screen",
    )

    # # 3) 复用第 11 章的 3D 点云 → 2D LaserScan 参数
    # pointcloud_to_scan = Node(
    #     package="pointcloud_to_laserscan",
    #     executable="pointcloud_to_laserscan_node",
    #     name="pointcloud_to_laserscan",
    #     parameters=[scan_params],
    #     remappings=[
    #         ("cloud_in", "/utlidar/cloud_fixed"),
    #         ("scan", "/scan"),
    #     ],
    #     output="screen",
    # )
    pointcloud_to_scan = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        name="pointcloud_to_laserscan",
        parameters=[
            scan_params,
            {"target_frame": "base"},
        ],
        remappings=[
            ("cloud_in", "/utlidar/cloud_fixed"),
            ("scan", "/scan"),
        ],
        output="screen",
    )

    # 4) 统一仲裁导航、恢复行为和人工接管
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        name="twist_mux",
        parameters=[twist_mux_params],
        remappings=[("cmd_vel_out", "/cmd_vel")],
        output="screen",
    )

    # 5) 定位相关节点
    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        parameters=[nav2_params, {"yaml_filename": map_yaml}],
        output="screen",
    )

    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        parameters=[nav2_params],
        output="screen",
    )

    localization_lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        parameters=[
            {
                "use_sim_time": False,
                "autostart": True,
                "node_names": ["map_server", "amcl"],
            }
        ],
        output="screen",
    )

    # 6) 导航相关节点
    planner_server = Node(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        parameters=[nav2_params],
        output="screen",
    )

    controller_server = Node(
        package="nav2_controller",
        executable="controller_server",
        name="controller_server",
        parameters=[nav2_params],
        remappings=[("cmd_vel", "/cmd_vel_nav")],
        output="screen",
    )

    behavior_server = Node(
        package="nav2_behaviors",
        executable="behavior_server",
        name="behavior_server",
        parameters=[nav2_params],
        remappings=[("cmd_vel", "/cmd_vel_behavior")],
        output="screen",
    )

    bt_navigator = Node(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        name="bt_navigator",
        parameters=[nav2_params],
        output="screen",
    )

    navigation_lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        parameters=[
            {
                "use_sim_time": False,
                "autostart": True,
                "node_names": [
                    "planner_server",
                    "controller_server",
                    "behavior_server",
                    "bt_navigator",
                ],
            }
        ],
        output="screen",
    )

    # 让 map_server + amcl 先进入工作态,再启导航主链
    delayed_navigation = TimerAction(
        period=3.0,
        actions=[
            planner_server,
            controller_server,
            behavior_server,
            bt_navigator,
            navigation_lifecycle,
        ],
    )

    # RViz:Fixed Frame=map,使用本章随包安装的 navigation.rviz
    # 注意:第一次打开时默认 Fixed Frame 可能是 "odom"/"base_link",如果看不到地图,
    # 先把左上角 Global Options → Fixed Frame 改成 "map" 再说
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        condition=IfCondition(use_rviz),
        output="screen",
    )

    return LaunchDescription(
        [
            # DeclareLaunchArgument 必须在使用 LaunchConfiguration 的 action 之前被 visit，
            # 否则 IfCondition(LaunchConfiguration("use_rviz")) 拿不到默认值，rviz 会被静默跳过
            DeclareLaunchArgument(
                "map",
                description="Path to the chapter-11 saved map yaml file.",
            ),
            DeclareLaunchArgument(
                "use_rviz",
                default_value="true",
                description="Whether to launch Nav2 RViz.",
            ),
            # 把 rviz 放到节点列表最前，避免被后续崩溃的节点拖累
            rviz,
            driver,
            timestamp_fix,
            pointcloud_to_scan,
            twist_mux,
            map_server,
            amcl,
            localization_lifecycle,
            delayed_navigation,
        ]
    )
