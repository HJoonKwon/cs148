#  simpleRT_plugin.py
#
#  Blender add-on for simpleRT render engine
#  a minimal ray tracing engine for CS148 HW3
#
#  Please read the handout before proceeding!
#  Lots of tips and tricks mentioned in I.3


bl_info = {
    "name": "simple_ray_tracer",
    "description": "Simple Ray-tracer for CS 148",
    "author": "CS148",
    "version": (0, 0, 2020),
    "blender": (2, 90, 0),
    "wiki_url": "http://web.stanford.edu/class/cs148/",
    "category": "Render",
}


import bpy
import numpy as np
from mathutils import Vector, Matrix
from math import sqrt, acos, cos, asin, sin

def normalize(arr):
    norm = np.linalg.norm(arr)
    return arr/norm

def ray_cast(scene, origin, direction):
    """wrapper around Blender's Scene.ray_cast() API

    Parameters
    ----------
    scene ： bpy.types.Scene
        The Blender scene we will cast a ray in
    origin : Vector, float array of 3 items
        Origin of the ray
    direction : Vector, float array of 3 items
        Direction of the ray

    Returns
    -------
    has_hit : bool
        The result of the ray cast, i.e. if the ray hits anything in the scene
    hit_loc : Vector, float array of 3 items
        The hit location of this ray cast
    hit_norm : Vector, float array of 3 items
        The face normal at the ray cast hit location
    index : int
        The face index of the hit face of the hit object
        -1 when original data isn’t available
    hit_obj : bpy_types.Object
        The hit object
    matrix: Matrix, float 4 * 4
        The matrix_world of the hit object
    """
    return scene.ray_cast(scene.view_layers[0].depsgraph, origin, direction)


def RT_trace_ray(scene, ray_orig, ray_dir, lights, depth=3):
    """Cast a single ray into the scene

    Parameters
    ----------
    scene : bpy.types.Scene
        The scene that will be rendered
        It stores information about the camera, lights, objects, and material
    ray_orig : Vector, float array of 3 items
        Origin of the current ray
    ray_dir : Vector, float array of 3 items
        Direction of the current ray
    lights : list of bpy_types.Object
        The list of lights in the scene
    depth: int
        The recursion depth of raytracing
        i.e. the number that light bounces in the scene

    Returns
    -------
    color : Vector, float array of 3 items
        Color of the pixel
    """

    # First, we cast a ray into the scene using Blender's built-in function
    has_hit, hit_loc, hit_norm, _, hit_obj, _ = ray_cast(scene, ray_orig, ray_dir)

    # set initial color (black) for the pixel
    color = np.zeros(3)

    # if the ray hits nothing in the scene
    # return black
    if not has_hit:
        return color

    # ray_cast returns the surface normal of the object geometry
    # this normal may be facing the other way when the ray origin is inside the object
    # here we flip the normal if its wrong, and populate the ray_is_inside variable
    # which will be handy when calculating transmission direction
    ray_inside_object = False
    if hit_norm.dot(ray_dir) > 0:
        hit_norm = -hit_norm
        ray_inside_object = True

    # get the ambient color of the scene
    ambient_color = scene.simpleRT.ambient_color

    # get the material of the object we hit
    mat = hit_obj.simpleRT_material

    # extract the diffuse and specular colors from the material
    # since we only need RGB instead of RGBA,
    # we use .xyz to extract the first three component of the color vector
    diffuse_color = Vector(mat.diffuse_color).xyz
    specular_color = Vector(mat.specular_color).xyz
    # get specular hardness
    specular_hardness = mat.specular_hardness

    # iterate through all the lights in the scene
    hit_by_light = False
    for light in lights:
        # get light color
        light_color = np.array(
            light.data.simpleRT_light.color * light.data.simpleRT_light.energy
        )

        # ----------
        # TODO 1: Shadow Ray
        #
        # Read the lines of code above to see the variables that are already there, e.g. hit_loc.
        #
        # we first cast a shadow ray from the hit location to the light
        # to see if the hit location is in shadow
        #
        # first, calculate the vector from hit location to the light: light_vec
        light_vec = light.location - hit_loc
