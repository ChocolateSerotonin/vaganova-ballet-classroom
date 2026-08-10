# Technical Appendix: Vaganova Classroom Simulator

## A.1. Purpose and Scope

The Vaganova Classroom Simulator is a discrete-time stochastic agent-based model designed to formalize a set of observed and experience-informed dynamics in an adult ballet classroom. The model represents how a changing student population, heterogeneous prior foundation, repeated attendance, delayed return, embodied learning, forgetting, day-to-day performance variation, and teacher adaptation may jointly shape class-level progression over an 18-class observation window.

The simulator is **not** an empirical predictive model of ballet learning, nor does it estimate causal effects from a large observational dataset. Its primary purpose is representational: it externalizes a qualitative understanding of classroom dynamics into an explicit computational system whose assumptions can be inspected, challenged, and calibrated against a limited real-world observation record.

Accordingly, the model should be interpreted as a **stochastic computational representation of classroom mechanisms**, not as a validated theory of motor learning or Vaganova pedagogy.

---

## A.2. Model Type and Time Scale

The simulator is a discrete-time agent-based model implemented in Python using Mesa.

One model step corresponds to one class:

\[
t = 1,2,\ldots,18.
\]

The calibrated observation window contains 18 classes.

The model contains two agent types:

1. **Student agents**, who may attend, return, drop out, learn, forget, and become stable members of the class;
2. **A teacher agent**, who maintains a long-term curriculum level, may temporarily reduce the difficulty of a specific class, evaluates returning students, and decides when the long-term curriculum is ready to advance.

There are no direct student-to-student interactions.

---

## A.3. Student State Variables

For student \(i\), the core state variables are:

### A.3.1. Ballet foundation \(B_i\)

\(B_i\in[0,100]\) represents the student's accumulated basic ballet technical foundation.

The normalized foundation used in the learning equation is

\[
b_i=\frac{B_i}{100}.
\]

Initial foundation is sampled from a two-point distribution:

\[
B_{i,0}=
\begin{cases}
10, & p=0.80,\\
30, & p=0.20.
\end{cases}
\]

After every attended class,

\[
B_{i,t+1}=\min(B_{\max},B_{i,t}+\eta_B),
\]

with

\[
B_{\max}=100,\qquad \eta_B=1.
\]

The current class uses the student's pre-class value of \(B_i\); the increment affects subsequent classes.

---

### A.3.2. Internalization effectiveness \(E_i\)

\(E_i\in[0,1]\) represents the student's effectiveness at understanding instruction, absorbing corrections, learning combinations, and converting instruction into embodied capability.

Initial \(E_i\) is sampled as

\[
E_{i,0}=
\begin{cases}
0.20, & p=0.75,\\
0.40, & p=0.20,\\
0.60, & p=0.05.
\end{cases}
\]

Learning-to-learn acceleration begins after six actual attendances.

Let \(C_i\) denote cumulative actual attendances. After an attended class,

\[
E_{i,t+1}
=
\min
\left(
1,\;
E_{i,t}+\eta_E(C_i)
\right),
\]

where

\[
\eta_E(C_i)=
\begin{cases}
0.02, & C_i\le 6,\\
0.04, & C_i>6.
\end{cases}
\]

Thus the seventh actual attendance is the first class after which the higher growth rate is applied.

This mechanism represents increasing familiarity with the teacher's instructional logic rather than a sudden "insight" event.

---

### A.3.3. Attendance count \(C_i\)

\(C_i\) records cumulative actual attendances.

It is used to distinguish early-stage students from stable students:

- \(C_i=0\): never previously attended;
- \(C_i=1\): attended once;
- \(C_i=2\): attended twice;
- \(C_i\ge 3\): stable student.

For teacher evaluation, however, any attending student with \(C_i>0\) is considered an **old student**. Therefore, a student attending for the second time already counts as old for teacher evaluation even though they have not yet entered the stable category.

---

## A.4. Population Initialization and New Arrivals

### A.4.1. Initial class

The first simulated class contains exactly eight students.

All eight are treated as first-time attendees:

\[
N_{\text{initial}}=8.
\]

