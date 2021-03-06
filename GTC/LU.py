"""
Provides LU decomposition functions for Python objects stored in 2D arrays.

:func:`solve` returns the solution vector `x` to the equation `a.x = b`
:func:`ludet` returns the determinant of a previously LU-decomposed matrix 
:func:`ludcmp` performs LU decomposition
:func:`invab` 
"""
from __future__ import division
from functools import reduce
try:
    xrange  # Python 2
except NameError:
    xrange = range

import numpy as np 
import array

__all__ = (
    'solve'
,   'invab'
,   'ludet'
,   'ludcmp'
)

# -------------------------------------------------------------
def ludcmp(a):
    """
    Return (a_lu,idx,parity), where 'a_lu' is `a` decomposed
    
    The array `a` is decomposed by row-wise LU decomposition;
    `idx` records the row permutations from partial pivoting,
    `parity` is the parity of row switching (+1 or -1, for even or odd)

    .. note:: 
        The array `a` is assigned the decomposition values.
    
    .. note:: 
        An implementation of :func:`abs()` must be defined 
        for the type of the array elements.

    Parameters
    ----------
    a : :class:`UncertainArray`
    
    """
    if len(a.shape) != 2:
        raise RuntimeError( 
            "A 2D array is needed, got  shape={}".format(a.shape)
        )
    elif a.shape[0] != a.shape[1]:
        raise RuntimeError( 
            "A square array is needed, shape={}".format(a.shape)
        )
        
    N = a.shape[0]

    indx = array.array('l',[0] * N)   # Holds indices
    vv = array.array('d',[0.0] * N)   
    parity = 1

    for i in xrange(N):
        big = 0.0
        for j in xrange(N):
            temp = abs( a[i,j] )
            big = temp if temp > big else big
                
        try:
            vv[i] = 1.0/big
        except ZeroDivisionError:
            raise RuntimeError('zero column')
            
    for j in xrange(N):
        for i in xrange(j):
            a[i,j] = reduce(
                lambda sum,k: sum - (a[i,k] * a[k,j]), 
                    xrange(i),  # for k in xrange(i)
                    a[i,j]      # initial value
            )

        big = 0.0
        for i in xrange(j,N):
            a[i,j] = reduce(
                lambda sum,k: sum - (a[i,k] * a[k,j]), 
                    xrange(j),  # for k in xrange(j)
                    a[i,j]      # initial value
            )
            dum = vv[i] * abs(a[i,j])
            if(dum >= big):
                big = dum
                imax = i
            
        if(j != imax):
            for k in xrange(N):
                a[imax,k], a[j,k] = a[j,k], a[imax,k]
            parity *= -1
            vv[imax] = vv[j]
            
        indx[j] = imax
        if( a[j,j] == 0.0 ):
            raise RuntimeError("singular pivot element")
        
        if(j != N-1):
            tmp = 1.0 / a[j,j]
            for i in xrange(j+1,N):
                a[i,j] *= tmp

    return (a,indx,parity)

#----------------------------------------------------------------------------
def _lubksb(a_lu,idx,b):
    """
    LU back-substitution 

    The argument `a_lu` is the LU decomposition of `a`,
    where `a` is a 2D array (`x` and `b` are 1D).
    
    The argument `a_lu` is not changed, so the routine 
    may be used successively on different cases of `b`.
    
    The contents of `b` are changed by the function:
    `b` becomes the solution vector.
    
    The argument `b` need only be a sequence type;
    `a_lu` must be array-like.

    Usage::
        a_lu, idx = _ludcmp(a)
        x = _lubksub( a_lu, idx, b )

    """
    
    # If `b` does not contain the same type as `a_lu` 
    # the algorithm can calculate unexpected results! 
    # It is necessary to try to harmonize them in 
    # the calling context.
            
    N = a_lu.shape[0]

    ii = -1
    for i in xrange(N):
        ip = idx[i]
        sum, b[ip] = b[ip], b[i]
        if( ii != -1 ):
            for j in xrange(ii,i):
                sum -= a_lu[i,j] * b[j]
        elif(sum != 0.0):
            ii = i
        b[i] = sum

    for i in xrange(N-1,-1,-1):
        b[i] = reduce(
            lambda sum,j: sum - a_lu[i,j]*b[j],
            xrange(i+1,N),
            b[i]
        )/a_lu[i,i]
            
    return b

#---------------------------------------------------------
def invab(a,b):
    """
    Return the solution `x` to the linear equation`a.x = b` when `b` is 2D
    
    `a` and `b` must be array-like
    Neither `a` or `b` are changed by the function 
    
    """
    # Required by _lubksb
    assert a.dtype == b.dtype,\
        "{} != {}".format(a.dtype, b.dtype)
        
    if len(b.shape) != 2:
        raise RuntimeError( 
            "A 2D array is needed for `b`, got  shape={}".format(b.shape)
        )
    # `a` shape is checked when `ludcmp` is called 
    a_lu,idx,p = ludcmp(a.copy())

    N = a_lu.shape[0]
    M = b.shape[1]
        
    y = np.empty( (N,M), a.dtype )

    # For each column in matrix `b`
    for j in xrange(M):
    
        # TODO: consider a slice here
        col = _lubksb(a_lu,idx,[ b[i,j] for i in xrange(N) ])
        
        # TODO: consider a slice here
        for i in xrange(N):
            y[i,j] = col[i]
            
    return y

# -----------------------------------------------------------------
def ludet(a_lu,p):
    """
    Return the determinant of a matrix `a` using its LU decomposition `a_lu`

    Usage::
        a = .... # some matrix
        parity = 1 # value is not important
        a_lu,i,p = ludcmp(a.copy())
        d = ludet(a_lu,p)

    """
    Nx,Ny = a_lu.shape
    if Nx != Ny:
        raise RuntimeError(
            "matrix must be square, got {}".format(a_lu.shape)
        )
    elif p not in (1,-1):
        raise RuntimeError(
            "parity must be +/- 1, got {!r}".format(p)
        )
        
    return reduce(
        lambda p,i: p * a_lu[i,i],
        xrange(Nx),
        p
    )

#------------------------------------------------
def solve(a,b):
    """
    Return the solution `x` for `a.x = b` 
    
    Both `a` and `b` must be array-like
    `a` is a square 2D array, `b` is a 1D array
    Neither `a` or `b` are changed by the function 

    """
    # Required by _lubksb
    assert a.dtype == b.dtype,\
        "{} != {}".format(a.dtype, b.dtype)
        
    a_lu,i,p = ludcmp( a.copy() )
    return _lubksb( a_lu,i,b.copy() )


    