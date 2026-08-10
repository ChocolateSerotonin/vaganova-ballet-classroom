import numpy as np
import mesa


class StudentAgent(mesa.Agent):

    def __init__(self, unique_id, model, B_init, E_init):
        super().__init__(unique_id, model)

        # Current accumulated ballet foundation
        self.B = B_init

        # Learning / internalization effectiveness
        self.E = E_init

        # Total actual attendances
        self.C = 0

        # Raw latent mastery by curriculum level
        self.M = {}

        # Historical peak mastery by level
        self.M_peak = {}

        # Whether this student is still in the population
        self.active = True

        # Consecutive absences
        self.absence_streak = 0

        # Early-stage absence after first attendance
        self.early_absence_streak = 0

        # Whether delayed return has ever happened
        self.had_delayed_return = False

        # Whether this student later became stable
        # after a delayed return
        self.stable_after_delayed_return = False

        # Attendance this class
        self.Y = 0

        # Performance observed in current class
        self.last_performance_ratio = np.nan


    # ========================================================
    # BASIC PROPERTIES
    # ========================================================

    @property
    def b(self):
        return self.B / 100.0


    @property
    def stage(self):

        if not self.active:
            return "dropped"

        if self.C <= 1:
            return "new"

        if self.C == 2:
            return "returning"

        return "stable"


    def is_new(self):
        return self.C == 0 and self.Y == 1


    # ========================================================
    # LATENT MASTERY
    # ========================================================

    def mastery_ratio(self, level):

        target = self.model.get_level_target(level)

        if target <= 0:
            return 0.0

        raw_mastery = self.M.get(level, 0.0)

        return min(
            1.0,
            raw_mastery / target
        )


    # ========================================================
    # OBSERVED PERFORMANCE
    # ========================================================

    def performance_ratio(self, level):

        latent_mastery = self.mastery_ratio(level)

        state_noise = (
            self.model.performance_rng.normal(
                0,
                self.model.performance_sigma
            )
        )

        observed_performance = np.clip(
            latent_mastery + state_noise,
            0.0,
            1.0
        )

        self.last_performance_ratio = (
            observed_performance
        )

        return observed_performance


    # ========================================================
    # ATTENDANCE
    # ========================================================

    def attend(self):

        if not self.active:
            self.Y = 0
            return 0


        # ----------------------------------------------------
        # First-ever attendance
        # ----------------------------------------------------

        if self.C == 0:

            self.Y = 1
            return 1


        # ----------------------------------------------------
        # Has attended once
        # ----------------------------------------------------

        if self.C == 1:

            # Immediate return opportunity
            if self.early_absence_streak == 0:

                if (
                    self.model.attendance_rng.random()
                    < self.model.first_return_prob
                ):

                    self.Y = 1

                else:

                    self.Y = 0
                    self.early_absence_streak = 1

                return self.Y


            # ------------------------------------------------
            # Delayed-return window
            # ------------------------------------------------

            if (
                self.early_absence_streak
                <= self.model.delayed_return_window
            ):

                if (
                    self.model.attendance_rng.random()
                    < self.model.delayed_return_prob
                ):

                    self.Y = 1

                    self.had_delayed_return = True

                    self.early_absence_streak = 0

                    return 1

                else:

                    self.Y = 0

                    self.early_absence_streak += 1

                    if (
                        self.early_absence_streak
                        > self.model.delayed_return_window
                    ):

                        self.active = False

                    return 0


        # ----------------------------------------------------
        # Has attended twice
        # ----------------------------------------------------

        if self.C == 2:

            if (
                self.model.attendance_rng.random()
                < self.model.second_return_prob
            ):

                self.Y = 1

            else:

                self.Y = 0
                self.active = False

            return self.Y


        # ----------------------------------------------------
        # Stable student
        # ----------------------------------------------------

        self.Y = (
            1
            if (
                self.model.attendance_rng.random()
                < self.model.stable_attend_prob
            )
            else 0
        )

        return self.Y


    # ========================================================
    # LEARNING
    # ========================================================

    def learn(self, teaching_level):

        if self.Y == 0 or not self.active:
            return


        if teaching_level not in self.M:

            self.M[teaching_level] = 0.0
            self.M_peak[teaching_level] = 0.0


        # Latent mastery accumulation.
        # Day-to-day performance noise does not enter here.
        #
        # Attending a class cannot reduce already
        # internalized mastery.

        delta = (
            self.model.alpha * self.b
            + self.model.gamma * self.E
            - self.model.beta * teaching_level
        )

        delta = max(
            0.0,
            delta
        )


        target = self.model.get_level_target(
            teaching_level
        )


        self.M[teaching_level] = np.clip(
            self.M[teaching_level] + delta,
            0.0,
            target
        )


        self.M_peak[teaching_level] = max(
            self.M_peak.get(
                teaching_level,
                0.0
            ),
            self.M[teaching_level]
        )


    # ========================================================
    # FORGETTING
    # ========================================================

    def forget(self):

        self.absence_streak += 1


        forgetting_amount = min(
            self.model.forgetting_base
            * self.absence_streak,
            self.model.forgetting_cap
        )


        for level in list(self.M.keys()):

            peak = self.M_peak.get(
                level,
                self.M[level]
            )


            retention_floor = (
                self.model.mastery_retention_floor
                * peak
            )


            self.M[level] = max(
                retention_floor,
                self.M[level] - forgetting_amount
            )


    # ========================================================
    # POST-CLASS UPDATE
    # ========================================================

    def update_attributes(self):

        if not self.active:
            return


        # ----------------------------------------------------
        # Absent
        # ----------------------------------------------------

        if self.Y == 0:

            # Any student who has attended before
            # can forget previously learned material.
            if self.C > 0:
                self.forget()

            return


        # ----------------------------------------------------
        # Attended
        # ----------------------------------------------------

        self.absence_streak = 0
        self.early_absence_streak = 0


        self.C += 1


        # ----------------------------------------------------
        # Delayed return -> stable
        # ----------------------------------------------------

        if (
            self.C >= 3
            and self.had_delayed_return
        ):

            self.stable_after_delayed_return = True


        # ----------------------------------------------------
        # B growth
        # ----------------------------------------------------

        self.B = min(
            self.model.B_max,
            self.B + self.model.eta_B
        )


        # ----------------------------------------------------
        # E growth
        # ----------------------------------------------------

        if (
            self.C
            <= self.model.internalization_acceleration_after
        ):

            efficiency_growth = (
                self.model.eta_E_low
            )

        else:

            efficiency_growth = (
                self.model.eta_E_high
            )


        self.E = min(
            1.0,
            self.E + efficiency_growth
        )