No additional stochastic arrivals are added in the first class.

---

### A.4.2. New arrivals from Class 2 onward

From the second class onward, the number of first-time students arriving in class \(t\) is

\[
K_t\sim \mathrm{Poisson}(\lambda),
\]

with

\[
\lambda=1.30.
\]

Every newly generated student is an actual attendee in the class in which they appear.

The model does not impose a hard enrollment cap. Physical capacity is retained as a diagnostic reference:

\[
N_{\text{capacity}}=15.
\]

If actual attendance exceeds 15, the event is recorded as over-capacity, but students are not removed or resampled.

---

## A.5. Attendance, Return, and Stabilization

The model distinguishes immediate return, delayed return, second return, and stable attendance.

### A.5.1. Immediate return after the first class

After a student's first attendance, the probability of attending the next class is

\[
p_{\text{first return}}=0.30.
\]

If the student does not immediately return, they do not leave the model at once. Instead, they enter a delayed-return window.

---

### A.5.2. Delayed return

The delayed-return window lasts for two additional classes:

\[
W_{\text{delay}}=2.
\]

In each delayed-return opportunity, the student returns with probability

\[
p_{\text{delay}}=0.12.
\]

If the student fails both delayed-return opportunities, they become inactive.

A delayed return is recorded explicitly so that the model can track both:

- the number of students who return after a gap;
- the number of those students who later become stable.

---

### A.5.3. Transition from two attendances to stable membership

A student with two actual attendances returns for a third class with probability

\[
p_{\text{second return}}=0.50.
\]

If they attend, \(C_i\) becomes 3 and they enter the stable category.

If they fail to return, they become inactive.

---

### A.5.4. Stable attendance

Once \(C_i\ge 3\), the student remains part of the stable population during the 18-class window.

Their class-by-class attendance is stochastic:

\[
Y_{i,t}\sim \mathrm{Bernoulli}(0.70).
\]

Thus stable status does not imply perfect attendance.

Permanent dropout of stable students is not modeled within this short observation window.

---

## A.6. Long-Term Curriculum Level and Actual Teaching Level

The teacher maintains two distinct difficulty variables.

### A.6.1. Long-term curriculum level \(L_t\)

\(L_t\) is the persistent long-term level of the class.

It begins at

\[
L_1=1
\]

and is monotone non-decreasing.

---

### A.6.2. Actual teaching level \(D_t\)

\(D_t\) is the difficulty actually taught in class \(t\).

Let

\[
R_t=\frac{N_{\text{new},t}}{N_{\text{total},t}}
\]

be the newcomer ratio when the class is non-empty.

If newcomers constitute strictly more than half of actual attendees,

\[
R_t>0.50,
\]

the teacher temporarily reduces difficulty by one level:

\[
D_t=\max(1,L_t-1).
\]

Otherwise,

\[
D_t=L_t.
\]

The reduction affects only the current class. It does not decrease \(L_t\).

### Empty-class convention

If no students attend,

\[
N_{\text{total},t}=0,
\]

the model operationally codes

\[
R_t=1.
\]

This is a modeling convention rather than a mathematical claim that \(0/0=1\). It ensures that an empty class is treated as newcomer-heavy: no curriculum upgrade is consumed, no learning occurs, and previously accumulated upgrade readiness is preserved.

---

## A.7. Level-Specific Latent Mastery

Each student has a separate raw latent mastery state for each curriculum level:

\[
M_{i,\ell}.
\]

This quantity represents already internalized capability at level \(\ell\), not day-to-day visible performance.

---

### A.7.1. Level mastery target

The full-mastery target for level \(\ell\) is

\[
T_\ell
=
T_1g^{\ell-1},
\]

with calibrated base

\[
T_1=16
\]

and growth factor

\[
g=1.25.
\]

Therefore:

\[
T_1=16,
\]

\[
T_2=20,
\]

\[
T_3=25,
\]

\[
T_4=31.25,
\]

and so on.

Relative latent mastery is

\[
m_{i,\ell}
=
\min
\left(
1,\frac{M_{i,\ell}}{T_\ell}
\right).
\]

---

## A.8. Learning

