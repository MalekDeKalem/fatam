import vtk

class Extractor:

    def __init__(self, extractor):
        self.extractor = extractor
        self.time_steps = 0

    def extract_time_component(self, image):
        self.extractor.SetInputData(image)
        time_steps = vtk.GetTimeDimension()
        print(f"Time Steps from image: {time_steps}")
        self.extractor.Update()