class Teacher(mesa.Agent):

    def __init__(self, unique_id, model):

        super().__init__(
            unique_id,
            model
        )

        # Long-term curriculum level
        self.L = 1

        # Actual teaching level this class
        self.D = 1

        # Persistent upgrade readiness
        self.U = 0

        self.upgrade_count = 0


    # ========================================================
    # DECIDE CURRENT TEACHING LEVEL
    # ========================================================

    def decide_level(self, new_ratio):

        newcomer_heavy = (
            new_ratio
            > self.model.newcomer_difficulty_threshold
        )


        # Consume existing upgrade permission
        if (
            self.U == 1
            and not newcomer_heavy
        ):

            self.L += 1

            self.upgrade_count += 1

            self.U = 0


        # Temporary teaching-level reduction
        if newcomer_heavy:

            self.D = max(
                1,
                self.L - 1
            )

        else:

            self.D = self.L


        return self.D


    # ========================================================
    # EVALUATE CLASS
    # ========================================================

    def evaluate_and_permit(
        self,
        old_students,
        long_term_level,
        newcomer_heavy
    ):

        # No old students:
        # do not clear existing Permission
        if len(old_students) == 0:

            return 0.0, 0.0


        # ----------------------------------------------------
        # Latent mastery
        # ----------------------------------------------------

        mastery_ratios = [
            student.mastery_ratio(
                long_term_level
            )
            for student in old_students
        ]


        avg_mastery_ratio = np.mean(
            mastery_ratios
        )


        # ----------------------------------------------------
        # Observed performance
        # ----------------------------------------------------

        performance_ratios = [
            student.performance_ratio(
                long_term_level
            )
            for student in old_students
        ]


        avg_performance_ratio = np.mean(
            performance_ratios
        )


        # ----------------------------------------------------
        # Newcomer-heavy class:
        #
        # Report long-term-level mastery/performance,
        # but do not create new upgrade permission.
        # Existing Permission remains unchanged.
        # ----------------------------------------------------

        if newcomer_heavy:

            return (
                avg_mastery_ratio * 100,
                avg_performance_ratio * 100
            )


        # Teacher judges observed performance
        if (
            avg_performance_ratio
            >= self.model.mastery_threshold_ratio
        ):

            self.U = 1


        return (
            avg_mastery_ratio * 100,
            avg_performance_ratio * 100
        )