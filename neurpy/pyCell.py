import neuron
from random import shuffle, randint


class pyCell():
    def __init__( self, cellName, synEn=0, **kwargs ):
        if kwargs.get( "caller", "notNeurpy" ) != "neurpy":
            print( "Warning: Creating a cell without going through\
                    neurpy module, which is not recommended" )
        neuronCall = "neuron.h.%s(%i)" % ( cellName, synEn )
        # Use eval to turn the cell name into a neuron function call
        print( "Calling %s" % neuronCall )
        self.neurCell = eval( neuronCall )
        self.cellName = cellName
        self.boundingSize = self.getSize()
        self.position = [ 0.0, 0.0, 0.0 ]
        self.rotation = [ 0.0, 0.0, 0.0 ] #Euler rotation (for now)
        self.children = []
        self.parents = []
        self.synapses = None

    def loadCellSynapses( self, synapsePath ):
        self.synapses = Synapses( synapsePath, self.neurCell )

    
    def tempStim( self ):
        pass
        # Temp function to turn on all excitatory stimuli
        # synType = self.neurCell.synapses.pre_mtypes_excinh
        # excInd = [ i for i, x in enumerate( synType ) if x == 0 ]
        # for ind in excInd:
        #     mtypeNetcons = self.neurCell.synapses.pre_mtype_netconlists.o( ind )
        #     for netcon in mtypeNetcons:
        #         netcon.weight[ 0 ] = 1.0
        #     #self.neurCell.synapses.netcon_list.o( ind ).weight[ 0 ] = 10.0



    def getSize( self ):
        '''
        Get the bounding-box dimensions of this cell
        '''
        initSec = [ sec for sec in self.neurCell.all ][ 0 ]
        xPos = neuron.h.x3d( 0, sec=initSec )
        yPos = neuron.h.y3d( 0, sec=initSec )
        zPos = neuron.h.z3d( 0, sec=initSec )

        minmax = [ [ xPos, xPos ], [ yPos, yPos ], [ zPos, zPos ] ]

        for sec in self.neurCell.all:
            for i in range( 0, int( neuron.h.n3d( sec=sec ) ) ):
                xPos = neuron.h.x3d( i, sec=sec )
                yPos = neuron.h.y3d( i, sec=sec )
                zPos = neuron.h.z3d( i, sec=sec )
                minmax[ 0 ][ 0 ] = min( minmax[ 0 ][ 0 ], xPos )
                minmax[ 0 ][ 1 ] = max( minmax[ 0 ][ 1 ], xPos )
                minmax[ 1 ][ 0 ] = min( minmax[ 1 ][ 0 ], yPos )
                minmax[ 1 ][ 1 ] = max( minmax[ 1 ][ 1 ], yPos )
                minmax[ 2 ][ 0 ] = min( minmax[ 2 ][ 0 ], zPos )
                minmax[ 2 ][ 1 ] = max( minmax[ 2 ][ 1 ], zPos )

        xSize = minmax[ 0 ][ 1 ] - minmax[ 0 ][ 0 ]
        ySize = minmax[ 1 ][ 1 ] - minmax[ 1 ][ 0 ]
        zSize = minmax[ 2 ][ 1 ] - minmax[ 2 ][ 0 ]
        return ( xSize, ySize, zSize )

    def translate( self, translation ):
        ''' 
        Translate this Cell instance by a given amount.
        Input is a list with xyz translation points.
        '''

        for sec in self.neurCell.all:
           # print( "%s -> %i" % ( sec.name(), sec.L ) )
            for i in range( 0, int( neuron.h.n3d( sec=sec ) ) ):
                xNew = neuron.h.x3d( i, sec=sec ) + translation[ 0 ]
                yNew = neuron.h.y3d( i, sec=sec ) + translation[ 1 ]
                zNew = neuron.h.z3d( i, sec=sec ) + translation[ 2 ]
                diam = neuron.h.diam3d( i, sec=sec )
                neuron.h.pt3dchange( i, xNew, yNew, zNew, diam, sec=sec )
        self.position[ 0 ] += translation[ 0 ]
        self.position[ 1 ] += translation[ 1 ]
        self.position[ 2 ] += translation[ 2 ]

    def addChild( self, targetCell, synType, conCount, weight, delay, threshold=None ):
        ''' 
        Connect to `prop` random cells for both excitatory and
        inhibitory
        ''' 
        if( conCount == 0 ):
            print( "Warning: Adding child cell with no connected synapses!" )
        # Start by getting the indices of the excitatory synapses
        synapse = []#list( targetCell.neurCell.synapses.pre_mtypes_excinh )
        if synType == 1:
            synapses = targetCell.synapses.excSyn#inhSyn
        else:
            synapses = targetCell.synapses.excSyn


        if conCount > len( synapses ):
            print( "Warning! More connections requested than synapses exist! "
                    "Requested %i, but cell has %i" %( conCount, len( synapses ) ) )
            conCount = len( synapses ) - 1

        # Randomly select synapses by shuffling and selecting the first
        # N indices based on the connection proportion
        shuffle( synapses )
        conCount = len( synapses ) - 1
        synapses = synapses[ 0 : conCount ]
        
        for syn in synapses:
            syn.initialise( )

            # Create a new NetCon object to connect our cell to the target synapse
            ourSoma = self.neurCell.soma[ 0 ]
            netCon = neuron.h.NetCon( ourSoma(0.5)._ref_v, syn.synapse, sec=ourSoma )

            # Append some info about the connection to our cell and the target cell
            self.children.append( ( targetCell, netCon, synType ) )
            targetCell.parents.append( ( self, netCon, synType ) )

            # Set the parameters of the NetCon
            netCon.weight[ 0 ] = weight
            netCon.delay = delay
            if threshold:
                netCon.threshold = threshold


        # # Now connect up to the synapses
        # for ind in synapses:
        #     # Get the synapse object (hoc type)
        #     synapse = targetCell.neurCell.synapses.synapse_list.o( ind )
        #     weight = targetCell.neurCell.synapses.weights.x[ ind ]
        #     delay = targetCell.neurCell.synapses.delays.x[ ind ]

        #     # Create a new NetCon object to connect our cell to the target synapse
        #     ourSoma = self.neurCell.soma[ 0 ]
        #     netCon = neuron.h.NetCon( ourSoma(0.5)._ref_v, synapse, sec=ourSoma )

        #     # Append some info about the connection to our cell and the target cell
        #     self.children.append( ( targetCell, netCon, ind, synType ) )
        #     targetCell.parents.append( ( self, netCon, ind, synType ) )

        #     # Set the parameters of the NetCon
        #     netCon.weight[ 0 ] = weight
        #     netCon.delay = delay
        #     if threshold:
        #         netCon.threshold = threshold



