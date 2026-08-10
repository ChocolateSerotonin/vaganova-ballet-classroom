import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from model import ClassroomModel
from agents import StudentAgent


# ============================================================
# CALIBRATION SETTINGS
# ============================================================

N_RUNS = 500
N_CLASSES = 18


# ============================================================
# FINAL VALIDATED PARAMETERS
#
# Keep this parameter set synchronized with run.py and model.py.
# These values correspond to the final calibrated model.
# ============================================================

BASE_PARAMS = {

    # Population
    "n_initial": 8,
    "class_capacity": 15,

    # New students
    "new_student_lambda": 1.30,

    # Early retention
    "first_return_prob": 0.30,

    "delayed_return_prob": 0.12,
    "delayed_return_window": 2,

    "second_return_prob": 0.50,

    # Stable students
    "stable_attend_prob": 0.70,

    # Learning
    "alpha": 10,
    "gamma": 15,
    "beta": 1,
    "performance_sigma": 0.15,

    # B
    "eta_B": 1,
    "B_max": 100,

    # E
    "eta_E_low": 0.02,
    "eta_E_high": 0.04,
    "internalization_acceleration_after": 6,

    # Mastery
    "level_target_base": 16,
    "level_target_growth": 1.25,
    "mastery_threshold_ratio": 0.60,

    # Newcomer-related temporary difficulty reduction
    "newcomer_difficulty_threshold": 0.50,

    # Forgetting
    "forgetting_base": 2,
    "forgetting_cap": 8,
    "mastery_retention_floor": 0.50,
}


# ============================================================
# ONE SIMULATION
# ============================================================

def run_one_simulation(seed):

    params = BASE_PARAMS.copy()
    params["seed"] = seed

    model = ClassroomModel(
        **params
    )

    for _ in range(N_CLASSES):
        model.step()

    df = (
        model.datacollector
        .get_model_vars_dataframe()
    )


    # --------------------------------------------------------
    # Upgrade timing
    # --------------------------------------------------------

    levels = df["Level"].to_numpy()

    upgrade_classes = []

    for i in range(1, len(levels)):

        if levels[i] > levels[i - 1]:

            # dataframe index 0 = Class 1
            upgrade_classes.append(i + 1)


    # --------------------------------------------------------
    # All students ever created
    # --------------------------------------------------------

    students = [

        agent

        for agent in model.schedule.agents

        if isinstance(
            agent,
            StudentAgent
        )
    ]


    # --------------------------------------------------------
    # Delayed-return metrics
    # --------------------------------------------------------

    n_delayed_return = sum(

        1

        for student in students

        if student.had_delayed_return
    )


    n_stable_after_delayed = sum(

        1

        for student in students

        if student.stable_after_delayed_return
    )


    # --------------------------------------------------------
    # Attendance metrics
    # --------------------------------------------------------

    attendance = df["N_Total"]


    # 实际课堂落在4–6人的比例
    attendance_4_to_6_rate = (

        (
            (attendance >= 4)
            &
            (attendance <= 6)
        )
        .mean()
    )


    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    result = {

        "seed": seed,

        "mean_attendance":
            attendance.mean(),

        "median_attendance":
            attendance.median(),

        "max_attendance":
            attendance.max(),

        "min_attendance":
            attendance.min(),

        "attendance_4_to_6_rate":
            attendance_4_to_6_rate,

        "newcomer_class_rate":
            (df["N_New"] > 0).mean(),

        "final_stable":
            model.n_stable,

        "final_active":
            model.n_active,

        "upgrade_count":
            model.teacher.upgrade_count,

        "final_level":
            model.teacher.L,

        "delayed_return_students":
            n_delayed_return,

        "stable_after_delayed_return":
            n_stable_after_delayed,
    }


    # --------------------------------------------------------
    # Store timing of first 4 upgrades
    # --------------------------------------------------------

    for n in range(1, 5):

        key = f"upgrade_{n}_class"

        if len(upgrade_classes) >= n:

            result[key] = upgrade_classes[n - 1]

        else:

            result[key] = np.nan


    return result


# ============================================================
# RUN 500 SIMULATIONS
# ============================================================

