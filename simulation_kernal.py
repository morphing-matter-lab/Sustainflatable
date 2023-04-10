import math

p_atm = 1.013e2
p_check = 0 # 3.45
beta = 0

def linlist(a, b, step):
    r = []
    if step == 0:
        r = [a, b]
    else:
        i = a
        if a < b:
            while i <= b:
                r.append(i)
                i+=step
            #r.append(b)
        elif a > b:
            while i >= b:
                r.append(i)
                i-=step
            #r.append(b)
        else:
            r = [a, b]
    return r

class Environment:
    pressure = 0
    temperature = 0
    wetness = 0
    windspeed = 0
    pumping_pressure = 0
    
    def __init__(self, temperature, wetness, windspeed):
        self.pressure = p_atm
        self.wetness = wetness
        self.temperature = temperature
        self.windspeed = windspeed
        self.pumping_pressure = p_atm

def LBL_pressure(T, type): # celces
    p_vapor_acetaldehyde = math.exp((-1637.083/(T+273.15+22.317) + 5.1883)*math.log1p(9))*p_atm
    p_vapor_butadiene = math.exp((-1121.000/(T+251.000) + 7.16190)*math.log1p(9))*0.133
    p_vapor_novec = math.exp(-3548.6/(T+273.15) + 22.978)/1000
        
    p_vapor = 0
    if type == 1:
        p_vapor = p_vapor_novec
    elif type == 2:
        p_vapor = p_vapor_acetaldehyde
    elif type == 3:
        p_vapor = p_vapor_butadiene
    return p_vapor

def Wet_pressure(wet):
    if wet>0.5:
        p = 28.5 + p_atm
    else:
        p = p_atm
    return p

def Wind_pressure(speed):
    p = 0
    p = p_atm+0.1019*speed*speed
    return p

class Pump:
    type = 0 # 1-thermal, 2-wet, 3-mechanical
    max_pumping_volume_0 = 0

    max_pumping_volume = 0 #mL
    body_volume = 0 #mL 
    
    pumping_volume = 0
    pressure = p_atm

    LBLtype = 0 # 1-novec, 2-acetaldehyde, 3-butadiene
    
    def __init__(self, typeindex, args): # initiate
        self.type = typeindex
        if self.type == 1:
            self.body_volume = 56.54
            self.max_pumping_volume_0 = 22
            self.LBLtype = args
        elif self.type == 2:
            self.body_volume = 56.54
            self.max_pumping_volume_0 = 18
        elif self.type == 3:
            self.body_volume = 56.54
            self.max_pumping_volume_0 = 22
            
    def Update(self, pumping_volume_new, pressure_new):
        self.pumping_volume = pumping_volume_new
        self.max_pumping_volume = self.max_pumping_volume_0
        self.pressure = pressure_new
    
    def Modify_pumping_volume(self, p):
        if p > p_atm:
            #self.max_pumping_volume = self.max_pumping_volume_0 * p_atm / ((p-p_atm)*beta + p_atm)
            aa = p-p_atm
            self.max_pumping_volume = self.max_pumping_volume_0 * (math.exp(-aa*beta))
        else:
            self.max_pumping_volume = self.max_pumping_volume_0
            