class Synapse():
    def __init__( self, cellRef ):
        self.synapseId = None
        self.synapse = None
        self.preCellId = None
        self.preMType = None
        self.sectionlistId = None
        self.sectionlistIdx = None
        self.segX = None
        self.synType = None
        self.dep = None
        self.fac = None
        self.use = None
        self.tau_d = None
        self.delay = None
        self.weight = None
        self.initialised = False
        self.section = None
        self.sectionListName = ''
        self.synapseTypeName = ''
        self.synapseType = None
        self.rnList = []
        self.cellRef = cellRef

    def initialise( self ):
        '''
        Connect synapse to the given position on the cell
        '''
        if self.initialised:
            return

        celRef = self.cellRef

        # Create sectionref to the section the synapse will be placed on
        if ( self.sectionlistId == 0 ):
            self.section = neuron.h.SectionRef(
                sec=celRef.soma[ self.sectionlistIdx ] )
            self.sectionListName = "somatic"
        elif ( self.sectionlistId == 1 ):
            dList = list( celRef.dend )
            self.section = neuron.h.SectionRef(
                sec=celRef.dend[ self.sectionlistIdx ] )
            self.sectionListName = "basal"
        elif ( self.sectionlistId == 2 ):
            self.section = neuron.h.SectionRef(
                sec=celRef.apic[ self.sectionlistIdx ] )
            self.sectionListName = "apical"
        elif ( self.sectionlistId == 3 ):
            self.section = neuron.h.SectionRef(
                sec=celRef.axon[ self.sectionlistIdx ] )
            self.sectionListName = "axonal"
        else:
            print( "Sectionlist ID %i not supported!" % self.sectionlistId )
            return

        # If synapse_type < 100 the synapse is inhibitory, otherwise
        # excitatory
        if self.synType < 100:
            self.synapseTypeName = "inhibitory"
            self.synapseType = 1
            self.synapse = neuron.h.ProbGABAAB_EMS( self.segX, sec=self.section.sec )
            self.synapse.tau_d_GABAA  = self.tau_d
            rng = neuron.h.Random()
            rng.MCellRan4( randint( 0, 700 )*100000+100, randint( 0, 7000 )+250 )
            rng.lognormal(0.2, 0.1)
            self.synapse.tau_r_GABAA = rng.repick()
        else:
            self.synapseTypeName = "excitatory"
            self.synapseType = 0
            self.synapse = neuron.h.ProbAMPANMDA_EMS( self.segX, sec=self.section.sec )
            self.synapse.tau_d_AMPA = self.tau_d

        
        self.synapse.Use = abs( self.use )
        self.synapse.Dep = abs( self.dep )
        self.synapse.Fac = abs( self.fac )

        # TODO - Add extra synconf handling here

        rng = neuron.h.Random()
        rng.MCellRan4( randint( 0, 700 )*100000+100, randint( 0, 7000 )+250 )
        rng.uniform( 0, 1 )
        self.synapse.setRNG( rng )         
        self.rnList.append( rng )

        self.initialised = True



