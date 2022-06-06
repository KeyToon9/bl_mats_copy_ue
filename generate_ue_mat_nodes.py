from typing import List
import uuid

NodeClassMap = {
    "VALUE" : "/Script/Engine.MaterialExpressionConstant",
    "RGB" : "/Script/Engine.MaterialExpressionConstant4Vector",
    # Math Node Two Input
    "ADD" : "/Script/Engine.MaterialExpressionAdd",
    "SUBTRACT" : "/Script/Engine.MaterialExpressionSubtract",
    "MULTIPLY" : "/Script/Engine.MaterialExpressionMultiply",
    "DIVIDE" : "/Script/Engine.MaterialExpressionDivide",
    "POWER" : "/Script/Engine.MaterialExpressionPower",
    "MINIMUM" : "/Script/Engine.MaterialExpressionMin",
    "MAXIMUM" : "/Script/Engine.MaterialExpressionMax",
    "MODULO" : "/Script/Engine.MaterialExpressionFmod",
    "ARCTAN2" : "/Script/Engine.MaterialExpressionArctangent2Fast",
    # Math Node One Input
    'SQRT': "/Script/Engine.MaterialExpressionSquareRoot",
	'ABSOLUTE': "/Script/Engine.MaterialExpressionAbs",
	'ROUND': "/Script/Engine.MaterialExpressionRound",
	'FLOOR': "/Script/Engine.MaterialExpressionFloor",
	'CEIL': "/Script/Engine.MaterialExpressionCeil",
	'FRACT': "/Script/Engine.MaterialExpressionFrac",
	'SINE': "/Script/Engine.MaterialExpressionSine",
	'COSINE': "/Script/Engine.MaterialExpressionCosine",
	'TANGENT': "/Script/Engine.MaterialExpressionTangent",
	'ARCSINE': "/Script/Engine.MaterialExpressionArcsineFast",
	'ARCCOSINE': "/Script/Engine.MaterialExpressionArccosineFast",
	'ARCTANGENT': "/Script/Engine.MaterialExpressionArctangentFast",
	'SIGN': "/Script/Engine.MaterialExpressionSign",
	'TRUNC': "/Script/Engine.MaterialExpressionTruncate",
}

NodeNameMap = {
    # Constant
    "VALUE" : "MaterialExpressionConstant",
    "RGB" : "MaterialExpressionConstant4Vector",
    # Math Node Two Input
    "ADD" : "MaterialExpressionAdd",
    "SUBTRACT" : "MaterialExpressionSubtract",
    "MULTIPLY" : "MaterialExpressionMultiply",
    "DIVIDE" : "MaterialExpressionDivide",
    "POWER" : "MaterialExpressionPower",
    "MINIMUM" : "MaterialExpressionMin",
    "MAXIMUM" : "MaterialExpressionMax",
    "MODULO" : "MaterialExpressionFmod",
    "ARCTAN2" : "MaterialExpressionArctangent2Fast",
    # Math Node One Input
    'SQRT': "MaterialExpressionSquareRoot",
	'ABSOLUTE': "MaterialExpressionAbs",
	'ROUND': "MaterialExpressionRound",
	'FLOOR': "MaterialExpressionFloor",
	'CEIL': "MaterialExpressionCeil",
	'FRACT': "MaterialExpressionFrac",
	'SINE': "MaterialExpressionSine",
	'COSINE': "MaterialExpressionCosine",
	'TANGENT': "MaterialExpressionTangent",
	'ARCSINE': "MaterialExpressionArcsineFast",
	'ARCCOSINE': "MaterialExpressionArccosineFast",
	'ARCTANGENT': "MaterialExpressionArctangentFast",
	'SIGN': "MaterialExpressionSign",
	'TRUNC': "MaterialExpressionTruncate",
}

GlobalName = "MaterialGraphNode_{}"
ClassOption = "Class={}"
NameOption = 'Name="{}"'
HeadTemplate = 'Begin Object {} {}\n'
EndTemplate = 'End Object\n'
MatExpTemplate = "\tMaterialExpression={}\'\"{}\"\'\n"
NodePosTemplate = "\tNodePosX={}\n\tNodePosY={}\n"

