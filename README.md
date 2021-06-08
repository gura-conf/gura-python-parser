# Gura Python parser

This repository contains the implementation of a [Gura][gura] (compliant with version 1.0.0) format parser in Python.


## Installation

`pip install gura-parser`


## Usage

```python
import gura

gura_string = """
# This is a Gura document.
title: "Gura Example"

an_object:
    username: "Stephen"
    pass: "Hawking"

# Line breaks are OK when inside arrays
hosts: [
  "alpha",
  "omega"
]
"""

# Loads: transforms a Gura string into a dictionary
parsed_gura = gura.loads(gura_string)
print(parsed_gura)  # {'title': 'Gura Example', 'an_object': {'username': 'Stephen', 'pass': 'Hawking'}, 'hosts': ['alpha', 'omega']}

# Access a specific field
print(f"Title -> {parsed_gura['title']}")

# Iterate over structure
for host in parsed_gura['hosts']:
    print(f'Host -> {host}')

# Dumps: transforms a dictionary into a Gura string
print(gura.dumps(parsed_gura))
```


## Contributing

All kind of contribution is welcome! If you want to contribute just:

1. Fork this repository.
1. Create a new branch and introduce there your new changes.
1. Make a Pull Request!


### Tests

To run all the tests: `python -m unittest`. More info in [official Unittest docs][unittest-docs]

[unittest-docs]: https://docs.python.org/3/library/unittest.html#module-unittest
[gura]: https://github.com/gura-conf/gura


### Building

1. Create a virtual environment: `python3 -m venv venv`
1. Activate it: `source venv/bin/activate`
1. Install some dependencies: `pip install -r requirements.txt`
1. Clean and build `rm -rf ./dist/* && python3 setup.py sdist`


## Licence

This repository is distributed under the terms of the MIT license.