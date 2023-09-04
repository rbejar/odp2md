# A fork of odp2md
Original repository: <https://github.com/seichter/odp2md>.

This script transforms ODP files to Markdown. Although the original intention seemed to be transform Libre/OpenOffice presentations to reveal or beamer presentations, it is now also used to generate mkdocs web sites from lecture notes which originally were in the ODP format.

## Build and use
Possibly you want to create a virtual environment first. After that:
```
pip install .
```

And then you can run it, for example like `python3 ./odp2md/odp2md.py -i PATH_TO_ODP_FILE -x -m > RESULT.md`.

The original odp2md is in PyPi, but this version has a number of modifications and has not been, yet?, published there.

## Copyright and License
&copy; Copyright 2023- Rubén Béjar <https://www.rubenbejar.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This is a derivate work, based on <https://github.com/seichter/odp2md>, &copy; 2019-2021 Hartmut Seichter.


