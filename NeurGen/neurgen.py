#!/usr/bin/env python3

import re
import json
import collections
import random
import sys
import os
from xml.etree.cElementTree import Element, ElementTree, SubElement
from xml.etree.ElementTree import tostring
from xml.dom import minidom
from numpy.random import normal


class Pathway:
    '''
    Represents information on the connection between two given cells.
    '''
    def __init__( self, anData, phData, preCell, postCell ):
        self.preCell = preCell
        self.postCell = postCell
        
        self.gsynMean = float( phData.get( "gsyn_mean", None ) )
        self.epspMean = float( phData.get( "epsp_mean", None ) )
        self.risetimeStd = float( phData.get( "risetime_std", None ) )
        self.fStd = float( phData.get( "f_std", None ) )
        self.gsynStd = float( phData.get( "gsyn_std", None ) )
        self.uStd = float( phData.get( "u_std", None ) )
        self.decayMean = float( phData.get( "decay_mean", None ) )
        self.latencyMean = float( phData.get( "latency_mean", None ) )
        self.failuresMean = float( phData.get( "failures_mean", None ) )
        self.uMean = float( phData.get( "u_mean", None ) )
        self.dStd = float( phData.get( "d_std", None ) )
        self.synapseType = phData.get( "synapse_type", '' )
        self.spaceClampCorrectionFactor = \
            phData.get( "space_clamp_correction_factor", '' )
        self.latencyStd = float( phData.get( "latency_std", None ) )
        self.decayStd = float( phData.get( "decay_std", None ) )
        self.cvPspAmplitudeStd = \
            float( phData.get( "cv_psp_amplitude_std", None ) )
        self.risetimeMean = float( phData.get( "risetime_mean", None ) )
        self.cvPspAmplitudeMean = \
            float( phData.get( "cv_psp_amplitude_mean", None ) )
        self.epspStd = float( phData.get( "epsp_std", None ) )
        self.dMean = float( phData.get( "d_mean", None ) )
        self.fMean = float( phData.get( "f_mean", None ) )
        self.failuresStd = float( phData.get( "failures_std", None ) )

        self.numConvergentNeuronStd = \
            float( anData.get( "number_of_convergent_neuron_std", None ) )
        self.connectionProbability = \
            float( anData.get( "connection_probability", None ) )
        self.numDivergentNeuronStd = \
            float( anData.get( "number_of_divergent_neuron_std", None ) )
        self.totalSynapseCount = \
            float( anData.get( "total_synapse_count", None ) )
        self.meanNumSynapsePerConn = \
            float( anData.get( "mean_number_of_synapse_per_connection", None ) )
        self.commonNeighborBias = \
            float( anData.get( "common_neighbor_bias", None ) )
        self.numConvergentNeuronMean = \
            float( anData.get( "number_of_convergent_neuron_mean", None ) )
        self.numSynapsePerConnectionStd = \
            float( anData.get( "number_of_synapse_per_connection_std", None ) )
        self.numDivergentNeuronMean = \
            float( anData.get( "number_of_divergent_neuron_mean", None ) )


