
            
# # Instantiate the cell from the template
#testEn = NeuronEnviron( "./modelBase", "./modelBase/global_mechanisms" )
#network = testEn.loadTopology( './SimCode/net.xml' )
#testEn.networks[0].cellDict[ "0" ].translate( [ 0.0, 750.0, 0.0 ] )
#testEn.networks[0].cellDict[ "1" ].translate( [ 0.0, 500.0, 0.0 ] )
#testEn.networks[0].cellDict[ "2" ].translate( [ 0.0, 250.0, 0.0 ] )
#testEn.networks[0].cellDict[ "3" ].translate( [ 0.0, 0.0, 0.0 ] )
#list( testEn.networks[0].cellDict.values() )[ 2 ].translate( [ 0.0, 250.0, 0.0 ] )
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
#while( 1 ):
#    pass

#vec = neuron.h.Vector()
#vecCurrent = neuron.h.Vector()
#headCell = testEn.networks[0].cellDict[ "0" ]
#recNetCon = neuron.h.NetCon( headCell.neurCell.axon[ 0 ]( 0.5 )._ref_v, None, sec=headCell.neurCell.axon[ 0 ] )
#recNetCon.weight[ 0 ] = 1.0
#recNetCon = testEn.networks[0].cellDict[ "0" ].children[ 0 ][ 1 ]
#recNetCon.record( vec )
#expSyn = testEn.networks[0].cellDict[ "0" ].children[ 0 ][ 2 ]
#vecCurrent.record( expSyn._ref_i, 0.1 )
#valid = recNetCon.valid()
#active = recNetCon.active()
#recNetCon.active( True )

#testEn.runSimulation( './output.csv' )
#recVec = testEn.networks[0].cellDict[ "0" ].children[ 0 ][ 1 ].get_recordvec().as_numpy()
#recVec = vecCurrent.as_numpy()
#recNp = np.array( recVec )
#recNp = np.transpose( recNp )
#np.savetxt( "./blah.csv", recNp, delimiter=',', 
#s                        header='', comments='' )

#lSize = list( testEn.networks[0].cellDict.values() )[ 1 ].getSize()

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
#gui = testEn.generateGUI( headCell.neurCell, synapses=True )
#gui.createMainWindow()

#gui = testEn.generateGUI( cell.neurCell.soma[0] )
#gui.createMainWindow()

def runSim( netName, outName ):
    import neurpy
    from neurpy.NeuronEnviron import NeuronEnviron
    from neurpy.Neurtwork import Neurtwork
    import neuron
    import os
    import numpy as np

    if not os.path.exists( './x86_64' ):
        print( "WARNING: You're probably running without compiling\
                the mechanisms first. This isn't recommended." )

    netEnv = NeuronEnviron( "./modelBase", "./modelBase/global_mechanisms" )
    network = netEnv.loadTopology( './SimCode/net.xml' )
   
    outPath = os.path.join( outDir, outName )
    netEnv.runSimulation( outPath )
    

import os
import sys

netDir = os.path.dirname( "./NeurGen/networks/" )
outDir = os.path.dirname( "./outputs/" )
outBase = "output"

if not os.path.exists( outDir ):
    os.makedirs( outDir )

for i, file in enumerate( os.listdir( netDir ) ):
    if not file.endswith( ".xml" ):
        continue
    print( "Forking" )
    try:
        pid = os.fork()
    except OSError:
        print( "No fork" )
    if pid == -1:
        print( "No fork" )
    elif pid == 0:
        print( "Child running file %s" % file )
        outName = "%s-%02i.csv" % ( outBase, i )
        runSim( file, outName )
        exit()
        
    else:
        print( "Waiting" )
        os.waitpid( pid, 0 )
        print( "Child done %i" % i )

