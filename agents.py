import numpy as np
import mesa


class StudentAgent(mesa.Agent):
    def __init__(self, unique_id, model, B_init, E_init):
        super().__init__(unique_id, model)

        # -------------------------
        # 核心状态
        # -------------------------
        self.B = B_init          # 当前芭蕾基础能力 [0, 100]
        self.E = E_init          # 教学内化效率 [0, 1]
        self.C = 0               # 累计实际上课次数

        # 不同课程等级的掌握度
        self.M = {}              # {level: mastery}

        # 每个等级历史最高掌握度，用于计算遗忘下限
        self.M_peak = {}         # {level: peak_mastery}

        # -------------------------
        # 人口 / 留存状态
        # -------------------------
        self.active = True       # 是否仍属于课堂系统

        # 连续缺课次数
        self.absence_streak = 0

        # -------------------------
        # 本节课状态
        # -------------------------
        self.Y = 0               # 本节课是否到场

    @property
    def b(self):
        """标准化基础能力"""
        return self.B / 100.0

    @property
    def stage(self):
        """
        留存阶段：
        new       = 只上过0-1次
        returning = 已连续上过2次
        stable    = 已连续上过>=3次
        dropped   = 早期流失
        """
        if not self.active:
            return "dropped"
        elif self.C <= 1:
            return "new"
        elif self.C == 2:
            return "returning"
        else:
            return "stable"

    def is_new(self):
        """
        老师眼中的“新人”：
        本节课第一次实际到场。
        """
        return self.C == 0 and self.Y == 1

    def attend(self):
        """
        决定本节课是否到场。

        - 第一次来之后，30%概率连续来第二次；
        - 已经连续来两次后，50%概率连续来第三次；
        - 连续来满3次后成为稳定成员；
        - 稳定成员每节课70%概率到场。
        """

        if not self.active:
            self.Y = 0
            return 0

        # C=0 的学生正常情况下是本节新生成学生，
        # 会在 model.step() 中被强制设为到场。
        if self.C == 0:
            self.Y = 1
            return 1

        # 上过一次：是否连续来第二次
        if self.C == 1:
            if self.random.random() < self.model.first_return_prob:
                self.Y = 1
            else:
                self.Y = 0
                self.active = False
            return self.Y

        # 已经连续上过两次：是否来第三次
        if self.C == 2:
            if self.random.random() < self.model.second_return_prob:
                self.Y = 1
            else:
                self.Y = 0
                self.active = False
            return self.Y

        # 连续来满三次：稳定成员，允许偶尔缺课
        self.Y = (
            1
            if self.random.random() < self.model.stable_attend_prob
            else 0
        )

        return self.Y

    def learn(self, D_t):
        """
        按本节课实际教学难度 D_t 学习。
        """

        if self.Y == 0 or not self.active:
            return

        # 第一次学习这个 level
        if D_t not in self.M:
            self.M[D_t] = 0.0
            self.M_peak[D_t] = 0.0

        # 单节随机状态波动
        epsilon = self.model.np_random.normal(
            0,
            self.model.sigma
        )

        # 学习增量
        delta = (
            self.model.alpha * self.b
            + self.model.gamma * self.E
            - self.model.beta * D_t
            + epsilon
        )

        self.M[D_t] = np.clip(
            self.M[D_t] + delta,
            0,
            100
        )

        # 更新该等级历史最高 mastery
        self.M_peak[D_t] = max(
            self.M_peak.get(D_t, 0),
            self.M[D_t]
        )

    def forget(self):
        """
        连续缺课造成加速遗忘。

        第1次缺课：-2
        第2次：-4
        第3次：-6
        第4次及以后：每次最多-8

        但 mastery 不低于该 level
        历史最高掌握度的50%。
        """

        self.absence_streak += 1

        forgetting = min(
            self.model.forgetting_base
            * self.absence_streak,
            self.model.forgetting_cap
        )

        for lvl in list(self.M.keys()):

            peak = self.M_peak.get(
                lvl,
                self.M[lvl]
            )

            floor = (
                self.model.mastery_retention_floor
                * peak
            )

            self.M[lvl] = max(
                floor,
                self.M[lvl] - forgetting
            )

    def update_attributes(self):
        """
        课后更新学生状态。
        """

        # 已经永久退出的早期学生不再演化
        if not self.active:
            return

        # -------------------------
        # 缺课
        # -------------------------
        if self.Y == 0:

            # 只有稳定学生的缺课属于正常 absence
            # 早期学生未连续回来已经在 attend() 中 dropped
            if self.C >= 3:
                self.forget()

            return

        # -------------------------
        # 到场
        # -------------------------

        # 回来上课后，连续缺课次数归零
        self.absence_streak = 0

        # 累计实际上课次数
        self.C += 1

        # 基础能力缓慢积累
        self.B = min(
            self.model.B_max,
            self.B + self.model.eta_B
        )

        # 教学内化效率增长
        #
        # 完整上完6节课以后，
        # 从第7次出勤开始进入高速增长阶段。
        if self.C <= self.model.internalization_acceleration_after:
            growth = self.model.eta_E_low
        else:
            growth = self.model.eta_E_high

        self.E = min(
            1.0,
            self.E + growth
        )


class Teacher(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        # 长期课程进度
        self.L = 1

        # 本节实际教学难度
        self.D = 1

        # 上节课给出的长期升级许可
        self.U = 0

        # 累计长期升级次数
        self.upgrade_count = 0

    def decide_level(self, R_t):
        """
        课前决定：

        1. 是否推进长期课程等级 L；
        2. 本节实际教学难度 D。

        如果新人超过一半：
        - 不升级长期等级；
        - 当堂难度临时下降一个level。
        """

        newcomer_heavy = (
            R_t > self.model.newcomer_difficulty_threshold
        )

        # 长期升级
        if self.U == 1 and not newcomer_heavy:
            self.L += 1
            self.upgrade_count += 1

        # 本节实际教学难度
        if newcomer_heavy:
            self.D = max(1, self.L - 1)
        else:
            self.D = self.L

        return self.D

    def evaluate_and_permit(
        self,
        old_students,
        teaching_level,
        newcomer_heavy
    ):
        """
        课后评价所有“以前来过”的学生。

        只要以前来过一次，
        老师就认为是老生。

        如果本节新人超过一半，
        本节不产生新的长期升级许可。
        """

        if len(old_students) == 0:
            self.U = 0
            return 0.0

        avg_mastery = np.mean([
            s.M.get(teaching_level, 0)
            for s in old_students
        ])

        # 新生占多数的课堂：
        # 即使老生在较低难度表现不错，
        # 也不据此决定长期升级
        if newcomer_heavy:
            self.U = 0
        else:
            self.U = (
                1
                if avg_mastery
                >= self.model.mastery_threshold
                else 0
            )

        return avg_mastery
