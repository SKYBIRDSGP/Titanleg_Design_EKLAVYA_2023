#!/usr/bin/python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument,  ExecuteProcess, RegisterEventHandler
from launch.substitutions import Command
from launch_ros.actions import Node
import launch_ros.descriptions
from launch.event_handlers import (OnProcessStart, OnProcessExit)
from launch.actions import IncludeLaunchDescription
from launch_ros.descriptions import ParameterValue
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_prefix
import random

# this is the function launch which the system will look for
def generate_launch_description():
    
    ##########DATA_INPUT##########
    urdf_file = 'URDF_Slider.urdf'
    package_description = 'titanleg_gazebo'
    ##########DATA_INPUT_END##########
    config = os.path.join( get_package_share_directory('titanleg_gazebo'),
    'config',
    'titanleg.yaml'
    )
    robot_desc_path = os.path.join(get_package_share_directory(package_description), "urdf", urdf_file)
    print("Searching for the Design ===>")
    robot_description_content =  ParameterValue(Command(['xacro ', robot_desc_path]),value_type=str)
    robot_description = {"robot_description": robot_description_content}
    
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, config],
        output="both",
    )
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    robot_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["forward_position_controller", "--controller-manager", "/controller_manager"],
    )
    
    ### Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        emulate_tty=True,
        parameters=[{'use_sim_time': True, 'robot_description': ParameterValue(Command(['xacro ', robot_desc_path]),value_type=str)}],
        output = "screen"
    )
    # Position and orientaion of the Leg : 
    # [X, Y, Z]
    position = [0.0, 0.0, 0.0]
    # [Roll, Pitch, Yaw]
    orientation = [0.0, 0.0, 0.0]
    # base name of the bot: 
    robot_base_name = "titanleg"
    # Spawn Leg Set Gazebo
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_entity',
        output='screen',
        arguments=['-entity', robot_base_name,
                   '-x', str(position[0]), '-y', str(position[1]
                                                     ), '-z', str(position[2]),
                    '-R', str(orientation[0]), '-P', str(orientation[1]
                                                         ), '-Y', str(orientation[2]),
                    '-topic', '/robot_description'                                                                     
                   ]
    )

    # create and return launch description object
    delay_joint_state_broadcaster_spawner_after_spawn_robot = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[joint_state_broadcaster_spawner],
        )
    )
    delay_robot_controller_spawner_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[robot_controller_spawner],
        )
    )
    control_node_after_gazebo = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[control_node],
        )
    )

    return LaunchDescription([
        spawn_robot,
        control_node_after_gazebo,
        robot_state_publisher_node,
        delay_joint_state_broadcaster_spawner_after_spawn_robot,
        delay_robot_controller_spawner_after_joint_state_broadcaster_spawner
        
        ]
    )
          