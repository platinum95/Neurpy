import neuron
import os
from neurpy.pyCell import pyCell
from neurpy.NeurGUI import NeurGUI
from neurpy.Neurtwork import Neurtwork
import subprocess
from importlib import reload
import numpy as np
import sys
import re
import pickle

class NeuronEnviron( object ):
    def __init__(  self, modelRoot, mechanismRoot ):
        self.modelRoot = modelRoot
        self.loadedCells = {}
        subprocess.call( [ 'nrnivmodl', mechanismRoot ])
        neuron.h.load_file("stdrun.hoc")
        neuron.h.load_file("import3d.hoc")
        neuron.h.tstop = 1000
        self.networks = []

        # Next make sure we have a cache of the mtype-> template names
        # for all the cells
        self.templateCachePath = './.tmpl_cache'
        self.templateCache = {}
        if not os.path.exists( self.templateCachePath ):
            print( "No template cache found, creating..." )
            self.__recurseFolders( modelRoot )
            with open( self.templateCachePath, "wb" ) as pklFile:
                pickle.dump( self.templateCache, pklFile )
        else:
            print( "Template cache found, loading..." )
            with open( self.templateCachePath, "rb" ) as pklFile:
                self.templateCache = pickle.load( pklFile )

    def createCell( self, cellDirName, synEn=0 ):
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
        cellTypeName = self.templateCache[ cellDirName ]
        newCell = pyCell( cellTypeName, synEn, caller="neurpy" )
        synapseDataPath = os.path.join( cellRoot, "synapses/synapses.tsv" )
        newCell.loadCellSynapses( synapseDataPath )
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

        timeRecording = neuron.h.Vector()
        timeRecording.record( neuron.h._ref_t, 0.1 )
        neuron.h.cvode_active( 0 )

        import matplotlib
        matplotlib.rcParams['path.simplify'] = False

        import pylab

        fig = pylab.figure()
        ax = fig.add_subplot(111)
      #  lineA, = ax.plot(x, y, 'r-')
      #  lineB, = ax.plot(x, y, 'r-')
      #  lineC, = ax.plot(x, y, 'r-')
        
        pylab.xlabel( 'time (ms)' )
        pylab.ylabel( 'Vm (mV)' )
        pylab.gcf().canvas.set_window_title( 'Test' )


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

        neuron.h.run()
        time = np.array( timeRecording )
        recs = []
        header = 'time'

        graphCols = [ 'r-', 'g-', 'b-', 'c-', 'm-' ]

        i = 0
        for network in self.networks:
            for rec in network.recordings:
                recVec = rec[ 1 ].as_numpy()
                recNp = np.array( recVec )
                recs.append( recNp )
                header += ', %s' % rec[ 0 ]
                ax.plot( time, recNp, graphCols[ i ], label=rec[ 0 ] )
                i += 1

        fig.legend()
        pylab.show()
        recs.insert( 0, time )
        
        if( outputFilepath ):
            data = np.transpose( np.vstack( tuple( recs ) ) )
            np.savetxt( outputFilepath, data, delimiter=',', 
                        header=header, comments='' )
                         
        return recs

    def generateGUI( self, recSec, synapses=False ):
        return NeurGUI( recSec, synapses )


    def __cacheCellName( self, templatePath ):
        root, templateName = os.path.split( templatePath )
        cellMTypeName = os.path.basename( root )
        templateStr = None
        with open( templatePath, 'r' ) as tmplFile:
            for line in tmplFile:
                if( re.search( r"^begintemplate.*", line ) ):
                    line = re.sub( r"(.*begintemplate)|[\r\n]|[ ]", '', line )
                    templateStr = line.strip()
                    break
        if not templateStr:
            print( "Warning! Could not find template name for %s" % templatePath )
            return
        
        self.templateCache[ cellMTypeName ] = templateStr


    def __recurseFolders( self, rootDir ):
        # Check for the cell template file
        dirListing = [ sub for sub in os.listdir( rootDir ) ]
        templateFiles = [ os.path.join( rootDir, tmpl ) for tmpl in dirListing if re.search( r'template\.hoc', tmpl ) and os.path.isfile( os.path.join( rootDir, tmpl ) ) ]
        if templateFiles:
            if len( templateFiles ) != 1:
                print( "More than 1 template file? Wat" )
            self.__cacheCellName( templateFiles[ 0 ] )    
            
        else:
            dirs = [ os.path.join( rootDir, dir ) for dir in dirListing if os.path.isdir( os.path.join( rootDir, dir ) ) ]
            for dir in dirs:
                self.__recurseFolders( dir )
