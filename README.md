bio-graph-infer
===============

A Tool for Biological Network Inference using Probabilistic Graphical Models

The currently supported PGM "engine" is:

	https://staff.fnwi.uva.nl/j.m.mooij/libDAI/doc/fileformats.html
	
I'm including a compiled version of this C++ library. This project includes a Python library
to train and evaluate probabilistic graphical models from subnetworks generated by the 
TieDIE method (github.com/epaull/TieDIE) and other small to medium sized networks. A cross-validation
framework is used to evalute fitted models, as is a null model based on random rewiring of the 
input networks. 
