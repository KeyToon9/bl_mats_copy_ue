from random import random
from typing import List
import uuid

from .node_map import NodeClassMap
from .node_map import NodeNameMap

gl_nodes = []

GlobalName = "MaterialGraphNode_{}"
ClassOption = "Class={}"
NameOption = 'Name="{}"'
HeadTemplate = 'Begin Object {} {}\n'
EndTemplate = 'End Object\n'
MatExpTemplate = "\tMaterialExpression={}\'\"{}\"\'\n"
NodePosTemplate = "\tNodePosX={}\n\tNodePosY={}\n"

MatFuncTemplate = "\t\tMaterialFunction=MaterialFunction\'\"{}\"\'\n"
FuncInputTemplate = "\t\tFunctionInputs({})=({})\n"
CustomInputTemplate = "\t\tInputs({})=(InputName=\"{}\",{})\n"
FuncExpInputTemplate = "{}=(Expression={}\'\"{}.{}\"\')"
InputTemplate = "\t\t{}=(Expression={}\'\"{}.{}\"\')\n"
MatContentExpTemplate = "Expression={Type}\'\"{Graph}.{Name}\"\'"
LinkTemplate = "{Graph} {UUID},"
LinkedToTemplate = "LinkedTo=({}),"
PinTemplate = "\tCustomProperties Pin (PinId={UUID},{LinkStr})\n"

gl_uuid_namespace = uuid.uuid1()

gl_height = 0

def get_uuid(name) -> str:
    global gl_uuid_namespace
    return str(uuid.uuid3(namespace=gl_uuid_namespace, name=name).hex).upper()

gl_node_map = {}
gl_node_socket_map = {}

def _get_node_names(id, node) -> List[str]:
    global gl_node_map
    if not (node in gl_node_map):
        node_type = ""
        if node.type in NodeClassMap:
            node_type = NodeNameMap[node.type]
        elif node.operation in NodeClassMap:
            node_type = NodeNameMap[node.operation]

        graph_name = GlobalName.format(str(id))
        node_name = node_type + '_' + str(id)
        
        if node.type == "REROUTE":
            insert_index = graph_name.find("_")
            graph_name = graph_name[:insert_index] + "_Knot" + graph_name[insert_index:]

        gl_node_map[node] = [graph_name, node_name, node_type].copy()

    return gl_node_map[node]

def _gen_linked_infos(id, node):
    '''
    returns:
        node_names[0]: all input sockets linked node graph names
        node_names[1]: all output sockets linked node graph names
        inputs_uuid: first uuid is itself, others are linked sockets uuid
        outputs_uuid: first uuid is itself, others are linked sockets uuid
    '''
    global gl_node_map
    global gl_node_socket_map

    ret_in_node_names = []
    ret_out_node_names = []
    # input and output pins array
    # the first uuid is itself
    # others are linkto socket uuid
    ret_input_pins_uuid = []
    ret_output_pins_uuid = []

    # print(node.name)
    for input in node.inputs:
        # print(type(input))
        if input.enabled:
            pin_info = []
            # get current socket pin uuid
            pin_uuid = ''
            if not input in gl_node_socket_map:
                uuid_name = 'input' + node.type + node.name + input.identifier
                pin_uuid = get_uuid(uuid_name)
                gl_node_socket_map[input] = pin_uuid
            else:
                pin_uuid = gl_node_socket_map[input]
            pin_info.append(pin_uuid)
            # process input linked socket
            if input.is_linked:
                for link in input.links:
                    if not link.from_node in gl_nodes:
                        ret_in_node_names.append({'_CONSTANT_' : {"Type": input.type, "Value": input.default_value}})
                        continue
                    # get linked node info
                    to_node_names = []
                    if not link.from_node in gl_node_map:
                        id += 1
                    ret_in_node_names.append(_get_node_names(id+1, link.from_node))

                    link_to_pin_uuid = ''
                    if not link.from_socket in gl_node_socket_map:
                        uuid_name = link.from_node.name + link.from_socket.identifier
                        link_to_pin_uuid = get_uuid(uuid_name)
                        gl_node_socket_map[link.from_socket] = link_to_pin_uuid
                    else:
                        link_to_pin_uuid = gl_node_socket_map[link.from_socket]
                    
                    if (link_to_pin_uuid != ''):
                        pin_info.append(link_to_pin_uuid)

            # constant value input
            else:
                # if contant, will create a new contant value node in ue
                ret_in_node_names.append({'_CONSTANT_' : {"Type": input.type, "Value": input.default_value}})
            
            ret_input_pins_uuid.append(pin_info)
        
    # todo: outputs 要去ue里看看一个节点多个输出的pin是怎么样的
    for output in node.outputs:
        # only export linked output socket
        if output.enabled:
            pin_info = []
            # get current socket pin uuid
            pin_uuid = ''
            if not output in gl_node_socket_map:
                uuid_name = 'output' + node.type + node.name + output.identifier
                pin_uuid = get_uuid(uuid_name)
                gl_node_socket_map[output] = pin_uuid
            else:
                pin_uuid = gl_node_socket_map[output]
            pin_info.append(pin_uuid)

            if output.is_linked:
                for link in output.links:
                    if not link.to_node in gl_nodes:
                        continue
                    # get linked node info
                    to_node_names = []
                    if not link.to_node in gl_node_map:
                        id += 1
                    ret_out_node_names.append(_get_node_names(id+1, link.to_node))

                    link_to_pin_uuid = ''
                    if not link.to_socket in gl_node_socket_map:
                        uuid_name = link.to_node.name + link.to_socket.identifier
                        link_to_pin_uuid = get_uuid(uuid_name)
                        gl_node_socket_map[link.to_socket] = link_to_pin_uuid
                    else:
                        link_to_pin_uuid = gl_node_socket_map[link.to_socket]
                    
                    if (link_to_pin_uuid != ''):
                        pin_info.append(link_to_pin_uuid)
            # constant value input
            else:
                # if not connect
                #ret_output_pins_uuid.append({'_CONSTANT_' : {"Type": output.type, "Value": None}})
                pass
                    
            ret_output_pins_uuid.append(pin_info)
    
    # print(ret_node_names)
    # print(ret_input_pins_uuid)
    # print(ret_output_pins_uuid)
    return {'node_names': [ret_in_node_names, ret_out_node_names], 'inputs_uuid': ret_input_pins_uuid, 'outputs_uuid': ret_output_pins_uuid}

def _exp_reroute(node, linked_info):
    pin = ""
    if node.inputs[0].is_linked:
        for input in linked_info['outputs_uuid']:
            links_pin_str = ''
            for i in range(1, len(input)):
                links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=input[i])
            pin += PinTemplate.format(UUID=input[0], LinkStr=LinkedToTemplate.format(links_pin_str))
    if node.outputs[0].is_linked:
        for output in linked_info['outputs_uuid']:
            links_pin_str = ''
            for i in range(1, len(output)):
                links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=output[i])
            pin += PinTemplate.format(UUID=output[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))
    return { "Value": "", "Pin": pin, "Constant":[], "Replace": [] }

