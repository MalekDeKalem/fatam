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
from trame.ui.vuetify3 import (SinglePageLayout, VAppLayout)
from trame.widgets import vtk as vtk_widgets
from trame.widgets import vuetify3 as v3
from trame.widgets import html



base_path = "./CIA/BraTS-Africa/95_Glioma/BraTS-SSA-00002-000/"
file = "Healthy-Total-Body-CTs-016.nii"

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

    with VAppLayout(server, full_height=True) as layout:


        with v3.VToolbar():
            v3.VToolbarTitle("Visualizer")
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
            v3.VSpacer()
            v3.VCheckbox(density="compact", classes="mx-1", v_model=("cube_axes_visibility", True))

        with v3.VContainer(fluid=True, classes="pa-0 fill-height"):
            view = vtk_widgets.VtkLocalView(render_window, ref="view")
            ctrl.view_update = view.update 
            ctrl.view_reset_camera = view.reset_camera

        # State binding 
       
    render_window.Render()
    server.start()

