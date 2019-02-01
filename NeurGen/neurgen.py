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
        self.spaceClampCorrectionFactor = phData.get( "space_clamp_correction_factor", '' )
        self.latencyStd = float( phData.get( "latency_std", None ) )
        self.decayStd = float( phData.get( "decay_std", None ) )
        self.cvPspAmplitudeStd = float( phData.get( "cv_psp_amplitude_std", None ) )
        self.risetimeMean = float( phData.get( "risetime_mean", None ) )
        self.cvPspAmplitudeMean = float( phData.get( "cv_psp_amplitude_mean", None ) )
        self.epspStd = float( phData.get( "epsp_std", None ) )
        self.dMean = float( phData.get( "d_mean", None ) )
        self.fMean = float( phData.get( "f_mean", None ) )
        self.failuresStd = float( phData.get( "failures_std", None ) )

        self.numConvergentNeuronStd = float( anData.get( "number_of_convergent_neuron_std", None ) )
        self.connectionProbability = float( anData.get( "connection_probability", None ) )
        self.numDivergentNeuronStd = float( anData.get( "number_of_divergent_neuron_std", None ) )
        self.totalSynapseCount = float( anData.get( "total_synapse_count", None ) )
        self.meanNumSynapsePerConn = float( anData.get( "mean_number_of_synapse_per_connection", None ) )
        self.commonNeighborBias = float( anData.get( "common_neighbor_bias", None ) )
        self.numConvergentNeuronMean = float( anData.get( "number_of_convergent_neuron_mean", None ) )
        self.numSynapsePerConnectionStd = float( anData.get( "number_of_synapse_per_connection_std", None ) )
        self.numDivergentNeuronMean = float( anData.get( "number_of_divergent_neuron_mean", None ) )


class NeurGen:
    '''
    Class to handle the generation of a neocortical network
    '''
    def __init__( self ):
        self.cellIDs = {}
        self.cellNames = {}
        self.numMTypes = 0
        self.pathways = collections.defaultdict(dict)
        return

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
                    i += 1
                    self.pathways[ preID ][ postID ] = pWay

        print( "Loaded %i pathways" % i )

    def createNetwork( self, numCells ):
        '''
        Create a network of numCells cells given distribution
        data loaded in from pathway files
        '''
        cells = []
        edges = []
        stimuli = []
        probes = []

        curCell = 0
        curEdge = 0
        random.seed()
        preMType = random.randint( 0, self.numMTypes - 1 )

        cells.append( 
            { 
                "id" : str( curCell ),
                "label" : "Head",
                "cellType" : self.cellNames[ preMType ],
            }
        )

        for i in range( 1, numCells ):
            # For now, pick a random post m-type
            postMType = random.choice( list( self.pathways[ preMType ].keys() ) )

            curCell += 1
            cells.append( 
                { 
                    "id" : str( curCell ),
                    "cellType" : self.cellNames[ postMType ]
                }
            )

            pathway = self.pathways[ preMType ][ postMType ]
            edges.append( 
                { 
                    "id" : str( curEdge ),
                    "source" : str( curCell - 1 ),
                    "target" : str( curCell ),
                    "excProportion" : "0.7",
                    "inhProportion" : "0.3",
                    "weight" : "1.0",
                    "delay" : "1.0",
                }
            )
            curEdge += 1
            preMType = postMType

        
        docElement = Element( "Neurtwork" )
        graphElement = SubElement( docElement , "graph", attrib={ "mode":"static", "defaultedgetype":"directed" } )
        
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
        

        


if __name__ == "__main__":
    print( "Starting" )
    ng = NeurGen()
    print( "Loading data" )
    ng.loadPathwayData( 'physiology_pathways.json', 'anatomy_pathways.json' )
    print( "Finished, %i mtypes" % ng.numMTypes )
    ng.printConnectionMatrix()

    fileBase = os.path.dirname( "./networks/" )
    netNameBase = "testwork"
    if not os.path.exists( fileBase ):
        os.makedirs( fileBase )
    

    # Lets generate 10 random networks
    for i in range( 20 ):
        numCell = random.randint( 3, 6 )
        network = ng.createNetwork( numCell )
        netName = "%s-%02i.xml" % ( netNameBase, i )
        netPath = os.path.join( fileBase, netName )
        print( "Generating network %i, writing to %s" % ( i, netPath ) )
        with open( netPath, 'w' ) as netFile:
            netFile.write( network )   