class Synapses():
    def __init__( self, synInfoPath, cellRef ):
        self.synapseList = []
        self.excSyn = []
        self.inhSyn = []
        synDataList = []
        with open( synInfoPath, 'r' ) as synFile:
            # Load the synapse data, but don't create any yet
            import csv
            synReader = csv.reader( synFile, delimiter='\t' )
            synDataList = list( synReader )

        if not synDataList:
            print( "Error: Could not load synapse file %s " % synInfoPath )
            return

        # Truncate to get just the data
        synDataList = synDataList[ 1: ]

        # Row/column count in header
        numSynapse = int( len( synDataList ) )
        numCols = int(  len( synDataList[ 0 ] ) )

        for idx, synData in enumerate( synDataList ):
            newSyn = Synapse( cellRef )
            newSyn.synapseId = int( synData[ 0 ] )
            newSyn.preCellId = int( synData[ 1 ] )
            newSyn.preMType = int( synData[ 2 ] )
            newSyn.sectionlistId = int( synData[ 3 ] )
            newSyn.sectionlistIdx = int( synData[ 4 ] )
            newSyn.segX = float( synData[ 5 ] )
            newSyn.synType = int( synData[ 6 ] )
            newSyn.dep = float( synData[ 7 ] )
            newSyn.fac = float( synData[ 8 ] )
            newSyn.use = float( synData[ 9 ] )
            newSyn.tau_d = float( synData[ 10 ] )
            newSyn.delay = float( synData[ 11 ] )
            newSyn.weight = float( synData[ 12 ] )
            self.synapseList.append( newSyn )
          #  print( "Loading synapse %i" % newSyn.synapseId )
            if newSyn.synType < 100:
                self.inhSyn.append( newSyn )
            else:
                self.excSyn.append( newSyn )
