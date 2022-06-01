from typing import List
import uuid

NodeClassMap = {
    "VALUE" : "/Script/Engine.MaterialExpressionConstant",
    "RGB" : "/Script/Engine.MaterialExpressionConstant4Vector",
}

NodeNameMap = {
    # Constant
    "VALUE" : "MaterialExpressionConstant",
    "RGB" : "MaterialExpressionConstant4Vector",
    # Math Node Two Input
    "MULTIPLY" : "MaterialExpressionMultiply",
}

Math_Two_NodeClassMap = {
    "MULTIPLY" : "/Script/Engine.MaterialExpressionMultiply",
}

GlobalName = "MaterialGraphNode_{}"
ClassOption = "Class={}"
NameOption = 'Name="{}"'
HeadTemplate = 'Begin Object {} {}\n'
EndTemplate = 'End Object\n'
MatExpTemplate = "\tMaterialExpression={}\'\"{}\"\'\n"
NodePosTemplate = "\tNodePosX={}\n\tNodePosY={}\n"

MatContentExpTemplate = "Expression={Type}\'\"{Graph}.{Name}\"\'"
LinkTemplate = "{Graph} {UUID},"
LinkedToTemplate = "LinkedTo=({}),"
PinTemplate = "CustomProperties Pin (PinId={UUID},{LinkStr})"

gl_uuid_namespace = uuid.uuid1()

def get_uuid(name) -> str:
    global gl_uuid_namespace
    return str(uuid.uuid3(namespace=gl_uuid_namespace, name=name).hex).upper()

# todo: 要返回两个值，一个具体数值，一个是pin连接信息

gl_node_map = {}
gl_node_socket_map = {}

def _get_node_names(id, node) -> List[str]:
    node_type = ""
    if (node.type in NodeClassMap):
        node_type = NodeNameMap[node.type]
        
    gragh_name = GlobalName.format(str(id))
    node_name = node_type + '_' + str(id)

    return [gragh_name, node_name]

# 返回 按照inputs排序
# from node对应的graphname和nodename
# socket 对应的 pin uuid
def _gen_linked_infos(id, node):
    global gl_node_map
    global gl_node_socket_map

    ret_node_names = []
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
                        to_node_names = _get_node_names(id, link.from_node)
                        id += 1
                        gl_node_map[link.from_node] = to_node_names.copy()
                    else:
                        to_node_names = gl_node_map[link.from_node]
                    ret_node_names.append(to_node_names)

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
                ret_node_names.append('_CONSTANT_')
        
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
                        to_node_names = _get_node_names(id, link.to_node)
                        id += 1
                        gl_node_map[link.to_node] = to_node_names.copy()
                    else:
                        to_node_names = gl_node_map[link.to_node]
                    ret_node_names.append(to_node_names)

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
    
    print(ret_node_names)
    print(ret_input_pins_uuid)
    print(ret_output_pins_uuid)
    return {'node_names': ret_node_names, 'inputs_uuid': ret_input_pins_uuid, 'outputs_uuid': ret_output_pins_uuid}
                

def _exp_rgb(node):
    # if not node.get_out_nodes()[0].is_linked:
        value = node.outputs[0].default_value
        pin = ""
        if node.outputs[0].is_linked:
            pass
        return { "Value": "Constant=(R=%.6f,G=%.6f,B=%.6f,A=%.6f)\n"%tuple(value), "Pin": "" } 

def _exp_value(node):
    # if not node.get_out_nodes()[0].is_linked:
        value = node.outputs[0].default_value
        return { "Value": "R=%.6f\n"%(value), "Pin": "" }

def _exp_math(node):
    op = node.operation
    exp = None

    if op in Math_Two_NodeClassMap:
        pass


def _gen_node_str(id, node, height) -> str:
    node_expression : str = ""
    try:
        node_type = ""
        if (node.type in NodeClassMap):
            node_type = NodeNameMap[node.type]
        
        ObjectName = node_type + '_' + str(id)
        GraghNodeName = GlobalName.format(str(id))

        NodeNameStr = NameOption.format(ObjectName)

        #1 Head
        node_expression = HeadTemplate.format(
            ClassOption.format("/Script/UnrealEd.MaterialGraphNode"),
            NameOption.format(GraghNodeName))

        #2 Head
        node_expression += "\t"
        node_expression += HeadTemplate.format(
            ClassOption.format(NodeClassMap[node.type]),
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
        node_expression += "\t\t"
        if node.type == 'RGB':
            node_expression += _exp_rgb(node)["Value"]
        if node.type == 'VALUE':
            node_expression += _exp_value(node)["Value"]
        

        node_expression += "\t"
        node_expression += EndTemplate
        #3 End

        node_expression += MatExpTemplate.format(node_type, ObjectName)
        node_expression += NodePosTemplate.format(str(int(node.location.x)), str(int(height - node.location.y)))

        node_expression += EndTemplate
        #1 End
    
    except KeyError as ke:
        # todo: warning node type not surpport
        print(str(ke) + node.get_type())
    
    finally:
        return node_expression

def get_ue_mat_str(nodes, height):
    global gl_uuid_namespace
    global gl_node_map
    global gl_node_socket_map

    gl_uuid_namespace = uuid.uuid1()
    gl_node_map = {}
    gl_node_socket_map = {}
    for idx, node in enumerate(nodes):
        print(_gen_node_str(idx, node, height))
        _gen_linked_infos(idx, node)
        pass