If student \(i\) attends a class taught at level \(D_t\), the increment to latent mastery is

\[
\Delta M_{i,t}
=
\max
\left(
0,\;
\alpha b_i+\gamma E_i-\beta D_t
\right).
\]

The calibrated/assumed coefficients are

\[
\alpha=10,\qquad
\gamma=15,\qquad
\beta=1.
\]

Mastery then updates as

\[
M_{i,D_t,t+1}
=
\min
\left(
T_{D_t},
M_{i,D_t,t}
+
\Delta M_{i,t}
\right).
\]

Day-to-day random state variation is deliberately **not** included in this equation.

Therefore, attending a class cannot directly erase already internalized mastery. A poor day may reduce visible performance, but it does not make the student's latent capability disappear.

The coefficients \(\alpha,\gamma,\beta\) should not be interpreted as empirically estimated causal effect sizes. They are modeling parameters whose joint behavior was evaluated through system-level calibration.

---

## A.9. Observed Performance

The model distinguishes latent mastery from visible performance.

For an old student evaluated at long-term level \(L_t\),

\[
p_{i,t}
=
\operatorname{clip}
\left(
m_{i,L_t}
+
\xi_{i,t},
0,1
\right),
\]

where

\[
\xi_{i,t}
\sim
\mathcal{N}(0,\sigma_P^2)
\]

and

\[
\sigma_P=0.15.
\]

Thus observed performance may be better or worse than the student's latent mastery in a specific class.

For example, a student with latent mastery of 0.60 may visibly perform above or below 0.60 depending on day-to-day state.

The performance noise does not modify \(M_{i,\ell}\).

---

## A.10. Forgetting and Retention Floor

Any active student who has attended at least once may forget previously learned material during absence.

Let \(h_{i,t}\) denote the current consecutive absence streak.

The raw mastery loss during an absence is

\[
d(h)
=
\min(2h,8).
\]

Therefore the sequence of forgetting amounts for consecutive absences is

\[
2,\;4,\;6,\;8,\;8,\ldots
\]

For each level, the model also stores the student's historical peak mastery

\[
M^{\text{peak}}_{i,\ell}.
\]

The retention floor is

\[
F_{i,\ell}
=
0.50M^{\text{peak}}_{i,\ell}.
\]

Absent students update according to

\[
M_{i,\ell,t+1}
=
\max
\left(
F_{i,\ell},
M_{i,\ell,t}-d(h_{i,t})
\right).
\]

Returning to class resets the absence streak to zero.

Forgetting is modeled in absolute mastery units rather than as a level-specific percentage loss. This parsimonious assumption is retained because the observation record does not support estimating distinct forgetting functions across curriculum levels.

---

## A.11. Teacher Evaluation and Upgrade Readiness

The teacher evaluates only **attending old students**, defined as students with \(C_i>0\) before the current class's attendance count is updated.

The teacher's decision is based on the average **observed performance** at the current long-term level:

\[
\bar p_t
=
\frac{1}{N_{\text{old},t}}
\sum_{i\in\mathcal O_t}
p_{i,t}.
\]

The readiness threshold is

\[
\theta=0.60.
\]

If the class is not newcomer-heavy and

\[
\bar p_t\ge 0.60,
\]

the teacher sets persistent upgrade readiness

\[
U_t=1.
\]

Importantly, upgrade readiness is **latched**:

- once \(U=1\), a later low-performance class does not reset it;
- a newcomer-heavy class does not reset it;
- a class with no old students does not reset it.

The permission remains available until consumed.

---

## A.12. Upgrade Timing

Upgrade readiness is evaluated after students learn in class \(t\).

The actual long-term upgrade occurs at the start of a later suitable class.

If

\[
U=1
\]

and the current class is not newcomer-heavy, then

\[
L_t\leftarrow L_t+1
\]

and

\[
U\leftarrow 0.
\]

This creates a deliberate one-class separation between:

1. demonstrating sufficient observed performance;
2. actually teaching the next long-term level.

If the class is newcomer-heavy, the permission waits.

---

## A.13. Evaluation During Temporary Difficulty Reduction

