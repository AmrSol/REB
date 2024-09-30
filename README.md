# REB
This repository contains the codebase and data for the publication "Data-driven revenue characterisation and analysis of Long-Haul Low-Cost Carriers in the Southeast Asian market". 

# Code Philosophy
This version of this repo is a complete rework of the original code.
The first version was my first ever attempt at coding python and as a consequence it was slow, convoluted and messy.
This version follow object-oriented principles.
I highly recommend the book "Clean Code in Python" by Mariano Anaya.
If you are new to programming and have coded multiple projects for more than a year then it will greatly help you understand OOP and SOLID.

Following OOP, this code is structure in such a way that it is accessed as a library.
For the time being you will have to clone this repo and run the following command: ` pip install -e . `
This command installs `milap` as a package on your local system.

`milap` contains multiple modules/scripts.

`constants` contain all the constants.

`csvloader` handles all the csv imports depending on which database you downloaded your data from, i.e. OAG, Sabre MIDT, AirportIS, etc...

`pandastools` contains custom pandas functions that have been factored out as they are repeatedly used throughout the codebase.

`revenue` contains the classes relevant to REB calculations.
It starts off with the `RebDataContainer` object that is initialised with either `DataFrameLoader` or `DataFrameFolderLoader` objects.
Then `RebCalculator` calculates REB and saves all relevant information in the relevant object attributes.
Finally, `RebPlotter` plots the figures needed to visualise REB performance in the market.


## Instructions 
1. Clone repository.
2. Execute ` pip install -e . ` to install the milap package that contains the REB calculating classes.
3. Open main.py and run.

For now, this REB script works only for the data found in this repository. 
A future version will be developed to calculate REB on any data given.

The previous version (Old version directory) of this codebase produced all figures while this new version only produces the city-pair figures. 

This version is a restructured and refactored version that is easier to read, use, and performs at least an order of magnitude faster.

## License 
MIT License

Copyright (c) 2024 Amr Soliman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

- The software is used for academic purposes. 
- If the software is needed for commercial purposes, permission must be sought from the author of the software, Amr Soliman (@AmrSol)

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
