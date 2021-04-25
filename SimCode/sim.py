#!/usr/bin/env python3

import argparse
import curses
from curses import wrapper
from enum import Enum
from io import StringIO
import json
import math
import multiprocessing
from multiprocessing import Process, Pipe, Value
import numpy as np
import os
import pickle
import re
import sys
import time

parser = argparse.ArgumentParser( description="Run Neuron simulation" )
parser.add_argument( "-p", "--parallel", type=int, dest="numProcs", action="store", default=0, help="Number of simulations to run in parallel, 0 for automatic selection." )
parser.add_argument( "-l", "--logdir", type=str, dest="logDir", action="store", default="./logs", help="Path to location to store process logs" )
args = parser.parse_args()

availCores = int( multiprocessing.cpu_count() )
numProcs = availCores if args.numProcs == 0 else args.numProcs
multiProc = numProcs > 1

logDir = args.logDir

netDir = os.path.dirname( "./2cell_networks_l1force/" )
outDir = os.path.dirname( "./2cell_outputs_allSyn/" )

modelBaseDir = "./modelBase"
globalMechanismsDir = "./modelBase/global_mechanisms"

if not os.path.exists( './x86_64' ):
    print( f"ERROR: Missing mechanisms. Run `nrnivmodl {globalMechanismsDir}` before starting simulations." )
    sys.exit( 0 )

outBase = "output"

if not os.path.exists( outDir ):
    os.makedirs( outDir )

if not os.path.exists( logDir ):
    os.makedirs( logDir )

validFiles = [ ( x, int( re.search( "[0-9]+", x )[ 0 ] ) )
                for x in os.listdir( netDir ) if x.endswith( ".xml" ) ]
validFiles.sort( key=lambda val:val[ 1 ] )

# Filenumber, last piped time, pipe
affinities = []
getAffinity = lambda pId : ( pId * 2 ) % ( availCores ) +\
               ( 1 if( pId * 2 >= availCores and availCores % 2 == 0 ) else 0 )
for i in range( numProcs ):
    affinities.append( getAffinity( i ) )


startOffset = 3420

curFile = startOffset
finitio = False

startTime = time.time()
throughput = 0.0

class SimIpcMessageBase:
    def __init__( self ):
        pass

    def Send( self, pipe ):
        pipe.send( self )

class SimStatusMessage( SimIpcMessageBase ):
    def __init__( self ):
        super().__init__()

class SimProgress( SimStatusMessage ):
    progress = 0
    def __init__( self, progress ):
        super().__init__()
        self.progress = progress

class SimComplete( SimStatusMessage ):
    def __init__( self ):
        super().__init__()

class SimFailure( SimStatusMessage ):
    message = None
    def __init__( self, failureMessage ):
        super().__init__()
        self.message = failureMessage

class SimJob( SimIpcMessageBase ):
    networkId = 0
    networkPath = None

    def __init__( self, networkId, networkPath ):
        super().__init__()
        self.networkId = networkId
        self.networkPath = networkPath

class SimTerminate( SimIpcMessageBase ):
    def __init__( self ):
        super().__init__()

class SimState( Enum ):
    IDLE = 0
    SIMULATING = 1
    FAILURE = 2
    INIT = 3

