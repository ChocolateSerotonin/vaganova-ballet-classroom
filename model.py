import mesa
import numpy as np

from agents import StudentAgent, Teacher


class ClassroomModel(mesa.Model):

    def __init__(
        self,

        # -------------------------
        # 真实课堂规模
        # -------------------------
        n_initial=8,
        class_capacity=15,

        # -------------------------
        # 新生流入
        # -------------------------
        new_student_lambda=0.92,

        # -------------------------
        # 早期留存
        # -------------------------
        first_return_prob=0.30,
        second_return_prob=0.50,
        stable_attend_prob=0.70,

        # -------------------------
        # 学习公式
        # -------------------------
        alpha=10,
        gamma=15,
        beta=2,
        sigma=3,

        # -------------------------
        # 基础能力增长
        # -------------------------
        eta_B=1,
        B_max=100,

        # -------------------------
        # 内化效率
        # -------------------------
        eta_E_low=0.02,
        eta_E_high=0.08,
        internalization_acceleration_after=6,

        # -------------------------
        # 教师升级
        # -------------------------
        mastery_threshold=60,
        newcomer_difficulty_threshold=0.50,

        # -------------------------
        # 遗忘
        # -------------------------
        forgetting_base=2,
        forgetting_cap=8,
        mastery_retention_floor=0.50,

        seed=None
    ):

        super().__init__(seed=seed)

        # NumPy 独立 RNG
        # 保证学习噪声和 Poisson 新生也可以复现
        self.np_random = np.random.default_rng(seed)

        # -------------------------
        # 保存参数
        # -------------------------

        self.n_initial = n_initial
        self.class_capacity = class_capacity

        self.new_student_lambda = new_student_lambda

        self.first_return_prob = first_return_prob
        self.second_return_prob = second_return_prob
        self.stable_attend_prob = stable_attend_prob

        self.alpha = alpha
        self.gamma = gamma
        self.beta = beta
        self.sigma = sigma

        self.eta_B = eta_B
        self.B_max = B_max

        self.eta_E_low = eta_E_low
        self.eta_E_high = eta_E_high
        self.internalization_acceleration_after = (
            internalization_acceleration_after
        )

        self.mastery_threshold = mastery_threshold
        self.newcomer_difficulty_threshold = (
            newcomer_difficulty_threshold
        )

        self.forgetting_base = forgetting_base
        self.forgetting_cap = forgetting_cap
        self.mastery_retention_floor = mastery_retention_floor

        # -------------------------
        # 调度器
        # -------------------------
        self.schedule = mesa.time.BaseScheduler(self)

        # -------------------------
        # 教师
        # -------------------------
        self.teacher = Teacher(0, self)
        self.schedule.add(self.teacher)

        # -------------------------
        # 初始学生
        # -------------------------
        self._next_student_id = 1
        self.initial_students = []

        for _ in range(n_initial):
            s = self._spawn_student()
            self.initial_students.append(s)

        # -------------------------
        # 运行时指标
        # -------------------------
        self.new_ratio = 0.0

        self.avg_mastery_old = 0.0

        self.n_total = 0
        self.n_old = 0
        self.n_new = 0

        self.n_active = n_initial
        self.n_stable = 0
        self.n_dropped = 0

        self.teaching_level = 1

        self.step_count = 0

        # -------------------------
        # 数据收集器
        # -------------------------
        self.datacollector = mesa.DataCollector(

            model_reporters={

                "Level":
                    lambda m: m.teacher.L,

                "Teaching_Level":
                    lambda m: m.teacher.D,

                "Permission":
                    lambda m: m.teacher.U,

                "Upgrade_Count":
                    lambda m: m.teacher.upgrade_count,

                "New_Ratio":
                    "new_ratio",

                "Avg_Mastery_Old":
                    "avg_mastery_old",

                "N_Total":
                    "n_total",

                "N_Old":
                    "n_old",

                "N_New":
                    "n_new",

                "N_Active":
                    "n_active",

                "N_Stable":
                    "n_stable",

                "N_Dropped":
                    "n_dropped",

                # 目前只作为校准警报，
                # 不主动截断课堂人数
                "Over_Capacity":
                    lambda m: (
                        1
                        if m.n_total > m.class_capacity
                        else 0
                    )
            },

            agent_reporters={

                "B":
                    lambda a: getattr(a, "B", None),

                "E":
                    lambda a: getattr(a, "E", None),

                "C":
                    lambda a: getattr(a, "C", None),

                "Y":
                    lambda a: getattr(a, "Y", None),

                "Stage":
                    lambda a: getattr(a, "stage", None),

                "Active":
                    lambda a: getattr(a, "active", None),

                "Absence_Streak":
                    lambda a: getattr(
                        a,
                        "absence_streak",
                        None
                    ),

                "M_Current":
                    lambda a: (
                        getattr(a, "M", {}).get(
                            getattr(
                                a.model.teacher,
                                "D",
                                None
                            ),
                            None
                        )
                        if hasattr(a, "M")
                        else None
                    )
            }
        )

    # =================================================
    # 新生初始化
    # =================================================

    def _sample_initial_B(self):
        """
        80%低基础：B=10
        20%有一定基础：B=30
        """
        if self.random.random() < 0.80:
            return 10
        else:
            return 30

    def _sample_initial_E(self):
        """
        暂定建模假设：

        75% -> E=0.2
        20% -> E=0.4
         5% -> E=0.6
        """

        r = self.random.random()

        if r < 0.75:
            return 0.2
        elif r < 0.95:
            return 0.4
        else:
            return 0.6

    def _spawn_student(self):

        B0 = self._sample_initial_B()
        E0 = self._sample_initial_E()

        s = StudentAgent(
            self._next_student_id,
            self,
            B0,
            E0
        )

        self.schedule.add(s)

        self._next_student_id += 1

        return s

    # =================================================
    # 新生流入
    # =================================================

    def add_new_students(self):
        """
        从第二节课开始：

        K_t ~ Poisson(lambda=0.92)

        新生成的学生就是本节实际第一次到场的人。
        """

        n_new = self.np_random.poisson(
            self.new_student_lambda
        )

        new_students = []

        for _ in range(n_new):
            s = self._spawn_student()

            # 第一次进入系统意味着本节实际到场
            s.Y = 1

            new_students.append(s)

        return new_students

    # =================================================
    # 单节课
    # =================================================

    def step(self):

        # =============================================
        # 阶段0：确定本节第一次到场的新生
        # =============================================

        if self.step_count == 0:

            # 第一节严格复现真实观察：
            # 8名初始学生全部实际到场
            new_students = self.initial_students

            for s in new_students:
                s.Y = 1

        else:

            new_students = self.add_new_students()

        # =============================================
        # 阶段1：学生出勤 / 早期留存
        # =============================================

        students = [
            a
            for a in self.schedule.agents
            if isinstance(a, StudentAgent)
        ]

        for s in students:

            # 本节新生已经被强制设为到场
            if s in new_students:
                continue

            s.attend()

        attending = [
            s
            for s in students
            if s.active and s.Y == 1
        ]

        # 老师眼中的老生：
        # 本节开始前已经至少上过一次课
        old_students = [
            s
            for s in attending
            if s.C > 0
        ]

        first_time_students = [
            s
            for s in attending
            if s.C == 0
        ]

        self.n_total = len(attending)
        self.n_old = len(old_students)
        self.n_new = len(first_time_students)

        self.new_ratio = (
            self.n_new / self.n_total
            if self.n_total > 0
            else 1.0
        )

        # =============================================
        # 阶段2：老师决定长期等级 + 本节实际难度
        # =============================================

        self.teaching_level = (
            self.teacher.decide_level(
                self.new_ratio
            )
        )

        D_t = self.teaching_level

        newcomer_heavy = (
            self.new_ratio
            > self.newcomer_difficulty_threshold
        )

        # =============================================
        # 阶段3：教学
        # =============================================

        for s in attending:
            s.learn(D_t)

        # =============================================
        # 阶段4：教师评价老生
        # =============================================

        self.avg_mastery_old = (
            self.teacher.evaluate_and_permit(
                old_students,
                D_t,
                newcomer_heavy
            )
        )

        # =============================================
        # 阶段5：学生状态更新
        # =============================================

        for s in students:
            s.update_attributes()

        # =============================================
        # 更新人口统计
        # =============================================

        self.n_active = sum(
            1
            for s in students
            if s.active
        )

        self.n_stable = sum(
            1
            for s in students
            if s.active and s.C >= 3
        )

        self.n_dropped = sum(
            1
            for s in students
            if not s.active
        )

        # =============================================
        # 收集数据
        # =============================================

        self.datacollector.collect(self)

        self.step_count += 1