class Storage:
    type = 0 # 1-soft, 2-rigid, 3-elastic
    max_volume = 0
    
    pressure = p_atm # current pressure
    volume_in_p0 = 0 # current volume of stored air at p0
    p_elastic = 10
    
    k = 1
    
    def __init__(self, typeindex, args, k): # initiate
        self.type = typeindex
        if self.type == 1:
            self.max_volume = args # max volume
            self.k = k
        elif self.type == 2:
            self.max_volume = args # constant volume
            self.volume_in_p0 += self.max_volume
            self.k = k
        elif self.type == 3: # constant pressure
            self.max_volume = args
            self.p_elastic = k
    
    def Evaluate_pressure(self, v_in_p0): # input new v_in, output new pressure
        p = 0
        if self.type == 1:
            if v_in_p0 < self.max_volume:
                p = p_atm
            else:
                p = p_atm / self.max_volume * ((v_in_p0 - self.max_volume)*self.k+self.max_volume)
        elif self.type == 2:
            p = p_atm / self.max_volume * ((v_in_p0 - self.max_volume)*self.k+self.max_volume)
        elif self.type == 3:
            if 0 < v_in_p0 < self.max_volume:
                p = self.p_elastic + p_atm
            elif v_in_p0 >= self.max_volume:
                p = self.p_elastic + p_atm + 100
            else:
                p = p_atm
        return p

    def Evaluate_v_in(self, p, v_in): # input new pressure and old v_in, output new v_in
        new_v_in = 0
        if self.type == 1:
            if p <= p_atm:
                if v_in > self.max_volume:
                    new_v_in = self.max_volume
                else:
                    new_v_in = v_in
            else:
                new_v_in = ((p / p_atm -1)/self.k + 1)* self.max_volume
        elif self.type == 2:
            new_v_in = ((p / p_atm -1)/self.k + 1)* self.max_volume
        elif self.type == 3:
            if p <= p_atm:
                new_v_in = 0
            else:
                new_v_in = v_in
        return new_v_in
    
    def Set_air(self, v_in):
        self.volume_in_p0 = v_in
        self.pressure = self.Evaluate_pressure(v_in)
        
    def Add_air(self, v_in_new):
        self.Set_air(v_in_new + self.volume_in_p0)
        
    def Set_pressure(self, p):
        if self.type == 3:
            if p < self.p_elastic + p_atm:
                self.pressure = p_atm
                self.volume_in_p0 = 0
            else:
                self.pressure = self.p_elastic
        else:
            self.pressure = p
            self.volume_in_p0 = self.Evaluate_v_in(p, self.volume_in_p0)

        
class Valve:
    type = 0 # 1-thermal, 2-wet, 3-bursting
    state_normal = False # normally off
    orientation = 0 # 0-isolate, 1-bridge, 2-connect to air
    
    threshold_to_on = 0
    threshold_to_off = 0
    # threshold_triger = 0
    
    state = False # on-True, off-False
    
    buffer_list = []
    buffer_length = 5
    
    def __init__(self, typeindex, normal_state, orientation, args1, args2, arg_triger): # initiate
        self.type = typeindex
        self.state_normal = normal_state
        self.orientation = orientation
        
        self.threshold_to_on = args1
        self.threshold_to_off = args2
        self.threshold_triger = arg_triger
        
        self.buffer_list = []
        for i in range(self.buffer_length):
            self.buffer_list.append(0)
            
    def Update(self, args=-100):
        threshold = 0
        if self.state == self.state_normal:
            threshold = self.threshold_to_on
        else:
            threshold = self.threshold_to_off
        
        t = 0
        if args > -100:
            t = args
        else:
            if self.type == 3:
                t = self.threshold_triger.pressure
            elif self.type == 2:
                t = self.threshold_triger.wetness
            elif self.type == 1:
                t = self.threshold_triger.temperature
        
        self.buffer_list.append(t)
        if len(self.buffer_list) > self.buffer_length:
            self.buffer_list.pop(0)
        t_mean = 0
        for i in range(self.buffer_length):
            t_mean += self.buffer_list[i]
        t_mean = t_mean / self.buffer_length

        # if self.type == 3:
        #     print(t_mean, threshold)
        if t_mean <= threshold:
            self.state = self.state_normal
        else:
            self.state = not self.state_normal
        #print(self.buffer_list)

    def Set_state(self, state):
        self.state = state
    
    
