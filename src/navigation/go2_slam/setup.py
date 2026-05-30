from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'go2_slam'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 安装 launch 文件
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # 安装 config 文件
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        # 保留 maps 目录
        (os.path.join('share', package_name, 'maps'), glob('maps/*') if os.path.exists('maps') else []),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ztl',
    maintainer_email='ztl3106742440@gmail.com',
    description='Unitree Go2 SLAM mapping package',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        "console_scripts": [
        ],
    },
)
