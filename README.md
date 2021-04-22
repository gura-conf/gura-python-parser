# Gura parser

This repository contains the implementation of a [Gura][gura] format parser in Python.


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

parsed_Gura = gura.loads(gura_string)

# Loads: transforms a Gura string into a dictionary
print(parsed_Gura)  # {'title': 'Gura Example', 'an_object': {'username': 'Stephen', 'pass': 'Hawking'}, 'hosts': ['alpha', 'omega']}

# Dumps: transforms a dictionary into a Gura string
print(gura.dumps(parsed_Gura))
```


## Contributing

All kind of contribution is welcome! **This is the first parser I've ever done.** So there are probably a lot of things that could be done in a better way.

There are some TODOs in mind to complete:

- [ ] Add line and position in semantics errors (like InvalidIndentationError) messages.
- [ ] Replace `getattr` in `match()` method for a tuple of Callable objects to make the code more typed.
- [ ] Add some more tests.


### Tests

To run all the tests: `python -m unittest`. More info in [official Unittest docs][unittest-docs]

[unittest-docs]: https://docs.python.org/3/library/unittest.html#module-unittest
[gura]: https://github.com/jware-solutions/gura


## Licence

This repository is distributed under the terms of the MIT license.