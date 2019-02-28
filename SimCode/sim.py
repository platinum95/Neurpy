
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
    network = netEnv.loadTopology( netName )
   
    outPath = os.path.join( outDir, outName )    
    netEnv.runSimulation( outPath )


import os
import sys
import time

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
network = netEnv.loadTopology( "./networks/testwork-00.xml" )
outPath = os.path.join( "./outputs/", "output.csv" )    
netEnv.runSimulation( outPath )

sys.exit( 0 )
    
print("start")



netDir = os.path.dirname( "./networks/" )
outDir = os.path.dirname( "./outputs/" )
outBase = "output"

if not os.path.exists( outDir ):
    os.makedirs( outDir )

for i, file in enumerate( os.listdir( netDir ) ):
    if not file.endswith( ".xml" ):
        continue
    file = os.path.join( netDir, file )
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

print( "Finishing..." )
