from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from nav2_common.launch import RewrittenYaml
import os

def generate_launch_description():
    """
    启动 Nav2 导航栈进行自主导航
    前提：
      - 已有建好的地图
      - 机器人驱动正在运行（提供 /odom 和 TF）
      - 传感器数据可用（/scan）
    """

    # 获取功能包路径
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    go2_navigation_dir = get_package_share_directory('go2_navigation')

    # 参数声明
    use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true'
    )

    map_yaml_file = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(go2_navigation_dir, 'maps', 'my_map.yaml'),
        description='Full path to map yaml file to load'
    )

    params_file = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(go2_navigation_dir, 'config', 'nav2_params.yaml'),
        description='Full path to the ROS2 parameters file to use'
    )

    autostart = DeclareLaunchArgument(
        'autostart',
        default_value='True',
        description='Automatically startup the nav2 stack'
    )

    use_composition = DeclareLaunchArgument(
        'use_composition',
        default_value='True',
        description='Use composed bringup if true'
    )

    use_respawn = DeclareLaunchArgument(
        'use_respawn',
        default_value='false',
        description='Whether to respawn if a node crashes'
    )

    # 加载并重写参数
    param_substitutions = {
        'use_sim_time': LaunchConfiguration('use_sim_time'),
        'yaml_filename': LaunchConfiguration('map')
    }

    configured_params = RewrittenYaml(
        source_file=LaunchConfiguration('params_file'),
        root_key='',
        param_rewrites=param_substitutions,
        convert_types=True
    )

    # Nav2 Bringup（包含所有导航节点）
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': configured_params,
            'autostart': LaunchConfiguration('autostart'),
            'use_composition': LaunchConfiguration('use_composition'),
            'use_respawn': LaunchConfiguration('use_respawn'),
        }.items()
    )

    return LaunchDescription([
        use_sim_time,
        map_yaml_file,
        params_file,
        autostart,
        use_composition,
        use_respawn,
        nav2_bringup_launch,
    ])