When newcomers constitute more than half the class, the teacher may teach

\[
D_t=L_t-1.
\]

However, old students are still evaluated with respect to the long-term curriculum level \(L_t\), not the temporary teaching level \(D_t\).

This encodes the distinction between:

- temporarily simplifying the current class for composition reasons;
- changing the long-term curricular goal.

A newcomer-heavy class cannot create new upgrade readiness.

---

## A.14. Within-Class Update Order

Each model step follows the sequence below.

### Class 1

1. The eight initial students attend.
2. No additional newcomers are generated.

### Class 2 onward

1. Existing active students decide attendance.
2. New students arrive.
3. Attending students are classified as new or old.
4. The newcomer ratio is calculated.
5. Existing upgrade readiness may be consumed.
6. The teacher chooses actual teaching level \(D_t\).
7. Attending students accumulate latent mastery at \(D_t\).
8. The teacher observes old students' latent mastery and noisy performance at long-term level \(L_t\).
9. New upgrade readiness may be created.
10. Attendance counts, \(B\), and \(E\) are updated.
11. Absent previously attending students undergo forgetting.
12. Population statistics are updated.
13. Model data are recorded.

Because \(B\) and \(E\) update after learning, gains in technical foundation or internalization effectiveness affect subsequent classes rather than retroactively changing the class just completed.

---

## A.15. Independent Random Number Streams

The final model uses four independent NumPy random streams derived from a common seed:

1. **arrival RNG** — number of new students;
2. **attribute RNG** — initial \(B\) and \(E\);
3. **attendance RNG** — return, delayed return, second return, and stable attendance;
4. **performance RNG** — day-to-day performance noise.

This separation prevents a change in one stochastic mechanism from silently advancing the random sequence of another mechanism.

For example, changing performance noise should not alter the future number of arriving newcomers.

The same overall seed therefore supports reproducibility while maintaining stochastic modularity.

---

## A.16. Parameter Provenance

The parameter values do not all have the same epistemic status. The table below distinguishes observational anchors, experience-informed estimates, modeling assumptions, and calibration-selected values.

| Parameter / rule | Final value | Primary basis |
|---|---:|---|
| Observation window | 18 classes | Direct observation |
| Initial class size | 8 | Direct observation |
| Physical capacity reference | 15 | Direct/experience-based physical estimate |
| Typical class size | 4–6 | Direct observation |
| Observed approximate maximum attendance | 10 | Direct observation |
| Stable cohort reference | ~5 | Direct/retrospective observation |
| Stable attendance probability | 0.70 | Experience-informed estimate |
| First immediate return probability | 0.30 | Experience-informed estimate |
| Second-to-third attendance probability | 0.50 | Experience-informed estimate |
| Delayed-return window | 2 classes | Modeling assumption informed by observed return patterns |
| Delayed-return probability | 0.12 | Calibration-selected / experience-informed |
| New-student Poisson rate | 1.30 | Calibration-selected / experience-informed |
| Initial \(B\) distribution | 80% at 10; 20% at 30 | Experience-informed observation |
| \(B\) increment | 1 | Modeling assumption |
| Initial \(E\) distribution | 75% at .20; 20% at .40; 5% at .60 | Provisional modeling assumption |
| E acceleration point | after 6 attendances | Experience-informed |
| \(\eta_{E,\text{low}}\) | 0.02 | Modeling assumption |
| \(\eta_{E,\text{high}}\) | 0.04 | Modeling assumption adjusted after logic audit |
| \(\alpha\) | 10 | Modeling assumption / jointly calibrated |
| \(\gamma\) | 15 | Modeling assumption / jointly calibrated |
| \(\beta\) | 1 | Modeling assumption / jointly calibrated |
| Performance sigma | 0.15 | Modeling assumption informed by observed variability |
| Newcomer-heavy threshold | >0.50 | Experience-informed |
| Temporary difficulty reduction | 1 level | Experience-informed |
| Teacher performance threshold | 0.60 | Experience-informed |
| Level target growth | 1.25 | Modeling assumption |
| Level target base | 16 | Calibration-selected |
| Forgetting base | 2 | Modeling assumption informed by qualitative observation |
| Forgetting cap | 8 | Modeling assumption informed by qualitative observation |
| Retention floor | 50% of historical peak | Modeling assumption informed by qualitative observation |

