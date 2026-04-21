import nibabel as nib
import os 
import matplotlib
matplotlib.use("Agg")
import matplotlib.pylab as plt
import vtk
import sys
import argparse
from dataclasses import dataclass
from trame.app import get_server
from trame.ui.vuetify3 import (SinglePageLayout)
from trame.widgets import vtk as vtk_widgets
from trame.widgets import vuetify3 as v3



base_path = "./CIA/BraTS-Africa/95_Glioma/BraTS-SSA-00002-000/"
file = "Healthy-Total-Body-CTs-016.nii"


def make_slider_properties():
    tube_width = 0.01
    slider_length = 0.05
    title_height = 0.05
    label_height = 0.045

    # Setup a slider widget for each varying parameter.
    sp = vtk.Slider2DProperties()
    sp.Text.title_bold = True
    sp.Text.title_italic = False
    sp.Text.title_shadow = True
    sp.Text.label_bold = True
    sp.Text.label_italic = False
    sp.Text.label_shadow = True
    sp.Range.minimum_value = -1.0
    sp.Range.maximum_value = 1.0
    sp.Position.point1 = (0.1, 0.1)
    sp.Position.point2 = (0.3, 0.1)
    sp.Dimensions.slider_length = slider_length
    sp.Dimensions.slider_width = tube_width * 2.5
    sp.Dimensions.tube_width = tube_width
    sp.Dimensions.end_cap_length = tube_width * 1.25
    sp.Dimensions.end_cap_width = tube_width * 3.0
    sp.Dimensions.title_height = title_height
    sp.Dimensions.label_height = label_height
    # Set color properties:
    # Change the color of the knob that slides.
    sp.Colors.slider_color = 'Green'
    # Change the color of the text indicating what the slider controls.
    sp.Colors.title_color = 'LemonChiffon'
    # Change the color of the text displaying the value.
    sp.Colors.label_color = 'PapayaWhip'
    # Change the color of the knob when the mouse is held on it.
    sp.Colors.selected_color = 'DeepPink'
    # Change the color of the bar.
    sp.Colors.bar_color = 'Beige'
    # Change the color of the ends of the bar.
    sp.Colors.bar_ends_color = 'PeachPuff'

    return sp


def make_2d_slider_widget(properties, interactor):
    """
    Make a 2D slider widget.

    :param properties: The 2D slider properties.
    :param interactor: The vtkInteractor.
    :return: The slider widget.
    """
    colors = vtk.vtkNamedColors()

    slider_rep = vtk.vtkSliderRepresentation2D(minimum_value=properties.Range.minimum_value,
                                           maximum_value=properties.Range.maximum_value,
                                           value=properties.Range.value,
                                           title_text=properties.Text.title,
                                           tube_width=properties.Dimensions.tube_width,
                                           slider_length=properties.Dimensions.slider_length,
                                           slider_width=properties.Dimensions.slider_width,
                                           end_cap_length=properties.Dimensions.end_cap_length,
                                           end_cap_width=properties.Dimensions.end_cap_width,
                                           title_height=properties.Dimensions.title_height,
                                           label_height=properties.Dimensions.label_height,
                                           )

    # Set the color properties.
    slider_rep.title_property.color = colors.GetColor3d(properties.Colors.title_color)
    slider_rep.label_property.color = colors.GetColor3d(properties.Colors.label_color)
    slider_rep.tube_property.color = colors.GetColor3d(properties.Colors.bar_color)
    slider_rep.cap_property.color = colors.GetColor3d(properties.Colors.bar_ends_color)
    slider_rep.slider_property.color = colors.GetColor3d(properties.Colors.slider_color)
    slider_rep.selected_property.color = colors.GetColor3d(properties.Colors.selected_color)

    # Set the position.
    slider_rep.point1_coordinate.coordinate_system = properties.Position.coordinate_system
    slider_rep.point1_coordinate.value = properties.Position.point1
    slider_rep.point2_coordinate.coordinate_system = properties.Position.coordinate_system
    slider_rep.point2_coordinate.value = properties.Position.point2

    title_font_family = properties.Text.title_font_family
    match title_font_family:
        case 'Courier':
            slider_rep.title_property.SetFontFamilyToCourier()
        case 'Times':
            slider_rep.title_property.SetFontFamilyToTimes()
        case _:
            slider_rep.title_property.SetFontFamilyToArial()
    slider_rep.title_property.bold = properties.Text.title_bold
    slider_rep.title_property.italic = properties.Text.title_italic
    slider_rep.title_property.shadow = properties.Text.title_shadow
    label_font_family = properties.Text.label_font_family
    match label_font_family:
        case 'Courier':
            slider_rep.label_property.SetFontFamilyToCourier()
        case 'Times':
            slider_rep.label_property.SetFontFamilyToTimes()
        case _:
            slider_rep.label_property.SetFontFamilyToArial()
    slider_rep.label_property.bold = properties.Text.label_bold
    slider_rep.label_property.italic = properties.Text.label_italic
    slider_rep.label_property.shadow = properties.Text.label_shadow

    widget = vtk.vtkSliderWidget(representation=slider_rep, interactor=interactor, enabled=True)
    widget.SetAnimationModeToAnimate()

    return widget