class Sim:
    simFilePath = None
    simOutputpath = None
    processId = 0
    affinity = 0
    progress = 0
    simFile = None
    handle = None
    pipeTx = None
    pipeRx = None
    jobQueue = []

    state = SimState.INIT

    def __init__( self, processId, affinity ):
        self.processId = processId
        self.affinity = affinity
        
        self.pipeRx, self.pipeTx = multiprocessing.Pipe()
        self.handle = Process( target=self.simProcess )
        self.handle.start()

        if not self.pipeRx.poll( 1 ):
            self.state = SimState.FAILURE
            return
        
        while self.pipeRx.poll():
            try:
                recvd = self.pipeRx.recv()
                if isinstance( recvd, SimProgress ):
                    self.state = SimState.IDLE
                    return
            except EOFError:
                # Pipe closed unexpectedly
                self.state = SimState.FAILURE

    def queueSim( self, networkId, networkFilePath ):
        SimJob( networkId, networkFilePath ).Send( self.pipeTx )

    def update( self ):
        if self.state == SimState.FAILURE:
            return
        if not self.handle.is_alive():
            self.state = SimState.FAILURE
            return

        if not self.pipeRx.poll( 0.1 ):
            return
        try:
            while self.pipeRx.poll():
                message = self.pipeRx.recv()
                if isinstance( message, SimProgress ):
                    self.progress = message.progress
                    self.state = SimState.SIMULATING
                elif isinstance( message, SimFailure ):
                    self.state = SimState.FAILURE
                elif isinstance( message, SimComplete ):
                    self.state = SimState.IDLE
        except EOFError:
            # Pipe closed, process ended
            self.handle.join( 1 )
            if self.handle.exitcode == None:
                self.handle.kill()

    def getStatusString( self, availSpace ):
        if self.state == SimState.IDLE:
            return "Idle"
        elif self.state == SimState.FAILURE:
            return "Error"
        elif self.state == SimState.INIT:
            return "Initialising"
        else:
            numBars = math.floor( availSpace * self.progress )
            return ( "|" * numBars ) + ( " " * ( availSpace - numBars ) )

    def runJob( self, job ):
        print( f"Loading topology {job.networkPath}" )
        network = self.netEnv.loadTopology( job.networkPath )

        baseName = "%s-%02i" % ( outBase, job.networkId )
        simOutputBasePath = os.path.join( outDir, baseName )
        metadataOutputPath =  os.path.join( outDir, baseName + "_meta.json" )

        srcCell = network.cellDict[ '0' ]
        destCell = network.cellDict[ '1' ]

        # Lets move the destination cell down by a certain amount
        srcYSize = srcCell.getSize()[ 1 ]

        destCell.translate( [ 0, srcYSize /2.0 , 0 ] )
        srcPos = srcCell.position
        destPos = destCell.position
        distance = math.sqrt( pow( srcPos[ 0 ] - destPos[ 0 ], 2.0 ) +
                            pow( srcPos[ 1 ] - destPos[ 1 ], 2.0 ) +
                            pow( srcPos[ 2 ] - destPos[ 2 ], 2.0 ) )
        edge = network.edges[ '0' ][ '1' ]

        # Only 1 stimulus
        stimulus = network.stimuli[ 0 ]
        stimDelay = 1.0
        stimWeight = 1.5
        stimInterval = 50
        stimulus[ 5 ].setProperties( weight=stimWeight, delay=stimDelay,
                                interval=stimInterval )
        stimulus[ 5 ].symbolProbability = 1.0
        stimulus[ 5 ].netstim.number = 1000

        # Build the JSON metadata file
        metadata = {
            "preSynType" : network.cellDict[ '0' ].cellName,
            "postSynType" : network.cellDict[ '1' ].cellName,
            "connCount" : network.edges[ '0' ][ '1' ].connCount,
            "edgeDelay" : network.edges[ '0' ][ '1' ].delay,
            "edgeWeight" : network.edges[ '0' ][ '1' ].weight,
            "edgeSynType" : network.edges[ '0' ][ '1' ].synType,
            "distance" : distance,
            "stimulus" : {
                "interval" : stimulus[ 5 ].interval,
                "weight" : stimulus[ 5 ].weight,
                "delay" : stimulus[ 5 ].delay,
            },
        }

        metadataStr = json.dumps( metadata, indent=4 )

        with open( metadataOutputPath, 'w' ) as metaFile:
            metaFile.write( metadataStr )

        SimProgress( 0 ).Send( self.pipeTx )

        def SimCB( time ):
            SimProgress( time / 1000.0 ).Send( self.pipeTx )
            if ( self.pipeRx.poll() ):
                message = self.pipeRx.recv()
                if isinstance( message, SimTerminate ):
                    return False
                elif isinstance( message, SimJob ):
                    self.jobQueue.append( message )
                
            return True

        self.netEnv.runSimulation( simOutputBasePath, SimCB )

        SimComplete().Send( self.pipeTx )
        print( f"Simulation {job.networkId} complete" )

    def simProcess( self ):
        # Send initial heartbeat
        SimProgress( 0 ).Send( self.pipeTx )
        shouldExit = False

        with open( os.path.join( logDir, f"proc-{self.processId}.log" ), 'w' ) as logFile:
            sys.stdout = logFile
            sys.stderr = logFile

            try:
                # Tie process to core
                import psutil
                p = psutil.Process()
                p.cpu_affinity( [ self.affinity ] )

                import neurpy
                from neurpy.NeuronEnviron import NeuronEnviron
                from neurpy.Neurtwork import Neurtwork
                import neuron
                import numpy as np
                import random

                self.netEnv = NeuronEnviron( modelBaseDir, globalMechanismsDir )

                while not shouldExit:
                    message = self.pipeRx.recv()
                    if isinstance( message, SimTerminate ):
                        shouldExit = True
                        break
                    elif isinstance( message, SimJob ):
                        self.jobQueue.append( message )
                    
                    while len( self.jobQueue ) > 0:
                        self.runJob( self.jobQueue.pop( 0 ) )
                    
            except Exception as e:
                msg = f"Sim Process -- Exception Caught: {str( e )}"
                print( msg )
                SimFailure( msg ).Send( self.pipeTx )
            finally:
                self.pipeTx.close()
                self.pipeRx.close()
                sys.exit( 0 )
        


