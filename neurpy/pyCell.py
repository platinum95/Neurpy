import neuron

class pyCell():
    def __init__( self, cellName, **kwargs ):
        if kwargs.get( "caller", "notNeurpy" ) != "neurpy":
            print( "Warning: Creating a cell without going through\
                    neurpy module, which is not recommended" )
        neuronCall = "neuron.h.%s(0)" % cellName
        # Use eval to turn the cell name into a neuron function call
        print( "Calling %s" % neuronCall )
        self.neurCell = eval( neuronCall )
        self.position = [ 0.0, 0.0, 0.0 ]
        self.rotation = [ 0.0, 0.0, 0.0 ] #Euler rotation (for now)
        self.children = []
        self.parents = []

    def translate( self, translation ):
        ''' 
        Translate this Cell instance by a given amount.
        Input is a list with xyz translation points.
        '''

        for sec in self.neurCell.all:
            print( sec.name() )
            for i in range( 0, int( neuron.h.n3d( sec=sec ) ) ):
                xNew = neuron.h.x3d( i, sec=sec ) + translation[ 0 ]
                yNew = neuron.h.y3d( i, sec=sec ) + translation[ 1 ]
                zNew = neuron.h.z3d( i, sec=sec ) + translation[ 2 ]
                diam = neuron.h.diam3d( i, sec=sec )
                neuron.h.pt3dchange( i, xNew, yNew, zNew, diam, sec=sec )
        self.position[ 0 ] += translation[ 0 ]
        self.position[ 1 ] += translation[ 1 ]
        self.position[ 2 ] += translation[ 2 ]


    def addChild( self, targetCell, connectProportion ):
       # targetSec = targetCell.dend[ 0 ].allseg()[ 0 ]]
        expSyn = neuron.h.ExpSyn( targetCell.neurCell.dend[ 0 ]( 0 ) )
        ourSoma = self.neurCell.soma[ 0 ]
        netCon = neuron.h.NetCon( ourSoma( 0.5 )._ref_v, expSyn, sec=ourSoma )
        self.children.append( ( targetCell, netCon, expSyn ) )
        targetCell.parents.append( ( self, netCon, expSyn ) )