@dataclass(frozen=True)
class Coordinate:
    @dataclass(frozen=True)
    class CoordinateSystem:
        VTK_DISPLAY: int = 0
        VTK_NORMALIZED_DISPLAY: int = 1
        VTK_VIEWPORT: int = 2
        VTK_NORMALIZED_VIEWPORT: int = 3
        VTK_VIEW: int = 4
        VTK_POSE: int = 5
        VTK_WORLD: int = 6
        VTK_USERDEFINED: int = 7


@dataclass
class Slider2DProperties:
    @dataclass
    class Colors:
        title_color: str = 'White'
        label_color: str = 'White'
        slider_color: str = 'White'
        selected_color: str = 'HotPink'
        bar_color: str = 'White'
        bar_ends_color: str = 'White'

    @dataclass
    class Dimensions:
        tube_width: float = 0.008
        slider_length: float = 0.01
        slider_width: float = 0.02
        end_cap_length: float = 0.005
        end_cap_width: float = 0.05
        title_height: float = 0.03
        label_height: float = 0.025

    @dataclass
    class Position:
        coordinate_system: int = Coordinate.CoordinateSystem.VTK_NORMALIZED_VIEWPORT
        point1: tuple = (0.1, 0.1)
        point2: tuple = (0.9, 0.1)

    @dataclass
    class Range:
        minimum_value: float = 0.0
        maximum_value: float = 1.0
        value: float = 0.0

    @dataclass
    class Text:
        # Font families are: Ariel, Courier and Times
        title: str = ''
        title_font_family = 'Arial'
        title_bold: bool = True
        title_italic: bool = False
        title_shadow: bool = True
        label_font_family = 'Arial'
        label_bold: bool = True
        label_italic: bool = False
        label_shadow: bool = True

class SliderCallBackOpacity:

    def __init__(self, actor):
        self.actor = actor

    def __call__(self, caller, ev):
        slider_rep = caller.GetRepresentation()
        value = slider_rep.GetValue()
        self.actor.GetProperty().SetOpacity(value)



class IPWCallback:
    def __init__(self, plane):
        self.plane = plane

    def __call__(self, caller, ev):
        rep = caller.GetRepresentation()
        rep.GetPlane(self.plane)

def create_images(path, output_name):
    img = nib.load(path).get_fdata()
    print(img.shape)

    plt.style.use('default')
    fig, axes = plt.subplots(20, 20, figsize=(50, 50))
    for i, ax in enumerate(axes.reshape(-1)):
        ax.imshow(img[:,:,1+i])

    plt.tight_layout()
    plt.savefig(output_name + ".png" , dpi=200)
    plt.close()

def extract_time_component(image, t):
    extract = vtk.vtkImageExtractComponents()
    extract.SetInputData(image)
    extract.SetComponents(t)
    extract.Update()
    return extract.GetOutput()

def convert_nifti_to_vtk(nifti_file):
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(nifti_file)
    reader.Update()
    image = reader.GetOutput()

    print(reader)

    polydata = vtk.vtkPolyData()

    mc = vtk.vtkMarchingCubes()
    mc.SetInputData(image)
    mc.SetValue(0, 0.5)
    mc.Update()

    polydata.ShallowCopy(mc.GetOutput())
    return polydata



