import numpy as np
import mesa

from agents import StudentAgent, Teacher


class ClassroomModel(mesa.Model):

    def __init__(

        self,

        # =====================================================
        # Population
        # =====================================================

        n_initial=8,
        class_capacity=15,

        # =====================================================
        # New-student arrival
        # =====================================================

        new_student_lambda=1.30,

        # =====================================================
        # Attendance / retention
        # =====================================================

        first_return_prob=0.30,

        delayed_return_prob=0.12,
        delayed_return_window=2,

        second_return_prob=0.50,

        stable_attend_prob=0.70,

        # =====================================================
        # Learning
        # =====================================================

        alpha=10,
        gamma=15,
        beta=1,

        # Day-to-day observed performance variability
        performance_sigma=0.15,

        # =====================================================
        # B
        # =====================================================

        eta_B=1,
        B_max=100,

        # =====================================================
        # E
        # =====================================================

        eta_E_low=0.02,
        eta_E_high=0.04,

        internalization_acceleration_after=6,

        # =====================================================
        # Level mastery
        # =====================================================

        level_target_base=16,
        level_target_growth=1.25,

        mastery_threshold_ratio=0.60,

        # =====================================================
        # Teacher adaptation
        # =====================================================

        newcomer_difficulty_threshold=0.50,

        # =====================================================
        # Forgetting
        # =====================================================

        forgetting_base=2,
        forgetting_cap=8,

        mastery_retention_floor=0.50,

        # =====================================================
        # Random seed
        # =====================================================

        seed=None
    ):

        super().__init__(
            seed=seed
        )


        # =====================================================
        # PARAMETERS
        # =====================================================

        self.n_initial = n_initial
        self.class_capacity = class_capacity

        self.new_student_lambda = (
            new_student_lambda
        )


        self.first_return_prob = (
            first_return_prob
        )

        self.delayed_return_prob = (
            delayed_return_prob
        )

        self.delayed_return_window = (
            delayed_return_window
        )

        self.second_return_prob = (
            second_return_prob
        )

        self.stable_attend_prob = (
            stable_attend_prob
        )


        self.alpha = alpha
        self.gamma = gamma
        self.beta = beta

        self.performance_sigma = (
            performance_sigma
        )


        self.eta_B = eta_B
        self.B_max = B_max


        self.eta_E_low = eta_E_low
        self.eta_E_high = eta_E_high

        self.internalization_acceleration_after = (
            internalization_acceleration_after
        )


        self.level_target_base = (
            level_target_base
        )

        self.level_target_growth = (
            level_target_growth
        )

        self.mastery_threshold_ratio = (
            mastery_threshold_ratio
        )


        self.newcomer_difficulty_threshold = (
            newcomer_difficulty_threshold
        )


        self.forgetting_base = (
            forgetting_base
        )

        self.forgetting_cap = (
            forgetting_cap
        )

        self.mastery_retention_floor = (
            mastery_retention_floor
        )


        # =====================================================
        # INDEPENDENT RANDOM STREAMS
        # =====================================================
        #
        # arrival_rng:
        #   How many new students arrive.
        #
        # attribute_rng:
        #   Initial B / E of newly created students.
        #
        # attendance_rng:
        #   Immediate return, delayed return,
        #   second return, stable attendance.
        #
        # performance_rng:
        #   Day-to-day observed performance noise.
        #
        # Changing one mechanism therefore does not
        # silently move the random sequence of another.
        # =====================================================

        seed_sequence = np.random.SeedSequence(
            seed
        )

        (
            arrival_seed,
            attribute_seed,
            attendance_seed,
            performance_seed
        ) = seed_sequence.spawn(4)


        self.arrival_rng = np.random.default_rng(
            arrival_seed
        )

        self.attribute_rng = np.random.default_rng(
            attribute_seed
        )

        self.attendance_rng = np.random.default_rng(
            attendance_seed
        )

        self.performance_rng = np.random.default_rng(
            performance_seed
        )


        # =====================================================
        # SCHEDULER
        # =====================================================

        self.schedule = mesa.time.BaseScheduler(
            self
        )


        # =====================================================
        # TEACHER
        # =====================================================

        self.teacher = Teacher(
            self.next_id(),
            self
        )

        self.schedule.add(
            self.teacher
        )


        # =====================================================
        # CLASS COUNTER
        # =====================================================

        self.class_index = 0


        # =====================================================
        # CURRENT-CLASS METRICS
        # =====================================================

        self.current_n_total = 0
        self.current_n_old = 0
        self.current_n_new = 0

        # Modeling convention:
        # empty classroom is treated as newcomer-heavy
        self.current_new_ratio = 1.0

        self.current_avg_mastery_old = 0.0

        self.current_avg_performance_old = 0.0


        # =====================================================
        # POPULATION METRICS
        # =====================================================

        self.n_stable = 0
        self.n_active = 0


        # =====================================================
        # INITIAL STUDENTS
        #
        # All 8 are first-time students in Class 1.
        # =====================================================

        for _ in range(
            self.n_initial
        ):

            self._spawn_student()


        self._update_population_counts()


        # =====================================================
        # DATA COLLECTOR
        # =====================================================

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
                    lambda m: m.current_new_ratio,

                "Avg_Mastery_Old":
                    lambda m: m.current_avg_mastery_old,

                "Avg_Performance_Old":
                    lambda m: m.current_avg_performance_old,

                "N_Total":
                    lambda m: m.current_n_total,

                "N_Old":
                    lambda m: m.current_n_old,

                "N_New":
                    lambda m: m.current_n_new,

                "N_Stable":
                    lambda m: m.n_stable,

                "N_Active":
                    lambda m: m.n_active,

                "Over_Capacity":
                    lambda m: (
                        1
                        if (
                            m.current_n_total
                            > m.class_capacity
                        )
                        else 0
                    ),
            },

            agent_reporters={

                "B":
                    lambda a: (
                        a.B
                        if isinstance(
                            a,
                            StudentAgent
                        )
                        else np.nan
                    ),

                "E":
                    lambda a: (
                        a.E
                        if isinstance(
                            a,
                            StudentAgent
                        )
                        else np.nan
                    ),

                "C":
                    lambda a: (
                        a.C
                        if isinstance(
                            a,
                            StudentAgent
                        )
                        else np.nan
                    ),

                "Y":
                    lambda a: (
                        a.Y
                        if isinstance(
                            a,
                            StudentAgent
                        )
                        else np.nan
                    ),
            }
        )


    # =========================================================
    # STUDENT HELPERS
    # =========================================================

    def get_students(self):

        return [
            agent
            for agent in self.schedule.agents
            if isinstance(
                agent,
                StudentAgent
            )
        ]


    # =========================================================
    # INITIAL B
    # =========================================================

    def _sample_initial_B(self):

        # 80% low foundation
        # 20% some prior foundation

        if self.attribute_rng.random() < 0.80:
            return 10

        return 30


    # =========================================================
    # INITIAL E
    # =========================================================

    def _sample_initial_E(self):

        r = self.attribute_rng.random()

        if r < 0.75:
            return 0.20

        elif r < 0.95:
            return 0.40

        else:
            return 0.60


    # =========================================================
    # SPAWN STUDENT
    # =========================================================

    def _spawn_student(self):

        student = StudentAgent(

            self.next_id(),

            self,

            self._sample_initial_B(),

            self._sample_initial_E()
        )


        self.schedule.add(
            student
        )


        return student


    # =========================================================
    # NEW STUDENT ARRIVAL
    # =========================================================

    def add_new_students(self):

        number_new = self.arrival_rng.poisson(
            self.new_student_lambda
        )


        new_students = []


        for _ in range(
            number_new
        ):

            student = self._spawn_student()

            # New arrivals are actual attendees
            # in the class in which they appear.
            student.Y = 1

            new_students.append(
                student
            )


        return new_students


    # =========================================================
    # LEVEL TARGET
    # =========================================================

    def get_level_target(self, level):

        return (
            self.level_target_base
            * (
                self.level_target_growth
                ** (level - 1)
            )
        )


    # =========================================================
    # POPULATION COUNTS
    # =========================================================

    def _update_population_counts(self):

        students = self.get_students()


        self.n_stable = sum(

            1

            for student in students

            if (
                student.active
                and student.C >= 3
            )
        )


        self.n_active = sum(

            1

            for student in students

            if student.active
        )


    # =========================================================
    # ONE CLASS
    # =========================================================

    def step(self):

        # -----------------------------------------------------
        # Reset current-class variables
        # -----------------------------------------------------

        students_before = self.get_students()


        for student in students_before:

            student.Y = 0

            student.last_performance_ratio = (
                np.nan
            )


        # -----------------------------------------------------
        # CLASS 1
        #
        # Initial 8 students are all first-time attendees.
        # No additional arrivals.
        # -----------------------------------------------------

        if self.class_index == 0:

            for student in students_before:

                if student.active:
                    student.Y = 1


        # -----------------------------------------------------
        # CLASS 2+
        # -----------------------------------------------------

        else:

            # Existing students decide whether to attend
            for student in students_before:

                if student.active:
                    student.attend()


            # New students arrive
            self.add_new_students()


        # -----------------------------------------------------
        # WHO IS ACTUALLY PRESENT?
        # -----------------------------------------------------

        students = self.get_students()


        attending_students = [

            student

            for student in students

            if (
                student.active
                and student.Y == 1
            )
        ]


        # Old = has attended at least once before
        old_students = [

            student

            for student in attending_students

            if student.C > 0
        ]


        # New = first-ever attendance
        new_students = [

            student

            for student in attending_students

            if student.C == 0
        ]


        self.current_n_total = len(
            attending_students
        )

        self.current_n_old = len(
            old_students
        )

        self.current_n_new = len(
            new_students
        )


        # -----------------------------------------------------
        # NEW RATIO
        #
        # Modeling convention:
        # empty classroom is coded as newcomer ratio = 1.
        # -----------------------------------------------------

        if self.current_n_total == 0:

            self.current_new_ratio = 1.0

        else:

            self.current_new_ratio = (
                self.current_n_new
                / self.current_n_total
            )


        newcomer_heavy = (
            self.current_new_ratio
            > self.newcomer_difficulty_threshold
        )


        # -----------------------------------------------------
        # TEACHER DECIDES LEVEL
        # -----------------------------------------------------

        teaching_level = (
            self.teacher.decide_level(
                self.current_new_ratio
            )
        )


        # -----------------------------------------------------
        # STUDENTS LEARN
        # -----------------------------------------------------

        for student in attending_students:

            student.learn(
                teaching_level
            )


        # -----------------------------------------------------
        # TEACHER OBSERVES OLD STUDENTS
        #
        # Even in newcomer-heavy classes where D < L,
        # evaluation still refers to long-term level L.
        # -----------------------------------------------------

        (
            avg_mastery,
            avg_performance
        ) = self.teacher.evaluate_and_permit(

            old_students,

            self.teacher.L,

            newcomer_heavy
        )


        self.current_avg_mastery_old = (
            avg_mastery
        )

        self.current_avg_performance_old = (
            avg_performance
        )


        # -----------------------------------------------------
        # POST-CLASS STUDENT UPDATES
        # -----------------------------------------------------

        for student in students:

            student.update_attributes()


        # -----------------------------------------------------
        # UPDATE POPULATION COUNTS
        # -----------------------------------------------------

        self._update_population_counts()


        # -----------------------------------------------------
        # COLLECT DATA
        # -----------------------------------------------------

        self.datacollector.collect(
            self
        )


        self.class_index += 1
