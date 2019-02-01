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

    def addChild( self, targetCell, exciteProp, inhibProp, weight, delay, threshold=None ):
        ''' 
        Connect to `prop` random cells for both excitatory and
        inhibitory
        '''
        if( exciteProp == 0 and inhibProp == 0 ):
            print( "Warning: Adding child cell with no connected synapses!" )
        # Start by getting the indices of the excitatory synapses
        synType = self.neurCell.synapses.pre_mtypes_excinh
        excInd = [ ( i, 0 ) for i, x in enumerate( synType ) if x == 0 ]
        inhInd = [ ( i, 1 ) for i, x in enumerate( synType ) if x == 1 ]

        # Randomly select synapses by shuffling and selecting the first
        # N indices based on the connection proportion
        shuffle( excInd )
        shuffle( inhInd )

        numSelectExc = int( exciteProp * float( len( excInd ) ) )
        numSelectInh = int( inhibProp  * float( len( inhInd ) ) )

        excInd = excInd[ 0 : numSelectExc ]
        inhInd = inhInd[ 0 : numSelectInh ]
        
        # Now connect up to the synapses
        for ind, typ in excInd + inhInd:
            # Get the synapse object (hoc type)
            synapse = targetCell.neurCell.synapses.synapse_list.o( ind )
            weight = targetCell.neurCell.synapses.weights.x[ ind ]
            delay = targetCell.neurCell.synapses.delays.x[ ind ]

            # Create a new NetCon object to connect our cell to the target synapse
            ourSoma = self.neurCell.soma[ 0 ]
            netCon = neuron.h.NetCon( ourSoma(0.5)._ref_v, synapse, sec=ourSoma )

            # Append some info about the connection to our cell and the target cell
            self.children.append( ( targetCell, netCon, ind, typ ) )
            targetCell.parents.append( ( self, netCon, ind, typ ) )

            # Set the parameters of the NetCon
            netCon.weight[ 0 ] = weight
            netCon.delay = delay
            if threshold:
                netCon.threshold = threshold

        