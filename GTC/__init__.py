"""
A Python package for evaluating measurement uncertainty 
in real and complex quantities.

The method of uncertainty propagation is compatible with the approach described 
in the 'Guide to the Expression of Uncertainty in Measurement' - the GUM.

Copyright (c) 2018, Measurement Standards Laboratory of New Zealand.

"""
from __future__ import division

import math
import cmath
import collections

#----------------------------------------------------------------------------
# Global constants, etc

# The degrees of freedom is considered infinite above `inf_dof`
inf_dof = 1E5               

inf = float('inf')
nan = float('nan') 

is_infinity = math.isinf 
is_undefined = math.isnan

LOG10_E = math.log10(math.e)

# Do not consider strings as sequences
def is_sequence(obj):
    if isinstance(obj, basestring):
        return False
    return isinstance(obj, collections.Sequence)
    
#----------------------------------------------------------------------------

__all__ = (
        'ureal'
    ,   'multiple_ureal'
    ,   'multiple_ucomplex'
    ,   'ucomplex'
    ,   'constant'
    ,   'value'
    ,   'uncertainty'
    ,   'variance'
    ,   'dof'
    ,   'label'
    ,   'component'
    ,   'inf'
    ,   'nan'
    ,   'get_correlation'
    ,   'set_correlation'
    ,   'result'
    ,   'get_covariance'
    ,   'cos'
    ,   'sin'
    ,   'tan'
    ,   'acos'
    ,   'asin'
    ,   'atan'
    ,   'atan2'
    ,   'exp'
    ,   'pow'
    ,   'log'
    ,   'log10'
    ,   'sqrt'
    ,   'sinh'
    ,   'cosh'
    ,   'tanh'
    ,   'acosh'
    ,   'asinh'
    ,   'atanh'
    ,   'mag_squared'
    ,   'magnitude'
    ,   'phase'
    ,   'copyright',    'version'
    ,   'reporting',    'rp'
    ,   'function',     'fn'
    ,   'type_b',       'tb'
    ,   'type_a',       'ta'
    ,   'math'
    ,   'cmath'
    ,   'is_infinity'
    ,   'is_undefined'
    ,   'inf'
    ,   'nan'
)
 
#----------------------------------------------------------------------------
version = "1.0.0"
copyright = """Copyright (c) 2018, \
Measurement Standards Laboratory of New Zealand"""

from .core import *
 



       