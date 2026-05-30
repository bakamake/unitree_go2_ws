sudo ip addr add 192.168.123.1/24 dev enp58s0
conda activate ros_humble
source ~/unitree_ros2/setup.sh
source $HOME/unitree_ros2/cyclonedds_ws/install/setup.bash
source ~/unitree_ros2/install/setup.bash
cd ~/u/unitree_go2_ws
colcon build
source install/setup.bash
