import vtk

class Extractor:

    def __init__(self):
        self.time_steps = 0

    def extract_time_component(self, volume):
        if len(volume.shape) == 4:
            self.time_steps = volume.shape[3]
        else:
            self.time_steps = 0
