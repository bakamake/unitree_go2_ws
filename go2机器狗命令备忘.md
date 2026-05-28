# 本机有线
<!-- 旧的，有线网卡，笔记本板载RJ45接口，松了，弃用 -->
7z a -tZip unitree_sdk2.zip unitree_sdk2 -mx0;scp ./unitree_sdk2.zip unitree@192.168.123.18:/home/unitree/;
sudo ip addr add 192.168.123.1/24 dev enp58s0;ssh unitree@192.168.123.18
<!-- 新的 -->

sudo ip addr del 192.168.123.1/24 dev wlp0s20f3;sudo ip addr add 192.168.123.1/24 dev enx0c3796dc7120;ip addr show enp58s0 ;ip route show table all;ip addr show enx0c3796dc7120
7z a -tZip unitree_sdk2.zip unitree_sdk2 -mx0;
scp ./unitree_sdk2.zip unitree@192.168.123.18:/home/unitree/;
sudo ip addr add 192.168.123.1/24 dev enx0c3796dc7120;
ssh unitree@192.168.123.18

## host本地

sudo ip addr del 192.168.123.1/24 dev wlp0s20f3;sudo ip addr add 192.168.123.1/24 dev enx0c3796dc7120;ip addr;ip route show table all

ping 192.168.123.18
ssh unitree@192.168.123.18 -X 


# 有线切无线
## 旧的，我自己开热点，机器狗无线网卡扫描AP连接热点
<!-- ## 机器狗 -->
<!-- sudo nmcli device wifi  list;sudo nmcli  device wifi connect "7838" password 721/5nC3 -->

## 新的
## 机器狗无线网卡连接实验室无线路由 wifi ，用x11 gnome控制中心触发有线网卡连接实验室AP


<!-- 机器狗内 -->


```
gnome-control-center
```
<!-- host -->
```
# 连接实验室AP
ssh unitree@192.168.101.4 -X

```



# 机器狗
## unitree_sdk2编译

rm unitree_sdk2/build/* -rf;cd  unitree_sdk2/build/*;cmake ..;make -j20

## 新的（环境先连有线 ssh unitree@192.168.123.18 -X ）

```
gnome-control-center 
```


# host 上的 ros2 开发环境

sudo podman run -it -v /home/bakamake/unitree_ros2:/unitree_ros2 -w /unitree_ros2 --net=host docker.io/osrf/ros:foxy-desktop bash




# 激活虚拟环境与ros humble环境与工作空间环境
（pwsh）exit

conda activate ros_humble
source ~/unitree_ros2/setup.sh
source $HOME/unitree_ros2/cyclonedds_ws/install/setup.bash
source ~/unitree_ros2/install/setup.bash
cd ~/u/unitree_go2_ws
colcon build
source install/setup.bash


ros2 launch go2_navigation navigation.launch.py map:=$HOME/u/unitree_go2_ws/maps/my_map.yaml \
 --debug 2>&1|uniq -u
