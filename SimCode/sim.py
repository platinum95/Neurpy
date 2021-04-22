
import os 
netDir = os.path.dirname( "./2cell_networks_l1force/" )
outDir = os.path.dirname( "./2cell_outputs_allSyn/" )

def runSim( netName, outName, pipe, affinity ):
    import neurpy
    from neurpy.NeuronEnviron import NeuronEnviron
    from neurpy.Neurtwork import Neurtwork
    import neuron
    import numpy as np
    import psutil
    import random

    p = psutil.Process()
    p.cpu_affinity( [ affinity ] )
    with open( f"./thread-{affinity}", 'w' ) as f:
        sys.stdout = f
        sys.stderr = f
        simOutputName = outName
        metadataOutputName = outName + "_meta.json"
        if not os.path.exists( './x86_64' ):
            print( "WARNING: You're probably running without compiling\
                    the mechanisms first. This isn't recommended." )

        netEnv = NeuronEnviron( "./modelBase", "./modelBase/global_mechanisms" )
        print( f"Running topology {netName}" )
        network = netEnv.loadTopology( netName )

        srcCell = network.cellDict[ '0' ]
        destCell = network.cellDict[ '1' ]
        # Lets move the destination cell down by a certain amount
        srcYSize = srcCell.getSize()[ 1 ]

        destCell.translate( [ 0, srcYSize /2.0 , 0 ] )
        srcPos = srcCell.position
        destPos = destCell.position
        distance = math.sqrt( pow( srcPos[ 0 ] - destPos[ 0 ], 2.0 ) +
                            pow( srcPos[ 1 ] - destPos[ 1 ], 2.0 ) +
                            pow( srcPos[ 2 ] - destPos[ 2 ], 2.0 ) )
        edge = network.edges[ '0' ][ '1' ]

        # Only 1 stimulus
     #   ncVec = neuron.h.Vector()
        stimulus = network.stimuli[ 0 ]
      #  stimulus[ 5 ].netcons[ 0 ].record( ncVec )
        stimDelay = 1.0#random.uniform( 0.1, 3.0 )
        stimWeight = 1.5#random.uniform( 1.0, 2.0 )
        stimInterval = 50#random.uniform( 50, 150 )
        stimulus[ 5 ].setProperties( weight=stimWeight, delay=stimDelay,
                                interval=stimInterval )
        stimulus[ 5 ].symbolProbability = 1.0
        stimulus[ 5 ].netstim.number = 1000

        #tgCell = network.cellDict[ "1" ]
      #  nGui = netEnv.generateGUI( tgCell.neurCell.soma[ 0 ], tgCell.neurCell )
      #  nGui.createMainWindow()
      #  while( 1 ):
      #      pass

        # Build the JSON metadata file
        metadata = {
            "preSynType" : network.cellDict[ '0' ].cellName,
            "postSynType" : network.cellDict[ '1' ].cellName,
            "connCount" : network.edges[ '0' ][ '1' ].connCount,
            "edgeDelay" : network.edges[ '0' ][ '1' ].delay,
            "edgeWeight" : network.edges[ '0' ][ '1' ].weight,
            "edgeSynType" : network.edges[ '0' ][ '1' ].synType,
            "distance" : distance,
            "stimulus" : {
                "interval" : stimulus[ 5 ].interval,
                "weight" : stimulus[ 5 ].weight,
                "delay" : stimulus[ 5 ].delay,
            },
        }

        metadataStr = json.dumps( metadata, indent=4 )
    
        simOutPath = os.path.join( outDir, simOutputName )
        metaOutPath = os.path.join( outDir, metadataOutputName )
        with open( metaOutPath, 'w' ) as metaFile:
            metaFile.write( metadataStr )
        netEnv.runSimulation( simOutPath, pipe )

      #  recVec = ncVec.as_numpy()
     #   recNp = np.array( recVec )
        print( "Simulation complete" )
    sys.exit( 0 )

