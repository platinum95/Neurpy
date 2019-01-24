import neurpy
from neurpy.NeuronEnviron import NeuronEnviron
from neurpy.Neurtwork import Neurtwork
import neuron
import os

if not os.path.exists( './x86_64' ):
    print( "WARNING: You're probably running without compiling\
            the mechanisms first. This isn't recommended." )
            
# # Instantiate the cell from the template
testEn = NeuronEnviron( "./modelBase", "./modelBase/global_mechanisms" )
network = testEn.loadTopology( './SimCode/net.xml' )
#cell2 = testEn.createCell( "L6_BP_bAC217_1", "bAC217_L6_BP_b41e8e0c23" )
#cell = testEn.createCell( "L1_DAC_bNAC219_1", "bNAC219_L1_DAC_ec2fc5f0de", synEn=1 )
#cell3 = testEn.createCell( "L1_DAC_bNAC219_1", "bNAC219_L1_DAC_ec2fc5f0de" )
#cell4 = testEn.createCell( "L1_DAC_bNAC219_1", "bNAC219_L1_DAC_ec2fc5f0de" )

#secs = [ sec for sec in cell.neurCell.all ]
#sec = secs[ 0 ]
#somaPre = [ neuron.h.x3d( 0, sec=sec ), neuron.h.y3d( 0, sec=sec ), neuron.h.z3d( 0, sec=sec ) ]
#somaPost = [ neuron.h.x3d( 0, sec=sec ), neuron.h.y3d( 0, sec=sec ), neuron.h.z3d( 0, sec=sec ) ]

#gui = testEn.generateGUI( list( network.cellDict.values() )[ 0 ].neurCell , synapses=True )
#gui.createMainWindow()


testEn.runSimulation( './output.dat' )
#lSize = list( testEn.networks[0].cellDict.values() )[ 1 ].getSize()

#list( testEn.networks[0].cellDict.values() )[ 1 ].translate( [ 0.0, 500.0, 0.0 ] )
#list( testEn.networks[0].cellDict.values() )[ 2 ].translate( [ 0.0, 250.0, 0.0 ] )

'''
print( "Went from %s to %s" % ( str( somaPre ), str( somaPost ) ) )

cell2.translate( [ 0.0, 500.0, 0.0 ] )
cell.addChild( cell2, 0.6 )
cell3.translate( [ 0.0, -500.0, 0.0 ] ) 
cell2.addChild( cell3, 0.5 )
cell4.translate( [ 0.0, 1000.0, 0.0 ] )
cell3.addChild( cell4, 0.5 )
'''
#cell = list( testEn.networks[0].cellDict.values() )[ 0 ]
#gui = testEn.generateGUI( cell.neurCell, synapses=True )
#gui.createMainWindow()

#while( 1 ):
#    pass