class Circuit:
    pump = Pump(0,0)
    storage = Storage(0,0,1)
    
    valve1 = Valve(0, False, 0, 0, 0, '')
    valve2 = Valve(0, False, 0, 0, 0, '')
    valve3 = Valve(0, False, 0, 0, 0, '')
    
    env = ''
    
    def __init__(self, env):
        self.env = env
        pass
    
    def Pump_air(self): 
        # pump to storage
        new_pressure = self.env.pumping_pressure
        
        pump_to_storage = False
        compare_pressure = 0
        if self.storage.type == 3:
            compare_pressure = self.storage.p_elastic + p_atm
        else:
            compare_pressure = self.storage.pressure

        if new_pressure - compare_pressure > p_check:
            if self.valve2.orientation == 0:
                pump_to_storage = True
            elif self.valve2.orientation == 1:
                if self.valve2.state == True:
                    pump_to_storage = True
            elif self.valve2.orientation == 2:
                if self.valve2.state == False:
                    pump_to_storage = True
        if pump_to_storage:
            step = 0.05
            v_in_new = 0
            flag = True
            
            while(flag):
                v_in_new = v_in_new + step
                
                p_new = self.storage.Evaluate_pressure(self.storage.volume_in_p0 + v_in_new) + p_check
                pumping_volume_new = self.pump.body_volume - (self.pump.pressure*(self.pump.body_volume-self.pump.pumping_volume)-p_atm*v_in_new)/p_new
            
                p_flag = p_new <= new_pressure
                v_flag = pumping_volume_new <= self.pump.max_pumping_volume
            
                if p_flag and v_flag:
                    flag = True
                else:
                    flag = False
                    v_in_new = v_in_new - step
                    self.storage.Add_air(v_in_new) # update storage
                    p_new = self.storage.pressure + p_check
                    
                    if v_flag == False:
                        pumping_volume_new = self.pump.max_pumping_volume
                    else:
                        pumping_volume_new = self.pump.body_volume - (self.pump.pressure*(self.pump.body_volume-self.pump.pumping_volume)-p_atm*v_in_new)/p_new
                    self.pump.Update(pumping_volume_new, p_new) # update pump
                    #print('%.2f'%v_in_new, '%.2f'%self.storage.volume_in_p0, '%.2f'%self.storage.pressure, '%.2f'%self.pump.pumping_volume, '%.2f'%self.pump.pressure, v_flag, p_flag, sep='\t')
        # air to pump
        air_to_pump = False
        aa = self.storage.pressure-p_atm
        #restore_volume = self.pump.max_pumping_volume * (1-math.exp(-aa*beta))
        restore_volume = 0
        if self.valve2.orientation == 2 and self.valve2.state == True:
            air_to_pump = True
            if self.valve2.threshold_triger == self.pump:
                self.pump.Update(restore_volume, self.valve2.threshold_to_off)
            else:
                self.pump.Update(restore_volume, p_atm)
        elif new_pressure < p_atm - p_check:
            if self.valve1.orientation == 1:
                if self.valve1.state == True:
                    air_to_pump = True
            else:
                air_to_pump = True
            if air_to_pump:
                self.pump.Update(restore_volume, p_atm - p_check)
        
        # pump to pump
        pump_to_pump = False
        if pump_to_storage == False and air_to_pump == False and abs(new_pressure - self.pump.pressure) > 0.01:
            pump_to_pump = True
        if pump_to_pump:
            pumping_volume_new = self.pump.body_volume - self.pump.pressure*(self.pump.body_volume-self.pump.pumping_volume)/new_pressure
            pump_pressure_new = new_pressure
            if pumping_volume_new > self.pump.max_pumping_volume:
                pumping_volume_new = self.pump.max_pumping_volume
                pump_pressure_new = self.pump.pressure*(self.pump.body_volume-self.pump.pumping_volume)/(self.pump.body_volume-pumping_volume_new)
            elif pumping_volume_new < 0:
                pumping_volume_new = 0
                pump_pressure_new = self.pump.pressure*(self.pump.body_volume-self.pump.pumping_volume)/(self.pump.body_volume-pumping_volume_new)
            self.pump.Update(pumping_volume_new, pump_pressure_new)
            # print('%.2f'%0, '%.2f'%self.storage.volume_in_p0, '%.2f'%self.storage.pressure, '%.2f'%self.pump.pumping_volume, '%.2f'%self.pump.pressure, '-', '-', sep='\t')
        
        # storage to air
        storage_to_air = False
        if self.storage.pressure > p_atm+p_check:
            if self.valve3.orientation == 1 or self.valve3.orientation == 2:
                if self.valve3.state == True:
                    storage_to_air = True
                    if self.valve3.threshold_triger == self.storage or self.valve3.threshold_triger == self.pump:
                        self.storage.Set_pressure(self.valve3.threshold_to_off)
                    else:
                        self.storage.Set_pressure(p_atm + p_check)
        
        self.pump.Modify_pumping_volume(self.storage.pressure)

        self.valve1.Update()
        self.valve2.Update()
        self.valve3.Update()
        