import time

import numpy as np
import multiprocessing
from multiprocessing import Process, Pipe, Value
import json
import math
from io import StringIO
import sys
import re

print("start")


#runSim( "./SimCode/net.xml", "test", None, 1 )
#runSim( "./2cell_networks_l1force/network-00.xml", "test", None, 1 )

outBase = "output"

if not os.path.exists( outDir ):
    os.makedirs( outDir )

validFiles = [ ( x, int( re.search( "[0-9]+", x )[ 0 ] ) )
                for x in os.listdir( netDir ) if x.endswith( ".xml" ) ]
validFiles.sort( key=lambda val:val[ 1 ] )
print( "Running over %i files" % len( validFiles ) )
numAvailCpus = multiprocessing.cpu_count()
numProcs = int( numAvailCpus )
procHandles = [ None ] * numProcs
# Filenumber, last piped time, pipe
procInfo = [ ]
getAffinity = lambda pId : ( pId * 2 ) % ( numAvailCpus ) +\
               ( 1 if( pId * 2 >= numAvailCpus and numAvailCpus % 2 == 0 ) else 0 )
for i in range( numProcs ):
    procInfo.append( [ 0, 0, Value( 'L', 0 ), getAffinity( i ) ] )

startOffset = 3420

curFile = startOffset
finitio = False

startTime = time.time()
throughput = 0.0

while curFile < len( validFiles ) and not finitio:
    finitio = True
    for i in range( numProcs ):
        if not procHandles[ i ] or not procHandles[ i ].is_alive():
            if curFile < len( validFiles ):
                if( procHandles[ i ] and procHandles[ i ].exitcode ):
                    print( "\nERROR: Thread %i exited with code %i."
                            % ( i, procHandles[ i ].exitcode ) )
                    #sys.exit( 1 )
                    #break
                # Get the simulation time in seconds
                simTime = time.time() - startTime
                # Get the throughput in sims/min
                throughput = ( ( curFile - startOffset ) / simTime ) * 60.0
                nextFile = validFiles[ curFile ][ 0 ]
                procInfo[ i ][ 0 ] = curFile           
                nextFile = os.path.join( netDir, nextFile )
                outName = "%s-%02i" % ( outBase, curFile )
                curFile += 1
                #runSim( nextFile, outName, procInfo[ i ][ 2 ], procInfo[ i ][ 3 ] )
                procHandles[ i ] = Process( target=runSim, 
                                            args=( nextFile, 
                                                   outName, 
                                                   procInfo[ i ][ 2 ],
                                                   procInfo[ i ][ 3 ]
                                                 )
                                           )
                procHandles[ i ].start()
                finitio = False
        else:
            finitio = False

    sys.stdout.write('\r')
   # sys.stdout.write( '\033[F' )
    sys.stdout.flush()
    sys.stdout.write( "Process/file/sim time | " )
    for i in range( numProcs ):
        pFile = procInfo[ i ][ 0 ]
        pTime = procInfo[ i ][ 2 ].value
        sys.stdout.write( "%i/%i/%i | " % ( i, pFile, pTime ) )
    sys.stdout.write( "Throughput %i sims/min" % throughput )
    sys.stdout.flush()
    time.sleep( 0.001 )
        
    

print( "All done!" )
# for i, file in enumerate( os.listdir( netDir ) ):
#     if not file.endswith( ".xml" ):
#         continue
#     file = os.path.join( netDir, file )
#     print( "Forking" )
#     try:
#         pid = os.fork()
#     except OSError:
#         print( "No fork" )
#     if pid == -1:
#         print( "No fork" )
#     elif pid == 0:
#         print( "Child running file %s" % file )
#         outName = "%s-%02i.csv" % ( outBase, i )
#         runSim( file, outName )
#         exit()
        
#     else:
#         print( "Waiting" )
#         os.waitpid( pid, 0 )
#         print( "Child done %i" % i )

print( "Finishing..." )
