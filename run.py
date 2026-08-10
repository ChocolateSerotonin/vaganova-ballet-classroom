from model import ClassroomModel
import matplotlib.pyplot as plt


# =====================================================
# 参数设置
# =====================================================

model = ClassroomModel(

    # 真实课堂人口
    n_initial=8,
    class_capacity=15,

    # 新生
    new_student_lambda=0.92,

    # 早期留存
    first_return_prob=0.30,
    second_return_prob=0.50,
    stable_attend_prob=0.70,

    # 学习
    alpha=10,
    gamma=15,
    beta=2,
    sigma=3,

    # 基本功
    eta_B=1,
    B_max=100,

    # 内化效率
    eta_E_low=0.02,
    eta_E_high=0.08,
    internalization_acceleration_after=6,

    # 教师
    mastery_threshold=60,
    newcomer_difficulty_threshold=0.50,

    # 遗忘
    forgetting_base=2,
    forgetting_cap=8,
    mastery_retention_floor=0.50,

    seed=42
)


# =====================================================
# 运行18节课
# =====================================================

n_classes = 18

for _ in range(n_classes):
    model.step()


# =====================================================
# 提取数据
# =====================================================

df_model = (
    model.datacollector
    .get_model_vars_dataframe()
)

df_agent = (
    model.datacollector
    .get_agent_vars_dataframe()
)


print("=== 17节课堂记录 ===")
print(df_model)

print("\n=== 最终结果 ===")

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


# =====================================================
# 可视化
# =====================================================

fig, axes = plt.subplots(
    3,
    2,
    figsize=(14, 12)
)

df_model["N_Total"].plot(
    ax=axes[0, 0],
    marker="o",
    title="Attendance"
)

df_model["N_New"].plot(
    ax=axes[0, 1],
    marker="o",
    title="New Students"
)

df_model[[
    "Level",
    "Teaching_Level"
]].plot(
    ax=axes[1, 0],
    marker="o",
    title="Long-term Level vs Teaching Level"
)

df_model["Avg_Mastery_Old"].plot(
    ax=axes[1, 1],
    marker="o",
    title="Old Students Avg Mastery"
)

df_model["N_Stable"].plot(
    ax=axes[2, 0],
    marker="o",
    title="Stable Students"
)

df_model["New_Ratio"].plot(
    ax=axes[2, 1],
    marker="o",
    title="New Student Ratio"
)

plt.tight_layout()

plt.savefig(
    "simulation_results_v2.png",
    dpi=150
)

plt.show()

print(
    "\n✅ 图表已保存为 "
    "simulation_results_v2.png"
)
