from os import link
from random import random
from typing import List
import uuid

NodeClassMap = {
    "VALUE" : "/Script/Engine.MaterialExpressionConstant",
    "RGB" : "/Script/Engine.MaterialExpressionConstant4Vector",
    "RGBA" : "/Script/Engine.MaterialExpressionConstant4Vector",
    "VECTOR" : "/Script/Engine.MaterialExpressionConstant4Vector",
    # Combine
    "COMBXYZ" : "/Script/Engine.MaterialExpressionMaterialFunctionCall",
    "COMBRGB" : "/Script/Engine.MaterialExpressionMaterialFunctionCall",
    # Separate
    "SEPXYZ" : "/Script/Engine.MaterialExpressionMaterialFunctionCall",
    "SEPRGB" : "/Script/Engine.MaterialExpressionMaterialFunctionCall",
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
    "SQRT" : "/Script/Engine.MaterialExpressionSquareRoot",
	"ABSOLUTE" : "/Script/Engine.MaterialExpressionAbs",
	"ROUND" : "/Script/Engine.MaterialExpressionRound",
	"FLOOR" : "/Script/Engine.MaterialExpressionFloor",
	"CEIL" : "/Script/Engine.MaterialExpressionCeil",
	"FRACT" : "/Script/Engine.MaterialExpressionFrac",
	"SINE" : "/Script/Engine.MaterialExpressionSine",
	"COSINE" : "/Script/Engine.MaterialExpressionCosine",
	"TANGENT" : "/Script/Engine.MaterialExpressionTangent",
	"ARCSINE" : "/Script/Engine.MaterialExpressionArcsineFast",
	'ARCCOSINE': "/Script/Engine.MaterialExpressionArccosineFast",
	"ARCTANGENT" : "/Script/Engine.MaterialExpressionArctangentFast",
	"SIGN" : "/Script/Engine.MaterialExpressionSign",
	"TRUNC" : "/Script/Engine.MaterialExpressionTruncate",
    # Vector Math Two Input
    "CROSS_PRODUCT" : "/Script/Engine.MaterialExpressionCrossProduct",
    "DOT_PRODUCT": "/Script/Engine.MaterialExpressionDotProduct",
    "DISTANCE" : "/Script/Engine.MaterialExpressionDistance",
    "SCALE" : "/Script/Engine.MaterialExpressionMultiply",
    # Vector Math One Input
    "NORMALIZE" : "/Script/Engine.MaterialExpressionNormalize",
    "LENGTH" : "/Script/Engine.MaterialExpressionDistance",
}

NodeNameMap = {
    # Constant
    "VALUE" : "MaterialExpressionConstant",
    "RGB" : "MaterialExpressionConstant4Vector",
    "RGBA" : "MaterialExpressionConstant4Vector",
    "VECTOR" : "MaterialExpressionConstant4Vector",
    # Combine
    "COMBXYZ" : "MaterialExpressionMaterialFunctionCall",
    "COMBRGB" : "MaterialExpressionMaterialFunctionCall",
    # Separate
    "SEPXYZ" : "MaterialExpressionMaterialFunctionCall",
    "SEPRGB" : "MaterialExpressionMaterialFunctionCall",
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
    "SQRT": "MaterialExpressionSquareRoot",
	"ABSOLUTE": "MaterialExpressionAbs",
	"ROUND": "MaterialExpressionRound",
	"FLOOR": "MaterialExpressionFloor",
	"CEIL": "MaterialExpressionCeil",
	"FRACT": "MaterialExpressionFrac",
	"SINE": "MaterialExpressionSine",
	"COSINE": "MaterialExpressionCosine",
	"TANGENT": "MaterialExpressionTangent",
	"ARCSINE": "MaterialExpressionArcsineFast",
	"ARCCOSINE": "MaterialExpressionArccosineFast",
	"ARCTANGENT": "MaterialExpressionArctangentFast",
	"SIGN": "MaterialExpressionSign",
	"TRUNC": "MaterialExpressionTruncate",
    # Vector Math Two Input
    "CROSS_PRODUCT" : "MaterialExpressionCrossProduct",
    "DOT_PRODUCT": "MaterialExpressionDotProduct",
    "DISTANCE" : "MaterialExpressionDistance",
    "SCALE" : "MaterialExpressionMultiply",
    # Vector Math One Input
    "NORMALIZE" : "MaterialExpressionNormalize",
    "LENGTH" : "MaterialExpressionDistance",
}

GlobalName = "MaterialGraphNode_{}"
ClassOption = "Class={}"
NameOption = 'Name="{}"'
HeadTemplate = 'Begin Object {} {}\n'
EndTemplate = 'End Object\n'
MatExpTemplate = "\tMaterialExpression={}\'\"{}\"\'\n"
NodePosTemplate = "\tNodePosX={}\n\tNodePosY={}\n"

