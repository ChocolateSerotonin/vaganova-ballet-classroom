import matplotlib.pyplot as plt

import model as model_module
from model import ClassroomModel


# ============================================================
# PARAMETERS FOR THIS RUN
# ============================================================

PARAMS = {

    # Population
    "n_initial": 8,
    "class_capacity": 15,

    # Arrival
    "new_student_lambda": 1.30,

    # Retention
    "first_return_prob": 0.30,

    "delayed_return_prob": 0.12,
    "delayed_return_window": 2,

    "second_return_prob": 0.50,

    "stable_attend_prob": 0.70,

    # Learning
    "alpha": 10,
    "gamma": 15,
    "beta": 1,

    # Day-to-day observed performance variability
    "performance_sigma": 0.15,

    # B
    "eta_B": 1,
    "B_max": 100,

    # E
    "eta_E_low": 0.02,
    "eta_E_high": 0.04,

    "internalization_acceleration_after": 6,

    # Level mastery
    "level_target_base": 16,
    "level_target_growth": 1.25,

    "mastery_threshold_ratio": 0.60,

    # Teacher adaptation
    "newcomer_difficulty_threshold": 0.50,

    # Forgetting
    "forgetting_base": 2,
    "forgetting_cap": 8,

    "mastery_retention_floor": 0.50,

    # Reproducibility
    "seed": 42,
}


# ============================================================
# START
# ============================================================

print("\n========================================")
print("VAGANOVA CLASSROOM SIMULATOR")
print("========================================")


print("\nRUNNING MODEL FILE:")
print(
    model_module.__file__
)


print("\nPARAMETERS USED IN THIS RUN:")

for key, value in PARAMS.items():

    print(
        f"{key}: {value}"
    )


# ============================================================
# CREATE MODEL
# ============================================================

model = ClassroomModel(
    **PARAMS
)


# ============================================================
# PARAMETER CHECK
# ============================================================

print("\n========================================")
print("PARAMETER CHECK")
print("========================================")


print(
    "level_target_base =",
    model.level_target_base
)

print(
    "performance_sigma =",
    model.performance_sigma
)

print(
    "new_student_lambda =",
    model.new_student_lambda
)

print(
    "delayed_return_prob =",
    model.delayed_return_prob
)


# ============================================================
# RUN 18 CLASSES
# ============================================================

N_CLASSES = 18


for _ in range(
    N_CLASSES
):

    model.step()


# ============================================================
# DATA
# ============================================================

df_model = (
    model.datacollector
    .get_model_vars_dataframe()
)


# ============================================================
# CLASS-BY-CLASS TABLE
# ============================================================

print("\n========================================")
print("18节课堂记录")
print("========================================\n")


columns_to_show = [

    "Level",

    "Teaching_Level",

    "Permission",

    "Avg_Mastery_Old",

    "Avg_Performance_Old",

    "N_Total",

    "N_Old",

    "N_New",

    "New_Ratio",

    "N_Stable",
]


print(
    df_model[
        columns_to_show
    ].to_string()
)


# ============================================================
# FINAL RESULTS
# ============================================================

print("\n========================================")
print("最终结果")
print("========================================")


print(
    f"长期课程等级: "
    f"{model.teacher.L}"
)


print(
    f"累计升级次数: "
    f"{model.teacher.upgrade_count}"
)


print(
    f"最终稳定学生数: "
    f"{model.n_stable}"
)


print(
    f"最终活跃学生数: "
    f"{model.n_active}"
)


print(
    f"观察期间最大实际到场人数: "
    f"{df_model['N_Total'].max()}"
)


print(
    f"平均实际到场人数: "
    f"{df_model['N_Total'].mean():.2f}"
)


print(
    f"有新人的课堂比例: "
    f"{(df_model['N_New'] > 0).mean():.2%}"
)


print(
    f"是否出现超过15人的课堂: "
    f"{'是' if df_model['Over_Capacity'].sum() > 0 else '否'}"
)


# ============================================================
# DELAYED RETURN
# ============================================================

students = [

    agent

    for agent in model.schedule.agents

    if hasattr(
        agent,
        "had_delayed_return"
    )
]


