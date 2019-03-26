import neuron
import os
from neurpy.pyCell import pyCell
from neurpy.Neurtwork import Neurtwork
import subprocess
from subprocess import PIPE
from importlib import reload
import numpy as np
import sys
import re
import pickle

class NeuronEnviron( object ):
    def __init__(  self, modelRoot, mechanismRoot ):
        self.modelRoot = modelRoot
        self.loadedCells = {}
        if not os.path.isdir( "./x86_64" ):
            subprocess.Popen( [ 'nrnivmodl', mechanismRoot ], stdin=PIPE, 
                                                            stdout=PIPE, 
                                                            stderr=PIPE )
        neuron.h.load_file("stdrun.hoc")
        neuron.h.load_file("import3d.hoc")
        neuron.h.tstop = 1000
        self.symbolTimeStep = 50
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

    def runSimulation( self, outputFilepath, pipe ):

        statEvent = neuron.h.StateTransitionEvent( 1 )
        symbEvent = neuron.h.StateTransitionEvent( 1 )

        tnext = neuron.h.ref( 1 )
        symbTime = neuron.h.ref( 1 )

        def fteinit():
            tnext[ 0 ] = 1.0 # first transition at 1.0
            symbTime[ 0 ] = 0.0 # Update symbols now

            statEvent.state( 0 )   # initial state
            symbEvent.state( 0 )
            print( "Starting simulation of length %ims" % neuron.h.tstop )

        fih = neuron.h.FInitializeHandler( 1, fteinit )

        timeRecording = neuron.h.Vector()
        timeRecording.record( neuron.h._ref_t, 0.1 )
        neuron.h.cvode_active( 0 )

    #    import matplotlib
    #    matplotlib.rcParams['path.simplify'] = False

#        import pylab

 #       fig = pylab.figure()
  #      ax = fig.add_subplot(111)
      #  lineA, = ax.plot(x, y, 'r-')
      #  lineB, = ax.plot(x, y, 'r-')
      #  lineC, = ax.plot(x, y, 'r-')
        
   #     pylab.xlabel( 'time (ms)' )
    #    pylab.ylabel( 'Vm (mV)' )
     #   pylab.gcf().canvas.set_window_title( 'Test' )


        def printStat( src ): # current state is the destination. arg gives the source
            if( src != 0 ):
                return
            # Write over the same line...
         #   sys.stdout.write('\r')
         #   sys.stdout.flush()
         #   sys.stdout.write( "Time: %ims" % int( neuron.h.t ) )
         #   sys.stdout.flush()
            tnext[0] += 1.0 # update for next transition
            pipe.value = int( neuron.h.t )
        
        def updateSymbols( src ):
            if( src != 0 ):
                return
            for network in self.networks:
                network.updateStimuli()
            symbTime[ 0 ] += self.symbolTimeStep


        statEvent.transition( 0, 0, neuron.h._ref_t, tnext, ( printStat, 0 ) )
        symbEvent.transition( 0, 0, neuron.h._ref_t, symbTime, 
                              ( updateSymbols, 0 ) )

        neuron.h.run()
        symbHist  = []
        for network in self.networks:
            for stim in network.stimuli:
                symbHist.append( [ stim[ 0 ], stim[ 5 ].activeHistory ] )

        symbTimeVec = [ i * self.symbolTimeStep 
                            for i in range( len( symbHist[ 0 ][ 1 ] ) ) ]
        
        time = np.array( timeRecording )
        recs = []
        header = 'time'
        header2 = 'time'

        graphCols = [ 'r-', 'g-', 'b-', 'c-', 'm-' ]

        i = 0
        for network in self.networks:
            for rec in network.recordings:
                recVec = rec[ 1 ].as_numpy()
                recNp = np.array( recVec )
                recs.append( recNp )
                header += ', %s' % rec[ 0 ]
     #           ax.plot( time, recNp, graphCols[ i ], label=rec[ 0 ] )
                i += 1

        symbs = []
        for symb in symbHist:
            header2 += ', %s' % symb[ 0 ]
            symbs.append( np.array( symb[ 1 ] ) )
        
 #       fig.legend()
        
  #     fig2 = pylab.figure()
   #     ax2 = fig2.add_subplot(111)
  #      for symb in symbHist:
  #          ax2.step( symbTimeVec, symb[ 1 ] )

        # for symb in symbHist:
        #     fig3 = pylab.figure()
        #     ax3 = fig3.add_subplot( 111 )
        #     vs = [ x for x in self.networks[ 0 ].recordings 
        #             if x[ 2 ] == symb[ 0 ] ][ 0 ]
        #     recVec = vs[ 1 ].as_numpy()
        #     recNp = np.array( recVec )

        #     ax3.step( symbTimeVec, symb[ 1 ] )
        #     ax3.plot( time, recNp )
     #   pylab.show()
        recs.insert( 0, time )
        symbs.insert( 0, symbTimeVec )        
        if( outputFilepath ):

            probeData = np.transpose( np.vstack( tuple( recs ) ) )
            probeFilepath = outputFilepath + "_probes.csv"
            np.savetxt( probeFilepath, probeData, delimiter=',', 
                        header=header, comments='' )

            stimFilepath = outputFilepath + "_stim.csv"
            stimData = np.transpose( np.vstack( tuple( symbs ) ) )
            np.savetxt( stimFilepath, stimData, delimiter=',',
                        header=header2, comments='' )
                         
        return recs

    def generateGUI( self, recSec, stimCell, synapses=False ):
        from neurpy.NeurGUI import NeurGUI
        return NeurGUI( recSec, stimCell, synapses )


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