The table is intended to prevent calibrated or assumed parameters from being misrepresented as directly measured empirical quantities.

---

## A.17. Level-Target Parameter Scan

After the final learning, performance, forgetting, and random-stream structure had been defined, the level-target base was scanned across:

\[
\{12.5,\;14,\;15,\;16,\;17.5,\;20\}.
\]

Each candidate was evaluated over 300 seeds and 18 classes per seed, with all other parameters held fixed.

The final comparison was:

| Level target base | Mean upgrades | Median upgrades | Exactly 3 upgrades | 4+ upgrades | Median upgrade classes |
|---:|---:|---:|---:|---:|---|
| 12.5 | 3.39 | 3 | 55% | 40% | 4 / 8 / 13 |
| 14 | 3.17 | 3 | 64% | 26% | 4 / 9 / 14 |
| 15 | 3.09 | 3 | 67% | 21% | 4 / 9 / 14 |
| **16** | **2.95** | **3** | **65%** | **15%** | **4 / 9 / 15** |
| 17.5 | 2.79 | 3 | 61% | 9% | 5 / 10 / 15 |
| 20 | 2.57 | 3 | 51% | 4% | 5 / 11 / 16 |

The final choice,

\[
T_1=16,
\]

was selected because it centered the overall upgrade distribution close to three upgrades while maintaining a high probability of exactly three upgrades and reducing systematic over-progression.

This calibration criterion prioritized the stronger observational constraint—approximately three major upgrades over 18 classes—over exact matching of retrospectively estimated upgrade dates.

---

## A.18. Final Multi-Seed Validation

With the final parameter set fixed, the model was run for:

\[
500
\]

independent seeds, each covering

\[
18
\]

classes.

Key outcomes were:

| Validation statistic | Final result |
|---|---:|
| Mean attendance per class | 4.88 |
| Median of run-level median attendance | 5.00 |
| Mean maximum attendance | 8.90 |
| Runs with maximum attendance \(\le 10\) | 87.20% |
| Mean newcomer-class rate | 74.08% |
| Median final stable students | 6 |
| Runs ending with 4–6 stable students | 44.00% |
| Mean delayed-return students | 4.15 |
| Mean delayed-return students later becoming stable | 1.95 |
| Mean upgrade count | 2.92 |
| Median upgrade count | 3 |
| Runs with exactly 3 upgrades | 64.00% |

The upgrade-count distribution was:

| Upgrades over 18 classes | Runs |
|---:|---:|
| 0 | 1 |
| 1 | 8 |
| 2 | 98 |
| 3 | 320 |
| 4 | 71 |
| 5 | 2 |

Thus, three upgrades formed the clear modal outcome.

Upgrade timing among runs containing the respective upgrade had the following medians:

- first upgrade: Class 4;
- second upgrade: Class 10;
- third upgrade: Class 15.

The middle 50% intervals were:

- first upgrade: Classes 4–6;
- second upgrade: Classes 8–12;
- third upgrade: Classes 13–17.

These results are treated as **internal calibration and face validation**, not out-of-sample empirical validation. The same limited classroom observation record informed both model construction and calibration targets.

---

## A.19. Interpretation of the Final Model

The final model distinguishes three processes that were conflated in earlier prototypes.

### Learning

\[
\text{attendance}
\rightarrow
\text{latent mastery accumulation}.
\]

### Forgetting

\[
\text{absence}
\rightarrow
\text{latent mastery decline subject to a body-memory floor}.
\]

### Performance

\[
\text{latent mastery}
+
\text{day-specific noise}
\rightarrow
\text{visible classroom performance}.
\]

The teacher responds to visible performance, while latent mastery evolves according to learning and forgetting.

This distinction allows a student to:

- know more than they visibly show on a bad day;
- visibly outperform their average mastery on a good day;
- lose latent mastery through repeated absence without treating ordinary day-to-day variability as genuine skill loss.

---