n_delayed = sum(

    1

    for student in students

    if student.had_delayed_return
)


n_delayed_stable = sum(

    1

    for student in students

    if student.stable_after_delayed_return
)


print(
    f"发生 delayed return 的学生数: "
    f"{n_delayed}"
)


print(
    f"delayed return 后成为 stable 的学生数: "
    f"{n_delayed_stable}"
)


# ============================================================
# LEVEL TARGETS
# ============================================================

print("\n========================================")
print("LEVEL MASTERY TARGETS")
print("========================================")


max_level_to_print = max(
    5,
    model.teacher.L + 2
)


for level in range(
    1,
    max_level_to_print + 1
):

    target = (
        model.get_level_target(
            level
        )
    )

    threshold = (
        target
        * model.mastery_threshold_ratio
    )


    print(
        f"Level {level}: "
        f"100% target = {target:.2f}, "
        f"60% threshold = {threshold:.2f}"
    )


# ============================================================
# PLOTS
# ============================================================

fig, axes = plt.subplots(
    3,
    2,
    figsize=(15, 12)
)


# ------------------------------------------------------------
# Attendance
# ------------------------------------------------------------

df_model[
    "N_Total"
].plot(

    ax=axes[0, 0],

    marker="o",

    title="Attendance"
)


axes[0, 0].axhline(
    y=15,
    linestyle="--",
    alpha=0.4,
    label="Physical Capacity (15)"
)


axes[0, 0].set_ylabel(
    "Students"
)

axes[0, 0].legend()


# ------------------------------------------------------------
# New students
# ------------------------------------------------------------

df_model[
    "N_New"
].plot(

    ax=axes[0, 1],

    marker="o",

    title="New Students"
)


axes[0, 1].set_ylabel(
    "Students"
)


# ------------------------------------------------------------
# Curriculum Level
# ------------------------------------------------------------

df_model[
    [
        "Level",
        "Teaching_Level"
    ]
].plot(

    ax=axes[1, 0],

    marker="o",

    title="Long-term Level vs Teaching Level"
)


axes[1, 0].set_ylabel(
    "Level"
)


# ------------------------------------------------------------
# Mastery vs Performance
# ------------------------------------------------------------

df_model[
    [
        "Avg_Mastery_Old",
        "Avg_Performance_Old"
    ]
].plot(

    ax=axes[1, 1],

    marker="o",

    title="Latent Mastery vs Observed Performance"
)


axes[1, 1].axhline(
    y=60,
    linestyle="--",
    alpha=0.6,
    label="Upgrade Threshold (60%)"
)


axes[1, 1].set_ylim(
    0,
    105
)


axes[1, 1].set_ylabel(
    "Percent"
)


axes[1, 1].legend()


# ------------------------------------------------------------
# Stable students
# ------------------------------------------------------------

df_model[
    "N_Stable"
].plot(

    ax=axes[2, 0],

    marker="o",

    title="Stable Students"
)


axes[2, 0].axhline(
    y=5,
    linestyle="--",
    alpha=0.5,
    label="Observed Reference (~5)"
)


axes[2, 0].set_ylabel(
    "Students"
)


axes[2, 0].legend()


# ------------------------------------------------------------
# New student ratio
# ------------------------------------------------------------

df_model[
    "New_Ratio"
].plot(

    ax=axes[2, 1],

    marker="o",

    title="New Student Ratio"
)


axes[2, 1].axhline(
    y=0.5,
    linestyle="--",
    alpha=0.6,
    label="Difficulty Reduction Threshold"
)


axes[2, 1].set_ylim(
    0,
    1.05
)


axes[2, 1].set_ylabel(
    "Ratio"
)


axes[2, 1].legend()


# ============================================================
# SAVE
# ============================================================

plt.tight_layout()


OUTPUT_FILE = (
    "simulation_results_performance_model.png"
)


plt.savefig(
    OUTPUT_FILE,
    dpi=150
)


plt.show()


print(
    f"\n✅ 图表已保存为 {OUTPUT_FILE}"
)