def _exp_constant(type, value, linkto_names, linkto_uuid, location):
    node_expression : str = ""

    graph_name = GlobalName.format(str(int(random()*1000) + int(random()*999)))
    node_type = NodeNameMap[type]
    object_name = node_type + '_' + str(int(random()*99))

    NodeNameStr = NameOption.format(object_name)

    #1 Head
    node_expression = HeadTemplate.format(
        ClassOption.format("/Script/UnrealEd.MaterialGraphNode"),
        NameOption.format(graph_name))

    #2 Head
    node_expression += "\t"
    node_expression += HeadTemplate.format(
        ClassOption.format(node_type),
        NodeNameStr)
    node_expression += "\t"
    node_expression += EndTemplate
    #2 End

    #3 Head
    node_expression += "\t"
    node_expression += HeadTemplate.format(
        "",
        NodeNameStr)

    # todo: change to swtich
    if type == 'RGB':
        node_expression += "\t\tConstant=(R=%.6f,G=%.6f,B=%.6f,A=%.6f)\n"%tuple(value)
    elif type == 'RGBA':
        node_expression += "\t\tConstant=(R=%.6f,G=%.6f,B=%.6f,A=%.6f)\n"%tuple(value)
    elif type == 'VECTOR':
        node_expression += "\t\tConstant=(R=%.6f,G=%.6f,B=%.6f,A=1.0)\n"%tuple(value)
    elif type == 'VALUE':
        node_expression += "\t\tR=%.6f\n"%(value)
    elif type == '_NORMALWS' or type == '_CAMVECWS' or type == '_CAMERA_POS' or type == '_OBJ_POS':
        pass
    

    node_expression += "\t"
    node_expression += EndTemplate
    #3 End

    node_expression += MatExpTemplate.format(node_type, object_name)
    node_expression += NodePosTemplate.format(str(int(location.x-60)), str(int(gl_height - location.y)))

    # CustomProperties
    output_uuid = get_uuid(graph_name + object_name)
    links_pin_str = LinkTemplate.format(Graph=linkto_names[0], UUID=linkto_uuid)
    node_expression += PinTemplate.format(UUID=output_uuid, LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    node_expression += EndTemplate
    #1 End

    return node_expression, [graph_name, object_name, node_type], output_uuid

def _exp_rgb(node, linked_info):
    # if not node.get_out_nodes()[0].is_linked:
        value = node.outputs[0].default_value
        pin = ""
        if node.outputs[0].is_linked:
            for output in linked_info['outputs_uuid']:
                links_pin_str = ''
                for i in range(1, len(output)):
                    links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=output[i])
                pin += PinTemplate.format(UUID=output[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))
        return { "Value": "\t\tConstant=(R=%.6f,G=%.6f,B=%.6f,A=%.6f)\n"%tuple(value), "Pin": pin, "Constant":[], "Replace": [] } 

def _exp_value(node, linked_info):
    # if not node.get_out_nodes()[0].is_linked:
    value = node.outputs[0].default_value
    pin = ""
    if node.outputs[0].is_linked:
        for output in linked_info['outputs_uuid']:
            links_pin_str = ''
            for i in range(1, len(output)):
                links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=output[i])
            pin += PinTemplate.format(UUID=output[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))
    return { "Value": "\t\tR=%.6f\n"%(value), "Pin": pin, "Constant":[], "Replace": [] }

Transform_Source_Type = {
    "WORLD" : "TRANSFORMSOURCE_World",
    "OBJECT" : "TRANSFORMSOURCE_Local",
    "CAMERA" : "TRANSFORMSOURCE_Camera",
    "VIEW" : "TRANSFORMSOURCE_View"
}

Transform_Target_Type = {
    "WORLD" : "TRANSFORM_World",
    "OBJECT" : "TRANSFORM_Local",
    "CAMERA" : "TRANSFORM_Camera",
    "VIEW" : "TRANSFORM_View"
}

TransformPos_Source_Type = {
    "WORLD" : "TRANSFORMPOSSOURCE_World",
    "OBJECT" : "TRANSFORPOSMSOURCE_Local",
    "CAMERA" : "TRANSFORPOSMSOURCE_Camera",
    "VIEW" : "TRANSFORMPOSSOURCE_View"
}

TransformPos_Target_Type = {
    "WORLD" : "TRANSFORMPOSSOURCE_World",
    "OBJECT" : "TRANSFORMPOSSOURCE_Local",
    "CAMERA" : "TRANSFORMPOSSOURCE_Camera",
    "VIEW" : "TRANSFORMPOSSOURCE_View"
}