MatFuncTemplate = "\t\tMaterialFunction=MaterialFunction\'\"{}\"\'\n"
FuncInputTemplate = "\t\tFunctionInputs({})=({})\n"
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

        gragh_name = GlobalName.format(str(id))
        node_name = node_type + '_' + str(id)

        gl_node_map[node] = [gragh_name, node_name, node_type].copy()

    return gl_node_map[node]

# 返回 按照inputs排序
# from node对应的graphname和nodename
# socket 对应的 pin uuid
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
                uuid_name = 'input' + node.name + input.identifier
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
                uuid_name = 'output' + node.name + output.identifier
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
                
def _exp_constant(type, value, linkto_names, linkto_uuid, location):
    node_expression : str = ""

    gragh_name = GlobalName.format(str(int(random()*1000) + int(random()*999)))
    node_type = NodeNameMap[type]
    object_name = node_type + '_' + str(int(random()*99))

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

    # todo: change to swtich
    if type == 'RGB' or type == 'RGBA':
        node_expression += "\t\tConstant=(R=%.6f,G=%.6f,B=%.6f,A=%.6f)\n"%tuple(value)
    if type == 'VECTOR':
        node_expression += "\t\tConstant=(R=%.6f,G=%.6f,B=%.6f,A=1.0)\n"%tuple(value)
    if type == 'VALUE':
        node_expression += "\t\tR=%.6f\n"%(value)
    

    node_expression += "\t"
    node_expression += EndTemplate
    #3 End

    node_expression += MatExpTemplate.format(node_type, object_name)
    node_expression += NodePosTemplate.format(str(int(location.x-60)), str(int(gl_height - location.y)))

    # CustomProperties
    output_uuid = get_uuid(gragh_name + object_name)
    links_pin_str = LinkTemplate.format(Graph=linkto_names[0], UUID=linkto_uuid)
    node_expression += PinTemplate.format(UUID=output_uuid, LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    node_expression += EndTemplate
    #1 End

    return node_expression, [gragh_name, object_name, node_type], output_uuid

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
        return { "Value": "\t\tConstant=(R=%.6f,G=%.6f,B=%.6f,A=%.6f)\n"%tuple(value), "Pin": pin, "Constant":[] } 

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
        return { "Value": "\t\tR=%.6f\n"%(value), "Pin": pin, "Constant":[] }

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

    return {"Value": exp, "Pin": pin, "Constant": exp_constants}

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
            links_pin_str += LinkTemplate.format(Graph=linked_info['node_names'][1][j][0], UUID=outputs[j])
        pin += PinTemplate.format(UUID=outputs[0], LinkStr='Direction="EGPD_Output",' + LinkedToTemplate.format(links_pin_str))

    return {"Value": exp, "Pin": pin, "Constant": exp_constants}

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

def _exp_math(node, linked_info):
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

    return {"Value": exp, "Pin": pin, "Constant": exp_constants}

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

def _exp_vect_math(node, linked_info):
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

    return {"Value": exp, "Pin": pin, "Constant": exp_constants}

def _gen_node_str(id, node) -> str:
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
    content = { "Value": "", "Pin": "" } 
    # todo: change to swtich
    if node.type == 'RGB':
        content = _exp_rgb(node, linked_info)
    elif node.type == 'VALUE':
        content = _exp_value(node, linked_info)
    elif node.type == 'MATH':
        content = _exp_math(node, linked_info)
    elif node.type == 'VECT_MATH':
        content = _exp_vect_math(node, linked_info)
    elif node.type == 'COMBXYZ' or node.type == 'COMBRGB':
        content = _exp_comb_xyz(node, linked_info)
    elif node.type == 'SEPXYZ' or node.type == 'SEPRGB':
        content = _exp_sep_xyz(node, linked_info)

    node_expression += content["Value"]
    

    node_expression += "\t"
    node_expression += EndTemplate
    #3 End

    node_expression += MatExpTemplate.format(node_type, object_name)
    node_expression += NodePosTemplate.format(str(int(node.location.x)), str(int(gl_height - node.location.y)))

    # CustomProperties
    node_expression += content['Pin']

    node_expression += EndTemplate
    #1 End
    
    # except KeyError as ke:
    #     # todo: warning node type not surpport
    #     print(str(ke) + node.get_type())
    
    # finally:

    for exp_constant in content["Constant"]:
        node_expression = exp_constant + node_expression

    return node_expression

def get_ue_mat_str(nodes, height, op=None):
    global gl_uuid_namespace
    global gl_node_map
    global gl_node_socket_map
    global gl_height

    gl_uuid_namespace = uuid.uuid1()
    gl_node_map = {}
    gl_node_socket_map = {}
    gl_height = height

    ue_mat_str = ''
    for idx, node in enumerate(nodes):
        if node.type in NodeClassMap or node.operation in NodeClassMap:
            ue_mat_str += _gen_node_str(idx, node)
        elif op:
            op.report({'WARNING'}, "%s is not supported, will be skipped."%(node.bl_idname))
    
    print(ue_mat_str)
    return ue_mat_str