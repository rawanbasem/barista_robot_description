import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import Command, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Setup Paths
    pkg_description = get_package_share_directory('barista_robot_description')
    install_dir = get_package_prefix('barista_robot_description')
    
    xacro_file = os.path.join(pkg_description, 'xacro', 'barista_robot_model.urdf.xacro')
    rviz_config = os.path.join(pkg_description, 'rviz', 'robot_vis.rviz')

    # 2. Declare Launch Arguments
    declare_include_laser = DeclareLaunchArgument(
        'include_laser',
        default_value='true',
        description='Whether to include the laser scanner'
    )

    # 3. Set Environment Variables (Fix for meshes and graphics)
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[os.path.join(install_dir, 'share')]
    )
    
    set_render_engine = SetEnvironmentVariable(
        name='LIBGL_ALWAYS_SOFTWARE',
        value='1'
    )

    # 4. Robot State Publisher (Processes Xacro on the fly)
    # We pass the include_laser argument directly into the xacro command
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': Command([
                'xacro ', xacro_file, 
                ' include_laser:=', LaunchConfiguration('include_laser')
            ])
        }]
    )

    # 5. Gazebo Sim
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # 6. Spawn Robot
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'barista_robot',
            '-z', '0.2'
        ],
    )

    # 7. Bridge (Connects Gazebo and ROS 2)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model'
        ],
        output='screen'
    )

    # 8. RViz2
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        set_gz_resource_path,
        set_render_engine,
        declare_include_laser,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge,
        rviz
    ])