class Cycle:
    envs = []
    
    def __init__(self, t1, t2, t3, wetness, windspeed):
        envs = []
        env1 = Environment(t1, wetness, windspeed)
        env2 = Environment(t2, wetness, windspeed)
        env3 = Environment(t3, wetness, windspeed)
        
        envs.append(env1)
        envs.append(env2)
        envs.append(env3)
        
        self.envs = envs
    
    def __getitem__(self, i):
        return self.envs[i]

class CycleRun:
    cycle_frame_count = 20 # frame count in simulation of every cycle
    current_cycle_index = 0
    current_cycle_frame_index = 0
    
    cycle_list = []
    cycle_count = 0
    
    circuit = ''
    env = ''
    pumping_time = 0
    max_pumping_time = 50
    
    # cycle_index, temperature, wetness, wind_speed, pumping_pressure, pump_pressure, pump_pumping_volume, storage_pressure, storage_vin_p0, v1, v2, v3, pumping_time 
    simulation_result = []
    v1_t = False
    v1_is_change = False
    v2_t = False
    v2_is_change = False
    v3_t = False
    v3_is_change = False

    last_storage_pressure = 0
    last_storage_volume_in_p0 = 0
    
    def __init__(self, cycle_list, circuit, env):
        self.cycle_list = cycle_list
        self.cycle_count = len(self.cycle_list)
        self.circuit = circuit
        self.env = env
        
        # self.env.temperature = 23
        # self.env.wetness = 0
        # self.env.windspeed = 0
        self.SimulatePressureList([p_atm, p_atm, p_atm, p_atm, p_atm])
        #print(1, '%.2f'%self.env.temperature, '%.2f'%self.env.wetness, '%.2f'%self.env.windspeed, '%.2f'%(self.env.pumping_pressure - p_atm), '%.2f'%(self.circuit.pump.pressure-p_atm), '%.2f'%self.circuit.pump.pumping_volume, '%.2f'%(self.circuit.storage.pressure-p_atm), '%.2f'%self.circuit.storage.volume_in_p0, \
        #        self.circuit.valve1.state, self.circuit.valve2.state, self.circuit.valve3.state, self.pumping_time, sep='\t')       

        self.last_storage_pressure = self.circuit.storage.pressure
        self.last_storage_volume_in_p0 = self.circuit.storage.volume_in_p0
    
    def to_Pressure(self, new_temperature, new_wetness, new_windspeed):
        type = self.circuit.pump.type
        simulate_pressure_list = []
        if type == 1:
            if new_temperature != self.env.temperature:
                new_pressure = LBL_pressure(new_temperature, self.circuit.pump.LBLtype)
                if new_pressure < p_atm - p_check:
                    new_pressure = p_atm - p_check - 0.2
                simulate_pressure_list = [new_pressure]
        elif type == 2:
            new_pressure = Wet_pressure(new_wetness)
            if new_wetness != self.env.wetness:
                if new_pressure == p_atm:
                    new_pressure = p_atm - p_check - 0.2
                old_pressure = self.env.pumping_pressure
                simulate_pressure_list = linlist(old_pressure, new_pressure, 0.2)
            else:
                simulate_pressure_list = [new_pressure]
        elif type == 3:
            new_pressure = Wind_pressure(new_windspeed)
            if new_windspeed != self.env.windspeed:
                if new_pressure == p_atm:
                    new_pressure = p_atm - p_check - 0.2
                old_pressure = self.env.pumping_pressure
                simulate_pressure_list = linlist(old_pressure, p_atm - p_check - 0.1, 0.1) + linlist(p_atm - p_check - 0.1, new_pressure, 0.1)
            else:
                simulate_pressure_list = [new_pressure]
        return simulate_pressure_list
    
    def Run(self): # simulate one frame
        running = True
        current_cycle = self.cycle_list[self.current_cycle_index]
        
        self.v1_t = self.circuit.valve1.state
        self.v1_is_change = False
        self.v2_t = self.circuit.valve2.state
        self.v2_is_change = False
        self.v3_t = self.circuit.valve3.state
        self.v3_is_change = False

        new_temperature = 0
        new_wetness = 0
        new_windspeed = 0
        
        if self.current_cycle_frame_index < self.cycle_frame_count/2:
            new_temperature = current_cycle[0].temperature + (current_cycle[1].temperature - current_cycle[0].temperature) * \
                ((self.current_cycle_frame_index)/self.cycle_frame_count*2) 
        else:
            new_temperature = current_cycle[1].temperature - (current_cycle[1].temperature - current_cycle[2].temperature) * \
                ((self.current_cycle_frame_index - self.cycle_frame_count/2)/self.cycle_frame_count*2)
        
        new_wetness = current_cycle[0].wetness
        new_windspeed = current_cycle[0].windspeed
        
        # calculate new environment parameter
        simulate_pressure_list = self.to_Pressure(new_temperature, new_wetness, new_windspeed)
        self.env.temperature = new_temperature
        self.env.wetness = new_wetness
        self.env.windspeed = new_windspeed

        # simulate
        self.SimulatePressureList(simulate_pressure_list)
        #print(simulate_pressure_list)
        
        if self.circuit.pump.type == 3 and len(simulate_pressure_list) > 1:
            new_pressure = simulate_pressure_list[-1]
            print(new_pressure-p_atm)
            cycle_pressure_list = linlist(new_pressure, p_atm - p_check - 0.1, 0.1) + linlist(p_atm - p_check - 0.1, new_pressure, 0.1)
            
            last_storage_pressure = 0
            last_storage_volume_in_p0 = 0
            wind_cycle_running = True
            while wind_cycle_running:    
                last_storage_pressure = self.circuit.storage.pressure
                last_storage_volume_in_p0 = self.circuit.storage.volume_in_p0
                self.SimulatePressureList(cycle_pressure_list)
                self.pumping_time += 1
                if self.circuit.storage.type != 3:
                    if abs(last_storage_volume_in_p0 - self.circuit.storage.volume_in_p0) < 0.01 and \
                        abs(last_storage_pressure - self.circuit.storage.pressure) < 0.01:
                        wind_cycle_running = False
                else:
                    if new_pressure < self.circuit.storage.p_elastic + p_atm:
                        wind_cycle_running = False
                    elif abs(self.circuit.storage.volume_in_p0 - self.circuit.storage.max_volume) < 0.1 or self.pumping_time > self.max_pumping_time:
                        wind_cycle_running = False
        # end of a cycle
        self.current_cycle_frame_index += 1
        if self.current_cycle_frame_index == self.cycle_frame_count:
            if self.circuit.pump.type == 1 or (self.circuit.pump.type == 2):
                if  abs(self.last_storage_volume_in_p0 - self.circuit.storage.volume_in_p0) > 0.01 or abs(self.last_storage_pressure - self.circuit.storage.pressure) > 0.01:
                    self.pumping_time += 1
                    self.last_storage_pressure = self.circuit.storage.pressure
                    self.last_storage_volume_in_p0 = self.circuit.storage.volume_in_p0

            self.current_cycle_frame_index = 0
            self.current_cycle_index += 1
            if self.current_cycle_index == self.cycle_count:
                self.current_cycle_index = 0
                running = False
                
        result = []
        result.append(self.current_cycle_frame_index/self.cycle_frame_count + self.current_cycle_index + 1)
        result.append(self.env.temperature)
        result.append(self.env.wetness)
        result.append(self.env.windspeed)
        result.append(self.env.pumping_pressure - p_atm)
        result.append(self.circuit.pump.pressure-p_atm)
        result.append(self.circuit.pump.pumping_volume)
        result.append(self.circuit.storage.pressure-p_atm)
        result.append(self.circuit.storage.volume_in_p0)
        result.append(self.v1_t)
        result.append(self.v2_t)
        result.append(self.v3_t)
        result.append(self.pumping_time)
        self.simulation_result.append(result)
        
        # for i in range(9):
        #     print(round(result[i], 2), end='\t')
        # print(result[12])
        
        return running
    
    def SimulatePressureList(self, p_list):
        for i in range(len(p_list)):
            p = p_list[i]
            self.env.pumping_pressure = p
            p1, p2, p3, p4 = 0,0,0,0
            running = True
            running_time = 0
            while running:
                p1 = self.circuit.pump.pressure
                p2 = self.circuit.pump.pumping_volume
                p3 = self.circuit.storage.pressure
                p4 = self.circuit.storage.volume_in_p0
                self.circuit.Pump_air()
                if self.circuit.valve1.state != self.v1_t and self.v1_is_change == False:
                    self.v1_t = self.circuit.valve1.state
                    self.v1_is_change = True
                if self.circuit.valve2.state != self.v2_t and self.v2_is_change == False:
                    self.v2_t = self.circuit.valve2.state
                    self.v2_is_change = True
                if self.circuit.valve3.state != self.v3_t and self.v3_is_change == False:
                    self.v3_t = self.circuit.valve3.state
                    self.v3_is_change = True
                running_time += 1
                if abs(p1 - self.circuit.pump.pressure) < 0.01 and \
                    abs(p2 - self.circuit.pump.pumping_volume)<0.01 and \
                    abs(p3 - self.circuit.storage.pressure)<0.01 and \
                    abs(p4 - self.circuit.storage.volume_in_p0)<0.01:
                    running = False
            #if p-p_atm >= 5.13:
            #print(' ', 'running:',running_time, '%.2f'%(p-p_atm), '%.2f'%(self.circuit.pump.pressure-p_atm), '%.2f'%self.circuit.pump.pumping_volume, '%.2f'%(self.circuit.storage.pressure-p_atm), '%.2f'%self.circuit.storage.volume_in_p0, self.pumping_time,sep='\t')
            #self.circuit.valve1.state, self.circuit.valve2.state, self.circuit.valve3.state, self.pumping_time, sep='\t')       

