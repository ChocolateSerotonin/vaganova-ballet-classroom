# vaganova-ballet-classroom-simulator
An Agent-Based Model of Learning Progression in Open Enrollment Classrooms

Project Overview

This project explores a common but surprisingly under-studied educational phenomenon:

Why do open-enrollment classrooms often progress much more slowly than expected?

In many adult learning environments—such as ballet, yoga, language learning or programming—new students continuously join existing classes. Teachers must constantly balance the learning needs of beginners and experienced learners, making curriculum progression a dynamic decision rather than a fixed schedule.

This project builds an Agent-Based Model (ABM) to simulate this process.

Using an adult Vaganova ballet classroom as a case study, the model represents students, teachers and classroom progression as interacting agents, allowing different teaching strategies and classroom conditions to be explored through simulation.

Research Motivation

Traditional educational models often assume:

a fixed group of students;
a predefined syllabus;
homogeneous learning speed.

However, real-world adult education rarely works this way.

Instead, classrooms are dynamic systems where:

students join and leave;
attendance fluctuates;
learning ability evolves;
teachers continuously adjust curriculum based on classroom performance.

The goal of this project is to understand how these individual behaviors collectively shape classroom progression.

Model Design
Student Agent

Each student is represented by several evolving state variables:

Baseline Ability
Learning Efficiency
Mastery of Each Level
Attendance
Number of Classes Attended

Students gradually improve through learning while forgetting previously learned material after absences.

Learning efficiency itself also evolves through accumulated learning experience ("learning how to learn").

Teacher Agent

The teacher is modeled as an adaptive decision-maker rather than following a fixed syllabus.

Before each class, the teacher decides whether to introduce a new level based on:

proportion of new students;
mastery level of experienced students;
previous promotion decision.

The teaching strategy therefore emerges dynamically rather than being predetermined.

Classroom Dynamics

Each class follows five stages:

New student arrival
Attendance generation
Teacher selects current teaching level
Student learning
Teacher evaluation and curriculum update

The interaction of these stages produces long-term classroom evolution.

Simulation Variables

Major state variables include:

Student
Baseline Ability (B)
Learning Efficiency (E)
Mastery (M)
Attendance (Y)
Experience (C)
Teacher
Current Teaching Level (L)
Upgrade Permission (U)
Classroom
New Student Ratio
Average Mastery of Experienced Students
Total Attendance
Technical Stack
Python
Mesa (Agent-Based Modeling)
NumPy
Matplotlib
Pandas
Current Outputs

The simulation currently visualizes:

classroom progression
curriculum upgrade decisions
mastery evolution
attendance
proportion of new students

These outputs help explain why classroom progression may stagnate even when individual students continue improving.

Future Work

Future extensions include:

Learning notes as knowledge externalization
Peer learning and collaborative learning
Different teacher policies
Multiple classroom types
Bayesian parameter estimation
Reinforcement Learning teacher agents
Classroom optimization under different enrollment policies
Why This Project

Although inspired by an adult ballet classroom, this model is intended as a general framework for studying learning dynamics in open educational communities.

Potential applications include:

Adult education
Continuing education
Corporate training
Online learning communities
Open enrollment classrooms