class SimWin:
    statusWindow = None
    numProcs = 0
    multiProc = False
    statusWindow = None
    mainScreen = None
    winSize = (0,0)
    numProgressRows = 0
    sims = []
    fileId = 0
    shouldExit = True

    def __init__( self, stdscr ):
        self.mainScreen = stdscr
        self.mainScreen.nodelay( True )
        curses.curs_set( 0 )
        self.numProcs = availCores if args.numProcs == 0 else args.numProcs
        self.sims = [ Sim( procId, getAffinity( procId ) ) for procId in range( self.numProcs ) ]

        self.multiProc = self.numProcs > 1
        self.layoutScreen()

    def layoutScreen( self ):
        self.mainScreen.erase()
        maxY, maxX = self.mainScreen.getmaxyx()
        self.winSize = ( maxX, maxY )
        self.numProgressRows = math.ceil( self.numProcs / 4 )
        self.statusWindow = curses.newwin( self.numProgressRows + 3, maxX, 0, 0 )
        self.statusWindow.border()
        
        self.updateScreen()

    def updateStatusWindow( self ):
        self.statusWindow.clear()
        maxIdLen = math.floor( math.log10( self.numProcs ) + 1 )
        fixedWidthStr = "{0:" + str( maxIdLen ) + "}"
        progressLen =  ( self.winSize[ 0 ] - 7 - ( 4 * maxIdLen ) ) // 4
        progressSpace = progressLen - 2
        procLen = progressLen + maxIdLen + 1
        filesAvailable = self.fileId < len( validFiles )
        allComplete = not filesAvailable

        for procId, sim in enumerate( self.sims ):
            procX = procId % 4
            procY = ( procId // 4 ) + 1
            procWinXPos = 2 + ( procLen * procX )

            if ( sim.state == SimState.IDLE ) and filesAvailable:
                allComplete = False

                nextFile = os.path.join( netDir, validFiles[ self.fileId ][ 0 ] )
                sim.queueSim( self.fileId, nextFile )
                self.fileId += 1

            elif sim.state == SimState.SIMULATING:
                allComplete = False
            
            sim.update()
            progressStr = sim.getStatusString( progressSpace )
            
            statusStr = fixedWidthStr.format( procId ) + "[" + progressStr + "]"
            self.statusWindow.addstr( procY, procWinXPos, statusStr )
        
        statusStr = "Default"
        if allComplete:
            statusStr = "Simulation Complete"
        else:
            statusStr = f"File {self.fileId} / {len( validFiles )}"

        self.statusWindow.addstr( self.numProgressRows + 1, 1, statusStr )
        self.statusWindow.border()
        self.statusWindow.noutrefresh()

    def updateScreen( self ):
        self.updateStatusWindow()
        self.mainScreen.noutrefresh()
        curses.doupdate()

    def mainLoop( self ):
        self.shouldExit = False
        while not self.shouldExit:
            maxY, maxX = self.mainScreen.getmaxyx()
            #self.mainScreen.border()#'|', '|', '-', '-', '+', '+', '+', '+')
            #self.mainScreen.addstr(4, 2, "MaxY: " + str(maxY))
            #self.mainScreen.addstr(5, 2, "MaxX: " + str(maxX))
            self.updateScreen()            
            x = self.mainScreen.getch()

            if x == ord( "q" ):
                self.shouldExit = True
                curses.endwin()
            elif x == curses.KEY_RESIZE:
                self.layoutScreen()

            time.sleep( 0.1 )

        # TODO - wait for Sims to exit


def cMain( stdscr ):
    simWin = SimWin( stdscr )
    simWin.mainLoop()

wrapper( cMain )