env = Environment(23, 0, 0)
circuit1 = Circuit(env)

# configure the system
circuit1.pump = Pump(1, 1)
circuit1.storage = Storage(1, 43.2, 0.52)
# circuit1.valve1 = Valve(1, False, 0, 35, 35, env)
circuit1.valve2 = Valve(1, False, 0, 35, 35, env)
# circuit1.valve2 = Valve(3, False, 1, p_atm+1, p_atm+1, circuit1.pump)
circuit1.valve3 = Valve(1, False, 0, p_atm+6, p_atm+6, env)

# configure the environment cycles
TM=41.6
cycle1 = Cycle(20,TM,20,0,7.1)
cycle2 = Cycle(20,TM,20,1,10)
cycle3 = Cycle(20,TM,20,0,10)
cycle4 = Cycle(20,TM,20,1,10)
cycle5 = Cycle(20,TM,20,0,10)
cycle6 = Cycle(20,TM,20,1,10)
cycle7 = Cycle(20,TM,20,0,7)
cycle8 = Cycle(20,TM,20,1,7)
cycle9 = Cycle(20,TM,20,0,7)
cycle10 = Cycle(20,TM,20,1,7)
cycle11 = Cycle(20,TM,20,0,7)
cycle12 = Cycle(20,TM,20,1,7)