InputTemplate = "\t\t{}=(Expression={}\'\"{}.{}\"\')\n"
MatContentExpTemplate = "Expression={Type}\'\"{Graph}.{Name}\"\'"
LinkTemplate = "{Graph} {UUID},"
LinkedToTemplate = "LinkedTo=({}),"
PinTemplate = "\tCustomProperties Pin (PinId={UUID},{LinkStr})\n"

gl_uuid_namespace = uuid.uuid1()

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

        gragh_name = GlobalName.format(str(id))
        node_name = node_type + '_' + str(id)

        gl_node_map[node] = [gragh_name, node_name, node_type].copy()

    return gl_node_map[node]

# 返回 按照inputs排序
# from node对应的graphname和nodename
# socket 对应的 pin uuid
# todo: 不应该把没链接的也放进来
def _gen_linked_infos(id, node):
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
                uuid_name = node.name + input.identifier
                pin_uuid = get_uuid(uuid_name)
                gl_node_socket_map[input] = pin_uuid
            else:
                pin_uuid = gl_node_socket_map[input]
            pin_info.append(pin_uuid)
            # 目前算法只考虑了一个节点输出一次，没有考虑一个节点输出多条路
            # 所以目前先只写了input
            # process input linked socket
            if input.is_linked:
                for link in input.links:
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
                    
                ret_input_pins_uuid.append(pin_info)

            # constant value input
            else:
                # if contant, will create a new contant value node in ue
                ret_in_node_names.append('_CONSTANT_')
        
    # todo: outputs 要去ue里看看一个节点多个输出的pin是怎么样的
    for output in node.outputs:
        # only export linked output socket
        if output.enabled:
            pin_info = []
            # get current socket pin uuid
            pin_uuid = ''
            if not output in gl_node_socket_map:
                uuid_name = node.name + output.identifier
                pin_uuid = get_uuid(uuid_name)
                gl_node_socket_map[output] = pin_uuid
            else:
                pin_uuid = gl_node_socket_map[output]
            pin_info.append(pin_uuid)

            if output.is_linked:
                for link in output.links:
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
                    
            ret_output_pins_uuid.append(pin_info)
    
    # print(ret_node_names)
    # print(ret_input_pins_uuid)
    # print(ret_output_pins_uuid)
    return {'node_names': [ret_in_node_names, ret_out_node_names], 'inputs_uuid': ret_input_pins_uuid, 'outputs_uuid': ret_output_pins_uuid}
                

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
        return { "Value": "\t\tConstant=(R=%.6f,G=%.6f,B=%.6f,A=%.6f)\n"%tuple(value), "Pin": pin } 

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
        return { "Value": "\t\tR=%.6f\n"%(value), "Pin": pin }

# A B
Math_Two_NodeClassMap = {
    "ADD" : "/Script/Engine.MaterialExpressionAdd",
    "SUBTRACT" : "/Script/Engine.MaterialExpressionSubtract",
    "MULTIPLY" : "/Script/Engine.MaterialExpressionMultiply",
    "DIVIDE" : "/Script/Engine.MaterialExpressionDivide",
    "POWER" : "/Script/Engine.MaterialExpressionPower",
    "MINIMUM" : "/Script/Engine.MaterialExpressionMin",
    "MAXIMUM" : "/Script/Engine.MaterialExpressionMax",
    "MODULO" : "/Script/Engine.MaterialExpressionFmod",
    # You can change to normal node
    "ARCTAN2" : "/Script/Engine.MaterialExpressionArctangent2Fast",
}

# Input
Math_One_NodeClassMap = {
	'SQRT': "/Script/Engine.MaterialExpressionSquareRoot",
	'ABSOLUTE': "/Script/Engine.MaterialExpressionAbs",
	'ROUND': "/Script/Engine.MaterialExpressionRound",
	'FLOOR': "/Script/Engine.MaterialExpressionFloor",
	'CEIL': "/Script/Engine.MaterialExpressionCeil",
	'FRACT': "/Script/Engine.MaterialExpressionFrac",
	'SINE': "/Script/Engine.MaterialExpressionSine",
	'COSINE': "/Script/Engine.MaterialExpressionCosine",
	'TANGENT': "/Script/Engine.MaterialExpressionTangent",
    # You can change to normal node
	'ARCSINE': "/Script/Engine.MaterialExpressionArcsineFast",
	'ARCCOSINE': "/Script/Engine.MaterialExpressionArccosineFast",
	'ARCTANGENT': "/Script/Engine.MaterialExpressionArctangentFast",
	'SIGN': "/Script/Engine.MaterialExpressionSign",
	'TRUNC': "/Script/Engine.MaterialExpressionTruncate",
}

