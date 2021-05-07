#!/usr/bin/env python3

import argparse
import curses
from curses import wrapper
from io import StringIO
import json
import math
import multiprocessing
from multiprocessing import Process, Pipe, Value
import numpy as np
import os
import re
import sys
import time

parser = argparse.ArgumentParser( description="Run Neuron simulation" )
parser.add_argument( "-i", "--input_dir", type=str, dest="inputDir", action="store", required=True, help="Path to directory of network topologies" )
parser.add_argument( "-o", "--output_dir", type=str, dest="outputDir", action="store", required=True, help="Path to directory for simulation outputs" )
parser.add_argument( "-p", "--parallel", type=int, dest="numProcs", action="store", default=0, help="Number of simulations to run in parallel, 0 for automatic selection." )
parser.add_argument( "-s", "--start", type=int, dest="startAt", action="store", default=0, help="File ID to start at" )
parser.add_argument( "-l", "--logdir", type=str, dest="logDir", action="store", default="./logs", help="Directory to store the process logs" )

args = parser.parse_args()
availCores = int( multiprocessing.cpu_count() )
numProcs = availCores if args.numProcs == 0 else args.numProcs
multiProc = numProcs > 1

netDir = args.inputDir
outDir = args.outputDir
logDir = args.logDir



modelBaseDir = "./modelBase"
globalMechanismsDir = "./modelBase/global_mechanisms"

if not os.path.exists( './x86_64' ):
    print( f"ERROR: Missing mechanisms. Run `nrnivmodl {globalMechanismsDir}` before starting simulations." )

outBase = "output"

if not os.path.exists( outDir ):
    os.makedirs( outDir )
elif not os.path.isdir( outDir ):
    print( f"ERROR: Output path '{outDir}' is not a directory" )
    sys.exit( 1 )
elif len( os.listdir( outDir ) ) != 0:
    print( f"ERROR: Output path '{outDir}' is not empty" )
    sys.exit( 1 )

if ( not os.path.exists( netDir ) ) or ( not os.path.isdir( netDir ) ):
    print( f"ERROR: Input path '{outDir}' is invalid" )

if not os.path.exists( logDir ):
    os.makedirs( logDir )

validFiles = [ ( x, int( re.search( "[0-9]+", x )[ 0 ] ) )
                for x in os.listdir( netDir ) if x.endswith( ".xml" ) ]
validFiles.sort( key=lambda val:val[ 1 ] )

procHandles = [ None ] * numProcs
# Filenumber, last piped time, pipe
procInfo = [ ]
affinities = []
getAffinity = lambda pId : ( pId * 2 ) % ( availCores ) +\
               ( 1 if( pId * 2 >= availCores and availCores % 2 == 0 ) else 0 )
for i in range( numProcs ):
    affinities.append( getAffinity( i ) )
    procInfo.append( [ 0, 0, Value( 'L', 0 ), getAffinity( i ) ] )