print("\n========================================")
print("VAGANOVA MODEL — MULTI-SEED CALIBRATION")
print("========================================")

print(f"\nNumber of runs: {N_RUNS}")
print(f"Classes per run: {N_CLASSES}")

print("\nRunning simulations...\n")


all_results = []


for seed in range(N_RUNS):

    result = run_one_simulation(
        seed
    )

    all_results.append(
        result
    )

    if (seed + 1) % 50 == 0:

        print(
            f"Completed {seed + 1} / {N_RUNS}"
        )


results = pd.DataFrame(
    all_results
)


# ============================================================
# SAVE RAW RESULTS
# ============================================================

results.to_csv(
    "calibration_500_runs.csv",
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

summary_columns = [

    "mean_attendance",

    "median_attendance",

    "max_attendance",

    "attendance_4_to_6_rate",

    "newcomer_class_rate",

    "final_stable",

    "final_active",

    "upgrade_count",

    "final_level",

    "delayed_return_students",

    "stable_after_delayed_return",

    "upgrade_1_class",

    "upgrade_2_class",

    "upgrade_3_class",
]


summary_rows = []


for column in summary_columns:

    values = (
        results[column]
        .dropna()
    )

    summary_rows.append({

        "metric": column,

        "mean":
            values.mean(),

        "median":
            values.median(),

        "std":
            values.std(),

        "p10":
            values.quantile(0.10),

        "p25":
            values.quantile(0.25),

        "p75":
            values.quantile(0.75),

        "p90":
            values.quantile(0.90),

        "min":
            values.min(),

        "max":
            values.max(),
    })


summary = pd.DataFrame(
    summary_rows
)


summary.to_csv(
    "calibration_summary.csv",
    index=False
)


# ============================================================
# PRINT SUMMARY
# ============================================================

print("\n========================================")
print("CALIBRATION SUMMARY")
print("========================================\n")

print(
    summary.to_string(
        index=False,
        float_format=lambda x: f"{x:.2f}"
    )
)


# ============================================================
# IMPORTANT DISTRIBUTIONS
# ============================================================

print("\n========================================")
print("UPGRADE COUNT DISTRIBUTION")
print("========================================\n")

print(
    results[
        "upgrade_count"
    ]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\n========================================")
print("FINAL STABLE DISTRIBUTION")
print("========================================\n")

print(
    results[
        "final_stable"
    ]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\n========================================")
print("DELAYED RETURN DISTRIBUTION")
print("========================================\n")

print(
    results[
        "delayed_return_students"
    ]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\n========================================")
print("STABLE AFTER DELAYED RETURN DISTRIBUTION")
print("========================================\n")

print(
    results[
        "stable_after_delayed_return"
    ]
    .value_counts()
    .sort_index()
    .to_string()
)


# ============================================================
# SIMPLE CALIBRATION INDICATORS
# ============================================================

print("\n========================================")
print("KEY CALIBRATION INDICATORS")
print("========================================")


print(
    "\nMean attendance across simulations:",
    f"{results['mean_attendance'].mean():.2f}"
)


print(
    "Median final stable students:",
    f"{results['final_stable'].median():.0f}"
)


print(
    "Mean newcomer-class rate:",
    f"{results['newcomer_class_rate'].mean():.2%}"
)


print(
    "Median upgrade count:",
    f"{results['upgrade_count'].median():.0f}"
)


print(
    "Runs with exactly 3 upgrades:",
    f"{(results['upgrade_count'] == 3).mean():.2%}"
)


print(
    "Runs ending with 4–6 stable students:",
    f"{results['final_stable'].between(4, 6).mean():.2%}"
)


print(
    "Runs with max attendance <= 10:",
    f"{(results['max_attendance'] <= 10).mean():.2%}"
)


print(
    "Average percentage of classes with 4–6 students:",
    f"{results['attendance_4_to_6_rate'].mean():.2%}"
)


print(
    "Mean delayed-return students:",
    f"{results['delayed_return_students'].mean():.2f}"
)


print(
    "Mean delayed-return students becoming stable:",
    f"{results['stable_after_delayed_return'].mean():.2f}"
)


# ============================================================
# UPGRADE TIMING
# ============================================================

print("\n========================================")
print("UPGRADE TIMING")
print("========================================")


for n in range(1, 4):

    column = f"upgrade_{n}_class"

    valid = results[column].dropna()

    print(
        f"\nUpgrade {n}:"
    )

    print(
        f"  simulations containing this upgrade: "
        f"{len(valid)} / {N_RUNS}"
    )

    if len(valid) > 0:

        print(
            f"  median class: "
            f"{valid.median():.1f}"
        )

        print(
            f"  middle 50%: "
            f"{valid.quantile(.25):.1f}"
            f" – "
            f"{valid.quantile(.75):.1f}"
        )


# ============================================================
# PLOTS
# ============================================================

fig, axes = plt.subplots(
    3,
    2,
    figsize=(14, 12)
)


# ------------------------------------------------------------
# Mean attendance
# ------------------------------------------------------------

axes[0, 0].hist(
    results["mean_attendance"],
    bins=20
)

axes[0, 0].axvline(
    4,
    linestyle="--"
)

axes[0, 0].axvline(
    6,
    linestyle="--"
)

axes[0, 0].set_title(
    "Mean Attendance per 18-Class Run"
)

axes[0, 0].set_xlabel(
    "Mean students per class"
)


# ------------------------------------------------------------
# Stable students
# ------------------------------------------------------------

stable_bins = np.arange(
    results["final_stable"].min() - 0.5,
    results["final_stable"].max() + 1.5,
    1
)

axes[0, 1].hist(
    results["final_stable"],
    bins=stable_bins
)

axes[0, 1].axvline(
    5,
    linestyle="--"
)

axes[0, 1].set_title(
    "Final Stable Students"
)

axes[0, 1].set_xlabel(
    "Stable students"
)


# ------------------------------------------------------------
# Upgrade count
# ------------------------------------------------------------

upgrade_bins = np.arange(
    results["upgrade_count"].min() - 0.5,
    results["upgrade_count"].max() + 1.5,
    1
)

axes[1, 0].hist(
    results["upgrade_count"],
    bins=upgrade_bins
)

axes[1, 0].axvline(
    3,
    linestyle="--"
)

axes[1, 0].set_title(
    "Upgrade Count over 18 Classes"
)

axes[1, 0].set_xlabel(
    "Number of upgrades"
)


# ------------------------------------------------------------
# Newcomer class rate
# ------------------------------------------------------------

axes[1, 1].hist(
    results["newcomer_class_rate"],
    bins=20
)

axes[1, 1].set_title(
    "Classes Containing New Students"
)

axes[1, 1].set_xlabel(
    "Proportion of classes"
)


# ------------------------------------------------------------
# Delayed return
# ------------------------------------------------------------

axes[2, 0].hist(
    results["delayed_return_students"],
    bins=np.arange(
        results["delayed_return_students"].min() - 0.5,
        results["delayed_return_students"].max() + 1.5,
        1
    )
)

axes[2, 0].axvline(
    5,
    linestyle="--"
)

axes[2, 0].set_title(
    "Delayed-Return Students"
)

axes[2, 0].set_xlabel(
    "Students"
)


# ------------------------------------------------------------
# Stable after delayed return
# ------------------------------------------------------------

axes[2, 1].hist(
    results[
        "stable_after_delayed_return"
    ],
    bins=np.arange(
        results[
            "stable_after_delayed_return"
        ].min() - 0.5,

        results[
            "stable_after_delayed_return"
        ].max() + 1.5,

        1
    )
)

axes[2, 1].axvline(
    2,
    linestyle="--"
)

axes[2, 1].set_title(
    "Delayed Return → Stable"
)

axes[2, 1].set_xlabel(
    "Students"
)


plt.tight_layout()

plt.savefig(
    "calibration_500_runs.png",
    dpi=150
)

plt.show()


print("\n========================================")
print("DONE")
print("========================================")

print(
    "\nSaved:"
)

print(
    "  calibration_500_runs.csv"
)

print(
    "  calibration_summary.csv"
)

print(
    "  calibration_500_runs.png"
)