#        light_dir = light_vec / np.linalg.norm(light_vec)  # do not change
        light_dir = light_vec.normalized()

        # next, calculate the origin of the shadow ray: new_orig
        # raise shadow ray loc by small Epsilon in direction of normal to avoid self-occlusion
        eps = 1e-3
        new_orig = hit_loc + hit_norm * eps
        #
        # cast the shadow ray from hit location to the light
        has_light_hit, _, _, _, _, _ = ray_cast(
            scene, new_orig, light_dir
        )  # do not change
        #
        # re-run this script, and render the scene to check your result with checkpoint 1
        # if you see black pixels, recall how we solve self-occlusion in lecture 5
        # ----------

        # if we hit something we are in the shadow of the light
        # so this light will have no contribution to the color
        if has_light_hit:
            continue

        hit_by_light = True
        # otherwise, we shade with Blinn-Phong model:
        # I = I_diffuse + I_specular
        #       I_diffuse: diffuse component
        #       I_specular: specular component
        #
        # The diffuse component can be calculated as:
        # I_diffuse = k_diffuse * I_light * (light_dir dot normal_dir)
        #       k_diffuse: intensity of diffuse component, in our case diffuse_color
        #       I_light: intensity of the light, light_color attenuated by inverse-square law
        #       light_dir: direction from the surface point to the light, in our case light_dir
        #       normal_dir: normal at the point on the surface, in our case hit_norm
        #
        # The specular component can be calculated as:
        # I_specular = k_specular * I_light
        #              * (normal_dir dot half_vector)^power
        #       k_specular: intensity of specular component, in our case specular_color
        #       I_light: same as above
        #       normal_dir: same as above
        #       half_vector: halfway vector between the view direction and light direction
        #       power: in our case specular_hardness
        # where:
        #       half_vector = the normalized vector of light_dir + view_dir
        #           light_dir: same as above
        #           view_dir: direction from the surface point to the viewer, the negative of ray_dir
        # ----------
        # TODO 2.1: Blinn-Phong Shading -- Diffuse
        #
        # calculate intensity of the light: I_light.

        # calculate diffuse component, add that to the pixel color
        distance = np.linalg.norm(light_vec) ** 2
        I_light = light_color / distance
        I_diffuse = I_light * diffuse_color * light_dir.dot(hit_norm)
        color += I_diffuse  # replace this line

        #
        # re-run this script, and render the scene to check your result with checkpoint 2.1
        # ----------
        # TODO 2.2: Blinn-Phong Shading -- Specular
        #
        # calculate half_vector
        # calculate specular component, add that to the pixel color
        view_dir = -ray_dir
        H = (view_dir + light_dir).normalized()
        I_specular = I_light * specular_color * pow(H.dot(hit_norm), specular_hardness)
        color += I_specular


        # re-run this script, and render the scene to check your result with checkpoint 2.2
        # ----------

    # ----------
    # TODO 3: AMBIENT
    #
    # if none of the lights hit the object, add the ambient component I_ambient to the pixel color
    # else, pass here
    #
    # I_ambient = k_diffuse * k_ambient
    #
    # you might also need to add code elsewhere to make this work
    # e.g. you'll need to find a way to determine whether the object got hit by any of the lights above
    #
    # re-run this script, and render the scene to check your result with checkpoint 3
    # ----------
    if not hit_by_light:
        color += diffuse_color * Vector(ambient_color).xyz

    # ----------
    # TODO 5: FRESNEL
    #
    # if don't use fresnel, get reflectivity k_r directly
    reflectivity = mat.mirror_reflectivity
    # otherwise, calculate k_r using schlick’s approximation
    n1 = 1
    n2 = mat.ior
    if ray_inside_object:
        n1 = mat.ior
        n2 = 1

    if mat.use_fresnel:
        # calculate R_0: R_0 = ((n1 - n2) / (n1 + n2))^2
        # Here n1 is the IOR of air, so n1 = 1
        # n2 is the IOR of the object, you can read it from the material property using: mat.ior
        #
        # calculate reflectivity k_r = R_0 + (1 - R_0) (1 - cos(theta))^5
        # theta is the incident angle. Refer to lecture 6 for definition
        cos_theta = hit_norm.dot(-ray_dir)
        R_0 = ((n1 - n2) / (n1 + n2))**2
        reflectivity = R_0 + (1 - R_0) * (1-cos_theta)**5
#
    #
    # re-run this script, and render the scene to check your result with checkpoint 5
    # you won't see the effects of this until TODO 4 is also done
    # ----------

    # ----------
    # TODO 4: RECURSION
    #
    # if depth > 0, cast a reflected ray from current intersection point
    # with direction D_reflect to get the color contribution of the ray L_reflect
    # multiply L_reflect with reflectivity k_r, and add the result to the pixel color
    #
    # Equation for D_reflect is on lecture 6 slides
    # Reflectivity k_r has been already declared in TODO 5 above
    #
    # just like casting a shadow ray, we need to take care of self-occlusion here
    # remember to update depth
    #
    # re-run this script, and render the scene to check your result with checkpoint 4
    # ----------
    if depth > 0:
        # cast ray from hit pointcos
        D_reflect = (ray_dir - 2 * hit_norm.dot(ray_dir) * hit_norm).normalized()
        color += RT_trace_ray(scene, new_orig, D_reflect, lights, depth-1) * reflectivity

    # ----------
    # TODO 6: TRANSMISSION
    #
    # if depth > 0, cast a transmitted ray from current intersection point
    # with direction D_transmit to get the color contribution of the ray L_transmit
    # multiply that with (1 - k_r) * mat.transmission, and add the result to the pixel color
    #
    # Equation for D_transmit is on lecture 6 slides
    # the ray goes from n1 media to n2 media
    # set n1 and n2 according to ray_inside_object
    # the IOR of the object is mat.ior, and the IOR of air is 1
    # continue only when the term under the square root is positive
    #
    # just like casting a shadow ray, we need to take care of self-occlusion here
    # remember to update depth
    #
    # re-run this script, and render the scene to check your result with checkpoint 6
    # ----------
    if depth > 0:
        squared_term = 1 - (n1/n2)**2 * (1 - hit_norm.dot(ray_dir)**2)
        if squared_term > 0:

            transmit_orig = hit_loc - hit_norm * eps
            D_transmit = n1/n2 * ray_dir - (n1/n2 * hit_norm.dot(ray_dir) + squared_term**0.5) * hit_norm
            D_transmit = D_transmit.normalized()
            color += RT_trace_ray(scene, transmit_orig, D_transmit, lights, depth-1) * (1 - reflectivity) * mat.transmission

    return color


