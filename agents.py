import numpy as np
import mesa


class StudentAgent(mesa.Agent):
    def __init__(self, unique_id, model, B_init, E_init):
        super().__init__(unique_id, model)
        
        # 核心状态
        self.B = B_init          # 基础能力 [0, 100]
        self.E = E_init          # 学习效率 [0, 1]
        self.C = 0               # 累计上课次数
        self.M = {}              # 掌握度: {level: mastery}
        
        # 本节课状态
        self.Y = 0               # 是否到场
        
    @property
    def b(self):
        return self.B / 100.0
    
    def attend(self):
        """阶段1：生成出勤"""
        self.Y = 1 if self.random.random() < self.model.p_attend else 0
        return self.Y
    
    def learn(self, L_t):
        """阶段3：按本节课等级 L_t 学习"""
        if self.Y == 0:
            return
        
        # 首次学习该等级，初始化
        if L_t not in self.M:
            self.M[L_t] = 0
        
        # 学习增量
        epsilon = np.random.normal(0, self.model.sigma)
        delta = (self.model.alpha * self.b 
                 + self.model.gamma * self.E 
                 - self.model.beta * L_t 
                 + epsilon)
        
        self.M[L_t] = np.clip(self.M[L_t] + delta, 0, 100)
    
    def update_attributes(self):
        """阶段5：更新 B 和 E，缺课则掌握度衰减"""
        if self.Y == 0:
            # 缺课：所有已学等级遗忘
            for lvl in list(self.M.keys()):
                self.M[lvl] = max(0, self.M[lvl] - self.model.delta_M)
            return
        
        # 到场：累计次数 +1
        self.C += 1
        
        # 基础能力增长
        self.B = min(self.model.B_max, self.B + self.model.eta_B)
        
        # 学习效率（顿悟机制）
        if self.C < self.model.k:
            self.E = min(1.0, self.E + self.model.eta_E_low)
        else:
            self.E = min(1.0, self.E + self.model.eta_E_high)
    
    def is_new(self):
        """是否为本节课的新学生（首次到场）"""
        return self.C == 0 and self.Y == 1


class Teacher(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.L = 1       # 当前教授等级
        self.U = 0       # 上节课给出的升级许可
    
    def decide_level(self, R_t):
        """阶段2：课前看到新学生比例，临时决定本节课等级"""
        if R_t < 0.5 and self.U == 1:
            self.L += 1
        # 否则维持原等级
    
    def evaluate_and_permit(self, old_students, current_L):
        """阶段4：课后计算老学生平均掌握度，决定下节课许可 U_t"""
        if len(old_students) == 0:
            self.U = 0
            return 0.0
        
        avg_mastery = np.mean([s.M.get(current_L, 0) for s in old_students])
        self.U = 1 if avg_mastery >= 60 else 0
        return avg_mastery
