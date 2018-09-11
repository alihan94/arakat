from domain.ErrorTypes import ErrorTypes
import TaskPreprocessor
from domain import ImportInfo, DomainUtils
from utils import GeneralUtils

import copy
import os

# No need to keep data/state, so I did not make it a class..
# This will be safe for multi-thread use as well~

def generate_code(graph):
    # Get task_args from task node itself
    dependents_info, requireds_info, waiting_queue = TaskPreprocessor.preprocess_graph(graph)
    requireds_info_clone=copy.deepcopy(requireds_info)
    generation_order, error_code = TaskPreprocessor.determine_generation_order(dependents_info, requireds_info_clone, waiting_queue)

    task_code = []
    errors=[]
    if(error_code == ErrorTypes.NO_ERROR):
        task_code.extend(__generate_initialization_codes(graph))
        task_code.append(os.linesep)
        code, errors = __generate_remaining_codes(generation_order, requireds_info, graph)
        task_code.extend(code)

    return task_code, errors

def __generate_initialization_codes(graph):
    # graph is the task node itself

    initialization_code=["from pyspark import SparkContext", os.linesep, "from pyspark.sql import SparkSession", os.linesep]
    # Maybe improve the following in the future...
    initialization_code.extend(["from pyspark.sql.types import *", os.linesep])

    import_set=set()
    for node_id in graph["nodes"]:
        import_statements_for_node=ImportInfo.get_import_statements(graph["nodes"][node_id])
        for elem in import_statements_for_node:
            import_set.add(elem)

    for statement in import_set:
        initialization_code.extend([statement, os.linesep])

    initialization_code.append(os.linesep)

    initialization_code.extend(['sc = SparkContext(appName="'+graph["app_id"] + '_Task_' + graph["id"] + '")', os.linesep])
    initialization_code.extend(['spark = SparkSession(sc)', os.linesep, os.linesep])

    return initialization_code

def __generate_remaining_codes(generation_order, requireds_info, graph):
    code=[]
    errors=[]
    for elem in generation_order:
        cur_code, error=GeneralUtils.call_function_by_name("pipeline_generator.family_base."+DomainUtils.get_node_family_name(graph["nodes"][elem]["family"]), "generate_code", {"node": graph["nodes"][elem], "requireds_info": requireds_info, "edges": graph["edges"]})
        if(error == ErrorTypes.NO_ERROR):
            code.extend(cur_code)
        else:
            errors.append(error)

    # Do not break to capture all errors...
    return code, errors