if __name__ == "__main__":
    # main volume
    file = sys.argv[1]
    nifti_file = os.path.join(base_path, file)
    polydata = convert_nifti_to_vtk(nifti_file)
    
    # segment volume
    segment_file = sys.argv[2]
    segment_nifti_file = os.path.join(base_path, segment_file)
    segment_polydata = convert_nifti_to_vtk(segment_nifti_file)

    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName("data.vtp")
    writer.SetInputData(polydata)
    writer.Write() 

    segment_writer = vtk.vtkPolyDataWriter()
    segment_writer.SetFileName("segment.vtp")
    segment_writer.SetInputData(segment_polydata)
    segment_writer.Write()

    colors = vtk.vtkNamedColors()
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName("data.vtp")

    segment_reader = vtk.vtkPolyDataReader()
    segment_reader.SetFileName("segment.vtp")

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    mapper.ScalarVisibilityOff()

    segment_mapper = vtk.vtkPolyDataMapper()
    segment_mapper.SetInputConnection(segment_reader.GetOutputPort())
    segment_mapper.ScalarVisibilityOff()

    segment_actor = vtk.vtkActor()
    segment_actor.SetMapper(segment_mapper)
    segment_actor.GetProperty().SetColor(colors.GetColor3d("Green"))


    mesh = vtk.vtkActor()
    mesh.SetMapper(mapper)
    mesh.GetProperty().SetColor(colors.GetColor3d("Red"))
    mesh.GetProperty().SetOpacity(1.0)


    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetWindowName("Visualize")
    render_window.SetSize(800, 800)


    renderer.AddActor(mesh)
    renderer.AddActor(segment_actor)
    renderer.ResetCamera()
    renderer.SetBackground(colors.GetColor3d("CadetBlue"))

    server = get_server("Trame Segmentation")
    state, ctrl = server.state, server.controller 
    

    @state.change("opacity")
    def update_opacity(opacity, **kwargs):
        mesh.GetProperty().SetOpacity(opacity)
        ctrl.view_update()

    renderer.ResetCamera()

    with SinglePageLayout(server, full_height=True) as layout:
        layout.title.set_text("Trame Visualize")
        with layout.toolbar:
            v3.VSpacer()
            v3.VSlider(
                v_model=("opacity", 1.0),
                min=0.0,
                max=1.0,
                step = 0.01,
                density="compact",
                label="Opacity",
                classes="position-absolute",
                style="right: 1rem; top: 1rem; width: 400px; z-index: 1",
            )

        with layout.content:
            with v3.VContainer(fluid=True, classes="pa-0 fill-height"):
                view = vtk_widgets.VtkLocalView(render_window, ref="view")
                view.set_orientation_axes = True
                ctrl.view_update = view.update 
                ctrl.view_reset_camera = view.reset_camera

        # State binding 
       
    render_window.Render()
    server.start()


# 
#     segment_mapper = vtk.vtkPolyDataMapper()
#     segment_mapper.SetInputConnection(segment_reader.GetOutputPort())
#     segment_mapper.ScalarVisibilityOff()
# 
# 
#     segment_actor = vtk.vtkActor()
#     segment_actor.SetMapper(segment_mapper)
#     segment_actor.GetProperty().SetColor(colors.GetColor3d("Green"))
# 
 
#     slider_rep = vtk.vtkSliderRepresentation2D()
#     slider_rep.SetMinimumValue(0.0)
#     slider_rep.SetMaximumValue(1.0)
#     slider_rep.SetValue(1.0)
#     slider_rep.SetTitleText("Opacity")
# 
#     slider_rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
#     slider_rep.GetPoint1Coordinate().SetValue(0.2, 0.1)
# 
#     slider_rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
#     slider_rep.GetPoint2Coordinate().SetValue(0.8, 0.1)
# 
#     slider_widget = vtk.vtkSliderWidget()
#     slider_widget.SetInteractor(render_window_interactor)
#     slider_widget.SetRepresentation(slider_rep)
#     slider_widget.SetAnimationModeToAnimate()
#     callback = SliderCallBackOpacity(actor)
#     slider_widget.AddObserver("InteractionEvent", callback)
#     slider_widget.EnabledOn()
# 
# 
#     render_window.Render()
#     render_window_interactor.Initialize()
#     render_window_interactor.Start()
# 
