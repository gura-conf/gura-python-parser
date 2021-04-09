import unittest
from typing import Dict
from gura_parser import GuraParser
import math
import os


class TestFullGura(unittest.TestCase):
    content: str
    parser: GuraParser
    parsed_data: Dict

    def setUp(self):
        file_dir = os.path.dirname(os.path.abspath(__file__))
        full_test_path = os.path.join(file_dir, 'tests-files/full.ura')
        with open(full_test_path, 'r') as file:
            self.content = file.read()
        self.parser = GuraParser()
        self.parsed_data = self.parser.parse(self.content)
        self.maxDiff = 4096

    def test_loads(self):
        target_dir = {
            "a_string": "test string",
            "int1": +99,
            "int2": 42,
            "int3": 0,
            "int4": -17,
            "int5": 1000,
            "int6": 5349221,
            "int7": 5349221 ,
            "hex1": 3735928559,
            "hex2": 3735928559,
            "hex3": 3735928559,
            "oct1": 342391,
            "oct2": 493,
            "bin1": 214,
            "flt1": +1.0,
            "flt2": 3.1415,
            "flt3": -0.01,
            "flt4": 5e+22,
            "flt5": 1e06,
            "flt6": -2E-2,
            "flt7": 6.626e-34,
            "flt8": 224617.445991228,
            "sf1": math.inf,
            "sf2": math.inf,
            "sf3": -math.inf,
            "sf4": math.nan,
            "sf5": math.nan,
            "sf6": -math.nan,
            "bool1": True,
            "bool2": False,
            "services": {
                "nginx": {
                    "host": "127.0.0.1",
                    "port": 80
                },
                "apache": {
                    "virtual_host": "10.10.10.4",
                    "port": 81
                }
            },
            "integers": [ 1, 2, 3 ],
            "colors": [ "red", "yellow", "green" ],
            "nested_arrays_of_ints": [ [ 1, 2 ], [3, 4, 5] ],
            "nested_mixed_array": [ [ 1, 2 ], ["a", "b", "c"] ],
            "numbers": [ 0.1, 0.2, 0.5, 1, 2, 5 ],
            "tango_singers": [
                {
                    "user1": {
                        "name": "Carlos",
                        "surname": "Gardel",
                        "year_of_birth": 1890
                    }
                }, {
                    "user2": {
                        "name": "Aníbal",
                        "surname": "Troilo",
                        "year_of_birth": 1914
                    }
                }
            ],
            "integers2": [
              1, 2, 3
            ],
            "integers3": [
              1,
              2
            ],
            "my_server": {
                "host": "127.0.0.1",
                "port": 8080,
                "native_auth": True
            },
            "gura_is_cool": "Gura is cool"
        }
        self.assertDictEqual(self.parsed_data, target_dir)

    def test_dumps(self):
        # string_data = self.parser.dumps(self.content)
        pass


if __name__ == '__main__':
    unittest.main()