class NeurGen:
    '''
    Class to handle the generation of a neocortical network
    '''
    def __init__( self, modelBase ):
        self.cellIDs = {}
        self.cellNames = {}
        self.numMTypes = 0
        self.pathways = collections.defaultdict(dict)
        self.eTypes = {}
        self.__getETypes( modelBase )
        return

    def __getETypes( self, modelBase ):
        # Get all the model dirs by looking for folders that have
        # L followed by a digit in the name
        modelBasePath = os.path.dirname( modelBase )
        dirs = os.listdir( modelBasePath )
        dirs = [ dir for dir in dirs if re.match( r'L[0-9]', dir ) ]

        for cellName in dirs:
            cellMType = re.search( r'^(.*_.*)_.*_.*$', cellName )
            if cellMType:
                cellMTypeStr = cellMType.group( 1 )
                eList = self.eTypes.get( cellMTypeStr, [] )
                eList.append( cellName )
                self.eTypes[ cellMTypeStr ] = eList
            else:
                print( "Warning: Regex search failed for %s" % cellName )



    def printConnectionMatrix( self ):
        '''
        Print out the connection matrix, i.e. what cells have defined pathways
        to another given cell.
        '''
        x = range( 0, ng.numMTypes )
        sys.stdout.write( "   " )
        [ sys.stdout.write( "%-2i " %i ) for i in x ]
        sys.stdout.write( '\r\n' )
        yIDs = list( ng.pathways.keys() ).sort()
        
        for y in range( 0, ng.numMTypes ):
            sys.stdout.write( "%-2i " % y )
            row = ng.pathways.get( y, None )
            if not row:
                [ sys.stdout.write( "   " ) for i in x ]
            else:
                for xi in range( 0, ng.numMTypes ):
                    colV = row.get( xi, None )
                    if not colV:
                        sys.stdout.write( "   " )
                    else:
                        sys.stdout.write( "x  " )
            sys.stdout.write( '\n' )

    def getSetID( self, cellName ):
        '''
        Returns the ID of a given cell name.
        If the cell hasn't been encountered before, an ID is allocated
        '''
        id = 0
        if cellName not in self.cellIDs:
            id = self.numMTypes
            self.cellIDs[ cellName ] = id
            self.cellNames[ id ] = cellName 
            self.numMTypes += 1
        else:
            id = self.cellIDs.get( cellName, None )
        return id
        

    def loadPathwayData( self, physiologyPath, anatomyPath ):
        ''' 
        Load in JSON data and generate internal data structure
        '''

        # Anatomy file gives dictionary with cell names as key
        # and a further dict as a value, with information on the 
        # pathway anatomy.

        # Physiology file is the same format

        # Lets define a helper function to split the dict key
        # into pre-synaptic cell and post-synaptic cell.
        # Don't really need a function for this but may be useful
        # if it needs to be changed later
        def splitPathwayName( pathwayName ):
            pSplit = pathwayName.split( ':' )
            return pSplit[ 0 ], pSplit[ 1 ]

        i = 0
        # Load in the physiology data
        with open( physiologyPath ) as phFile:
            phData = json.load( phFile )

            # Now load in the anatomy data
            with open( anatomyPath ) as anFile:
                anData = json.load( anFile )
                anItems = anData.items()

                # Loop over each pathway
                for anPathway in anItems:
                    pStr = anPathway[ 0 ]
                    # Find associated pathway in physiology data
                    phPathway = phData.get( pStr, None )
                    # Make sure there's physiololgy data for this
                    if not phPathway:
                        print( "No data for %s in physiology" % pStr )
                        raise KeyError
                    
                    preCell, postCell = splitPathwayName( pStr )
                    
                    preID = self.getSetID( preCell )
                    postID = self.getSetID( postCell )

                    # Make a pathway object, set the data, and store
                    pWay = Pathway( anPathway[ 1 ], phPathway, 
                                    preCell, postCell )
                    if not re.search( 'excitatory', pWay.synapseType, 
                                      re.IGNORECASE ):
                        continue
                    i += 1
                    self.pathways[ preID ][ postID ] = pWay

        print( "Loaded %i pathways" % i )

    def getCellFromMType( self, mTypeStr ):
        '''
        Pathway deals with MType only, no e-types included.
        Here we return a random e-type of a given m-type
        '''
        cellETypes = self.eTypes.get( mTypeStr, [] )
        if not cellETypes:
            print( "ERROR: No etypes found for cell %s!" % mTypeStr )
            return None
        return random.choice( cellETypes )


    def createRandomNetwork( self, numCells ):
        '''
        Create a random network of numCells cells given distribution
        data loaded in from pathway files
        '''
        cells = []
        edges = []
        stimuli = []
        probes = []

        curCell = 0
        curEdge = 0
        random.seed()

        # Choose a random starting cell in layer 1
        cellsL1 = [ x for x in self.pathways.keys()
                    if re.match( 'L1', self.cellNames[ x ] ) ]
        preMType = random.choice( cellsL1 )

        # Insert the first cell into the network specificaiton
        cells.append( 
            { 
                "id" : str( curCell ),
                "label" : "Head",
                "cellType" : str( 
                    self.getCellFromMType( self.cellNames[ preMType ] ) ),
            }
        )

        for i in range( 1, numCells ):
            # Find a post-synaptic MType based on connection 
            # probabilities of the pathways.
            # First get the sum of all the possible connection probabilities.
            probSum = 0.0
            for pw in list( self.pathways[ preMType ].values() ):
                probSum += pw.connectionProbability
            
            # Next get a random value between 0 and this sum
            randSample = random.uniform( 0.0, probSum )

            # Next find the pathway that this sample belongs to, 
            # and choose it as our post-synaptic MType
            postMType = None
            curProb = 0.0
            for mTypeStr, pw in list( self.pathways[ preMType ].items() ):
                # For each mtype, check if our random value falls between the 
                # range [ curProb, conProbUpper ] where conProbUpper is 
                # just curProb + connection probability.
                conProbUpper = curProb + pw.connectionProbability
                if( randSample > curProb and randSample < conProbUpper ):
                    postMType = mTypeStr
                    break
                # If we didn't fall into this range then move onto the next
                # mtype, setting its lower bound to our upper bound
                curProb = conProbUpper
            if not postMType:
                # If we get here, an error has occurred
                print( "Couldn't find a cell! "
                        "Final prob was %i, sample was %i. "
                        "Choosing one at random." % 
                            ( int( curProb ) , randSample ) )
                postMType = random.choice( 
                    list( self.pathways[ preMType ].keys() ) )

            curCell += 1
            cells.append( 
                { 
                    "id" : str( curCell ),
                    "cellType" : str( 
                        self.getCellFromMType( self.cellNames[ postMType ] ) )
                }
            )

            pw = self.pathways[ preMType ][ postMType ]
            # Generate the edge data from distribution sampling
            delay = normal( loc=pw.latencyMean, scale=pw.latencyStd )
            connCount = normal( loc=pw.meanNumSynapsePerConn,
                                scale=pw.numSynapsePerConnectionStd )
            connCount = max( 1, int( connCount ) )
            connWeight = random.uniform( 0.8, 5.0 )
            conType = pw.synapseType
            conCode = 0
            # Find out what kind of synapse we're dealing with
            if( re.search( 'inhibitory', conType, re.IGNORECASE ) ):
                conCode = 1
            elif( re.search( 'excitatory', conType, re.IGNORECASE ) ):
                conCode = 0
            else:
                print( "Unknown connection type: %s" % conType )
            
            # Construct the edge object
            edges.append( 
                { 
                    "id" : str( curEdge ),
                    "source" : str( curCell - 1 ),
                    "target" : str( curCell ),
                    "connType" : str( conCode ),
                    "connCount" : str( connCount ),
                    "weight" : str( connWeight ),
                    "delay" : str( delay )
                }
            )
            curEdge += 1
            preMType = postMType
        
        # Place a probe on the input and the output
        probes.append( 
            { 
                "id" : str( 0 ),
                "target" : str( 0 ),
                "tag" : "headProbe"
            }
        )
        probes.append( 
            { 
                "id" : str( 1 ),
                "target" : str( curCell ),
                "tag" : "tailProbe"
            }
        )

        
        docElement = Element( "Neurtwork" )
        graphElement = SubElement( docElement , "graph", 
                                   attrib={ "mode":"static", 
                                            "defaultedgetype":"directed" } )
        
        cellsElement = SubElement( graphElement, "cells" )
        for cell in cells:
            cellElement = SubElement( cellsElement, "cell", attrib=cell )

        edgesElement = SubElement( graphElement, "edges" )
        for edge in edges:
            edgeElement = SubElement( edgesElement, "edge", attrib=edge )

        stimuliElement = SubElement( graphElement, "stimuli" )
        for stim in stimuli:
            stimulusElement = SubElement( stimuliElement, "stim", attrib=stim )

        probesElement = SubElement( graphElement, "probes" )
        for probe in probes:
            probeElement = SubElement( probesElement, "probe", attrib=probe )

        # Add lines + indentations
        eStr = tostring( docElement )
        networkXml = minidom.parseString( eStr ).toprettyxml( indent="   " )

        return networkXml

    def loadSingleCell( self, cType, cellList ):
        preMtype = ''
        if( cType == "any" ):
            preMType = self.cellNames[ random.choice( cellList ) ]
        else:
            cellNameList = [ self.cellNames[ x ]  for x in cellList ]
            validCells = [ x for x in cellNameList
                            if re.match( cType, x ) ]
            if not validCells:
                raise ValueError( "Warning! No valid cells found for %s" % 
                                  cType )
            preMtype = random.choice( validCells )
        return preMtype

    def getPathwayFromProb( self, pathList ):
        # Find a post-synaptic MType based on connection 
        # probabilities of the pathways.
        # First get the sum of all the possible connection probabilities.
        probSum = 0.0
        for pw in pathList:
            probSum += pw.connectionProbability
        
        # Next get a random value between 0 and this sum
        randSample = random.uniform( 0.0, probSum )

        # Next find the pathway that this sample belongs to, 
        # and choose it as our post-synaptic MType
        pathway = None
        curProb = 0.0
        for pw in pathList:
            # For each mtype, check if our random value falls between the 
            # range [ curProb, conProbUpper ] where conProbUpper is 
            # just curProb + connection probability.
            conProbUpper = curProb + pw.connectionProbability
            if( randSample > curProb and randSample < conProbUpper ):
                pathway = pw
                break
            # If we didn't fall into this range then move onto the next
            # mtype, setting its lower bound to our upper bound
            curProb = conProbUpper
        if not pathway:
            # If we get here, an error has occurred
            print( "Couldn't find a cell! "
                    "Final prob was %i, sample was %i. "
                    "Choosing one at random." % 
                        ( int( curProb ) , randSample ) )
            pathway = random.choice( pathList )
        
        return pathway

    def loadCellsFromEdge( self, sourceId, targetId, netCellList ):
        '''
        Load source cell if target is None, else
        load target based on the edge probability
        '''
        source = netCellList[ sourceId ]
        target = netCellList[ targetId ]
        # Get the current status of the cells (chosen/not chosen)
        sourceChosen = source[ 3 ]
        targetChosen = target[ 3 ]

        # If neither have been loaded, load the source cell
        if not sourceChosen and not targetChosen:
            chosen = False
            origSrc = source[ 1 ]
            while not chosen:
                source[ 1 ] = self.loadSingleCell( origSrc,#source[ 1 ], 
                                                self.pathways.keys() )
                source[ 3 ] = True
                # Now load target based on the source
                sourceCellID = self.getSetID( source[ 1 ] )
                validTargets = self.pathways[ sourceCellID ].items()
                validTargets = [ pw for x, pw in validTargets
                                if re.match( target[ 1 ], self.cellNames[ x ] ) ]
                if not validTargets:
                    continue
                chosen = True
                pWay = self.getPathwayFromProb( validTargets )
                target[ 1 ] = pWay.postCell
                target[ 3 ] = True
        
        elif sourceChosen and not targetChosen:
            validTargets = self.pathways[ source[ 1 ] ].items()
            validTargets = [ pw for x, pw in validTargets
                             if re.match( target[ 1 ], x ) ]
            pWay = self.getPathwayFromProb( validTargets )
            target[ 1 ] = pWay.postCell
            target[ 3 ] = True
        
        elif not sourceChosen and targetChosen:
            targetCellID = self.getSetID( target[ 1 ] )
            validSourceIds = [ x for x, pws in self.pathways.items() 
                               if ( targetCellID in pws.keys() ) ]
            validPws = []
            for sId in validSourceIds:
                for tId, pw in self.pathways[ sId ].items():
                    if tId == targetCellID:
                        validPws.append( pw )

            pWay = self.getPathwayFromProb( validPws )
            source[ 1 ] = pWay.preCell
            source[ 3 ] = True
        
        else:
            # Both already loaded
            pass

        netCellList[ sourceId ] = source
        netCellList[ targetId ] = target

    def createNetwork( self, topologyPath ):
        '''
        Create a network of cells given distribution
        data loaded in from pathway files and a topology template from file
        '''
        cells = []
        edges = []
        stimuli = []
        probes = []

        curCell = 0
        curEdge = 0
        random.seed()

        # Load in the topology
        domFile = minidom.parse( topologyPath )

        # Helper function; return default if attrib not found
        def getAttribDefault( element, name, default ):
            val = element.getAttribute( name )
            if not val:
                val = default
            return val            

        # Locate the elements required
        templCells = domFile.getElementsByTagName( 'cell' )
        templEdges = domFile.getElementsByTagName( 'edge' )
        templStimuli = domFile.getElementsByTagName( 'stim' )
        templProbes = domFile.getElementsByTagName( 'probe' )

        # Intermediate cell list of tuples of form:
        # ( id, cellStr, label, selected )
        # where id is the unique cell id, cellStr is the cell 
        # string identifier (placeholder for layer, actual cell
        # name, or "any"), and selected is a flag indicating if
        # the cell is a placeholder or actually chosen/loaded

        interCell = {}
        # Load in each cell
        for cell in templCells:
            cellId = cell.getAttribute( "id" )
            cellType = cell.getAttribute( "cellType" )
            label = cell.getAttribute( "label" )
            # Check if using a full-spec cell or a regex max
            cellChosen = ( len( cellType ) > 4 )
            cellTup = [ cellId, cellType, label, cellChosen ]
            interCell[ cellId ] = cellTup
        
        # Tuple of id, source, target
        edges = []
        for edge in templEdges:
            edgeId = edge.getAttribute( "id" )
            edgeSource = edge.getAttribute( "source" )
            edgeTarget = edge.getAttribute( "target" )
            edgeTup = ( edgeId, edgeSource, edgeTarget )
            edges.append( edgeTup )
            # Load in the source cell.
            sourceCell = interCell[ edgeSource ]
            targetCell = interCell[ edgeTarget ]
            self.loadCellsFromEdge( sourceCell[ 0 ], targetCell[ 0 ], interCell )

        stims = []
        for stim in templStimuli:
            # For now this is just the same as in the sample code.
            # May change later to something else

            target = stim.getAttribute( 'target' )
            stimFile = stim.getAttribute( 'stimFile' )
            getAttribDefault( stim, "delay", 0.0 )
            delay = float( getAttribDefault( stim, "delay", 0.0 ) )
            dur = float( getAttribDefault( stim, "dur", 0.0 ) )

            stims.append( ( target, stimFile, delay, dur ) )
            
        probes = []
        for probe in templProbes:
            target = probe.getAttribute( "target" )
            probeTag = probe.getAttribute( "tag" )
            probeID = probe.getAttribute( "id" )
            targetCell = interCell[ target ][ 1 ]
            if not probeTag:
                probeTag = "%s_%s" %( targetCell, probeID )
            
            probes.append( ( probeID, target, probeTag ) )


        outCells = []
        outEdges = []
        outStims = []
        outProbes = []

        for cell in interCell.values():
            if not cell[ 3 ]:
                continue
            outCells.append( 
                { 
                    "id" : str( cell[ 0 ] ),
                    "label" : str( cell[ 2 ] ),
                    "cellType" : str( self.getCellFromMType( cell[ 1 ] ) )
                }
            )

        for edge in edges:
            preCell = interCell[ edge[ 1 ] ]
            postCell = interCell[ edge[ 2 ] ]

            preCellId = self.getSetID( preCell[ 1 ] )
            postCellId = self.getSetID( postCell[ 1 ] )
            pw = self.pathways[ preCellId ][ postCellId ]

            # Generate the edge data from distribution sampling
            delay = normal( loc=pw.latencyMean, scale=pw.latencyStd )
            connCount = normal( loc=pw.meanNumSynapsePerConn,
                                scale=pw.numSynapsePerConnectionStd )
            connCount = max( 1, int( connCount ) )
            connWeight = random.uniform( 0.8, 5.0 )
            conType = pw.synapseType
            conCode = 0
            # Find out what kind of synapse we're dealing with
            if( re.search( 'inhibitory', conType, re.IGNORECASE ) ):
                conCode = 1
            elif( re.search( 'excitatory', conType, re.IGNORECASE ) ):
                conCode = 0
            else:
                print( "Unknown connection type: %s" % conType )
            
            # Construct the edge object
            outEdges.append( 
                { 
                    "id" : str( edge[ 0 ] ),
                    "source" : str( edge[ 1 ] ),
                    "target" : str( edge[ 2 ] ),
                    "connType" : str( conCode ),
                    "connCount" : str( connCount ),
                    "weight" : str( connWeight ),
                    "delay" : str( delay )
                }
            )
        for probe in probes:
            # Place a probe on the input and the output
            outProbes.append( 
                { 
                    "id" : str( probe[ 0 ] ),
                    "target" : str( probe[ 1 ] ),
                    "tag" : str( probe[ 2 ] )
                }
            )

        for stim in stims:
            outStims.append(
                {
                    "target"    : str( stim[ 0 ] ),
                    "stimFile"  : str( stim[ 1 ] ),
                    "delay"     : str( stim[ 2 ] ),
                    "dur"       : str( stim[ 3 ] )
                }
            )


        
        docElement = Element( "Neurtwork" )
        graphElement = SubElement( docElement , "graph", 
                                   attrib={ "mode":"static", 
                                            "defaultedgetype":"directed" } )
        
        cellsElement = SubElement( graphElement, "cells" )
        for cell in outCells:
            cellElement = SubElement( cellsElement, "cell", attrib=cell )

        edgesElement = SubElement( graphElement, "edges" )
        for edge in outEdges:
            edgeElement = SubElement( edgesElement, "edge", attrib=edge )

        stimuliElement = SubElement( graphElement, "stimuli" )
        for stim in outStims:
            stimulusElement = SubElement( stimuliElement, "stim", attrib=stim )

        probesElement = SubElement( graphElement, "probes" )
        for probe in outProbes:
            probeElement = SubElement( probesElement, "probe", attrib=probe )

        # Add lines + indentations
        eStr = tostring( docElement )
        networkXml = minidom.parseString( eStr ).toprettyxml( indent="   " )

        return networkXml
        

if __name__ == "__main__":
    print( "Starting" )
    ng = NeurGen( './modelBase/' )
    print( "Loading data" )
    ng.loadPathwayData( './NeurGen/physiology_pathways.json',
                        './NeurGen/anatomy_pathways.json' )
    print( "Finished, %i mtypes" % ng.numMTypes )
 #   ng.printConnectionMatrix()

    fileBase = os.path.dirname( "./networks/" )
    netNameBase = "testwork"
    if not os.path.exists( fileBase ):
        os.makedirs( fileBase )
    
    sys.argv.append( "./NeurGen/4-leaf-topology.xml" )
    # Lets generate 1000 random networks
    for i in range( 10000 ):
        if( len( sys.argv ) > 1 ):
            topologyPath = sys.argv[ 1 ]
            network = ng.createNetwork( topologyPath )
        else:
            numCell = random.randint( 3, 6 )
            network = ng.createRandomNetwork( numCell )
        
        netName = "%s-%02i.xml" % ( netNameBase, i )
        netPath = os.path.join( fileBase, netName )
        print( "Generating network %i, writing to %s" % ( i, netPath ) )
        with open( netPath, 'w' ) as netFile:
            netFile.write( network )   

