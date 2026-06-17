import nibabel as nib
import numpy as np
import os 
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pylab as plt
import vtk
import sys
from trame.app import get_server
from trame.ui.vuetify3 import (SinglePageLayout, VAppLayout)
from trame.widgets import vtk as vtk_widgets
from trame.widgets import vuetify3 as v3
from trame.widgets import html
from vtk.util.numpy_support import numpy_to_vtk

from extractor import Extractor




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
    

def convert_nifti_to_vtk(nifti_file, extractor: Extractor, time_index=0):
    nii = nib.load(nifti_file)
    print("Shape of data", nii.shape)
    dimensionality = len(nii.shape)
    extractor.extract_time_component(nii)
    data = nii.get_fdata()
    if (dimensionality == 4):
        volume = data[:, :, :, time_index]
    else:
        volume = data[:, :, :]
    volume = np.nan_to_num(volume)
    vtk_image = vtk.vtkImageData()

    depth_array = numpy_to_vtk(
        num_array=volume.ravel(order='F'),
        deep=True,
        array_type=vtk.VTK_FLOAT
    )

    vtk_image.SetDimensions(volume.shape)
    vtk_image.GetPointData().SetScalars(depth_array)


    mc = vtk.vtkMarchingCubes()
    mc.SetInputData(vtk_image)
    mc.SetValue(0, 0.1)
    mc.Update()

    polydata = vtk.vtkPolyData()
    polydata.ShallowCopy(mc.GetOutput())
    return polydata

def point_to_roi(actor_pos, target_pos):
    direction = np.array(target_pos) - np.array(actor_pos)
    direction /= np.linalg.norm(direction)
    yaw = np.degrees(np.arctan2(direction[0], direction[2]))
    pitch = np.degrees(np.arctan2(direction[1], np.sqrt(direction[0]**2 + direction[2]**2)))
    return pitch, yaw

def rot_matrix(actor_pos, target_pos):
    forward = np.array(target_pos) - np.array(actor_pos)
    forward /= np.linalg.norm(forward)

    up = np.array([0, 1, 0])
    right = np.cross(up, forward)
    right /= np.linalg.norm(right)

    up = np.cross(forward, right)

    m = vtk.vtkMatrix4x4()
    for i in range(3):
        m.SetElement(i, 0, right[i])
        m.SetElement(i, 1, up[i])
        m.SetElement(i, 2, forward[i])

    return m



