import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import Command
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, SetParameter

def generate_launch_description():
    # 1. Setup Paths
    pkg_description = get_package_share_directory('barista_robot_description')
    install_dir = get_package_prefix('barista_robot_description')
    xacro_file = os.path.join(pkg_description, 'xacro', 'barista_robot_model.urdf.xacro')
    rviz_config = os.path.join(pkg_description, 'rviz', 'robot_vis.rviz')

    # 2. Environment Variables
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[os.path.join(install_dir, 'share')]
    )
    set_render_engine = SetEnvironmentVariable(
        name='LIBGL_ALWAYS_SOFTWARE',
        value='1'
    )

    # 3. Gazebo Launch 
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # --- RICK (RED) ---
    name_rick = "rick"
    rsp_rick = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=name_rick,
        parameters=[{
            'frame_prefix': name_rick + '/',
            'use_sim_time': True,
            'robot_description': Command(['xacro ', xacro_file, ' robot_name:=', name_rick])
        }],
        remappings=[('/tf', '/tf'), ('/tf_static', '/tf_static')]
    )

    spawn_rick = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_rick',
        arguments=['-name', name_rick, '-topic', name_rick + '/robot_description', 
                   '-x', '0.0', '-y', '-0.5', '-z', '0.2'],
        output='screen'
    )

    static_tf_rick = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['--x', '0', '--y', '-0.5', '--z', '0', '--frame-id', 'world', '--child-frame-id', 'rick/odom'],
        parameters=[{'use_sim_time': True}]
    )

    # --- MORTY (BLUE) ---
    name_morty = "morty"
    rsp_morty = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=name_morty,
        parameters=[{
            'frame_prefix': name_morty + '/',
            'use_sim_time': True,
            'robot_description': Command(['xacro ', xacro_file, ' robot_name:=', name_morty])
        }],
        remappings=[('/tf', '/tf'), ('/tf_static', '/tf_static')]
    )

    spawn_morty = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_morty',
        arguments=['-name', name_morty, '-topic', name_morty + '/robot_description', 
                   '-x', '0.0', '-y', '0.5', '-z', '0.2'],
        output='screen'
    )

    static_tf_morty = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['--x', '0', '--y', '0.5', '--z', '0', '--frame-id', 'world', '--child-frame-id', 'morty/odom'],
        parameters=[{'use_sim_time': True}]
    )
    
    # 4. Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/model/rick/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/model/morty/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/rick/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/rick/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/rick/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/rick/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/morty/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/morty/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/morty/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/morty/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        remappings=[
            ('/model/rick/tf', '/tf'),
            ('/model/morty/tf', '/tf'),
        ],
        output='screen'
    )

    # 5. RViz
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        SetParameter(name='use_sim_time', value=True),
        set_gz_resource_path,
        set_render_engine,
        gazebo,
        rsp_rick,
        spawn_rick,
        static_tf_rick,
        rsp_morty,
        spawn_morty,
        static_tf_morty,
        bridge,
        rviz
    ])