def _exp_vec_transform(node, linked_info):
    exp = ''
    pin = ''
    exp_constants = []

    exp += "\t\tTransformSourceType=%s\n"%(Transform_Source_Type[node.convert_from])
    exp += "\t\tTransformType=%s\n"%(Transform_Target_Type[node.convert_to])
    for i, inputs in enumerate(linked_info['inputs_uuid']):
        links_pin_str = ''

        linkto_type = ''
        linkto_graph = ''
        linkto_node = ''

        # if not connected, continue
        if '_CONSTANT_' in linked_info['node_names'][0][i]:
            continue
        else:
            linkto_type = linked_info['node_names'][0][i][2]
            linkto_graph = linked_info['node_names'][0][i][0]
            linkto_node = linked_info['node_names'][0][i][1]

            for j in range(1, len(inputs)):
                links_pin_str += LinkTemplate.format(Graph=linkto_graph, UUID=inputs[j])

            pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
    
        exp += FuncInputTemplate.format(int(i), FuncExpInputTemplate.format("Input", linkto_type, linkto_graph, linkto_node))
    
    if node.outputs[0].is_linked:
        for output in linked_info['outputs_uuid']:
            links_pin_str = ''
            for i in range(1, len(output)):
                links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=output[i])
            pin += PinTemplate.format(UUID=output[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    return {"Value": exp, "Pin": pin, "Constant": exp_constants, "Replace": []}

def _internal_vect_transform(type, fromtype, totype, from_names, linkto_names, linkto_uuids, location):
    node_expression : str = ""

    graph_name = GlobalName.format(str(int(random()*3000) + int(random()*999)))
    node_type = NodeNameMap[type]
    object_name = node_type + '_' + str(int(random()*99))

    NodeNameStr = NameOption.format(object_name)

    #1 Head
    node_expression = HeadTemplate.format(
        ClassOption.format("/Script/UnrealEd.MaterialGraphNode"),
        NameOption.format(from_names[0]))

    #2 Head
    node_expression += "\t"
    node_expression += HeadTemplate.format(
        ClassOption.format(node_type),
        NodeNameStr)
    node_expression += "\t"
    node_expression += EndTemplate
    #2 End

    #3 Head
    node_expression += "\t"
    node_expression += HeadTemplate.format(
        "",
        NodeNameStr)
    if type == "VECT_TRANSFORM":
        node_expression += "\t\tTransformSourceType=%s\n"%(Transform_Source_Type[fromtype])
        node_expression += "\t\tTransformType=%s\n"%(Transform_Target_Type[totype])
        node_expression += InputTemplate.format("Input", from_names[2], from_names[0], from_names[1])
    elif type == "_POINT_TRANSFORM":
        node_expression += "\t\tTransformSourceType=%s\n"%(TransformPos_Source_Type[fromtype])
        node_expression += "\t\tTransformType=%s\n"%(TransformPos_Target_Type[totype])
        node_expression += InputTemplate.format("Input", from_names[2], from_names[0], from_names[1])
    
    node_expression += "\t"
    node_expression += EndTemplate
    #3 End

    node_expression += MatExpTemplate.format(node_type, object_name)
    node_expression += NodePosTemplate.format(str(int(location.x-60)), str(int(gl_height - location.y)))

    # CustomProperties
    input_uuid = get_uuid('intput' + graph_name + object_name)
    output_uuid = get_uuid('output' + graph_name + object_name)
    
    links_pin_str = LinkTemplate.format(Graph=graph_name, UUID=output_uuid)
    node_expression += PinTemplate.format(UUID=input_uuid, LinkStr=LinkedToTemplate.format(links_pin_str))

    links_pin_str = ''
    for i in range(1, len(linkto_uuids)):
        links_pin_str += LinkTemplate.format(Graph=linkto_names[i-1][0], UUID=linkto_uuids[i])
    node_expression += PinTemplate.format(UUID=linkto_uuids[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    node_expression += EndTemplate
    #1 End

    return node_expression, [graph_name, object_name, node_type], input_uuid, output_uuid

# todo:
# figure out the index of uvmap in blender 
# (we can only know the name of uvmap, but ue need index)
def _exp_uvmap(node, linked_info):
    exp = ''
    pin = ''

    for i, outputs in enumerate(linked_info['outputs_uuid']):
        links_pin_str = ''
        for j in range(1, len(outputs)):
            links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][j-1][0], UUID=outputs[j])
        pin += PinTemplate.format(UUID=outputs[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    return {"Value": exp, "Pin": pin, "Constant": [], "Replace": []}

# ue can only solve one vertex color
def _exp_vertex_color(node, linked_info):
    exp = ''
    pin = ''
    temp_pin = []

    for i, outputs in enumerate(linked_info['outputs_uuid']):
        links_pin_str = ''
        for j in range(1, len(outputs)):
            links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][j-1][0], UUID=outputs[j])
        temp_pin.append(PinTemplate.format(UUID=outputs[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str)))
    
    # For Alpha Output
    insert_str = "\tCustomProperties Pin (PinId=%s,Direction=\"EGPD_Output\",)\n"%(get_uuid(str(linked_info['outputs_uuid'][0])))
    for i in range(0, 3):
        temp_pin.insert(i+1, insert_str)

    for p in temp_pin:
        pin += p

    return {"Value": exp, "Pin": pin, "Constant": [], "Replace": []}

# Object Info node only have one valid socket: Location
def _exp_objinfo(node, linked_info):
    exp = ''
    pin = ''

    outputs = linked_info['outputs_uuid'][0]
    links_pin_str = ''
    for j in range(1, len(outputs)):
        links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][j-1][0], UUID=outputs[j])
    pin += PinTemplate.format(UUID=outputs[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    return {"Value": exp, "Pin": pin, "Constant": [], "Replace": []}

def _exp_single_output(linkto_names, linkto_uuids, type, location, index = 0, use_transform = False, transform_type = "", from_type = "", to_type = ""):
    node_expression : str = ""

    graph_name = GlobalName.format(str(int(random()*1000) + int(random()*999)))
    node_type = NodeNameMap[type]
    object_name = node_type + '_' + str(int(random()*99))

    NodeNameStr = NameOption.format(object_name)

    #1 Head
    node_expression = HeadTemplate.format(
        ClassOption.format("/Script/UnrealEd.MaterialGraphNode"),
        NameOption.format(graph_name))

    #2 Head
    node_expression += "\t"
    node_expression += HeadTemplate.format(
        ClassOption.format(node_type),
        NodeNameStr)
    node_expression += "\t"
    node_expression += EndTemplate
    #2 End

    #3 Head
    node_expression += "\t"
    node_expression += HeadTemplate.format(
        "",
        NodeNameStr)

    node_expression += "\t"
    node_expression += EndTemplate
    #3 End

    node_expression += MatExpTemplate.format(node_type, object_name)
    node_expression += NodePosTemplate.format(str(int(location.x-60)), str(int(gl_height - location.y)))

    

    # CustomProperties
    t_exp = ""
    if use_transform:
        t_linkto_names = []
        links_num = len(linkto_uuids)-1
        for i in range(index, index+links_num):
            t_linkto_names.append(linkto_names[i])
        t_exp, t_names, i_uuid, o_uuid = _internal_vect_transform(transform_type, from_type, to_type, [graph_name, object_name, node_type], t_linkto_names, linkto_uuids, location)
        links_pin_str = LinkTemplate.format(Graph=t_names[0], UUID=i_uuid)
        node_expression += PinTemplate.format(UUID=o_uuid, LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))
        node_expression = node_expression.replace(graph_name, t_names[0], 1)
        graph_name = t_names[0]
    else:
        links_pin_str = ''
        links_num = len(linkto_uuids)-1
        for i in range(index, index+links_num):
            links_pin_str += LinkTemplate.format(Graph=linkto_names[i][0], UUID=linkto_uuids[i-index])
        node_expression += PinTemplate.format(UUID=linkto_uuids[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    node_expression += EndTemplate
    #1 End
    node_expression = t_exp + node_expression
    return node_expression, [graph_name, linkto_uuids[0]] # change output linked pin info

def _exp_camera_vector(node, linked_info):
    exp = ''
    pin = ''
    temp_pin = []
    exp_content = []
    
    # todo: wrong impl, View Vector is Camera Vector in Camera Space
    camera_vector_out = linked_info['outputs_uuid'][0]
    links_pin_str = ''
    cam_vec_out_names = []
    for j in range(1, len(camera_vector_out)):
        cam_vec_out_names.append(linked_info['node_names'][1][j-1])

    t_names = None
    if len(linked_info['outputs_uuid'][0]) > 1:
        t_exp, t_names, i_uuid, o_uuid = _internal_vect_transform('VECT_TRANSFORM', 'WORLD', 'CAMERA', _get_node_names(-1, node), cam_vec_out_names, camera_vector_out, node.location)
        exp_content.append(t_exp)

        # swtich output uuid and graph name
        links_pin_str += LinkTemplate.format(Graph=_get_node_names(-1, node)[0], UUID=i_uuid)
        pin += PinTemplate.format(UUID=o_uuid, LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    # View Z Depth connected
    replace = []
    if len(linked_info['outputs_uuid'][1]) > 1:
        t_exp, t_replace = _exp_single_output(linked_info['node_names'][1], linked_info['outputs_uuid'][1], "_CAMERA_DEPTH", node.location, len(linked_info['outputs_uuid'][0])-1)
        t_replace.insert(0, _get_node_names(-1, node)[0])

        replace.append(t_replace)
        exp_content.append(t_exp)
    
    # todo: View Distance connected
    # distance of point to camera position
    # View Distance maybe need custom MF

    for p in temp_pin:
        pin += p

    return {"Value": exp, "Pin": pin, "Constant": exp_content, "InsertNames": t_names, "Replace": replace}

def _exp_texcoord(node, linked_info):
    exp = ''
    pin = ''
    exp_content = []

    # generated is not existed in ue
    outputs = linked_info['outputs_uuid'][0]
    if len(outputs) > 1:
        links_pin_str = ''
        for j in range(1, len(outputs)):
            links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][j-1][0], UUID=outputs[j])
        pin += PinTemplate.format(UUID=outputs[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    replace = []

    # Object space normal
    name_index = len(linked_info['outputs_uuid'][0])-1
    if len(linked_info['outputs_uuid'][1]) > 1:
        t_exp, t_replace = _exp_single_output(linked_info['node_names'][1], linked_info['outputs_uuid'][1], "_NORMALOS", node.location, name_index, 
                                                True, "VECT_TRANSFORM", "WORLD", "OBJECT")
        t_replace.insert(0, _get_node_names(-1, node)[0])

        replace.append(t_replace)
        exp_content.append(t_exp)
    
    # uv
    name_index += len(linked_info['outputs_uuid'][1])-1
    if len(linked_info['outputs_uuid'][2]) > 1:
        t_exp, t_replace = _exp_single_output(linked_info['node_names'][1], linked_info['outputs_uuid'][2], "_UV", node.location, name_index)
        t_replace.insert(0, _get_node_names(-1, node)[0])

        replace.append(t_replace)
        exp_content.append(t_exp)
    
    # object space position
    name_index += len(linked_info['outputs_uuid'][2])-1
    if len(linked_info['outputs_uuid'][3]) > 1:
        t_exp, t_replace = _exp_single_output(linked_info['node_names'][1], linked_info['outputs_uuid'][3], "_OBJ_POS", node.location, name_index,
                                                True, "_POINT_TRANSFORM", "WORLD", "OBJECT")
        t_replace.insert(0, _get_node_names(-1, node)[0])

        replace.append(t_replace)
        exp_content.append(t_exp)
    
     # camera space position
    name_index += len(linked_info['outputs_uuid'][3])-1
    if len(linked_info['outputs_uuid'][4]) > 1:
        t_exp, t_replace = _exp_single_output(linked_info['node_names'][1], linked_info['outputs_uuid'][4], "_CAM_POS", node.location, name_index,
                                                True, "_POINT_TRANSFORM", "WORLD", "CAMERA")
        t_replace.insert(0, _get_node_names(-1, node)[0])

        replace.append(t_replace)
        exp_content.append(t_exp)
    
    # windows uv
    name_index += len(linked_info['outputs_uuid'][4])-1
    if len(linked_info['outputs_uuid'][5]) > 1:
        t_exp, t_replace = _exp_single_output(linked_info['node_names'][1], linked_info['outputs_uuid'][5], "_WIN_POS", node.location, name_index)
        t_replace.insert(0, _get_node_names(-1, node)[0])

        replace.append(t_replace)
        exp_content.append(t_exp)
    
    # todo: relection
    
    return {"Value": exp, "Pin": pin, "Constant": exp_content, "Replace": replace}

def _exp_incomming(graph, linkto_names, linkto_uuids, location, index):
    node_expression : str = ""

    graph_name = GlobalName.format(str(int(random()*1000) + int(random()*999)))
    node_type = NodeNameMap["_INCOMMING"]
    object_name = node_type + '_' + str(int(random()*99))

    NodeNameStr = NameOption.format(object_name)

    #1 Head
    node_expression = HeadTemplate.format(
        ClassOption.format("/Script/UnrealEd.MaterialGraphNode"),
        NameOption.format(graph_name))

    #2 Head
    node_expression += "\t"
    node_expression += HeadTemplate.format(
        ClassOption.format(node_type),
        NodeNameStr)
    node_expression += "\t"
    node_expression += EndTemplate
    #2 End

    campos_input_uuid = get_uuid(graph + "_incomming_camera_position")
    pixpos_input_uuid = get_uuid(graph + "_incomming_pixel_position")

    constant_str_1, constant_names_1, constant_uuid_1 = _exp_constant("_CAMERA_POS", -1, [graph_name, object_name, node_type], campos_input_uuid, location)
    constant_str_2, constant_names_2, constant_uuid_2 = _exp_constant("_OBJ_POS", -1, [graph_name, object_name, node_type], pixpos_input_uuid, location)

    #3 Head
    node_expression += "\t"
    node_expression += HeadTemplate.format(
        "",
        NodeNameStr)

    node_expression += "\t\tCode=\"return normalize(camera_position - pixel_position);\"\n"
    node_expression += "\t\tDescription=\"Geometry_incomming\"\n"

    node_expression += CustomInputTemplate.format(0, "camera_position", FuncExpInputTemplate.format("Input", constant_names_1[2], constant_names_1[0], constant_names_1[1]))
    node_expression += CustomInputTemplate.format(1, "pixel_position", FuncExpInputTemplate.format("Input", constant_names_2[2], constant_names_2[0], constant_names_2[1]))

    node_expression += "\t"
    node_expression += EndTemplate
    #3 End

    node_expression += MatExpTemplate.format(node_type, object_name)
    node_expression += NodePosTemplate.format(str(int(location.x-60)), str(int(gl_height - location.y)))

    # input
    links_pin_str = LinkTemplate.format(Graph=constant_names_1[0], UUID=constant_uuid_1)
    node_expression += PinTemplate.format(UUID=campos_input_uuid + ",PinName=\"%s\""%("camera_position"), LinkStr=LinkedToTemplate.format(links_pin_str))
    links_pin_str = LinkTemplate.format(Graph=constant_names_2[0], UUID=constant_uuid_2)
    node_expression += PinTemplate.format(UUID=campos_input_uuid + ",PinName=\"%s\""%("pixel_position"), LinkStr=LinkedToTemplate.format(links_pin_str))

    # output
    links_pin_str = ''
    links_num = len(linkto_uuids)-1
    for i in range(index, index+links_num):
        links_pin_str += LinkTemplate.format(Graph=linkto_names[i][0], UUID=linkto_uuids[i-index])
    node_expression += PinTemplate.format(UUID=linkto_uuids[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    node_expression += EndTemplate
    #1 End

    node_expression = constant_str_2 + node_expression
    node_expression = constant_str_1 + node_expression

    return node_expression, [graph_name, linkto_uuids[0]]

def _exp_geometry(node, linked_info):
    exp = ''
    pin = ''
    exp_content = []
    replace = []

    outputs = linked_info['outputs_uuid'][0]
    if len(outputs) > 1:
        links_pin_str = ''
        for j in range(1, len(outputs)):
            links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][j-1][0], UUID=outputs[j])
        pin += PinTemplate.format(UUID=outputs[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))
    
    # normal
    name_index = len(linked_info['outputs_uuid'][0])-1
    if len(linked_info['outputs_uuid'][1]) > 1:
        t_exp, t_replace = _exp_single_output(linked_info['node_names'][1], linked_info['outputs_uuid'][1], "_NORMALWS", node.location, name_index)
        t_replace.insert(0, _get_node_names(-1, node)[0])

        replace.append(t_replace)
        exp_content.append(t_exp)
    
    # tangent
    name_index += len(linked_info['outputs_uuid'][1])-1
    if len(linked_info['outputs_uuid'][2]) > 1:
        t_exp, t_replace = _exp_single_output(linked_info['node_names'][1], linked_info['outputs_uuid'][2], "_TANGENTWS", node.location, name_index)
        t_replace.insert(0, _get_node_names(-1, node)[0])

        replace.append(t_replace)
        exp_content.append(t_exp)
    
    # true normal
    name_index += len(linked_info['outputs_uuid'][2])-1
    if len(linked_info['outputs_uuid'][3]) > 1:
        t_exp, t_replace = _exp_single_output(linked_info['node_names'][1], linked_info['outputs_uuid'][3], "_VERTEX_NORMAlWS", node.location, name_index)
        t_replace.insert(0, _get_node_names(-1, node)[0])

        replace.append(t_replace)
        exp_content.append(t_exp)

    # incomming
    name_index += len(linked_info['outputs_uuid'][3])-1
    if len(linked_info['outputs_uuid'][4]) > 1:
        t_exp, t_replace = _exp_incomming(_get_node_names(-1, node)[0], linked_info['node_names'][1], linked_info['outputs_uuid'][4], node.location, name_index)
        t_replace.insert(0, _get_node_names(-1, node)[0])

        replace.append(t_replace)
        exp_content.append(t_exp)

    return {"Value": exp, "Pin": pin, "Constant": exp_content, "Replace": replace}

# https://en.wikipedia.org/wiki/Blend_modes
# you can find the algorithm on https://github.com/blender/blender/blob/master/source/blender/blenkernel/intern/material.c#L1592
# https://www.deepskycolors.com/archivo/2010/04/21/formulas-for-Photoshop-blending-modes.html
# some color convert code on https://www.chilliant.com/rgb2hsv.html also ue official custom node
convert_func_code = "\
struct Functions\\n\
{\\n\
\\tfloat3 rgb_to_hsv(float3 c)\\n\
\\t{\\n\
\\t\\tfloat4 K = float4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);\\n\
\\t\\tfloat4 p = lerp(float4(c.bg, K.wz), float4(c.gb, K.xy), step(c.b, c.g));\\n\
\\t\\tfloat4 q = lerp(float4(p.xyw, c.r), float4(c.r, p.yzx), step(p.x, c.r));\\n\
\\t\\tfloat d = q.x - min(q.w, q.y);\\n\
\\t\\tfloat e = .0000001;\\n\
\\t\\treturn float3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);\\n\
\\t}\\n\
\\tfloat3 hsv_to_rgb(float3 hsv)\\n\
\\t{\\n\
\\t\\tfloat4 K = float4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);\\n\
\\t\\tfloat3 p = abs(frac(hsv.xxx + K.xyz) * 6.0 - K.www);\\n\
\\t\\treturn hsv.z * lerp(K.xxx, saturate(p - K.xxx), hsv.y);\\n\
\\t}\\n\
};\\n\
Functions f;\\n"

Mix_BlendeType_Code = {
    'MIX' : "return lerp(a, b, t);",
    'MULTIPLY' : "return a * (b * t);",
    'DIVIDE' : "return a / (b * t);",
    'ADD' : "return a + (b * t);",
    'SUBTRACT' : "return a - (b * t);",
    'SCREEN' : "float tm = 1 - t;\\nreturn 1 - (tm + t * (1 - b)) * (1 - a);",
    'DIFFERENCE' : "float tm = 1 - t;\\nreturn tm * a + t * abs(a - b);",
    'DARKEN' : "float tm = 1 - t;\\nreturn t * min(a, b) + tm * a;",
    'LIGHTEN' : "return max(a, t*b);",
    'DODGE' : "return a/(1-t*b);",
    'BURN' : "float tm = 1 - t;\\nreturn 1-(1-a)/(tm+t*b);",
    'SOFT_LIGHT' : "float tm = 1 - t;\\nfloat3 sc = 1 - (1 - a) * (1 - b);\\nreturn tm * a + t * ((1 - a) * b * a + a * sc);",
    'LINEAR_LIGHT' : "return a + t * ( 2 * (b - 0.5f));",
    ###
    'OVERLAY' : "\
struct Functions\\n\
{\\n\
\\tfloat overlay(float a, float b, float t)\\n\
\\t{\\n\
\\t\\tfloat tm = 1 - t;\\n\
\\t\\treturn a < 0.5 ? a*(tm+2*t*b) : 1-(tm+2*t*(1-b))*(1-a);\\n\
\\t}\\n\
\\tfloat3 overlay(float3 a, float3 b, float t)\\n\
\\t{\\n\
\\t\\treturn float3(overlay(a.x, b.x, t), overlay(a.y, b.y, t), overlay(a.z, b.z, t));\\n\
\\t}\\n\
};\\n\
Functions f;\\n\
return f.overlay(a, b, t);\\n",
    ###
    'VALUE' : convert_func_code + "\
float tm = 1 - t;\\n\
float3 a_hsv = f.rgb_to_hsv(a);\\n\
float3 b_hsv = f.rgb_to_hsv(b);\\n\
return f.hsv_to_rgb(float3(a_hsv.x, a_hsv.y, tm*a_hsv.z + t*b_hsv.z));",
    ###
    'COLOR' : convert_func_code + "\
float tm = 1 - t;\\n\
float3 b_hsv = f.rgb_to_hsv(b);\\n\
if (b_hsv.y != 0)\\n\
{\
\\tfloat3 a_hsv = f.rgb_to_hsv(a);\\n\
\\tfloat3 tempc = f.hsv_to_rgb(float3(b_hsv.x, b_hsv.y, a_hsv.z));\\n\
\\ta = tm * a + t * tempc;\\n\
}\
return a;",
    ###
    'HUE' : convert_func_code + "\
float tm = 1 - t;\\n\
float3 b_hsv = f.rgb_to_hsv(b);\\n\
float3 a_hsv = f.rgb_to_hsv(a);\\n\
float3 tmp = f.hsv_to_rgb(float3(b_hsv.x, a_hsv.y, a_hsv.z));\\n\
return b_hsv.y != 0 ? tm*a+t*tmp : a;",
    ###
    'SATURATION' : convert_func_code + "\
float tm = 1 - t;\\n\
float3 a_hsv = f.rgb_to_hsv(a);\\n\
float3 b_hsv = f.rgb_to_hsv(b);\\n\
float3 tmp = f.hsv_to_rgb(float3(a_hsv.x, (tm*a_hsv.y+t*b_hsv.y), a_hsv.z));\\n\
return a_hsv.y != 0 ? tmp : a;"
}

def _exp_mix(node, linked_info):
    exp = ''
    pin = ''
    exp_constants = []

    blend_type = node.blend_type

    var_name = ['t', 'a', 'b']

    if blend_type in Mix_BlendeType_Code:
        exp += "\t\tCode=\"%s\"\n"%(Mix_BlendeType_Code[blend_type])
        exp += "\t\tDescription=\"%s\"\n"%(blend_type)

        for i, inputs in enumerate(linked_info['inputs_uuid']):
            links_pin_str = ''

            linkto_type = ''
            linkto_graph = ''
            linkto_node = ''

            # if constant var, create a new node
            if '_CONSTANT_' in linked_info['node_names'][0][i]:
                constant_str, constant_names, constant_uuid = _exp_constant(linked_info['node_names'][0][i]['_CONSTANT_']["Type"], 
                                                            linked_info['node_names'][0][i]['_CONSTANT_']["Value"], 
                                                            _get_node_names(-1, node), inputs[0], node.location)
                exp_constants.append(constant_str)
                linkto_graph = constant_names[0]
                linkto_node = constant_names[1]
                linkto_type = constant_names[2]

                links_pin_str = LinkTemplate.format(Graph=constant_names[0], UUID=constant_uuid)
                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
            else:
                linkto_type = linked_info['node_names'][0][i][2]
                linkto_graph = linked_info['node_names'][0][i][0]
                linkto_node = linked_info['node_names'][0][i][1]

                for j in range(1, len(inputs)):
                    links_pin_str += LinkTemplate.format(Graph=linkto_graph, UUID=inputs[j])

                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
        
            exp += CustomInputTemplate.format(int(i), var_name[i], FuncExpInputTemplate.format("Input", linkto_type, linkto_graph, linkto_node))
        
    if node.outputs[0].is_linked:
        for output in linked_info['outputs_uuid']:
            links_pin_str = ''
            for i in range(1, len(output)):
                links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=output[i])
            pin += PinTemplate.format(UUID=output[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    return {"Value": exp, "Pin": pin, "Constant": exp_constants, "Replace": []}

def _exp_fresnel(node, linked_info):
    exp = ''
    pin = ''
    exp_constants = []

    exp += "\t\tCode=\"float Fraction = ((1-ior)*(1-ior)) / ((1+ior)*(1+ior));\\r\\n\\r\\nreturn Fraction + (1-Fraction)*pow(1-dot(camera_vector, normal), 5);\"\n"
    exp += "\t\tOutputType=CMOT_Float1\n"
    exp += "\t\tDescription=\"Fresnel_IOR\"\n"

    for i, inputs in enumerate(linked_info['inputs_uuid']):
        links_pin_str = ''

        linkto_type = ''
        linkto_graph = ''
        linkto_node = ''
        
        input_name = ''
        if i == 0:
            input_name = 'ior'
        else:
            input_name = 'normal'

        # if constant var, create a new node
        if '_CONSTANT_' in linked_info['node_names'][0][i]:
            _type = linked_info['node_names'][0][i]['_CONSTANT_']["Type"]
            if i == 1:
                _type = "_NORMALWS"
            constant_str, constant_names, constant_uuid = _exp_constant(_type, 
                                                        linked_info['node_names'][0][i]['_CONSTANT_']["Value"], 
                                                        _get_node_names(-1, node), inputs[0], node.location)
            exp_constants.append(constant_str)
            linkto_graph = constant_names[0]
            linkto_node = constant_names[1]
            linkto_type = constant_names[2]

            links_pin_str = LinkTemplate.format(Graph=constant_names[0], UUID=constant_uuid)
            pin += PinTemplate.format(UUID=inputs[0] + ",PinName=\"%s\""%(input_name), LinkStr=LinkedToTemplate.format(links_pin_str))
        else:
            linkto_type = linked_info['node_names'][0][i][2]
            linkto_graph = linked_info['node_names'][0][i][0]
            linkto_node = linked_info['node_names'][0][i][1]

            for j in range(1, len(inputs)):
                links_pin_str += LinkTemplate.format(Graph=linkto_graph, UUID=inputs[j])

            pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))

        exp += CustomInputTemplate.format(int(i), input_name, FuncExpInputTemplate.format("Input", linkto_type, linkto_graph, linkto_node))
    
    # Camera Vector
    input_uuid = get_uuid(_get_node_names(-1, node)[1] + "_CAMVECTOR")
    constant_str, constant_names, constant_uuid = _exp_constant('_CAMVECWS', -1, _get_node_names(-1, node), input_uuid, node.location)

    exp_constants.append(constant_str)
    links_pin_str = LinkTemplate.format(Graph=constant_names[0], UUID=constant_uuid)
    pin += PinTemplate.format(UUID=inputs[0] + ",PinName=\"%s\""%("camera_vector"), LinkStr=LinkedToTemplate.format(links_pin_str))
    exp += CustomInputTemplate.format(int(2), "camera_vector", FuncExpInputTemplate.format("Input", constant_names[2], constant_names[0], constant_names[1]))

    if node.outputs[0].is_linked:
        for output in linked_info['outputs_uuid']:
            links_pin_str = ''
            for i in range(1, len(output)):
                links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=output[i])
            pin += PinTemplate.format(UUID=output[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))
    
    return {"Value": exp, "Pin": pin, "Constant": exp_constants, "Replace": []}

def _exp_comb_xyz(node, linked_info):
    MatFunction = "/Engine/Functions/Engine_MaterialFunctions02/Utility/MakeFloat4.MakeFloat4"
    exp = ''
    pin = ''
    exp_constants = []

    exp += MatFuncTemplate.format(MatFunction)
    for i, inputs in enumerate(linked_info['inputs_uuid']):
        links_pin_str = ''

        linkto_type = ''
        linkto_graph = ''
        linkto_node = ''

        # if constant var, create a new node
        if '_CONSTANT_' in linked_info['node_names'][0][i]:
            constant_str, constant_names, constant_uuid = _exp_constant(linked_info['node_names'][0][i]['_CONSTANT_']["Type"], 
                                                        linked_info['node_names'][0][i]['_CONSTANT_']["Value"], 
                                                        _get_node_names(-1, node), inputs[0], node.location)
            exp_constants.append(constant_str)
            linkto_graph = constant_names[0]
            linkto_node = constant_names[1]
            linkto_type = constant_names[2]

            links_pin_str = LinkTemplate.format(Graph=constant_names[0], UUID=constant_uuid)
            pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
        else:
            linkto_type = linked_info['node_names'][0][i][2]
            linkto_graph = linked_info['node_names'][0][i][0]
            linkto_node = linked_info['node_names'][0][i][1]

            for j in range(1, len(inputs)):
                links_pin_str += LinkTemplate.format(Graph=linkto_graph, UUID=inputs[j])

            pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
    
        exp += FuncInputTemplate.format(int(i), FuncExpInputTemplate.format("Input", linkto_type, linkto_graph, linkto_node))
    
    # make float4
    exp += FuncInputTemplate.format(int(3), "Input=(OutputIndex=-1,InputName=\"A\")")
    exp += "\t\tFunctionOutputs(0)=(Output=(OutputName=\"Result\"))\n"
    exp += "\t\tOutputs(0)=(OutputName=\"Result\")\n"
    
    
    if node.outputs[0].is_linked:
        for output in linked_info['outputs_uuid']:
            links_pin_str = ''
            for i in range(1, len(output)):
                links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=output[i])
            pin += PinTemplate.format(UUID=output[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    return {"Value": exp, "Pin": pin, "Constant": exp_constants, "Replace": []}

def _exp_sep_xyz(node, linked_info):
    MatFunction = "/Engine/Functions/Engine_MaterialFunctions02/Utility/BreakOutFloat4Components.BreakOutFloat4Components"
    exp = ''
    pin = ''
    exp_constants = []

    exp += MatFuncTemplate.format(MatFunction)
    for i, inputs in enumerate(linked_info['inputs_uuid']):
        links_pin_str = ''

        linkto_type = ''
        linkto_graph = ''
        linkto_node = ''

        # if constant var, create a new node
        if '_CONSTANT_' in linked_info['node_names'][0][i]:
            constant_str, constant_names, constant_uuid = _exp_constant(linked_info['node_names'][0][i]['_CONSTANT_']["Type"], 
                                                        linked_info['node_names'][0][i]['_CONSTANT_']["Value"], 
                                                        _get_node_names(-1, node), inputs[0], node.location)
            exp_constants.append(constant_str)
            linkto_graph = constant_names[0]
            linkto_node = constant_names[1]
            linkto_type = constant_names[2]

            links_pin_str = LinkTemplate.format(Graph=constant_names[0], UUID=constant_uuid)
            pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
        else:
            linkto_type = linked_info['node_names'][0][i][2]
            linkto_graph = linked_info['node_names'][0][i][0]
            linkto_node = linked_info['node_names'][0][i][1]

            for j in range(1, len(inputs)):
                links_pin_str += LinkTemplate.format(Graph=linkto_graph, UUID=inputs[j])

            pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
    
        exp += FuncInputTemplate.format(int(i), FuncExpInputTemplate.format("Input", linkto_type, linkto_graph, linkto_node))
    
    # output
    exp += "\t\tFunctionOutputs(0)=(Output=(OutputName=\"R\"))\n"
    exp += "\t\tFunctionOutputs(1)=(Output=(OutputName=\"G\"))\n"
    exp += "\t\tFunctionOutputs(2)=(Output=(OutputName=\"B\"))\n"
    exp += "\t\tFunctionOutputs(3)=(Output=(OutputName=\"A\"))\n"
    exp += "\t\tOutputs(0)=(OutputName=\"R\")\n"
    exp += "\t\tOutputs(1)=(OutputName=\"G\")\n"
    exp += "\t\tOutputs(2)=(OutputName=\"B\")\n"
    exp += "\t\tOutputs(3)=(OutputName=\"A\")\n"
    
    for i, outputs in enumerate(linked_info['outputs_uuid']):
        links_pin_str = ''
        for j in range(1, len(outputs)):
            links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][j-1][0], UUID=outputs[j])
        pin += PinTemplate.format(UUID=outputs[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    return {"Value": exp, "Pin": pin, "Constant": exp_constants, "Replace": []}

# A B
Math_Two_NodeClassMap = {
    "ADD",
    "SUBTRACT",
    "MULTIPLY",
    "DIVIDE",
    # Base Exponent
    "POWER",
    "MINIMUM",
    "MAXIMUM",
    "MODULO",
    # You can change to normal node
    # Y X
    "ARCTAN2",
}

# Input
Math_One_NodeClassMap = {
	'SQRT',
	'ABSOLUTE',
	'ROUND',
	'FLOOR',
	'CEIL',
	'FRACT',
	'SINE',
	'COSINE',
	'TANGENT',
    # You can change to normal node
	'ARCSINE',
	'ARCCOSINE',
	'ARCTANGENT',
	'SIGN',
	'TRUNC',
}

def _exp_math(node, linked_info, force_op=None):
    if force_op != None:
        op = force_op
    else:
        op = node.operation
    exp = ''
    pin = ''
    exp_constants = []
    if op in Math_Two_NodeClassMap:
        for i, inputs in enumerate(linked_info['inputs_uuid']):
            links_pin_str = ''

            linkto_type = ''
            linkto_graph = ''
            linkto_node = ''

            # if constant var, create a new node
            if '_CONSTANT_' in linked_info['node_names'][0][i]:
                constant_str, constant_names, constant_uuid = _exp_constant(linked_info['node_names'][0][i]['_CONSTANT_']["Type"], 
                                                            linked_info['node_names'][0][i]['_CONSTANT_']["Value"], 
                                                            _get_node_names(-1, node), inputs[0], node.location)
                exp_constants.append(constant_str)
                linkto_graph = constant_names[0]
                linkto_node = constant_names[1]
                linkto_type = constant_names[2]

                links_pin_str = LinkTemplate.format(Graph=constant_names[0], UUID=constant_uuid)
                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
            else:
                linkto_type = linked_info['node_names'][0][i][2]
                linkto_graph = linked_info['node_names'][0][i][0]
                linkto_node = linked_info['node_names'][0][i][1]

                for j in range(1, len(inputs)):
                    links_pin_str += LinkTemplate.format(Graph=linkto_graph, UUID=inputs[j])
                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
            
            if i == 0:
                if op == 'POWER':
                    exp += InputTemplate.format("Base", linkto_type, linkto_graph, linkto_node)
                elif op == 'ARCTAN2':
                    exp += InputTemplate.format("Y", linkto_type, linkto_graph, linkto_node)
                else:
                    exp += InputTemplate.format("A", linkto_type, linkto_graph, linkto_node)
            else:
                if op == 'POWER':
                    exp += InputTemplate.format("Exponent", linkto_type, linkto_graph, linkto_node)
                elif op == 'ARCTAN2':
                    exp += InputTemplate.format("X", linkto_type, linkto_graph, linkto_node)
                else:
                    exp += InputTemplate.format("B", linkto_type, linkto_graph, linkto_node)

    elif op in Math_One_NodeClassMap:
        for i, inputs in enumerate(linked_info['inputs_uuid']):
            links_pin_str = ''
            
            linkto_type = ''
            linkto_graph = ''
            linkto_node = ''

            if '_CONSTANT_' in linked_info['node_names'][0][i]:
                constant_str, constant_names, constant_uuid = _exp_constant(linked_info['node_names'][0][i]['_CONSTANT_']["Type"], 
                                                            linked_info['node_names'][0][i]['_CONSTANT_']["Value"], 
                                                            _get_node_names(-1, node), inputs[0], node.location)
                exp_constants.append(constant_str)
                linkto_graph = constant_names[0]
                linkto_node = constant_names[1]
                linkto_type = constant_names[2]

                links_pin_str = LinkTemplate.format(Graph=constant_names[0], UUID=constant_uuid)
                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
                pass
            else:
                linkto_type = linked_info['node_names'][0][i][2]
                linkto_graph = linked_info['node_names'][0][i][0]
                linkto_node = linked_info['node_names'][0][i][1]

                for j in range(1, len(inputs)):
                        links_pin_str += LinkTemplate.format(Graph=linkto_graph, UUID=inputs[j])
                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
            
            exp += InputTemplate.format("Input", linkto_type, linkto_graph, linkto_node)
    
    if node.outputs[0].is_linked:
        for output in linked_info['outputs_uuid']:
            links_pin_str = ''
            for i in range(1, len(output)):
                links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=output[i])
            pin += PinTemplate.format(UUID=output[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    return {"Value": exp, "Pin": pin, "Constant": exp_constants, "Replace": []}

# todo
Vect_Math_Three_NodeClassMap = {

}

# Other types same as math
Vect_Math_Two_NodeClassMap = {
    'CROSS_PRODUCT',
    'DOT_PRODUCT',
    'DISTANCE',
    'SCALE',
}

Vect_Math_One_NodeClassMap = {
    # VectorInput
    'NORMALIZE' : "/Script/Engine.MaterialExpressionNormalize",
    # length(a) == distance(a, 0)
    'LENGTH' : "/Script/Engine.MaterialExpressionDistance",
}

def _exp_vect_math(node, linked_info, force_op=None):
    if force_op != None:
        op = force_op
    else:
        op = node.operation

    if op in Math_Two_NodeClassMap or op in Math_One_NodeClassMap:
        return _exp_math(node, linked_info)

    exp = ''
    pin = ''
    exp_constants = []

    if op in Vect_Math_Two_NodeClassMap:
        for i, inputs in enumerate(linked_info['inputs_uuid']):
            links_pin_str = ''

            linkto_type = ''
            linkto_graph = ''
            linkto_node = ''

            # if constant var, create a new node
            if '_CONSTANT_' in linked_info['node_names'][0][i]:
                constant_str, constant_names, constant_uuid = _exp_constant(linked_info['node_names'][0][i]['_CONSTANT_']["Type"], 
                                                            linked_info['node_names'][0][i]['_CONSTANT_']["Value"], 
                                                            _get_node_names(-1, node), inputs[0], node.location)
                exp_constants.append(constant_str)
                linkto_graph = constant_names[0]
                linkto_node = constant_names[1]
                linkto_type = constant_names[2]

                links_pin_str = LinkTemplate.format(Graph=constant_names[0], UUID=constant_uuid)
                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
            else:
                linkto_type = linked_info['node_names'][0][i][2]
                linkto_graph = linked_info['node_names'][0][i][0]
                linkto_node = linked_info['node_names'][0][i][1]

                for j in range(1, len(inputs)):
                    links_pin_str += LinkTemplate.format(Graph=linkto_graph, UUID=inputs[j])
                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
            
            if i == 0:
                exp += InputTemplate.format("A", linkto_type, linkto_graph, linkto_node)
            else:
                exp += InputTemplate.format("B", linkto_type, linkto_graph, linkto_node)

    elif op in Vect_Math_One_NodeClassMap:
        for i, inputs in enumerate(linked_info['inputs_uuid']):
            links_pin_str = ''
            
            linkto_type = ''
            linkto_graph = ''
            linkto_node = ''

            if '_CONSTANT_' in linked_info['node_names'][0][i]:
                constant_str, constant_names, constant_uuid = _exp_constant(linked_info['node_names'][0][i]['_CONSTANT_']["Type"], 
                                                            linked_info['node_names'][0][i]['_CONSTANT_']["Value"], 
                                                            _get_node_names(-1, node), inputs[0], node.location)
                exp_constants.append(constant_str)
                linkto_graph = constant_names[0]
                linkto_node = constant_names[1]
                linkto_type = constant_names[2]

                links_pin_str = LinkTemplate.format(Graph=constant_names[0], UUID=constant_uuid)
                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
                pass
            else:
                linkto_type = linked_info['node_names'][0][i][2]
                linkto_graph = linked_info['node_names'][0][i][0]
                linkto_node = linked_info['node_names'][0][i][1]

                for j in range(1, len(inputs)):
                        links_pin_str += LinkTemplate.format(Graph=linkto_graph, UUID=inputs[j])
                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))

            if op == 'NORMALIZE':
                exp += InputTemplate.format("VectorInput", linkto_type, linkto_graph, linkto_node)
            elif op == 'LENGTH':
                exp += InputTemplate.format("A", linkto_type, linkto_graph, linkto_node)

                # Distance B:
                b_uuid = get_uuid(_get_node_names(-1, node)[0]+_get_node_names(-1, node)[1]+'LENGTH')
                constant_str, constant_names, constant_uuid = _exp_constant('VALUE', 0, _get_node_names(-1, node), b_uuid, node.location)
                exp_constants.append(constant_str)

                b_linkto_graph = constant_names[0]
                b_linkto_node = constant_names[1]
                b_linkto_type = constant_names[2]
                exp += InputTemplate.format("B", b_linkto_type, b_linkto_graph, b_linkto_node)

                b_links_pin_str = LinkTemplate.format(Graph=constant_names[0], UUID=constant_uuid)
                pin += PinTemplate.format(UUID=b_uuid, LinkStr=LinkedToTemplate.format(b_links_pin_str))
            else:
                exp += InputTemplate.format("Input", linkto_type, linkto_graph, linkto_node)
    
    if node.outputs[0].is_linked:
        for output in linked_info['outputs_uuid']:
            links_pin_str = ''
            for i in range(1, len(output)):
                links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=output[i])
            pin += PinTemplate.format(UUID=output[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    return {"Value": exp, "Pin": pin, "Constant": exp_constants, "Replace": []}

def _gen_node_str(id, node, comment=None) -> str:
    node_expression : str = ""

    names = _get_node_names(id, node)
    graph_name = names[0]
    object_name = names[1]
    node_type = names[2]

    begin_class = "/Script/UnrealEd.MaterialGraphNode"
    if node.type == "REROUTE":
        begin_class += "_Knot"

    NodeNameStr = NameOption.format(object_name)

    #1 Head
    node_expression = HeadTemplate.format(
        ClassOption.format(begin_class),
        NameOption.format(graph_name))

    #2 Head
    node_expression += "\t"
    node_expression += HeadTemplate.format(
        ClassOption.format(node_type),
        NodeNameStr)
    node_expression += "\t"
    node_expression += EndTemplate
    #2 End

    #3 Head
    node_expression += "\t"
    node_expression += HeadTemplate.format(
        "",
        NodeNameStr)

    # todo: fill content by type
    linked_info = _gen_linked_infos(id, node)
    content = { "Value": "", "Pin": "" } 
    replace_pin = []
    # todo: change to swtich
    if node.type == 'RGB':
        content = _exp_rgb(node, linked_info)
    elif node.type == 'VALUE':
        content = _exp_value(node, linked_info)
    elif node.type == 'REROUTE':
        content = _exp_reroute(node, linked_info)
    elif node.type == 'VECT_TRANSFORM':
        content = _exp_vec_transform(node, linked_info)
    elif node.type == 'UVMAP':
        content = _exp_uvmap(node, linked_info)
    elif node.type == 'VERTEX_COLOR':
        content = _exp_vertex_color(node, linked_info)
    elif node.type == 'OBJECT_INFO':
        content = _exp_objinfo(node, linked_info)
    elif node.type == 'CAMERA':
        content = _exp_camera_vector(node, linked_info)
        if content["InsertNames"]:
            node_expression = node_expression.replace(graph_name, content["InsertNames"][0], 1)
    elif node.type == 'TEX_COORD':
        content = _exp_texcoord(node, linked_info)
    elif node.type == 'NEW_GEOMETRY':
        content = _exp_geometry(node, linked_info)
    elif node.type == 'MIX_RGB':
        content = _exp_mix(node, linked_info)
    elif node.type == 'FRESNEL':
        content = _exp_fresnel(node, linked_info)
    elif node.type == 'MATH':
        content = _exp_math(node, linked_info)
    elif node.type == 'VECT_MATH':
        content = _exp_vect_math(node, linked_info)
    elif node.type == 'COMBXYZ' or node.type == 'COMBRGB':
        content = _exp_comb_xyz(node, linked_info)
    elif node.type == 'SEPXYZ' or node.type == 'SEPRGB':
        content = _exp_sep_xyz(node, linked_info)
    elif node.type == 'GAMMA':
        content = _exp_math(node, linked_info, 'POWER')
        comment = "Gamma"

    node_expression += content["Value"]
    

    node_expression += "\t"
    node_expression += EndTemplate
    #3 End

    node_expression += MatExpTemplate.format(node_type, object_name)
    node_expression += NodePosTemplate.format(str(int(node.location.x)), str(int(gl_height - node.location.y)))

    # NodeComment
    if comment != None:
        node_expression += "\tbCommentBubbleVisible=True\n"
        node_expression += "\tNodeComment=\"%s\"\n"%(comment)

    # CustomProperties
    node_expression += content['Pin']

    node_expression += EndTemplate
    #1 End

    for exp_constant in content["Constant"]:
        node_expression = exp_constant + node_expression

    return node_expression, content["Replace"]

def get_ue_mat_str(nodes, height, op=None):
    global gl_uuid_namespace
    global gl_node_map
    global gl_node_socket_map
    global gl_height
    global gl_nodes

    gl_nodes = nodes

    gl_uuid_namespace = uuid.uuid1()
    gl_node_map = {}
    gl_node_socket_map = {}
    gl_height = height

    ue_mat_str = ''

    replace_strs = []
    for idx, node in enumerate(nodes):
        operation = None
        try:
            operation = node.operation
        except:
            pass

        if node.type in NodeClassMap or operation in NodeClassMap:
            mat_str, replace_arr = _gen_node_str(idx, node)
            replace_strs = replace_strs + replace_arr
            ue_mat_str += mat_str
        elif op:
            op.report({'WARNING'}, "%s is not supported, will be skipped."%(node.bl_idname))
    
    gl_nodes = []

    for r in replace_strs:
        old_str = r[0] + " " + r[2]
        new_str = r[1] + " " + r[2]
        ue_mat_str = ue_mat_str.replace(old_str, new_str)
    
    print(ue_mat_str)
    return ue_mat_str