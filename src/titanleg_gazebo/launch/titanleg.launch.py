#!/usr/bin/python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, LogInfo
from launch.substitutions import Command
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit
from launch_ros.descriptions import ParameterValue

def generate_launch_description():
    
    ##########DATA_INPUT##########
    sdf_file = 'titanleg.sdf'
    package_description = 'titanleg_gazebo'
    ##########DATA_INPUT_END##########
    
    config = os.path.join(get_package_share_directory('titanleg_gazebo'), 'config', 'titanleg.yaml')
    robot_desc_path = os.path.join(get_package_share_directory(package_description), "urdf", sdf_file)
    
    # Directly read the SDF content
    with open(robot_desc_path, 'r') as sdf_file:
        robot_description_content = sdf_file.read()

    robot_description = {"robot_description": robot_description_content}
    
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, config],
        output="screen",
        arguments=['--ros-args', '--log-level', 'debug']
    )
    
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    robot_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["forward_position_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )
    
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'use_sim_time': True, 'robot_description': robot_description_content}],
        output="screen",
    )
    
    position = [0.0, 0.0, 0.0]
    orientation = [0.0, 0.0, 0.0]
    robot_base_name = "titanleg"
    
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_entity',
        output='screen',
        arguments=['-entity', robot_base_name,
                   '-x', str(position[0]), '-y', str(position[1]), '-z', str(position[2]),
                   '-R', str(orientation[0]), '-P', str(orientation[1]), '-Y', str(orientation[2]),
                   '-topic', '/robot_description']
    )

    delay_joint_state_broadcaster_spawner_after_spawn_robot = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[LogInfo(msg="Spawning joint_state_broadcaster"), joint_state_broadcaster_spawner],
        )
    )
    
    delay_robot_controller_spawner_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[LogInfo(msg="Spawning forward_position_controller"), robot_controller_spawner],
        )
    )

    return LaunchDescription([
        LogInfo(msg="Starting control node"),
        control_node,
        robot_state_publisher_node,
        spawn_robot,
        delay_joint_state_broadcaster_spawner_after_spawn_robot,
        delay_robot_controller_spawner_after_joint_state_broadcaster_spawner,
        LogInfo(msg="Launch file executed successfully"),
    ])
