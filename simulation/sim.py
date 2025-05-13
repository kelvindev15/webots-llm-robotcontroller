from controller import Supervisor

class WebotsSimulation():
    def __init__(self, supervisor: Supervisor):
        self.supervisor = supervisor
        self.time_step = int(self.supervisor.getBasicTimeStep())
        
    def play(self):
        pass

    def stop(self):
        pass

    def run(self):
        """Main loop for the simulation"""
        while self.supervisor.step(self.time_step) != -1:
            # Perform simulation step
            pass

