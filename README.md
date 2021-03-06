# bl_mats_copy_ue
bl_mats_copy_ue is an add-on for copying Blender material nodes to UnrealEngine.

![Blender](./readme_res/b1.png)
![Unreal](./readme_res/u1.png)


## Install

Download the add_on and extract to your blender addons folder, or you can just install in Blender with zip file.

## Usage
Go to Blender -> Edit -> Preferences -> Add-ons: Search "copy", find the "Material Nodes Copy to UE" add-on, click the "Install Pyperclip" button.

Select shader nodes what you want to paste to Unreal material, find "CP" in Shader Node Editor Panel. 

Switch to CP2U Panel and click "Copy" button.

Go to UE material and press paste shotcut (Ctrl + V).

## Supported Nodes

Because of the limitation of **clipboard** and the **Render differences** between Blender and UE, this addon can't copy some node like **Shader**, **Image**, some special **attributes** in blender and so on...

And be aware that all texcoord nodes are float2 in UE but float3 in Blender. You need to append a value for texcoord.

### Symbol Meannig

âYes : Totally Supported.

â ï¸Part : Only some functions are supported or defective.

ð·Todo : Waiting for development.

âNo : Not supported at all.

### Input
| Blender Node | Is Supported |
| ---- | ---- |
| Ambient Occlusion | â |
| Attribute | â ï¸ |
| Bevel | â |
| Camera Data | â ï¸ |
| Fresnel | â |
| Geometry | â ï¸ |
| Hair Info | â |
| Layer Weight | â ï¸ |
| Light Path | â |
| Object Info | â ï¸ |
| Particle Info | â |
| Point Info | â |
| RGB | â |
| Texcoordinate | â ï¸ |
| UVMap | â ï¸ |
| Value | â |
| Vertex Color | â ï¸ |
| Volume Info | â |
| Wireframe | â |

### Output

âNo

### Shader

âNo

### Texture

ð·Todo

### Color

| Blender Node | Is Supported |
| ---- | ---- |
| Bright Contrast | ð· |
| Gamma | â |
| Hue/Saturation | ð· |
| Invert | ð· |
| Light Falloff | â |
| MixRGB | â |
| RGB Curves | â |

### Vector

| Blender Node | Is Supported |
| ---- | ---- |
| Bump | ð· |
| Displacement | â |
| Mapping | â |
| Normal | â |
| Normal Map | â |
| Vector Curve | â |
| Vector Displacement | â |
| Vector Rotate | ð· |
| Vector Transform | â ï¸ |

### Converter

| Blender Node | Is Supported |
| ---- | ---- |
| Black Body | â |
| Clamp | â |
| ColorRamp | â |
| Combine HSV | ð· |
| Combine RGB | â |
| Combine XYZ | â |
| Float Curves | â |
| Map Range | ð· |
| Math | â ï¸ |
| RGB to BW | â |
| Separate HSV | ð· |
| Separate RGB | â |
| Separate XYZ | â |
| Shader to RGB | â |
| Vector Math | â ï¸ |
| Wave Length | ð· |

### Script

âNo

### Group

âNo

You can create a material function.

### Layout

| Blender Node | Is Supported |
| ---- | ---- |
| Frame | ð· |
| Reroute | â |

