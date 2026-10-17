# -*- coding: utf-8 -*-
"""
Endo-concept generation subpackage.

Implements the endogenous concept-generation mechanism described in
the task report, entirely on top of the two postulates of the
original one-order cognitive graph:

    P1. A cognitive state is a dynamic network.
    P2. Evolution is driven by energy minimization.

The mechanism adds NO new assumption. It only observes the compression
events produced by the first-order system and turns them into:

    - fixpoint clusters        (fixpoint.py)
    - directed logic edges     (logic_derive.py)
    - boundary characterization(boundary.py)
    - structured definitions   (structure.py)
    - multi-channel init       (multichannel.py)
    - high-order internalization(high_order.py)
"""