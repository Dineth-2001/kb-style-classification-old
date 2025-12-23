from pydantic import BaseModel
from typing import List


class OperationData(BaseModel):
    operation_name: str
    machine_name: str
    sequence_number: int


def sort_ob_data(operation_data: List[OperationData]):
    # Sort operation data by sequence number
    sorted_operation_data = sorted(operation_data, key=lambda x: x.sequence_number)
    return sorted_operation_data


def get_operation_machine_list(operation_data):
    # Create a list of tuples containing operation name and machine name
    sorted_operation_data = sort_ob_data(operation_data)
    operation_machine_list = [
        (data.operation_name, data.machine_name) for data in sorted_operation_data
    ]
    return operation_machine_list


def get_operation_machine_list_db(operation_data):
    # Create a list of tuples containing operation name and machine name from the database records
    return [(data[0], data[1]) for data in sorted(operation_data, key=lambda x: x[2])]