## A.20. Main Simplifying Assumptions

The final simulator deliberately remains parsimonious.

### No peer effects

Students do not directly influence one another's learning, motivation, or attendance.

### No stable dropout within the 18-class window

Once a student reaches three attendances, they remain part of the stable population, although they may miss individual classes.

### Stationary arrival process

Newcomer arrivals follow a stationary Poisson process with constant \(\lambda\).

### Independent initial dimensions

Initial ballet foundation and internalization effectiveness are sampled separately.

### Independent level-specific mastery

Mastery is stored separately for each level. There is no explicit transfer of raw mastery from one level to another; cross-level improvement is represented indirectly through growing \(B\) and \(E\).

### Monotone long-term curriculum

The long-term level never decreases. Only the current teaching level may temporarily drop by one.

### Equal weighting of old students

The teacher uses the arithmetic mean of attending old students' observed performance. There is no minimum old-student sample size and no weighting by seniority.

### Absolute forgetting

Forgetting uses the same raw-unit loss function at all levels.

### Gaussian performance variation

Day-specific state noise is independent and normally distributed, with clipping at 0 and 1.

### Capacity is diagnostic, not enforced

The model records attendance above 15 but does not prevent it.

---

## A.21. Limitations

The most important limitation is the size and nature of the empirical basis. The simulator was constructed from one limited observational context and a mixture of direct observation, retrospective recall, embodied judgment, and explicit modeling choices.

The model therefore cannot support claims such as:

- the true probability that an adult ballet student will return is exactly 0.30;
- internalization effectiveness really increases by 0.04 per class after the sixth attendance;
- performance variation is truly Gaussian with standard deviation 0.15;
- \(E\) has exactly 1.5 times the effect of normalized \(B\);
- the causal effect of newcomer composition on teaching difficulty is precisely represented by the threshold rule.

These quantities are computational commitments required to make the qualitative theory executable.

Further limitations include:

1. no injury, fatigue, work schedule, motivation, or life-event variables;
2. no teacher-specific day-to-day variation;
3. no peer interaction or social belonging mechanism;
4. no explicit movement vocabulary or exercise-level representation;
5. no explicit distinction between memory for combinations and motor execution;
6. no heterogeneity in forgetting parameters;
7. no external validation classroom;
8. no estimation of parameter uncertainty from observed data.

---

## A.22. Appropriate Use

The simulator is best used for:

- inspecting the consequences of an explicit classroom theory;
- comparing alternative assumptions;
- generating stochastic classroom trajectories;
- examining the interaction between population turnover and curriculum progression;
- documenting how tacit and embodied observations can be translated into computational rules.

It should not be used to predict individual students, assess real teachers, or infer universal properties of ballet pedagogy.

---

## A.23. Reproducibility

The final implementation includes:

- `agents.py` — student and teacher agent logic;
- `model.py` — classroom model, parameters, update sequence, data collection, and independent random streams;
- `run.py` — an illustrative 18-class trajectory with a fixed seed;
- `calibrate.py` — 500-seed internal validation.

A fixed seed produces a reproducible trajectory. Multi-seed evaluation is required for model-level interpretation because a single trajectory may look unusually realistic or unrealistic by chance.

---

## A.24. Summary

The final Vaganova Classroom Simulator is a stochastic agent-based representation in which:

1. newcomers enter a changing classroom population;
2. students may return immediately, return after a gap, drop out, or stabilize;
3. technical foundation and internalization effectiveness develop with attendance;
4. students accumulate level-specific latent mastery;
5. absence produces capped forgetting subject to a body-memory floor;
6. visible performance fluctuates around latent mastery;
7. the teacher adapts the current teaching level to newcomer composition;
8. curriculum advancement depends on observed old-student performance;
9. upgrade readiness persists until a suitable class allows it to be consumed.

The calibrated model reproduces several broad features of the observed classroom at the distributional level, including typical attendance, delayed-return behavior, stable cohort size, and approximately three curriculum upgrades over an 18-class window. These matches are best understood as **face-valid calibration outcomes within a small, explicitly interpretive modeling exercise**, rather than as evidence of predictive accuracy.
