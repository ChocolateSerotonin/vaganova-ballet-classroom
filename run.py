from model import ClassroomModel
import matplotlib.pyplot as plt

# ==================== 参数设置 ====================
model = ClassroomModel(
    n_initial=30,           # 初始30个学生
    p_attend=0.85,          # 85%出勤率
    alpha=10,               # 基础能力权重
    gamma=15,               # 学习效率权重
    beta=2,                 # 等级难度阻碍
    sigma=3,                # 随机波动标准差
    eta_B=2,                # 每节课基础能力增长
    eta_E_low=0.02,         # 顿悟前效率增长
    eta_E_high=0.08,        # 顿悟后效率增长
    k=5,                    # 顿悟阈值（5节课）
    B_max=100,              # 基础能力上限
    delta_M=2,              # 缺课掌握度衰减
    new_student_rate=0.05,  # 每节课5%概率来新学生
    seed=42                 # 随机种子，保证可复现
)

# ==================== 运行模拟 ====================
n_classes = 50
for _ in range(n_classes):
    model.step()

# ==================== 提取数据 ====================
df_model = model.datacollector.get_model_vars_dataframe()
df_agent = model.datacollector.get_agent_vars_dataframe()

print("=== 模型级数据（前10节课）===")
print(df_model.head(10))
print("\n=== 模型级数据（最后5节课）===")
print(df_model.tail())

# ==================== 可视化 ====================
fig, axes = plt.subplots(2, 3, figsize=(15, 8))

df_model["Level"].plot(ax=axes[0,0], title="Class Level (L_t)", marker='o')
df_model["Permission"].plot(ax=axes[0,1], title="Upgrade Permission (U_t)", drawstyle='steps-post')
df_model["New_Ratio"].plot(ax=axes[0,2], title="New Student Ratio (R_t)")
df_model["Avg_Mastery_Old"].plot(ax=axes[1,0], title="Old Students Avg Mastery")
df_model["N_Total"].plot(ax=axes[1,1], title="Total Attendance")
df_model["N_New"].plot(ax=axes[1,2], title="New Students Count")

plt.tight_layout()
plt.savefig("simulation_results.png", dpi=150)
plt.show()

print("\n✅ 图表已保存为 simulation_results.png")
