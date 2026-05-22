import nibabel as nib
import base64 as b64 
import tempfile
import os 
import pathlib
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

def convert_dicom_to_vtk():
    volume = vtk.vtkImageData()
    polydata = vtk.vtkPolyData()
    reader = vtk.vtkDICOMImageReader()
    reader.SetDirectoryName("./dicomseries/")
    reader.Update()

    volume.DeepCopy(reader.GetOutput())
    
    surface = vtk.vtkFlyingEdges3D()
    surface.SetInputData(volume)
    surface.SetValue(0, 1)
    surface.SetComputeNormals(1)
    surface.Update()
    polydata.ShallowCopy(surface.GetOutput())
    return polydata
    
   

def convert_nifti_to_vtk(nifti_file):
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(nifti_file)
    reader.Update()
    image = reader.GetOutput()
 
    print(image)

    polydata = vtk.vtkPolyData()

    mc = vtk.vtkMarchingCubes()
    mc.SetInputData(image)
    mc.SetValue(0, 1)
    mc.Update()

    polydata.ShallowCopy(mc.GetOutput())
    return polydata

def generate_actor(filename):
    polydata = convert_nifti_to_vtk(filename)
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName("")




if __name__ == "__main__":
    file = sys.argv[1]
    nifti_file = os.path.join(base_path, file)
    polydata = convert_nifti_to_vtk(nifti_file)

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

    state.drawer = False
    state.mesh_color = "#FF0000"
    state.segment_color = "#00FF00"
    state.active_ui = "mesh"
    state.show_color_picker_mesh = False
    state.show_color_picker_segment = False

    def update_mesh_file(**kwargs):

        if not state.mesh_file:
            print("No file selected")
            return 

        name = state.mesh_file.get("name")
        content = state.mesh_file.get("content")

        upload_path = os.path.join("./uploads", name)
        print(upload_path)
        with open (upload_path, "wb") as f:
            f.write(content)

        if pathlib.Path(upload_path).suffix == ".nii.gz" or pathlib.Path(upload_path).suffix == ".nii":
            polydata = convert_nifti_to_vtk(upload_path)
        else:
            polydata = convert_dicom_to_vtk()

        base_name = os.path.splitext(name)[0]

        writer.SetFileName(f"./vtp/{base_name}.vtp")
        writer.SetInputData(polydata)
        writer.Write() 

        reader.SetFileName(f"./vtp/{base_name}.vtp")
        reader.Modified()
        reader.Update()
   
        mapper.SetInputConnection(reader.GetOutputPort())
        mapper.ScalarVisibilityOff()
        mapper.Update()
        mesh.SetMapper(mapper)
        print("Passed: ", name)
        ctrl.view_update()

    def update_segment_file(**kwargs):

        if not state.segment_file:
            print("No segment selected")
            return
        
        name = state.segment_file.get("name")
        content = state.segment_file.get("content")
        upload_path = os.path.join("./uploads", name)
        print(upload_path)
        with open (upload_path, "wb") as f:
            f.write(content)

        if pathlib.Path(upload_path).suffix == ".nii.gz" or pathlib.Path(upload_path).suffix == ".nii":
            segment_polydata = convert_nifti_to_vtk(upload_path)
        else:
            segment_polydata = convert_dicom_to_vtk()

        base_name = os.path.splitext(name)[0]
        segment_writer.SetFileName(f"./vtp/{base_name}.vtp")
        segment_writer.SetInputData(segment_polydata)
        segment_writer.Write()

        segment_reader.SetFileName(f"./vtp/{base_name}.vtp")
        segment_reader.Modified()
        segment_reader.Update()

        segment_mapper.SetInputConnection(segment_reader.GetOutputPort())
        segment_mapper.ScalarVisibilityOff()
        segment_mapper.Update()
        segment_actor.SetMapper(segment_mapper)
        print("Passed: ", name)
        ctrl.view_update()

    
    state.change("mesh_file")(update_mesh_file)
    state.change("segment_file")(update_segment_file)


    @state.change("opacity")
    def update_opacity(opacity, **kwargs):
        mesh.GetProperty().SetOpacity(opacity)
        ctrl.view_update()

    @state.change("segment_opacity")
    def update_segment_opacity(segment_opacity, **kwargs):
        segment_actor.GetProperty().SetOpacity(segment_opacity)
        ctrl.view_update()

    @state.change("mesh_color")
    def update_color_mesh(mesh_color, **kwargs):
        hex = mesh_color.lstrip("#")
        r = int(hex[0:2], 16) / 255.0
        g = int(hex[2:4], 16) / 255.0
        b = int(hex[4:6], 16) / 255.0
        print(r, g, b)
        mesh.GetProperty().SetColor(r, g, b)
        ctrl.view_update()

    @state.change("segment_color")
    def update_color_segment(segment_color, **kwargs):
        hex = segment_color.lstrip("#")
        r = int(hex[0:2], 16) / 255.0
        g = int(hex[2:4], 16) / 255.0
        b = int(hex[4:6], 16) / 255.0
        print(r, g, b)
        segment_actor.GetProperty().SetColor(r, g, b)
        ctrl.view_update()

    def ui_card(title, ui_name):
        with v3.VCard():
            v3.VCardTitle(
                title, 
                classes="grey lighten-1 py-1 grey--text text--darken-3",
                style="user-select: none; cursor: pointer",
                hide_details=True,
                density="compact",
            )
            content = v3.VCardText(classes="py-2")
        return content

    def mesh_card():
        with ui_card(title="Mesh", ui_name="mesh"):
            with v3.VRow(classes="pt-2", density="compact"):
                with v3.VMenu(
                    v_model=("show_color_picker_mesh", False),
                    close_on_content_click = False,
                    location = "bottom"
                ):
                    with v3.Template(v_slot_activator="{ props }"):
                        v3.VBtn("Pick Color", v_bind="props", density="compact", style="height: 50px;")

                    v3.VColorPicker(
                        v_model=("mesh_color", "#FF0000"),
                        mode="hexa",
                        flat=True,
                    )

                v3.VSpacer()

                v3.VFileInput(
                    label="Select NIFTI",
                    v_model=("mesh_file", None),
                    show_size=True,
                    truncate_length=30,
                    accept=".nii,.nii.gz",
                    dense=True,
                    chips=True,
                )

            v3.VDivider(vertical=True, classes="mx-2")
            v3.VSlider(
                v_model=("opacity", 1.0),
                min=0.0,
                max=1.0,
                step = 0.01,
                density="compact",
                label="Opacity",
            )

    def segment_card():
        with ui_card(title="Segment", ui_name="segment"):
            with v3.VRow(classes="pt-2", density="compact"):
                with v3.VMenu(
                    v_model=("show_color_picker_segment", False),
                    close_on_content_click = False,
                    location = "bottom"
                ):
                    with v3.Template(v_slot_activator="{ props }"):
                        v3.VBtn("Pick Color", v_bind="props", density="compact", style="height: 50px;")

                    v3.VColorPicker(
                        v_model=("segment_color", "#00FF00"),
                        mode="hexa",
                        flat=True,
                    )

                v3.VSpacer()

                v3.VFileInput(
                    label="Select NIFTI",
                    v_model=("segment_file", None),
                    show_size=True,
                    truncate_length=30,
                    accept=".nii,.nii.gz",
                    dense=True,
                    chips=True,
                )


            v3.VDivider(vertical=True, classes="mx-2")
            v3.VSlider(
                v_model=("segment_opacity", 1.0),
                min=0.0,
                max=1.0,
                step = 0.01,
                density="compact",
                label="Opacity",
            )

    renderer.ResetCamera()

    with VAppLayout(server, full_height=True) as layout:

        with v3.VNavigationDrawer(v_model=("drawer", False), temporary=True, app=True, width=500):
            mesh_card()
            segment_card()
        with v3.VToolbar():
            v3.VAppBarNavIcon(click="drawer = !drawer")
            v3.VToolbarTitle("Visualizer")
            v3.VSpacer()
            v3.VCheckbox(density="compact", classes="mx-1", v_model=("cube_axes_visibility", True))

        with v3.VContainer(fluid=True, classes="pa-0 fill-height"):
            view = vtk_widgets.VtkLocalView(render_window, ref="view")
            ctrl.view_update = view.update 
            ctrl.view_reset_camera = view.reset_camera

        # State binding 
       
    render_window.Render()
    server.start()