# simulate
#cycleRun = CycleRun([cycle1, cycle2, cycle3, cycle4, cycle5, cycle6, cycle7, cycle8, cycle9, cycle10, cycle11, cycle12], circuit1, env)
cycleRun = CycleRun([cycle1], circuit1, env)

running = True
while running: 
    running = cycleRun.Run()
    #pygame.time.delay(10)
simulation_result = cycleRun.simulation_result # simulation result

for result in simulation_result:
    output = False
    #if result[1] == 20 and result[2] == 1:
    if result[1]  >= TM:
        output = True
    output = True
    if not output:
        continue
    for i in range(9):
        print(round(result[i], 2), end='\t')
    print(result[12])

print('finish!')


manual_list = ''
if circuit1.pump.type == 1:
    manual_list += 'Thermal Pump Material List and Assembly Instruction .pdf\n'
elif circuit1.pump.type == 2:
    manual_list += 'Moisture Pump Material List and Assembly Instruction .pdf\n'
elif circuit1.pump.type == 3:
    manual_list += 'Kinetic Pump Material List and Assembly Instruction .pdf\n'

if circuit1.valve2.type == 1:
    if circuit1.valve2.state_normal == True:
        manual_list += 'NO Thermal Valve Material List and Assembly Instruction .pdf\n'
    elif circuit1.valve2.state_normal == False:
        manual_list += 'NC Thermal Valve Material List and Assembly Instruction .pdf\n'