def RT_render_scene(scene, width, height, depth, buf):
    """Main function for rendering the scene

    Parameters
    ----------
    scene : bpy.types.Scene
        The scene that will be rendered
        It stores information about the camera, lights, objects, and material
    width : int
        Width of the rendered image
    height : int
        Height of the rendered image
    depth : int
        The recursion depth of raytracing
        i.e. the number that light bounces in the scene
    buf: numpy.ndarray
        the buffer that will be populated to store the calculated color
        for each pixel
    """

    # get all the lights from the scene
    scene_lights = [o for o in scene.objects if o.type == "LIGHT"]

    # get the location and orientation of the active camera
    cam_location = scene.camera.location
    cam_orientation = scene.camera.rotation_euler

    # get camera focal length
    focal_length = scene.camera.data.lens / scene.camera.data.sensor_width
    aspect_ratio = height / width

    # iterate through all the pixels, cast a ray for each pixel
    for y in range(height):
        # get screen space coordinate for y
        screen_y = ((y - (height / 2)) / height) * aspect_ratio
        for x in range(width):
            # get screen space coordinate for x
            screen_x = (x - (width / 2)) / width
            # calculate the ray direction
            ray_dir = Vector((screen_x, screen_y, -focal_length))
            ray_dir.rotate(cam_orientation)
            ray_dir = ray_dir.normalized()
            # populate the RGB component of the buffer with ray tracing result
            buf[y, x, 0:3] = RT_trace_ray(
                scene, cam_location, ray_dir, scene_lights, depth
            )
            # populate the alpha component of the buffer
            # to make the pixel not transparent
            buf[y, x, 3] = 1
        yield y
    return buf


# modified from https://docs.blender.org/api/current/bpy.types.RenderEngine.html
class SimpleRTRenderEngine(bpy.types.RenderEngine):
    # These three members are used by blender to set up the
    # RenderEngine; define its internal name, visible name and capabilities.
    bl_idname = "simple_RT"
    bl_label = "SimpleRT"
    bl_use_preview = False

    # Init is called whenever a new render engine instance is created. Multiple
    # instances may exist at the same time, for example for a viewport and final
    # render.
    def __init__(self):
        self.draw_data = None

    # When the render engine instance is destroy, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        pass

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        self.size_x = int(scene.render.resolution_x * scale)
        self.size_y = int(scene.render.resolution_y * scale)

        if self.is_preview:
            pass
        else:
            self.render_scene(scene)

    def render_scene(self, scene):
        # create a buffer to store the calculated intensities
        # buffer is has four channels: Red, Green, Blue, and Alpha
        # default is set to (0, 0, 0, 0), which means black and fully transparent
        height, width = self.size_y, self.size_x
        buf = np.zeros((height, width, 4))

        result = self.begin_result(0, 0, self.size_x, self.size_y)
        layer = result.layers[0].passes["Combined"]

        # get the maximum ray tracing recursion depth
        depth = scene.simpleRT.recursion_depth

        # time the render
        import time
        from datetime import timedelta

        start_time = time.time()

        # start ray tracing
        update_cycle = int(10000 / width)
        for y in RT_render_scene(scene, width, height, depth, buf):

            # print render time info
            elapsed = int(time.time() - start_time)
            remain = int(elapsed / (y + 1) * (height - y - 1))
            print(
                f"rendering... Time {timedelta(seconds=elapsed)}"
                + f"| Remaining {timedelta(seconds=remain)}",
                end="\r",
            )

            # update Blender progress bar
            self.update_progress(y / height)

            # update render result
            # update too frequently will significantly slow down the rendering
            if y % update_cycle == 0 or y == height - 1:
                self.update_result(result)
                layer.rect = buf.reshape(-1, 4).tolist()

            # catch "ESC" event to cancel the render
            if self.test_break():
                break

        # tell Blender all pixels have been set and are final
        self.end_result(result)


def register():
    bpy.utils.register_class(SimpleRTRenderEngine)


def unregister():
    bpy.utils.unregister_class(SimpleRTRenderEngine)


if __name__ == "__main__":
    register()
