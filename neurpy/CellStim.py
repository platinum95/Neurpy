import neuron
import random

class CellStim:

    def __init__( self ):
        self.netstim = None
        self.netcons = []
        self.active = False
        self.symbolProbability = 1.0
        self.activeHistory = []
        self.interval = 100
        self.weight = 1.0
        self.delay = 0.0

    def setProperties( self, weight=None, delay=None, interval=None ):
        self.interval = interval
        self.delay = delay
        self.weight = weight

        self.netstim.interval = self.interval
        for netcon in self.netcons:
            netcon.delay = self.delay
            netcon.weight[ 0 ] = self.weight

    def createStim( self ):
        netstim = neuron.h.NetStim( )
        netstim.start = 0
        netstim.interval = self.interval
        netstim.number = 1e20
        netstim.noise = 1
        self.netstim = netstim

    def connectToSynapse( self, synapse ):
        netcon = neuron.h.NetCon( self.netstim, synapse )
        netcon.delay = self.delay
        netcon.weight[ 0 ] = self.weight
        self.netcons.append( netcon )


    def setActive( self, active ):
        if active and not self.active:
            for netcon in self.netcons:
                netcon.weight[ 0 ] = 1.0
            self.active = True
            return 0
        elif not active and self.active:
            for netcon in self.netcons:
                netcon.weight[ 0 ] = 0.0
            self.active = False
            return 0
        else:
            return 1

    def updateStimulus( self ):
        
        gProb = random.uniform( 0.0, 1.0 )
        if self.symbolProbability > gProb and not self.active:
            # Enable stim
            self.setActive( True )

        elif self.symbolProbability <= gProb and self.active:
            # Disable stim
            self.setActive( False )
        self.activeHistory.append( int( self.active ) )

