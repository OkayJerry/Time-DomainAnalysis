import numpy as np
from datetime import datetime
from scipy import signal

def random_flat(sec=5, s0=10, s1=1, s2=10):
    t0 = datetime.now()
    sd0 = t0.second
    r0 = np.random.RandomState(int(np.floor(sd0/sec)) + t0.minute + int(sec))
    v0 = 2*r0.rand()-1
    r1 = np.random.RandomState(t0.microsecond)
    v1 = r1.randn()
    return v0*s0 + v1*s1 + s2

def trapezoid(sec=20, s0=10, s1=0.4, s2=1):
    t0 = datetime.now()
    sd0 = t0.timestamp()
    v0 = signal.sawtooth(np.pi*sd0/sec, 0.5)
    v0 = np.max([v0, -0.5])
    v0 = np.min([v0,  0.5])
    
    r1 = np.random.RandomState(t0.microsecond)
    v1 = r1.randn()
    return v0*s0 + v1*s1 + s2

def sinusoidal(sec=20, s0=10, s1=2, s2=1):
    t0 = datetime.now()
    sd0 = t0.timestamp()
    v0 = np.sin(np.pi*sd0/sec)
    
    r1 = np.random.RandomState(t0.microsecond)
    v1 = r1.randn()
    return v0*s0 + v1*s1 + s2

class PV(object):
    """Dummy script to emulate EPICS PV class
    
    Available PV names:
    - 'dummy_pv_0': random_flat function
    - 'dummy_pv_1': random_walk function
    - 'dummy_pv_2': trapezoid function
    - 'dummy_pv_3': sinusoidal function
    
    How to use:
    ---
    from epics import PV
    import time
    
    pv1 = PV('dummy_pv_1') # Generate PV object access to 'dummy_pv_1'
    v = pv1.get() # get value of 'dummy_pv_1'
    
    # e.g. print pv1 value every 1 sec = 1 Hz
    for _ in range(60):
        print(pv1.get())
        time.sleep(1)
    
    """
    def __init__(self, name):
        """Choose from 'dummy_pv_0', 'dummy_pv_1', 'dummy_pv_2', or 'dummy_pv_3'"""
        if name == 'dummy_pv_0':
            self.func = lambda: random_flat(sec=5, s0=10, s1=1, s2=10)
        elif name == 'dummy_pv_1':
            self.func = lambda: self.random_walk(s0=10)
        elif name == 'dummy_pv_2':
            self.func = lambda: trapezoid(sec=25, s0=10, s1=0.4, s2=1)
        elif name == 'dummy_pv_3':
            self.func = lambda: sinusoidal(sec=20, s0=10, s1=2, s2=1)
        else:
            raise NameError("PV name was not found.")
        
        self.t = 1.0
            
    def random_walk(self, s0=10):
        v0 = np.random.randn()
        self.t = self.t+v0*s0
        return self.t
            
    def get(self):
        return self.func()