if __name__ == "__main__":
    file = sys.argv[1]
    nifti_file = os.path.join(base_path, file)
    extractor = Extractor()
    polydata = convert_nifti_to_vtk(nifti_file, extractor)

    segment_file = sys.argv[2]
    segment_nifti_file = os.path.join(base_path, segment_file)
    segment_polydata = convert_nifti_to_vtk(segment_nifti_file, extractor)

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

    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    mesh_box = vtk.vtkBoxWidget()
    mesh_box.SetInteractor(render_window_interactor)
    mesh_box.SetPlaceFactor(1.25)
    mesh_box.SetProp3D(mesh)
    center_x, center_y, center_z = mesh_box.GetProp3D().GetCenter()
    mesh_box.PlaceWidget()
    mesh_box.On()


    medicaltool = vtk.vtkGLTFImporter()
    medicaltool.SetFileName("./medicaltool.glb")
    medicaltool.SetRenderWindow(render_window)
    medicaltool.Update()

    medicalactors = medicaltool.GetImportedActors()
    medicalactors.GetLastActor().SetScale(50, 50, 50)
    medicalactors.GetLastActor().GetProperty().SetColor(colors.GetColor3d("Blue"))

    actor = medicalactors.GetLastActor()

    #pitch, yaw = point_to_roi(actor.GetPosition(), mesh.GetCenter())
    #actor.SetOrientation(-pitch, yaw, 0.0) 

    renderer.AddActor(mesh)
    renderer.AddActor(segment_actor)
    renderer.ResetCamera()
    renderer.SetBackground(colors.GetColor3d("CadetBlue"))
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(mesh.GetPosition())


    server = get_server("Trame Segmentation")
    state, ctrl = server.state, server.controller 

    state.drawer = False
    state.mesh_color = "#FF0000"
    state.segment_color = "#00FF00"
    state.active_ui = "mesh"
    state.show_color_picker_mesh = False
    state.show_color_picker_segment = False
    state.time_index = 0
    state.slider_time_index = 0

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

        if pathlib.Path(upload_path).suffix == ".nii.gz" or pathlib.Path(upload_path).suffix == ".nii" or pathlib.Path(upload_path).suffix == ".gz":
            polydata = convert_nifti_to_vtk(upload_path, extractor)
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
        state.flush()
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

        if pathlib.Path(upload_path).suffix == ".nii.gz" or pathlib.Path(upload_path).suffix == ".nii" or pathlib.Path(upload_path).suffix == ".gz":
            segment_polydata = convert_nifti_to_vtk(upload_path, extractor, state.time_index)
        else:
            segment_polydata = convert_dicom_to_vtk()

        base_name = os.path.splitext(name)[0]
        segment_writer.SetFileName(f"./vtp/{base_name}.vtp")
        segment_writer.SetInputData(segment_polydata)
        segment_writer.Write()

        segment_reader.SetFileName(f"./vtp/{base_name}.vtp")
        segment_reader.Modified()
        segment_reader.Update()

        print("Extractor max time steps: ", extractor.time_steps)
        segment_mapper.SetInputConnection(segment_reader.GetOutputPort())
        segment_mapper.ScalarVisibilityOff()
        segment_mapper.Update()
        segment_actor.SetMapper(segment_mapper)
        print("Passed: ", name)
        state.time_steps = extractor.time_steps - 1
        state.flush()
        ctrl.view_update()


    
    state.change("mesh_file")(update_mesh_file)
    state.change("segment_file")(update_segment_file)
    state.change("time_index")(update_segment_file)

    @state.change("tool_pos_x")
    def update_tool_pos_x(tool_pos_x, **kwargs):
        _, y, z = actor.GetPosition()
        actor.SetPosition(tool_pos_x, y, z)
        ctrl.view_update()

    @state.change("tool_yaw", "tool_pitch", "tool_roll")
    def update_orientation(**kwargs):
        actor.SetOrientation(state.tool_roll, state.tool_pitch, state.tool_yaw)
        ctrl.view_update()

   
    @state.change("tool_pos_y")
    def update_tool_pos_y(tool_pos_y, **kwargs):
        x, _, z = actor.GetPosition()
        actor.SetPosition(x, tool_pos_y, z)
        ctrl.view_update()

    @state.change("tool_pos_z")
    def update_tool_pos_z(tool_pos_z, **kwargs):
        x, y, _ = actor.GetPosition()
        actor.SetPosition(x, y, tool_pos_z)
        ctrl.view_update()

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

    def tool_card():
        with ui_card(title="Tool", ui_name="tool"):
            with v3.VRow(classes="pt-2", density="compact"):
                v3.VSlider(v_model=("tool_pos_x", 0), min=-1000, max=1000, step=1, label="x")
                v3.VSlider(v_model=("tool_pos_y", 0), min=-1000, max=1000, step=1, label="y")
                v3.VSlider(v_model=("tool_pos_z", 0), min=-1000, max=1000, step=1, label="z")

            v3.VDivider(vertical=True)

            with v3.VRow(classes="pt-2", density="compact"):
                v3.VSlider(v_model=("tool_yaw", 0), min=0, max=360, step=0.1, label="yaw")
                v3.VSlider(v_model=("tool_pitch", 0), min=0, max=360, step=0.1, label="pitch")
                v3.VSlider(v_model=("tool_roll", 0), min=0, max=360, step=0.1, label="roll")

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
            tool_card()
        with v3.VToolbar(style="display: flex; justify-content: center; overflow: visible; min-height: 75px;"):
            v3.VAppBarNavIcon(click="drawer = !drawer")
            v3.VToolbarTitle("Visualizer")
            v3.VSpacer()
            with html.Div(v_if="time_steps > 0", style="position: absolute; left: 50%; top: 50%; transform: translateX(-50%); width: 500px;"):
                with html.Div(v_if="time_steps > 0", style="max-width: 500px;"):
                    v3.VSlider(
                        key=("time_index"),
                        v_model_lazy=("time_index", 0),
                        thumb_label="always",
                        min=0,
                        max=("time_steps", 0),
                        step = 1,
                        density="comfortable",
                        label="Time Index",
                    )
        with v3.VContainer(fluid=True, classes="pa-0 fill-height"):
            view = vtk_widgets.VtkLocalView(render_window, ref="view")
            ctrl.view_update = view.update 
            ctrl.view_reset_camera = view.reset_camera

       
    render_window.Render()
    server.start()

