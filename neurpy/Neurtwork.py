
import networkx as nx
import matplotlib.pyplot as plt
from xml.dom import minidom
import neuron

class Neurtwork( object ):
    ''' 
    Class to handle neuronal networks, with functionality to load from file.
    File is of modified GEXF format, modifications allowing for probes, stimuli
    and other attribute classifications.
    
    The `recordings` member contains the neuron.h.Vector objects which
    correspond to the soma probe attached to a given cell, as specified by a
    `probe` object in the loaded file. Also has a "probe tag" to help identify
    what cell is being recorded; the tag can be specified within the file or
    can be automatically generated by `cell name`_`probe ID`.
    '''
    def __init__( self, env, filepath=None ):
        self.cells = []
        self.cellDict = {}
        self.headCell = []
        self.nxGraph = None
        self.recordings = []
        self.stimuli = []
        if( filepath ):
            self.loadTopology( filepath, env )
        
    def loadTopology( self, filePath, env ):
        ''' Load graph from pseudo-GEXF file '''
        domFile = minidom.parse( filePath )

        # Helper function; return default if attrib not found
        def getAttribDefault( element, name, default ):
            val = element.getAttribute( name )
            if not val:
                val = default
            return val            

        # Locate the elements required
        cells = domFile.getElementsByTagName( 'cell' )
        edges = domFile.getElementsByTagName( 'edge' )
        stimuli = domFile.getElementsByTagName( 'stim' )
        probes = domFile.getElementsByTagName( 'probe' )

        # Load in each cell
        for cell in cells:
            id = cell.getAttribute( "id" )
            cellType = cell.getAttribute( "cellType" )
            cellName = cell.getAttribute( "cellName" )
            enSyn = 1#cell.getAttribute( "label" ) == "Head"
            self.cellDict[ id ] = env.createCell( cellType, cellName, enSyn )
          #  self.cellDict[ id ].tempStim()
            if( cell.getAttribute( "label" ) == "Head" ):
                print( "Enabling all stimuli for cell %s" % id )
                self.cellDict[ id ].tempStim()
        i = 0
        for edge in edges:
            source = edge.getAttribute( "source" )
            target = edge.getAttribute( "target" )
            excProp = float( getAttribDefault( edge, "excProportion", "0.0" ) )
            inhProp = float( getAttribDefault( edge, "inhProportion", "0.0" ) )
            weight = getAttribDefault( edge, "weight", None )
            delay = getAttribDefault( edge, "delay", None )
            threshold = getAttribDefault( edge, "threshold", None )
            # Can't add a connection if theres no weight/delay
            if( not weight or not delay ):
                "Error: No weight/delay specification for edge!"
                continue
            weight = float( weight )
            delay = float( delay )
            if threshold:
                threshold = float( threshold )
            
            self.cellDict[ source ].addChild( self.cellDict[ target ], excProp, inhProp, weight, delay, threshold )
            i += 1
        
        for stim in stimuli:
            # For now this is just the same as in the sample code.
            # May change later to something else

            target = stim.getAttribute( 'target' )
            stimFile = stim.getAttribute( 'stimFile' )
            delay = float( stim.getAttribute( 'delay' ) )
            dur = float( stim.getAttribute( 'dur' ) )

            cell = self.cellDict[ target ].neurCell

            if not stimFile:
                stimFile = './current_amps.dat'
            
            step_amp = [0] * 3
            with open( 'current_amps.dat', 'r' ) as current_amps_file:
                first_line = current_amps_file.read().split( '\n' )[ 0 ].strip()
                hyp_amp, step_amp[ 0 ], step_amp[ 1 ], step_amp[ 2 ] = first_line.split( ' ' )

            iclamp = neuron.h.IClamp( 0.5, sec=cell.soma[ 0 ] )
            iclamp.delay = 700
            iclamp.dur = 2000
            iclamp.amp = float( step_amp[ 0 ] )

            self.stimuli.append( iclamp )

            hyp_iclamp = neuron.h.IClamp( 0.5, sec=cell.soma[ 0 ] )
            hyp_iclamp.delay = 0
            hyp_iclamp.dur = 3000
            hyp_iclamp.amp = float( hyp_amp )

            self.stimuli.append( hyp_iclamp )
            


        for probe in probes:
            target = probe.getAttribute( "target" )
            probeTag = probe.getAttribute( "tag" )
            probeID = probe.getAttribute( "id" )
            targetCell = self.cellDict[ target ]
            if not probeTag:
                probeTag = "%s_%s" %( targetCell.cellName, probeID )
            
            newRecording = neuron.h.Vector()
            newRecording.record( targetCell.neurCell.soma[ 0 ]( 0.5 )._ref_v, 0.1 )
            self.recordings.append( ( probeTag, newRecording ) )

        '''
        # Test: measure the voltage at some dendrites on the second cell.
        for i in range( 10 ):
        #    targetInd = self.cellDict[ "0" ].children[ i ][ 2 ]
        #    targetRec = self.cellDict[ "0" ].neurCell.synapses.synapse_list.o( targetInd )
            targetRec = self.cellDict[ "1" ].neurCell.dend[ i ]( 0.5 )
            newRecording = neuron.h.Vector()
            newRecording.record( targetRec._ref_v, 0.1 )
            self.recordings.append( ( "dend %i" % i, newRecording ) )
'''
        #self.nxGraph = nx.MultiDiGraph( nx.read_gexf( filePath ) )
        #plt.subplot( 122 )
        #nx.draw( self.nxGraph )
    
    def simulate( self ):
        pass