class Sim:
    running = False
    complete = False
    simFilePath = None
    simOutputpath = None
    processId = 0
    affinity = 0
    progress = 0
    simFile = None
    handle = None
    pipeTx = None
    pipeRx = None

    def __init__( self, processId, simFile, affinity, fileNum ):
        self.processId = processId
        self.simFile = simFile
        self.affinity = affinity

        baseName = "%s-%02i" % ( outBase, fileNum )
        self.simOutputBasePath = os.path.join( outDir, baseName )
        self.metadataOutputPath =  os.path.join( outDir, baseName + "_meta.json" )
        
        self.pipeRx, self.pipeTx = multiprocessing.Pipe()

    def runSim( self ):
        self.handle = Process( target=self.simProcess )
        self.handle.start()
        
        self.pipeTx.close()
        if not self.pipeRx.poll( 1 ):
            return
        
        recvd = self.pipeRx.recv() 
        if recvd != "heartbeat":
            return
        
        self.running = True

    def getStatus( self ):
        if ( not self.running ) or ( self.complete ) or ( not self.pipeRx.poll( 0.1 ) ):
            return self.progress

        try:
            while self.pipeRx.poll():
                self.progress = int( self.pipeRx.recv() )
        except EOFError:
            # Pipe closed, process ended
            self.running = False
            self.complete = True
            self.handle.join( 1 )
            if self.handle.exitcode == None:
                self.handle.kill()
            self.handle.close()


        return self.progress

    def getStatusString( self, availSpace ):
        progress = self.getStatus()

        if ( self.running == False ):
            return "Not Running"
        if ( self.complete == True ):
            return "Complete"
        
        progress = progress / 1000.0
        numBars = math.floor( availSpace * progress )
        return ( "|" * numBars ) + ( " " * ( availSpace - numBars ) )

    def simProcess( self ):
        
        self.pipeRx.close()
        self.pipeTx.send( 'heartbeat' )

        logFile = open( os.path.join( logDir, f"proc-{self.processId}.log" ), 'w' )
        sys.stdout = logFile
        sys.stderr = logFile

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

        netEnv = NeuronEnviron( modelBaseDir, globalMechanismsDir )
        print( f"Loading topology {self.simFile}" )
        network = netEnv.loadTopology( self.simFile )

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
        #   ncVec = neuron.h.Vector()
        stimulus = network.stimuli[ 0 ]
        #  stimulus[ 5 ].netcons[ 0 ].record( ncVec )
        stimDelay = 1.0#random.uniform( 0.1, 3.0 )
        stimWeight = 1.5#random.uniform( 1.0, 2.0 )
        stimInterval = 50#random.uniform( 50, 150 )
        stimulus[ 5 ].setProperties( weight=stimWeight, delay=stimDelay,
                                interval=stimInterval )
        stimulus[ 5 ].symbolProbability = 1.0
        stimulus[ 5 ].netstim.number = 1000

        #tgCell = network.cellDict[ "1" ]
        #  nGui = netEnv.generateGUI( tgCell.neurCell.soma[ 0 ], tgCell.neurCell )
        #  nGui.createMainWindow()
        #  while( 1 ):
        #      pass

        # Build the JSON metadata file
        # metadata = {
        #     "preSynType" : network.cellDict[ '0' ].cellName,
        #     "postSynType" : network.cellDict[ '1' ].cellName,
        #     "connCount" : network.edges[ '0' ][ '1' ].connCount,
        #     "edgeDelay" : network.edges[ '0' ][ '1' ].delay,
        #     "edgeWeight" : network.edges[ '0' ][ '1' ].weight,
        #     "edgeSynType" : network.edges[ '0' ][ '1' ].synType,
        #     "distance" : distance,
        #     "stimulus" : {
        #         "interval" : stimulus[ 5 ].interval,
        #         "weight" : stimulus[ 5 ].weight,
        #         "delay" : stimulus[ 5 ].delay,
        #     },
        # }

        metadata = {
            "leaf1Type" : network.cellDict[ '1' ].cellName,
            "leaf2Type" : network.cellDict[ '2' ].cellName,
            "leaf3Type" : network.cellDict[ '3' ].cellName,
            "leaf4Type" : network.cellDict[ '4' ].cellName
        }

        metadataStr = json.dumps( metadata, indent=4 )

        with open( self.metadataOutputPath, 'w' ) as metaFile:
            metaFile.write( metadataStr )

        netEnv.runSimulation( self.simOutputBasePath, self.pipeTx )

        print( "Simulation complete, processing exiting" )
        self.pipeTx.close()

        logFile.close()

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
        self.fileId = args.startAt
        self.mainScreen = stdscr
        self.mainScreen.nodelay( True )
        curses.curs_set( 0 )
        self.numProcs = availCores if args.numProcs == 0 else args.numProcs
        self.sims = [ None ] * self.numProcs
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
            
            if ( sim == None ) or ( sim.running == False ):
                if filesAvailable:
                    allComplete = False

                    nextFile = os.path.join( netDir, validFiles[ self.fileId ][ 0 ] )
                    sim = Sim( procId, nextFile, affinities[ procId ], self.fileId )
                    self.sims[ procId ] = sim
                    self.fileId += 1
                    sim.runSim()
                    #sim.simProcess()
                    if not sim.running:
                        # Failed to start sim
                        self.shouldExit = True
            elif ( sim != None ) and sim.running == True:
                allComplete = False
            
            progressStr = " " * progressSpace
            if sim != None:
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