def _exp_math(node, linked_info):
    op = node.operation
    exp = ''
    pin = ''
    if op in Math_Two_NodeClassMap:
        for i, inputs in enumerate(linked_info['inputs_uuid']):
            links_pin_str = ''
            if linked_info['node_names'][0][i] == '_CONSTANT_':
                # todo: 如果没有输入，是个常量，则需要新建一个常量节点
                pass
            else:
                if i == 0:
                    exp += InputTemplate.format("A", linked_info['node_names'][0][i][2], linked_info['node_names'][0][i][0], linked_info['node_names'][0][i][1])
                else:
                    exp += InputTemplate.format("B", linked_info['node_names'][0][i][2], linked_info['node_names'][0][i][0], linked_info['node_names'][0][i][1])
                
                for j in range(1, len(inputs)):
                    links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][0][i][0], UUID=inputs[j])
                pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))

    elif op in Math_One_NodeClassMap:
        for i, inputs in enumerate(linked_info['inputs_uuid']):
            links_pin_str = ''
            if linked_info['node_names'][0][i] == '_CONSTANT_':
                # todo: 如果没有输入，是个常量，则需要新建一个常量节点
                pass
            else:
                exp += InputTemplate.format("Input", linked_info['node_names'][0][i][2], linked_info['node_names'][0][i][0], linked_info['node_names'][0][i][1])

            for j in range(1, len(inputs)):
                    links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][0][i][0], UUID=inputs[j])
            pin += PinTemplate.format(UUID=inputs[0], LinkStr=LinkedToTemplate.format(links_pin_str))
    
    if node.outputs[0].is_linked:
        for output in linked_info['outputs_uuid']:
            links_pin_str = ''
            for i in range(1, len(output)):
                links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][i-1][0], UUID=output[i])
            pin += PinTemplate.format(UUID=output[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    return {"Value": exp, "Pin": pin}


def _gen_node_str(id, node, height) -> str:
    node_expression : str = ""
    # try:
    names = _get_node_names(id, node)
    gragh_name = names[0]
    object_name = names[1]
    node_type = names[2]

    NodeNameStr = NameOption.format(object_name)

    #1 Head
    node_expression = HeadTemplate.format(
        ClassOption.format("/Script/UnrealEd.MaterialGraphNode"),
        NameOption.format(gragh_name))

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
    content = None
    # todo: change to swtich
    if node.type == 'RGB':
        content = _exp_rgb(node, linked_info)
    if node.type == 'VALUE':
        content = _exp_value(node, linked_info)
    if node.type == 'MATH':
        content = _exp_math(node, linked_info)

    node_expression += content["Value"]
    

    node_expression += "\t"
    node_expression += EndTemplate
    #3 End

    node_expression += MatExpTemplate.format(node_type, object_name)
    node_expression += NodePosTemplate.format(str(int(node.location.x)), str(int(height - node.location.y)))

    # CustomProperties
    node_expression += content['Pin']

    node_expression += EndTemplate
    #1 End
    
    # except KeyError as ke:
    #     # todo: warning node type not surpport
    #     print(str(ke) + node.get_type())
    
    # finally:

    return node_expression

def get_ue_mat_str(nodes, height):
    global gl_uuid_namespace
    global gl_node_map
    global gl_node_socket_map

    gl_uuid_namespace = uuid.uuid1()
    gl_node_map = {}
    gl_node_socket_map = {}

    ue_mat_str = ''
    for idx, node in enumerate(nodes):
        ue_mat_str += _gen_node_str(idx, node, height)
    
    print(ue_mat_str)
    return ue_mat_str