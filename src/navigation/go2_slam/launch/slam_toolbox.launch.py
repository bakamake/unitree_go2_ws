from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.conditions import IfCondition
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    """
    启动 SLAM Toolbox 进行实时建图
    依赖：
      - /scan 话题（由 go2_sensors 提供）
      - /odom 话题（由 go2_driver 提供）
      - TF树：odom -> base_link（由 go2_driver 提供）
    """

    pkg_share = get_package_share_directory('go2_slam')
    config_file = os.path.join(pkg_share, 'config', 'mapper_params_online_async.yaml')

    # 参数声明
    use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation/Gazebo clock'
    )

    use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='True',
        description='Launch RViz for visualization'
    )

    # SLAM Toolbox 节点（异步模式）
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[
            config_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        output='screen'
    )

    # RViz2 可视化
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(pkg_share, 'config', 'slam.rviz')] if os.path.exists(
            os.path.join(pkg_share, 'config', 'slam.rviz')
        ) else [],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
        output='screen'
    )

    return LaunchDescription([
        use_sim_time,
        use_rviz,
        slam_toolbox_node,
        rviz_node,
    ])