elif circuit1.valve2.type == 2:
    manual_list += 'Moisture Valve Material List and Assembly Instruction .pdf\n'
elif circuit1.valve2.type == 3:
    manual_list += 'Bursting Valve Material List and Assembly Instruction .pdf\n'

if circuit1.valve3.type == 1:
    if circuit1.valve3.state_normal == True:
        manual_list += 'NO Thermal Valve Material List and Assembly Instruction .pdf\n'
    elif circuit1.valve3.state_normal == False:
        manual_list += 'NC Thermal Valve Material List and Assembly Instruction .pdf\n'
elif circuit1.valve3.type == 2:
    manual_list += 'Moisture Valve Material List and Assembly Instruction .pdf\n'
elif circuit1.valve3.type == 3:
    manual_list += 'Bursting Valve Material List and Assembly Instruction .pdf\n'

# print(manual_list)


# if not update:
#     results = x
# else:
#     env = Environment(23, 0, 0)
#     circuit1 = Circuit(env)
    
#     circuit1.pump = Pump(1, 50)
#     circuit1.storage = Storage(2, 100, 1.0)
    
#     i = 0
#     if valve_input[i][5] == 'pump':
#         circuit1.valve1 = Valve(int(valve_input[i][0]), bool(int(valve_input[i][1])), int(valve_input[i][2]), float(valve_input[i][3]), float(valve_input[i][4]), circuit1.pump)
#     elif valve_input[i][5] == 'storage':
#         circuit1.valve1 = Valve(int(valve_input[i][0]), bool(int(valve_input[i][1])), int(valve_input[i][2]), float(valve_input[i][3]), float(valve_input[i][4]), circuit1.storage)
#     else:
#         circuit1.valve1 = Valve(int(valve_input[i][0]), bool(int(valve_input[i][1])), int(valve_input[i][2]), float(valve_input[i][3]), float(valve_input[i][4]), env)
#     i = 1
#     if valve_input[i][5] == 'pump':
#         circuit1.valve2 = Valve(int(valve_input[i][0]), bool(int(valve_input[i][1])), int(valve_input[i][2]), float(valve_input[i][3]), float(valve_input[i][4]), circuit1.pump)
#     elif valve_input[i][5] == 'storage':
#         circuit1.valve2 = Valve(int(valve_input[i][0]), bool(int(valve_input[i][1])), int(valve_input[i][2]), float(valve_input[i][3]), float(valve_input[i][4]), circuit1.storage)
#     else:
#         circuit1.valve2 = Valve(int(valve_input[i][0]), bool(int(valve_input[i][1])), int(valve_input[i][2]), float(valve_input[i][3]), float(valve_input[i][4]), env)
#     i = 2
#     if valve_input[i][5] == 'pump':
#         circuit1.valve3 = Valve(int(valve_input[i][0]), bool(int(valve_input[i][1])), int(valve_input[i][2]), float(valve_input[i][3]), float(valve_input[i][4]), circuit1.pump)
#     elif valve_input[i][5] == 'storage':
#         circuit1.valve3 = Valve(int(valve_input[i][0]), bool(int(valve_input[i][1])), int(valve_input[i][2]), float(valve_input[i][3]), float(valve_input[i][4]), circuit1.storage)
#     else:
#         circuit1.valve3 = Valve(int(valve_input[i][0]), bool(int(valve_input[i][1])), int(valve_input[i][2]), float(valve_input[i][3]), float(valve_input[i][4]), env)
    
#     cycle_list_input = []
#     cycle_count = cycle_input[0]
#     for i in range(cycle_count):
#         new_cycle = Cycle(cycle_input[i+1][0],cycle_input[i+1][1],cycle_input[i+1][2],cycle_input[i+1][3],cycle_input[i+1][4])
#         cycle_list_input.append(new_cycle)

#     cycleRun = CycleRun(cycle_list_input, circuit1, env)
    
#     running = True
#     while running: 
#         running = cycleRun.Run()
#     x = cycleRun.simulation_result
