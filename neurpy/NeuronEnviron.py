import neuron
import os
from neurpy.pyCell import pyCell
from neurpy.NeurGUI import NeurGUI
from neurpy.Neurtwork import Neurtwork
import subprocess
from importlib import reload
import numpy as np
import sys

class NeuronEnviron( object ):
    def __init__(  self, modelRoot, mechanismRoot ):
        self.modelRoot = modelRoot
        self.loadedCells = {}
        subprocess.call( [ 'nrnivmodl', mechanismRoot ])
        neuron.h.load_file("stdrun.hoc")
        neuron.h.load_file("import3d.hoc")
        neuron.h.tstop = 1000
        self.networks = []

    def createCell( self, cellDirName, cellTypeName, synEn=0 ):
        cellRoot = os.path.join( self.modelRoot, cellDirName )
        cellRoot = os.path.abspath( cellRoot )
        cellLoaded = self.loadedCells.get( cellDirName, False )
        curDir = os.getcwd()
        os.chdir( cellRoot )
        if not cellLoaded:
            print( "Loading cell data from %s" % cellRoot )
            # Load main cell template, which will 
            # load biophysics and morphology
            templateFile = os.path.join( cellRoot, "template.hoc" )
            neuron.h.load_file( templateFile )
        newCell = pyCell( cellTypeName, synEn, caller="neurpy" )
        os.chdir( curDir )
        return newCell

    def loadTopology( self, filename ):
        neurtwork = Neurtwork( self, filename )
        self.networks.append( neurtwork )
        return neurtwork

    def addNetwork( self, network ):
        self.networks.append( network )

    def runSimulation( self, outputFilepath ):

        statEvent = neuron.h.StateTransitionEvent( 1 )

        tnext = neuron.h.ref(1)

        def fteinit():
            tnext[ 0 ] = 1.0 # first transition at 1.0
            statEvent.state( 0 )   # initial state
            print( "Starting simulation of length %ims" % neuron.h.tstop )

        fih = neuron.h.FInitializeHandler( 1, fteinit )

        def printStat( src ): # current state is the destination. arg gives the source
            if( src != 0 ):
                return
            # Write over the same line...
            sys.stdout.write('\r')
            sys.stdout.flush()
            sys.stdout.write( "Time: %ims" % int( neuron.h.t ) )
            sys.stdout.flush()
            tnext[0] += 1.0 # update for next transition

        statEvent.transition( 0, 0, neuron.h._ref_t, tnext, ( printStat, 0 ) )

        timeRecording = neuron.h.Vector()
        timeRecording.record( neuron.h._ref_t, 0.1 )
        neuron.h.cvode_active( 0 )
        neuron.h.run()
        time = np.array( timeRecording )
        recs = []
        header = 'time'

        for network in self.networks:
            for rec in network.recordings:
                recVec = rec[ 1 ].as_numpy()
                recNp = np.array( recVec )
                recs.append( recNp )
                header += ', %s' % rec[ 0 ]

        recs.insert( 0, time )
        
        if( outputFilepath ):
            data = np.transpose( np.vstack( tuple( recs ) ) )
            np.savetxt( outputFilepath, data, delimiter=',', 
                        header=header, comments='' )
                         
        return recs

    def generateGUI( self, recSec, synapses=False ):
        return NeurGUI( recSec, synapses )
