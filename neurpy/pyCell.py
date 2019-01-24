import neuron
from random import shuffle

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

    
    def tempStim( self ):
        # Temp function to turn on all excitatory stimuli
        synType = self.neurCell.synapses.pre_mtypes_excinh
        excInd = [ i for i, x in enumerate( synType ) if x == 1 ]
        for ind in excInd:
            self.neurCell.synapses.netcon_list.o( ind ).weight[ 0 ] = 1.0



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
            print( "%s -> %i" % ( sec.name(), sec.L ) )
            for i in range( 0, int( neuron.h.n3d( sec=sec ) ) ):
                xNew = neuron.h.x3d( i, sec=sec ) + translation[ 0 ]
                yNew = neuron.h.y3d( i, sec=sec ) + translation[ 1 ]
                zNew = neuron.h.z3d( i, sec=sec ) + translation[ 2 ]
                diam = neuron.h.diam3d( i, sec=sec )
                neuron.h.pt3dchange( i, xNew, yNew, zNew, diam, sec=sec )
        self.position[ 0 ] += translation[ 0 ]
        self.position[ 1 ] += translation[ 1 ]
        self.position[ 2 ] += translation[ 2 ]

    def addChild( self, targetCell, exciteProp, inhibProp ):
        # targetSec = targetCell.dend[ 0 ].allseg()[ 0 ]]
        # Connect to `prop` random cells for both excitatory and
        # inhibitory
        
        # TEST STAGE - CONNECT ONLY TO EXCITORY
        # TODO - CHANGE TO CONNECT TO BOTH
        # TODO - USE GIVEN PROPORTION (REMOVE FOLLOWING LINE)
        exciteProp = 1.0

        # Start by getting the indices of the excitatory synapses
        synType = self.neurCell.synapses.pre_mtypes_excinh
        excInd = [ i for i, x in enumerate( synType ) if x == 1 ]
        # Randomly select synapses by shuffling and selecting the first
        # N indices based on the connection proportion
        shuffle( excInd )
        numSelect = int( exciteProp * float( len( excInd ) ) )
        excInd = excInd[ 0 : numSelect ]

        for ind in excInd:
            synapse = self.neurCell.synapses.synapse_list.o( ind )
            ourAxon = self.neurCell.axon[ 1 ]
            netCon = neuron.h.NetCon( ourAxon( 0.5 )._ref_v, synapse, sec=ourAxon )
            self.children.append( ( targetCell, netCon, ind ) )
            targetCell.parents.append( ( self, netCon, ind ) )
            netCon.weight[ 0 ] = 1.0
            netCon.delay = 0.3
            netCon.threshold = -10
            x = self.children[ -1 ][1].delay
        
        for i in range( 40 ):
            expSyn = neuron.h.ExpSyn( targetCell.neurCell.dend[ i ]( 0 ) )
            ourSoma = self.neurCell.soma[ 0 ]
            netCon = neuron.h.NetCon( ourSoma( 0.5 )._ref_v, expSyn, sec=ourSoma )
            netCon.weight[ 0 ] = 1.0
            netCon.delay = 0.3
            netCon.threshold = -10
            self.children.append( ( targetCell, netCon, expSyn ) )
            targetCell.parents.append( ( self, netCon, expSyn ) )