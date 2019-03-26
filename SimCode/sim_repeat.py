
import os 
netDir = os.path.dirname( "./2cell_networks/" )
outDir = os.path.dirname( "./2cell_rpt_outputs/" )

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
    with open( "./thread-%i" % affinity, 'w' ) as f:
        sys.stdout = f
        sys.stderr = f
        simOutputName = outName
        metadataOutputName = outName + "_meta.json"
        if not os.path.exists( './x86_64' ):
            print( "WARNING: You're probably running without compiling\
                    the mechanisms first. This isn't recommended." )

        netEnv = NeuronEnviron( "./modelBase", "./modelBase/global_mechanisms" )
        network = netEnv.loadTopology( netName )

        srcCell = network.cellDict[ '0' ]
        destCell = network.cellDict[ '1' ]
        # Lets move the destination cell down by a certain amount
        srcYSize = srcCell.getSize()[ 1 ]

        destCell.translate( [ 0, srcYSize / 2.0 , 0 ] )
        srcPos = srcCell.position
        destPos = destCell.position
        distance = math.sqrt( pow( srcPos[ 0 ] - destPos[ 0 ], 2.0 ) +
                            pow( srcPos[ 1 ] - destPos[ 1 ], 2.0 ) +
                            pow( srcPos[ 2 ] - destPos[ 2 ], 2.0 ) )
        edge = network.edges[ '0' ][ '1' ]
        # Only 1 stimulus
        stimulus = network.stimuli[ 0 ]
        stimDelay = 3.0
        stimWeight = 1.0
        stimInterval = 120
        stimulus[ 5 ].setProperties( weight=stimWeight, delay=stimDelay,
                                interval=stimInterval )
        stimulus[ 5 ].symbolProbability = 1.0

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


print("start")

outBase = "output"

if not os.path.exists( outDir ):
    os.makedirs( outDir )

numAvailCpus = multiprocessing.cpu_count()
numProcs = int( numAvailCpus/2 )
procHandles = [ None ] * numProcs
# Filenumber, last piped time, pipe
procInfo = [ ]
getAffinity = lambda pId : ( pId * 2 ) % ( numAvailCpus ) +\
               ( 1 if( pId * 2 >= numAvailCpus and numAvailCpus % 2 == 0 ) else 0 )
for i in range( numProcs ):
    procInfo.append( [ 0, 0, Value( 'L', 0 ), getAffinity( i ) ] )

numRepeats = 100

curFile = 0
finitio = False

networkFile = "./2cell_networks/testwork-00.xml"

startTime = time.time()
throughput = 0.0

while curFile < numRepeats and not finitio:
    finitio = True
    for i in range( numProcs ):
        if not procHandles[ i ] or not procHandles[ i ].is_alive():
            if curFile < numRepeats:
                if( procHandles[ i ] and procHandles[ i ].exitcode ):
                    print( "\nERROR: Thread %i exited with code %i."
                            % ( i, procHandles[ i ].exitcode ) )
                    sys.exit( 1 )
                    break
                # Get the simulation time in seconds
                simTime = time.time() - startTime
                # Get the throughput in sims/min
                throughput = ( curFile / simTime ) * 60.0
                procInfo[ i ][ 0 ] = curFile           
                nextFile = networkFile
                outName = "output-00-%02i" % ( curFile )
                curFile += 1
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
print( "Finishing..." )
