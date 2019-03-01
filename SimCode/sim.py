import sys
import os

def runSim( netName, outName, pipe ):
    import neurpy
    from neurpy.NeuronEnviron import NeuronEnviron
    from neurpy.Neurtwork import Neurtwork
    import neuron
    import os
    import numpy as np
    f = open( os.devnull, 'w' )
    sys.stdout = f
    sys.stderr = f
    if not os.path.exists( './x86_64' ):
        print( "WARNING: You're probably running without compiling\
                the mechanisms first. This isn't recommended." )

    netEnv = NeuronEnviron( "./modelBase", "./modelBase/global_mechanisms" )
    network = netEnv.loadTopology( netName )
   
    outPath = os.path.join( outDir, outName )    
    netEnv.runSimulation( outPath, pipe )
    sys.exit( 0 )



import os

import time

import neurpy
from neurpy.NeuronEnviron import NeuronEnviron
from neurpy.Neurtwork import Neurtwork
import neuron
import os
import numpy as np
import multiprocessing
from multiprocessing import Process, Pipe, Value


# if not os.path.exists( './x86_64' ):
#     print( "WARNING: You're probably running without compiling\
#             the mechanisms first. This isn't recommended." )

# netEnv = NeuronEnviron( "./modelBase", "./modelBase/global_mechanisms" )
# network = netEnv.loadTopology( "./networks/testwork-00.xml" )
# outPath = os.path.join( "./outputs/", "output.csv" )
# neuron.h.tstop = 100
# netEnv.runSimulation( outPath, Value( 'L', 0 ) )

# sys.exit( 0 )
    
print("start")



netDir = os.path.dirname( "./networks/" )
outDir = os.path.dirname( "./outputs/" )
outBase = "output"

if not os.path.exists( outDir ):
    os.makedirs( outDir )

validFiles = [ x for x in os.listdir( netDir ) if x.endswith( ".xml" ) ]
validFiles.sort( )
print( "Running over %i files" % len( validFiles ) )
numProcs = int( multiprocessing.cpu_count() / 2 )
procHandles = [ None ] * numProcs
# Filenumber, last piped time, pipe
procInfo = [ ]

for i in range( numProcs ):
    procInfo.append( [ 0, 0, Pipe( False ), Value( 'L', 0 ) ] )

curFile = 0
finitio = False

while curFile < len( validFiles ) and not finitio:
    finitio = True
    for i in range( numProcs ):
        if not procHandles[ i ] or not procHandles[ i ].is_alive():
            if curFile < len( validFiles ):
                nextFile = validFiles[ curFile ]
                procInfo[ i ][ 0 ] = curFile           
                nextFile = os.path.join( netDir, nextFile )
                outName = "%s-%02i.csv" % ( outBase, curFile )
                curFile += 1
                procHandles[ i ] = Process( target=runSim, 
                                            args=( nextFile, 
                                                   outName, 
                                                   procInfo[ i ][ 3 ] 
                                                 ) 
                                           )
                procHandles[ i ].start()
                finitio = False
        else:
            finitio = False
        #if procInfo[ i ][ 2 ][ 0 ].poll():
        #    procInfo[ i ][ 1 ] = procInfo[ i ][ 2 ][ 0 ].recv()

    sys.stdout.write('\r')
    sys.stdout.flush()
    sys.stdout.write( "Process/file/sim time | " )
    for i in range( numProcs ):
        pFile = procInfo[ i ][ 0 ]
        pTime = procInfo[ i ][ 3 ].value
        sys.stdout.write( "%i/%i/%i | " % ( i, pFile, pTime ) )
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
