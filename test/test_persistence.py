import unittest
import sys
import math
import cmath
import itertools
import os

from GTC import *
from GTC.context import Context,_context
from GTC import persistence
from GTC.vector import is_ordered

from testing_tools import *

TOL = 1E-13 

#-----------------------------------------------------
class TestArchive(unittest.TestCase):

    def test_context_management(self):
        """
        Context registers should be updated when all dependence
        on an influence quantity disappears.
        
        """
        c1 = Context()
        x_seq = [1,1,1]
        u_seq = [1,1,1]
        label_seq = ['x1', 'x2', 'x3']
        x1, x2, x3 = multiple_ureal(x_seq,u_seq,df=5,label_seq=label_seq,context=c1)

        set_correlation(.5,x1,x2)
        set_correlation(.5,x2,x3)
        
        x4 = result(x1 + x2)
        x5 = result(x2 + x3)
        x6 = result(x4 + x5)

        ar = persistence.Archive(c1)
        ar.add(x1=x1,x2=x2,x3=x3,x4=x4,x5=x5,x6=x6)
        ar._freeze()

        # unpack and test
        c2 = Context()
        ar.context=c2
        ar._thaw()
        
        y1, y2, y3 = ar.extract('x1','x2','x3')
        y4, y5, y6 = ar.extract('x4','x5','x6')
        
        self.assert_( equivalent(
            get_correlation(x1,x2),
            get_correlation(y1,y2),
            TOL
        ))

        self.assertEqual( repr(x1), repr(y1) )
        self.assertEqual( repr(x2), repr(y2) )
        self.assertEqual( repr(x3), repr(y3) )
        self.assertEqual( repr(x4), repr(y4) )
        self.assertEqual( repr(x5), repr(y5) )
        self.assertEqual( repr(x6), repr(y6) )

        # self.assert_ ( y1._node in c2._correlations._mat )
        # self.assert_ ( y2._node in c2._correlations._mat )
        # self.assert_ ( y3._node in c2._correlations._mat )

        # del y6
        
        # self.assert_ ( y1._node in c2._correlations._mat )
        # self.assert_ ( y2._node in c2._correlations._mat )
        # self.assert_ ( y3._node in c2._correlations._mat )

        # del y3,y5

        # self.assert_ ( y1._node in c2._correlations._mat )
        # self.assert_ ( y2._node in c2._correlations._mat )

        # del y2, y4      

        # self.assert_ ( y1._node in c2._correlations._mat )

        # del y1

    def test_errors(self):
        """
        Error conditions:
##            - trying to archive a complex and one of its components, or vice versa
##            - trying to archive the same object with different names
            - trying to extract with the wrong name
            - adding to an archive that has been frozen
            - extracting from an archive that has not been thawed
            - restoring an archive to the same context
            
        """
        x = ureal(1,1)
        y = ureal(2,1)
        z = result( x + y )

        ar = persistence.Archive()

        ar.add(x=x,z=z)
        self.assertRaises(RuntimeError,ar.add,x=y)  # same name

        # These used to be illegal but are now allowed
        zc = ucomplex(1,1)
        ar.add(zc=zc)
        ar.add(zr=zc.real)  # a component
        
        zz = ucomplex(1,1)
        ar.add(zr2=zz.real)
        ar.add(zz=zz)  # a component was archived

        ar._freeze()

        self.assertRaises(RuntimeError,ar.extract,'x')  # cannot extract yet
        
        c2 = Context()
        ar.context = c2
        ar._thaw( )

        self.assertRaises(RuntimeError,ar.add,y=y)  # cannot add now
        
    def test(self):
        """
        Simple x,y z problem, but don't save
        one of the elementary uns.
        
        """
        x = ureal(1,1)
        y = ureal(2,1)
        z = result( x + y )

        self.assert_( z.is_intermediate )

        ar = persistence.Archive()

        ar.add(x=x,z=z)
        ar._freeze()
                
        # Unpack and check 
        c2 = Context()
        ar.context=c2
        ar._thaw()

        # Single argument unpacks to an object
        # not a sequence
        x1 = ar.extract('x')
        z1 = ar.extract('z')

        self.assert_( z1.is_intermediate )
        self.assert_(
            all( 
                z_i.uid == z1_i.uid 
                    for (z_i, z1_i) in itertools.izip(
                        z._i_components,z1._i_components) 
            )
        )

        a = component(z,x)
        b = component(z1,x1)
        self.assert_( equivalent(a,b,TOL) )

        # The restored uncertain numbers will
        # belog to different contexts
        self.assertRaises(RuntimeError,component,z1,x)
        self.assertRaises(RuntimeError,component,z,x1)
        # self.assert_( equivalent(a,b,TOL) )

        # Make sure the vectors are well-formed
        self.assert_( is_ordered(z1._u_components) )
        self.assert_( is_ordered(z1._d_components) )
        self.assert_( is_ordered(z1._i_components) )
        
    def test_attributes(self):
        """
        Dict-like attributes: keys(), values() items()
        and the 'iter' variants, also len()
        
        """
        x = ureal(1,1)
        y = ureal(2,1)
        z = result(x + y)

        ar = persistence.Archive()
        self.assertEqual( len(ar), 0)
        
        ar.add(x=x,z=z)
        self.assertEqual( len(ar) , 2)

        names = ['x','z']
        objs = [x,z]
        self.assertEqual( names,ar.keys() )
        self.assertEqual( objs,ar.values() )
        self.assertEqual( zip(names,objs),ar.items() )

        for i,k in enumerate( ar.iterkeys() ):
            self.assertEqual( names[i], k )

        for i,k in enumerate( ar.itervalues() ):
            self.assertEqual( objs[i], k )

        items = zip(names,objs)
        for i,k in enumerate( ar.iteritems() ):
            self.assertEqual( items[i], k )

    def test1(self):
        """
        Simple tests: elementary and intermediate
        uncertain numbers restored OK? Saving
        all objects.
        
        """
        x = ureal(1,1)
        y = ureal(2,1)
        z = result( x + y )

        ar = persistence.Archive()

        ar.add(x=x,y=y,z=z)
        ar._freeze()

        # Unpack and check 
        c2 = Context()
        ar.context=c2
        ar._thaw()

        x1, y1, z1 = ar.extract('x','y','z')

        self.assertEqual(x.x,x1.x)
        self.assertEqual(x.u,x1.u)
        self.assertEqual(x.df,x1.df)
        self.assertEqual(y.x,y1.x)
        self.assertEqual(y.u,y1.u)
        self.assertEqual(y.df,y1.df)
        self.assertEqual(z.x,z1.x)
        self.assertEqual(z.u,z1.u)
        self.assertEqual(z.df,z1.df)

        a = component(z,x)
        b = component(z1,x1)
        self.assert_( equivalent(a,b,TOL) )

        # The restored uncertain numbers have different contexts
        self.assertRaises(RuntimeError,component,z1,x)
        self.assertRaises(RuntimeError,component,z,x1)

    def test2(self):
        """
        Logical correlation works - I
        with all objects archived
        
        """
        x1 = ureal(1,1)
        x2 = ureal(1,1)
        x3 = ureal(1,1)
        x4 = result( x1 + x2 )
        x5 = result( x2 + x3 )
        x6 = result( x4 + x5 )

        ar = persistence.Archive()
        ar.add(x1=x1,x2=x2,x3=x3,x4=x4,x5=x5,x6=x6)
        ar._freeze()

        # unpack and test
        c2 = Context()
        ar.context=c2
        ar._thaw()
        
        y1, y2, y3 = ar.extract('x1','x2','x3')

        self.assertEqual( str(x1),str(y1) )
        self.assertEqual( str(x2),str(y2) )
        self.assertEqual( str(x3),str(y3) )

        y4, y5, y6 = ar.extract('x4','x5','x6')
        
        self.assertEqual( str(x4),str(y4) )
        self.assertEqual( str(x5),str(y5) )
        self.assertEqual( str(x6),str(y6) )

        a = component(x6,x4)
        b = component(y6,y4)
        self.assert_( equivalent(a,b,TOL) )

        a = component(x6,x2)
        b = component(y6,y2)
        self.assert_( equivalent(a,b,TOL) )

        a = get_correlation(x4,x5)
        b = get_correlation(y4,y5)
        self.assert_( equivalent(a,b,TOL) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(y6._u_components) )
        self.assert_( is_ordered(y6._d_components) )
        self.assert_( is_ordered(y6._i_components) )

    def test3(self):
        """
        Logical correlation works - II
        with all objects archived but not all restored
        
        """
        x1 = ureal(1,1)
        x2 = ureal(1,1)
        x3 = ureal(1,1)
        x4 = result( x1 + x2 )
        x5 = result( x2 + x3 )
        x6 = result( x4 + x5 )

        ar = persistence.Archive()
        ar.add(x1=x1,x2=x2,x3=x3,x4=x4,x5=x5,x6=x6)
        ar._freeze()

        # unpack without elementary uns and test
        c2 = Context()
        ar.context=c2
        ar._thaw()

        y4, y5, y6 = ar.extract('x4','x5','x6')
        
        self.assertEqual( str(x4),str(y4) )
        self.assertEqual( str(x5),str(y5) )
        self.assertEqual( str(x6),str(y6) )

        a = component(x6,x4)
        b = component(y6,y4)
        self.assert_( equivalent(a,b,TOL) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(y6._u_components) )
        self.assert_( is_ordered(y6._d_components) )
        self.assert_( is_ordered(y6._i_components) )

    def test3b(self):
        """
        Logical correlation works - III
        with not all objects archived or restored
        
        """
        x1 = ureal(1,1)
        x2 = ureal(1,1)
        x3 = ureal(1,1)
        x4 = result( x1 + x2 )
        x5 = result( x2 + x3 )
        x6 = result( x4 + x5 )

        ar = persistence.Archive()
        ar.add(x4=x4,x5=x5,x6=x6)
        ar._freeze()

        # unpack without elementary uns and test
        c2 = Context()
        ar.context=c2
        ar._thaw()

        y4, y5, y6 = ar.extract('x4','x5','x6')
        
        self.assertEqual( str(x4),str(y4) )
        self.assertEqual( str(x5),str(y5) )
        self.assertEqual( str(x6),str(y6) )

        a = component(x6,x4)
        b = component(y6,y4)
        self.assert_( equivalent(a,b,TOL) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(y6._u_components) )
        self.assert_( is_ordered(y6._d_components) )
        self.assert_( is_ordered(y6._i_components) )

    def test4(self):
        """
        Explicit correlation works - I
        with all objects archived
        
        """
        x1 = ureal(1,1,independent=False)
        x2 = ureal(1,1,independent=False)
        x3 = ureal(1,1,independent=False)
        x4 = result( x1 + x2 )
        x5 = result( x2 + x3 )
        x6 = result( x4 + x5 )

        set_correlation(0.5,x1,x2)
        set_correlation(-0.25,x3,x2)

        ar = persistence.Archive()
        ar.add(x1=x1,x2=x2,x3=x3,x4=x4,x5=x5,x6=x6)
        ar._freeze()

        # unpack without elementary uns and test
        c2 = Context()
        ar.context=c2
        ar._thaw()

        y1, y2, y3 = ar.extract('x1','x2','x3')

        a = get_correlation(x1,x2)
        b = get_correlation(y1,y2)
        self.assert_( equivalent(a,b,TOL) )

        a = get_correlation(x3,x2)
        b = get_correlation(y3,y2)
        self.assert_( equivalent(a,b,TOL) )

        y4, y5, y6 = ar.extract('x4','x5','x6')
        
        self.assertEqual( str(x4),str(y4) )
        self.assertEqual( str(x5),str(y5) )
        self.assertEqual( str(x6),str(y6) )

        a = get_correlation(x4,x5)
        b = get_correlation(y4,y5)
        self.assert_( equivalent(a,b,TOL) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(y6._u_components) )
        self.assert_( is_ordered(y6._d_components) )
        self.assert_( is_ordered(y6._i_components) )

    def test5(self):
        """
        Explicit correlation works - II
        with only some objects restored
        
        """
        x1 = ureal(1,1,independent=False)
        x2 = ureal(1,1,independent=False)
        x3 = ureal(1,1,independent=False)
        x4 = result( x1 + x2 )
        x5 = result( x2 + x3 )
        x6 = result( x4 + x5 )

        set_correlation(0.5,x1,x2)
        set_correlation(-0.25,x3,x2)

        ar = persistence.Archive()
        ar.add(x1=x1,x2=x2,x3=x3,x4=x4,x5=x5,x6=x6)
        ar._freeze()

        # unpack without elementary uns and test
        c2 = Context()
        ar.context=c2
        ar._thaw()

        y4, y5, y6 = ar.extract('x4','x5','x6')
        
        self.assertEqual( str(x4),str(y4) )
        self.assertEqual( str(x5),str(y5) )
        self.assertEqual( str(x6),str(y6) )

        a = get_correlation(x4,x5)
        b = get_correlation(y4,y5)
        self.assert_( equivalent(a,b,TOL) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(y6._u_components) )
        self.assert_( is_ordered(y6._d_components) )
        self.assert_( is_ordered(y6._i_components) )

    def test5b(self):
        """
        Explicit correlation works - II
        with only some objects archived and restored
        
        """
        x1 = ureal(1,1,independent=False)
        x2 = ureal(1,1,independent=False)
        x3 = ureal(1,1,independent=False)
        x4 = result( x1 + x2 )
        x5 = result( x2 + x3 )
        x6 = result( x4 + x5 )

        set_correlation(0.5,x1,x2)
        set_correlation(-0.25,x3,x2)

        ar = persistence.Archive()
        ar.add(x4=x4,x5=x5,x6=x6)
        ar._freeze()

        # unpack without elementary uns and test
        c2 = Context()
        ar.context=c2
        ar._thaw()
        y4, y5, y6 = ar.extract('x4','x5','x6')
        
        self.assertEqual( str(x4),str(y4) )
        self.assertEqual( str(x5),str(y5) )
        self.assertEqual( str(x6),str(y6) )

        a = get_correlation(x4,x5)
        b = get_correlation(y4,y5)
        self.assert_( equivalent(a,b,TOL) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(y6._u_components) )
        self.assert_( is_ordered(y6._d_components) )
        self.assert_( is_ordered(y6._i_components) )

    def test6(self):
        """
        Same as test 5 but with [] indexing
        
        """
        x1 = ureal(1,1,independent=False)
        x2 = ureal(1,1,independent=False)
        x3 = ureal(1,1,independent=False)
        x4 = result( x1 + x2 )
        x5 = result( x2 + x3 )
        x6 = result( x4 + x5 )

        set_correlation(0.5,x1,x2)
        set_correlation(-0.25,x3,x2)

        ar = persistence.Archive()
        ar['x1'] = x1
        ar['x2'] = x2
        ar['x3'] = x3
        ar['x4'] = x4
        ar['x5'] = x5
        ar['x6'] = x6
        ar._freeze()

        # unpack without elementary uns and test
        c2 = Context()
        ar.context=c2
        ar._thaw()

        y4 = ar['x4']
        y5 = ar['x5']
        y6 = ar['x6']
        
        self.assertEqual( str(x4),str(y4) )
        self.assertEqual( str(x5),str(y5) )
        self.assertEqual( str(x6),str(y6) )

        a = get_correlation(x4,x5)
        b = get_correlation(y4,y5)
        self.assert_( equivalent(a,b,TOL) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(y6._u_components) )
        self.assert_( is_ordered(y6._d_components) )
        self.assert_( is_ordered(y6._i_components) )

    def testGUMH2(self):
        """
        GUM H2 as an ensemble
        
        """
        # NB this is a dodgy test, because we are reusing 
        # the same archive object in a way that is not intended.
        
        c1 = Context()
        
        x = [4.999,0.019661,1.04446]
        u = [0.0032,0.0000095,0.00075]
        
        v,i,phi = multiple_ureal(x,u,5,context=c1)
        
        set_correlation(-0.36,v,i)
        set_correlation(0.86,v,phi)
        set_correlation(-0.65,i,phi)
        
        r = v * cos(phi)/i
        x = v * sin(phi)/i
        z = v/i

        ar = persistence.Archive(context=c1)
        ar.add(v=v,i=i,phi=phi)
        ar._freeze()
                
        # unpack without elementary UNs and test
        c2 = Context()
        assert c1 is not c2 
        # This is a fudge. Normally, a different 
        # archive object would be created from a 
        # file or string. 
        ar.context = c2
        ar._thaw()
        
        v1, i1, phi1 = ar.extract('v','i','phi')
        
        # self.assert_( v1._node in c2._ensemble )
        # self.assert_( i1._node in c2._ensemble )
        # self.assert_( phi1._node in c2._ensemble )

        self.assert_( hasattr(v1._node, 'ensemble') )
        self.assert_( v1._node.uid in v1._node.ensemble )
        self.assert_( hasattr(i1._node, 'ensemble') )
        self.assert_( i1._node.uid in i1._node.ensemble )
        self.assert_( hasattr(phi1._node, 'ensemble') )
        self.assert_( phi1._node.uid in phi1._node.ensemble )

        
        self.assertEqual( repr(v1), repr(v) )
        self.assertEqual( repr(i1) , repr(i) )
        self.assertEqual( repr(phi1) , repr(phi) )
        
        self.assert_( equivalent( get_correlation(v1,i1),-0.36) )
        self.assert_( equivalent( get_correlation(v1,phi1),0.86) )
        self.assert_( equivalent( get_correlation(i1,phi1),-0.65) )
           
        r1 = v1 * cos(phi1)/ i1
        x1 = v1 * sin(phi1)/ i1
        z1 = v1 / i1

        # The DoF calculation would fail if the inputs
        # are not part of the same ensemble.    
        self.assert_( equivalent( dof(r1),5,TOL) )
        self.assert_( equivalent( dof(x1),5,TOL) )
        self.assert_( equivalent( dof(z1),5,TOL) )

        self.assert_( equivalent( value(r1),value(r),TOL) )
        self.assert_( equivalent( value(x1),value(x),TOL) )
        self.assert_( equivalent( value(z1),value(z),TOL) )

        self.assert_( equivalent( uncertainty(r1),uncertainty(r),TOL) )
        self.assert_( equivalent( uncertainty(x1),uncertainty(x),TOL) )
        self.assert_( equivalent( uncertainty(z1),uncertainty(z),TOL) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(r1._u_components) )
        self.assert_( is_ordered(x1._u_components) )
        self.assert_( is_ordered(z1._u_components) )

    def testGUMH2_b(self):
        """
        GUM H2 as an ensemble. Only save the results this time.
        
        """
        c1 = Context()

        x = [4.999,0.019661,1.04446]
        u = [0.0032,0.0000095,0.00075]
        
        v,i,phi = multiple_ureal(x,u,5,context=c1)
        
        set_correlation(-0.36,v,i)
        set_correlation(0.86,v,phi)
        set_correlation(-0.65,i,phi)

        r = result( v * cos(phi)/ i )
        x = result( v * sin(phi)/ i )
        z = result( v / i )

        ar = persistence.Archive(c1)
        ar.add(r=r,x=x,z=z)
        ar._freeze()

        # unpack without elementary uns and test
        c2 = Context()
        ar.context = c2
        ar._thaw()

        r1, x1, z1 = ar.extract('r','x','z')
        
        self.assertEqual( repr(r1), repr(r) )
        self.assertEqual( repr(x1) , repr(x) )
        self.assertEqual( repr(z1) , repr(z) )
               
        # The DoF calculation would fail if the inputs
        # are not part of the same ensemble.    
        self.assert_( equivalent( dof(r1),5,TOL) )
        self.assert_( equivalent( dof(x1),5,TOL) )
        self.assert_( equivalent( dof(z1),5,TOL) )

        self.assert_( equivalent( value(r1),value(r),TOL) )
        self.assert_( equivalent( value(x1),value(x),TOL) )
        self.assert_( equivalent( value(z1),value(z),TOL) )

        self.assert_( equivalent( uncertainty(r1),uncertainty(r),TOL) )
        self.assert_( equivalent( uncertainty(x1),uncertainty(x),TOL) )
        self.assert_( equivalent( uncertainty(z1),uncertainty(z),TOL) )
        
        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(r1._u_components) )
        self.assert_( is_ordered(x1._u_components) )
        self.assert_( is_ordered(z1._u_components) )

    def test_intermediates_multipath(self):
        """
        Check the sensitivities when the tree structure
        has intermediates that depend on intermediates

        In this case y is directly connected to x1, x4 and x5
        but x4 and x5 also depend on x1 and x5 depends on x4

        """
        x1 = ureal(1.2,0.6,label='x1')
        x2 = ureal(2.5,1.6,label='x2')
        x3 = ureal(-5.3,.77,label='x3')
        x4 = result( 2.0 * (x1 + x2) )
        x5 = result( (x4 + x3)**2 )
        y = result( sqrt(x5 + x4 + x1) )

        c1 = Context()
        ar = persistence.Archive(c1)
        ar.add(y=y,x4=x4,x5=x5,x1=x1)
        ar._freeze()

        # unpack without elementary uns and test
        c2 = Context()
        ar.context=c2
        ar._thaw()
        yy, xx4, xx5, xx1 = ar.extract('y','x4','x5','x1')

        self.assert_(
            equivalent(
                rp.u_component(y,x4),
                rp.u_component(yy,xx4),
                TOL
            )
        )

        self.assert_(
            equivalent(
                rp.u_component(y,x5),
                rp.u_component(yy,xx5),
                TOL
            )
        )

        self.assert_(
            equivalent(
                rp.u_component(y,x1),
                rp.u_component(yy,xx1),
                TOL
            )
        )

        self.assert_(
            equivalent(
                rp.u_component(x5,x1),
                rp.u_component(xx5,xx1),
                TOL
            )
        )

        self.assert_(
            equivalent(
                rp.u_component(x4,x1),
                rp.u_component(xx4,xx1),
                TOL
            )
        )

        self.assert_(
            equivalent(
                rp.u_component(x5,x4),
                rp.u_component(xx5,xx4),
                TOL
            )
        )

        self.assert_(
            equivalent(
                rp.u_component(x4,x5),
                rp.u_component(xx4,xx5),
                TOL
            )
        )
     
    def test_complex_1(self):
        """
        Simple arithmetic - all objects stored
        and restored.
        
        """
        c1 = Context()
        
        x = ucomplex(1,[1,2],4,context=c1)
        y = ucomplex(1,[3,12],3,context=c1)
        z = result( x * y )

        ar = persistence.Archive(c1)
        ar.add(x=x)
        ar.add(y=y)
        ar.add(z=z)
        ar._freeze()

        # unpack 
        c2 = Context()
        ar.context=c2
        ar._thaw()

        x1, y1, z1 = ar.extract('x','y','z')

        self.assertEqual( repr(y1), repr(y) )
        self.assertEqual( repr(x1), repr(x) )

        self.assert_( equivalent_complex(x1.x,x.x) )
        self.assert_( equivalent_sequence(x1.u,x.u) )
        self.assert_( equivalent(x1.df,x.df) )

        self.assert_( equivalent_complex(y1.x,y.x) )
        self.assert_( equivalent_sequence(y1.u,y.u) )
        self.assert_( equivalent(y1.df,y.df) )
        
        self.assert_( equivalent_complex(z1.x,z.x) )
        self.assert_( equivalent_sequence(z1.u,z.u) )
        self.assert_( equivalent(z1.df,z.df) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(y1.real._u_components) )
        self.assert_( is_ordered(x1.real._u_components) )
        self.assert_( is_ordered(z1.real._u_components) )
        self.assert_( is_ordered(y1.imag._u_components) )
        self.assert_( is_ordered(x1.imag._u_components) )
        self.assert_( is_ordered(z1.imag._u_components) )

    def test_complex_2(self):
        """
        Complex logical correlation
        
        """
        c1 = Context()
        
        x1 = ucomplex(1,[3,2],4,context=c1)
        x2 = ucomplex(1,[1,1],5,context=c1)
        x3 = ucomplex(1,[4,5],6,context=c1)

        x4 = result( x1*x2 )
        x5 = result( x2*x3 )

        x6 = result( x4 + x5 )

        ar = persistence.Archive(c1)
        ar.add(x4=x4,x5=x5,x6=x6)
        ar._freeze()

        c2 = Context()
        ar.context=c2
        ar._thaw()
        y4, y5, y6 = ar.extract('x4','x5','x6')

        self.assertEqual( repr(x4), repr(y4) )
        self.assertEqual( repr(x5), repr(y5) )
        self.assertEqual( repr(x6), repr(y6) )

        self.assert_( equivalent_complex(x4.x,y4.x) )
        self.assert_( equivalent_sequence(x4.u,y4.u) )
        self.assert_( equivalent(x4.df,y4.df) )

        self.assert_( equivalent_complex(x5.x,y5.x) )
        self.assert_( equivalent_sequence(x5.u,y5.u) )
        self.assert_( equivalent(x5.df,y5.df) )
        
        self.assert_( equivalent_complex(x6.x,y6.x) )
        self.assert_( equivalent_sequence(x6.u,y6.u) )
        self.assert_( equivalent(x6.df,y6.df) )

        self.assert_( equivalent_sequence(
            get_correlation(x6,x5),
            get_correlation(y6,y5)
        ) )
                               
        self.assert_( equivalent_sequence(
            get_correlation(x6,x4),
            get_correlation(y6,y4)
        ) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(x6.real._u_components) )
        self.assert_( is_ordered(x6.imag._u_components) )

    def test_complex_3(self):
        """
        Complex logical and external correlation
        
        """
        c1 = Context()
        
        x1 = ucomplex(1,[3,2],independent=False,context=c1)
        x2 = ucomplex(1,[1,1],independent=False,context=c1)
        x3 = ucomplex(1,[4,5],context=c1)

        R = [.1,.2,.3,.4]
        set_correlation(R,x1,x2)
        # Make sure we get what we expect
        self.assert_( equivalent_sequence(
            R, get_correlation(x1,x2)
        ))
        
        x4 = result( x1*x2 )
        x5 = result( x2*x3 )

        x6 = result( x4 + x5 )

        ar = persistence.Archive(c1)
        ar.add(x1=x1,x2=x2,x3=x3,x4=x4,x5=x5,x6=x6)
        ar._freeze()

        c2 = Context()
        ar.context = c2
        ar._thaw( )
        y4, y5, y6 = ar.extract('x4','x5','x6')

        self.assertEqual( repr(x4), repr(y4) )
        self.assertEqual( repr(x5), repr(y5) )
        self.assertEqual( repr(x6), repr(y6) )
        
        self.assert_( equivalent_sequence(
            get_correlation(x6,x5),
            get_correlation(y6,y5)
        ) )
                               
        self.assert_( equivalent_sequence(
            get_correlation(x6,x4),
            get_correlation(y6,y4)
        ) )

        self.assert_( equivalent_sequence(
            variance(x6),
            variance(y6)
        ))
        
        # Now look at the elementary influences
        y1, y2 = ar.extract('x1','x2')
        self.assert_( equivalent_sequence(
            R, get_correlation(y1,y2)
        ))

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(x6.real._u_components) )
        self.assert_( is_ordered(x6.imag._u_components) )

    def test_complex_4(self):
        """
        Same as 'complex_3' but using [] indexing
        
        """
        c1 = Context()
        x1 = ucomplex(1,[3,2],independent=False,context=c1)
        x2 = ucomplex(1,[1,1],independent=False,context=c1)
        x3 = ucomplex(1,[4,5],context=c1)

        R = [.1,.2,.3,.4]
        set_correlation(R,x1,x2)
        # Make sure we get what we expect
        self.assert_( equivalent_sequence(
            R, get_correlation(x1,x2)
        ))
        
        x4 = result( x1*x2 )
        x5 = result( x2*x3 )

        x6 = result( x4 + x5 )

        ar = persistence.Archive(c1)
        ar['x1'] = x1 
        ar['x2'] = x2 
        ar['x3'] = x3 
        ar['x4'] = x4 
        ar['x5'] = x5 
        ar['x6'] = x6 
        ar._freeze()

        c2 = Context()
        ar.context = c2
        ar._thaw( )
        y4 = ar['x4']
        y5 = ar['x5']
        y6 = ar['x6']

        self.assertEqual( repr(x4), repr(y4) )
        self.assertEqual( repr(x5), repr(y5) )
        self.assertEqual( repr(x6), repr(y6) )
        
        self.assert_( equivalent_sequence(
            get_correlation(x6,x5),
            get_correlation(y6,y5)
        ) )
                               
        self.assert_( equivalent_sequence(
            get_correlation(x6,x4),
            get_correlation(y6,y4)
        ) )

        self.assert_( equivalent_sequence(
            variance(x6),
            variance(y6)
        ))
        
        # Now look at the elementary influences
        y1, y2 = ar.extract('x1','x2')
        self.assert_( equivalent_sequence(
            R, get_correlation(y1,y2)
        ))

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(x6.real._u_components) )
        self.assert_( is_ordered(x6.imag._u_components) )

    def test_complex_5(self):
        """
        Archive intermediate complex components
        
        """
        c1 = Context()
        x1 = ucomplex(1,[3,2],independent=False,context=c1)
        x2 = ucomplex(1,[1,1],independent=False,context=c1)
        x3 = ucomplex(1,[4,5],context=c1)

        R = [.1,.2,.3,.4]
        set_correlation(R,x1,x2)
        # Make sure we get what we expect
        self.assert_( equivalent_sequence(
            R, get_correlation(x1,x2)
        ))
        
        x4 = result( x1*x2 )
        x5 = result( x2*x3 )

        x6 = result( x4 + x5  )
        x7 = result( mag_squared(x6) + mag_squared(x4) )

        ar = persistence.Archive(c1)
        ar['x1'] = x1 
        ar['x2'] = x2 
        ar['x3'] = x3 
        ar['x4'] = x4.real  # just the real component
        ar['x5'] = x5 
        ar['x6'] = x6
        ar['x7'] = x7
        ar._freeze()

        c2 = Context()
        ar.context=c2
        ar._thaw()
        y4 = ar['x4']
        y5 = ar['x5']
        y6 = ar['x6']
        y7 = ar['x7']

        self.assertEqual( repr(x4.real), repr(y4) )
        self.assertEqual( repr(x5), repr(y5) )
        self.assertEqual( repr(x6), repr(y6) )
        

        # Archived as a complex influence of a complex quantity                
        self.assert_( equivalent_sequence(
            rp.u_component(x6,x5),
            rp.u_component(y6,y5)
        ) )

        # Archived as a real influence of a complex quantity                
        self.assert_( equivalent_sequence(
            rp.u_component(x6,x4.real),
            rp.u_component(y6,y4)
        ) )

        # Archived as a complex influence of a real quantity                
        self.assert_( equivalent_sequence(
            rp.u_component(x7,x5),
            rp.u_component(y7,y5)
        ))
        
        # Archived as a real influence of a real quantity                
        self.assert_( equivalent(
            rp.u_component(x7,x4.real),
            rp.u_component(y7,y4)
        ))

    def test_nop_intermediates(self):
        """
        Archiving irrelevant intermediate components
        
        """
        c1 = Context()
        x1 = ucomplex(1,[3,2],context=c1)
        x2 = ureal(1,1,context=c1)
        x3 = constant(1.3,context=c1)
        
        x4 = result( x1*x2 )
        x5 = result( x2*x3 )

        x6 = result( x4 + x5 )
        x7 = result( mag_squared(x6) )

        ar = persistence.Archive(c1)
        ar.add(
            x1=x1,x2=x2,x3=x3,x4=x4.real,
            x5=x5,x6=x6
        )
        ar.add(x7=x7)
        ar._freeze()

        c2 = Context()
        ar.context = c2
        ar._thaw( )
        y1 = ar['x1']
        y2 = ar['x2']
        y3 = ar['x3']
        y6 = ar['x6']
        y7 = result( ar['x7'] )

        self.assertEqual( repr(x1), repr(y1) )
        self.assertEqual( repr(x2), repr(y2) )
        self.assertEqual( repr(x3), repr(y3) )
        self.assertEqual( repr(x6), repr(y6) )
        self.assertEqual( repr(x7), repr(y7) )

        # Archived as a complex influence of a complex quantity                
        self.assert_( equivalent_sequence(
            rp.u_component(x6,x1),
            rp.u_component(y6,y1)
        ) )

        # Archived as a real influence of a complex quantity                
        self.assert_( equivalent_sequence(
            rp.u_component(x6,x2),
            rp.u_component(y6,y2)
        ) )

        # Archived as a complex influence of a real quantity                
        self.assert_( equivalent_sequence(
            rp.u_component(x7,x1),
            rp.u_component(y7,y1)
        ))
        
        # Archived as a real influence of a real quantity                
        self.assert_( equivalent(
            rp.u_component(x7,x2),
            rp.u_component(y7,y2)
        ))

        # Archived as a constant influence of a real quantity 
        self.assert_( equivalent(
            rp.u_component(x7,x3),
            rp.u_component(y7,y3)
        ))

        # Archived as a constant influence of a complex quantity                
        self.assert_( equivalent_sequence(
            rp.u_component(x6,x3),
            rp.u_component(y6,y3)
        ) )
                         
    def test_with_file(self):
        """
        Save to a file and then restore by reading
        """
        wdir = os.getcwd()
        fname = 'test_file.pkl'
        path = os.path.join(wdir,fname)

        c1 = Context()
        x = ureal(1,1,context=c1)
        y = ureal(2,1,context=c1)
        z = result( x + y )

        ar = persistence.Archive(c1)

        ar.add(x=x,y=y,z=z)

        f = open(path,'wb')
        persistence.dump(f,ar)
        f.close()

        c2 = Context()
        f = open(path,'rb')
        ar = persistence.load(f,c2)
        f.close()
        os.remove(path)

        x1, y1, z1 = ar.extract('x','y','z')

        self.assertEqual( repr(x1), repr(x) )
        self.assertEqual( repr(y1), repr(y) )
        self.assertEqual( repr(z1), repr(z) )

    def test_with_file2(self):
        """
        Save to a file and then restore several times
        to test the effectiveness of GTC's uid system.
        
        """
        wdir = os.getcwd()
        fname = 'test_file.pkl'
        path = os.path.join(wdir,fname)

        c1 = Context()
        x = ureal(1,1,3,label='x',context=c1)
        y = ureal(2,1,4,label='y',context=c1)
        z = result( x + y )

        ar = persistence.Archive()

        # Saving only `z` means that when the archive
        # is restored `x` and `y` are not recreated within
        # the archive. This creates a problem, because if
        # the archive is restored more than once in the same
        # context there could be different Leaf nodes associated
        # with these elementary UNs. If one of these LNs is
        # garbage collected it signals the context causing DoF and
        # label info to be removed from the registers.
        # A cache has been introduced to make sure that restored
        # leafNodes are unique. This test verifies that.
        
        ar.add(z=z)

        with open(path,'wb') as f:
            persistence.dump(f,ar)

        c2 = Context()
        
        with open(path,'rb') as f:
            ar1 = persistence.load(f,c2)

        z1 = ar1.extract('z')

        with open(path,'rb') as f:
            ar2 = persistence.load(f)

        z2 = ar2.extract('z')

        # z1 and z2 should be indistinguishable
        self.assertEqual( repr(z1), repr(z2) )
        
        # # but they are defined in different contexts 
        # self.assertRaises(RuntimeError,get_correlation,z1,z2)
        
        budgets = zip( rp.budget(z1,trim=0), rp.budget(z2,trim=0) )
        for c1,c2 in budgets:
            self.assertEqual(c1[0],c2[0])
            self.assert_( equivalent(c1[1],c2[1]) )

        # The contexts are different so correlation between
        # z and z2 will not be unity, however
        self.assertEqual( repr(z), repr(z2) )
        budgets = zip( rp.budget(z,trim=0), rp.budget(z2,trim=0) )
        for c1,c2 in budgets:
            self.assertEqual(c1[0],c2[0])
            self.assert_( equivalent(c1[1],c2[1]) )
          
        # Deleting `z1` will cause it's node tree to collapse
        # However, we require the leaves of that tree to endure
        # because `z2` is still alive.
        del z1
        
        # Testing the summary strings against `z` ensures that
        # the DoF information is still accessible to `z2`
        # (otherwise dof would be infinity).
        # Comparing the budgets ensures that the influence labels
        # have not been removed.
        # The removal of dof and label information would happen
        # if the `z1` tree LeafNodes were garbage collected, calling
        # the `deregister` context method.
        self.assertEqual( repr(z) , repr(z2) )
        budgets = zip( rp.budget(z,trim=0), rp.budget(z2,trim=0) )
        for c1,c2 in budgets:
            self.assertEqual(c1[0],c2[0])
            self.assert_( equivalent(c1[1],c2[1]) )

        os.remove(path)
 
    def test_with_string(self):
        """
        Save to a file and then restore by reading
        """
        c1 = Context()
        x = ureal(1,1,context=c1)
        y = ureal(2,1,context=c1)
        z = result( x + y )
        
        ar = persistence.Archive(c1)

        ar.add(x=x,y=y,z=z)

        db = persistence.dumps(ar)

        c2 = Context()
        ar = persistence.loads(db,c2)

        x1, y1, z1 = ar.extract('x','y','z')

        self.assertEqual( repr(x1), repr(x) )
        self.assertEqual( repr(y1), repr(y) )
        self.assertEqual( repr(z1), repr(z) )

    def test_multiple_names(self):
        """
        Different names may apply to the same UN
        
        """
        # use the default context first
        x1 = ureal(1,1)
        x2 = ureal(1,1)
        x3 = ureal(1,1)
        x4 = result( x1 + x2 )
        x5 = result( x2 + x3 )
        x6 = result( x4 + x5 )

        ar = persistence.Archive()
        ar.add(
            x1=x1,x2=x2,x3=x3,x4=x4,x5=x5,x6=x6,
            z1=x1,z4=x4,z6=x6
        )
        ar._freeze()

        # unpack and test
        c2 = Context()
        ar.context = c2
        ar._thaw()
        y1, y2, y3 = ar.extract('x1','x2','x3')
        yz1 = ar['z1']
        
        # This used to be the case, but thawing now allows multiple UNs
        # self.assert_( yz1 is y1 )
        
        self.assert_( yz1._node.uid is y1._node.uid )
        self.assertEqual( repr(x1), repr(y1) )
        self.assertEqual( repr(yz1),repr(y1) )

        # NB most of these tests are redundant
        # now that multiple names are restored
        # to the same object. 
        y4, y5, y6 = ar.extract('x4','x5','x6')
        yz4 = ar['z4']
        yz6 = ar['z6']
        # self.assert_( yz4 is y4 )
        # self.assert_( yz6 is y6 )
        self.assert_( yz4._node.uid is y4._node.uid )
        self.assert_( yz6._node.uid is y6._node.uid )
        
        self.assertEqual( repr(x4),repr(y4) )
        self.assertEqual( repr(yz4), repr(y4) )
        self.assertEqual( repr(x6), repr(y6) )
        self.assertEqual( repr(yz6), repr(y6) )

        a = component(x6,x4)
        b = component(y6,y4)
        self.assert_( equivalent(a,b,TOL) )

        b = component(yz6,y4)
        self.assert_( equivalent(a,b,TOL) )

        b = component(yz6,yz4)
        self.assert_( equivalent(a,b,TOL) )

        # Make sure the vector of components is well-formed
        self.assert_( is_ordered(yz6._u_components) )
        
    def test_archive_with_previously_archived(self):
        """
        Make sure that an archive can be created that
        includes some UNs that have been restored from
        another archive.

        NB some tests here imposed interchangeability of
        objects that belong to different contexts. But
        this is not a requirement, so I have commented
        out. We should never have to work with a mixture 
        of uncertain number instances created by different
        Contexts.
        
        """
        # Archive some simple stuff
        # This is the first archive. 
        c1 = Context()
        x1 = ureal(1,1,5,label='x1',context=c1)
        x2 = ucomplex(1,1,7,label='x2',context=c1)
        x3 = result( x1 + x2 )
        self.assert_( x3.real.is_intermediate )   

        ar = persistence.Archive(c1)
        ar.add(x1=x1,x2=x2,x3=x3)
        ar._freeze()

        # Now add some more stuff and store
        # in a second archive
        c2 = Context()
        ar.context = c2
        ar._thaw()
        
        y1 = ar['x1']
        y2 = ar['x2']
        y3 = ar['x3'] 

        self.assert_( y1.is_elementary )
        self.assert_( y2.is_elementary )
        self.assert_( not y3.is_elementary ) 

        self.assertEqual(y3.real._node.uid,x3.real._node.uid)
        self.assert_( y3.real.is_intermediate )   

        self.assert_(
            equivalent(component(x3,x1),component(y3,y1))
        )

        for i,j in zip(
            x3.real._i_components._index,
            y3.real._i_components._index
        ):
            self.assertEqual(i.uid,j.uid)
            self.assert_( equivalent(
                x3.real._i_components[i], 
                y3.real._i_components[j],
                TOL
            ))

        y4 = ureal(10,1,23,context=c2)
        y5 = ucomplex(2.5+7j,2,19,context=c2)
        y6 = result( y3 * (y4 + y5) )
        
        ar = persistence.Archive(c2)
        ar.add(
            y1=y1,
            y2=y2,
            y3=y3,
            y4=y4,y5=y5,y6=y6
        )
        ar._freeze()

        # Now restore into a third Context
        c3 = Context()
        ar.context=c3 
        ar._thaw()
        
        z1 = ar['y1']
        z2 = ar['y2']
        z3 = ar['y3']

        self.assert_( z1.is_elementary )
        self.assert_( z2.is_elementary )
        self.assert_( not z3.is_elementary )   

        # First just check that we get the same objects
        # and that the values are correct
        self.assertEqual(z1._node.uid,y1._node.uid)
        self.assertEqual(z1._node.uid[1],x1._node.uid[1])
        self.assertEqual(z1._node.uid[0],x1._node.uid[0])

        self.assert_(
            equivalent(value(z1),value(y1))
        )
        self.assert_(
            equivalent(value(z1),value(x1))
        )
        self.assert_(
            equivalent(uncertainty(z1),uncertainty(y1))
        )
        self.assert_(
            equivalent(uncertainty(z1),uncertainty(x1))
        )
        self.assert_(
            equivalent(dof(z1),dof(y1))
        )
        self.assert_(
            equivalent(dof(z1),dof(x1))
        )

        self.assertEqual(z2.imag._node.uid,y2.imag._node.uid)
        self.assertEqual(z2.real._node.uid,y2.real._node.uid)
        self.assertEqual(z2.real._node.uid,x2.real._node.uid)
        self.assertEqual(z2.imag._node.uid,x2.imag._node.uid)
        self.assert_(
            equivalent(value(z2.real),value(y2.real))
        )
        self.assert_(
            equivalent(value(z2.real),value(x2.real))
        )
        self.assert_(
            equivalent(uncertainty(z2.real),uncertainty(y2.real))
        )
        self.assert_(
            equivalent(uncertainty(z2.real),uncertainty(x2.real))
        )
        self.assert_(
            equivalent(dof(z2),dof(y2))
        )
        self.assert_(
            equivalent(dof(z2),dof(x2))
        )
        self.assertEqual(z2.imag._node.uid,y2.imag._node.uid)
        self.assertEqual(z2.imag._node.uid,x2.imag._node.uid)
        
        self.assert_(
            equivalent(value(z2.imag),value(y2.imag))
        )
        self.assert_(
            equivalent(value(z2.imag),value(x2.imag))
        )
        self.assert_(
            equivalent(uncertainty(z2.imag),uncertainty(y2.imag))
        )
        self.assert_(
            equivalent(uncertainty(z2.imag),uncertainty(x2.imag))
        )

        self.assert_(
            equivalent(value(z3.imag),value(y3.imag))
        )
        self.assert_(
            equivalent(value(z3.imag),value(x3.imag))
        )
        self.assert_(
            equivalent(uncertainty(z3.imag),uncertainty(y3.imag))
        )
        self.assert_(
            equivalent(uncertainty(z3.imag),uncertainty(x3.imag))
        )

        # Uncertainty components
        self.assert_(
            equivalent(component(x3,x1),component(z3,z1))
        )
        # Illegal, different contexts
        self.assertRaises(RuntimeError,component,z3,y1)
        
        self.assert_(
            equivalent_sequence(rp.u_component(x3,x2),rp.u_component(z3,z2))
        )

        # Continue to restore
        z4 = ar['y4']
        z5 = ar['y5']
        z6 = ar['y6']
        
        # Make sure the indexing of components is still ordered
        self.assert_( is_ordered(z6.real._u_components) )

        # First just check that we get the same objects
        # and that the values are correct
        self.assertEqual(z4._node.uid,y4._node.uid)
        self.assert_(
            equivalent(value(z4),value(y4))
        )
        self.assert_(
            equivalent(uncertainty(z4),uncertainty(y4))
        )
        self.assert_(
            equivalent(dof(z4),dof(y4))
        )

        self.assertEqual(z5.real._node.uid,y5.real._node.uid)
        self.assert_(
            equivalent(value(z5.real),value(y5.real))
        )
        self.assert_(
            equivalent(uncertainty(z5.real),uncertainty(y5.real))
        )
        self.assert_(
            equivalent(uncertainty(z5.imag),uncertainty(y5.imag))
        )

        # Components
        # We will get components wrt elementary inputs
        self.assert_(
            equivalent_sequence(rp.u_component(z6,z2),rp.u_component(y6,y2))
        )
        # And intermediates (provided this was requested)
        self.assert_(
            equivalent_sequence(rp.u_component(z6,z3),rp.u_component(y6,y3))
        )

        
#============================================================================
if(__name__== '__main__'):

    unittest.main()    # Runs all test methods starting with 'test'