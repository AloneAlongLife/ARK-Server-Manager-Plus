from copy import deepcopy
from typing import Any, Union

import orjson

class json:
    def dumps(data) -> str:
        return deepcopy(orjson.dumps(data, option=orjson.OPT_INDENT_2).decode('utf-8'))
    
    def loads(data: Union[bytes, bytearray, memoryview, str]) -> Any:
        return deepcopy(orjson.loads(data))

    def dump(file: str, data):
        # print(f'Write Data:{data}')
        with open(file, mode='wb') as in_file:
            in_file.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
            in_file.close()

    def load(file: str) -> Any:
        with open(file, mode='r') as in_file:
            data = in_file.read()
            in_file.close()
        return deepcopy(orjson.loads(data))
