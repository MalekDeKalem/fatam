import vtk

class Extractor:

    def __init__(self):
        self.extractor = vtk.vtkImageExtractComponents()
        self.time_steps = 0

    def extract_time_component(self, image):
        self.extractor.SetInputData(image)
        time_steps = vtk.GetTimeDimension(image)
        print(f"Time Steps from image: {time_steps}")
        self.extractor.Update()

