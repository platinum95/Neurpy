import neuron
import os
from neurpy.pyCell import pyCell
from neurpy.NeurGUI import NeurGUI
import subprocess

class NeuronEnviron( object ):
    def __init__(  self, modelRoot, mechanismRoot ):
        self.modelRoot = modelRoot
        self.loadedCells = {}
        subprocess.call( [ 'nrnivmodl', mechanismRoot ])
        neuron.h.load_file("stdrun.hoc")
        neuron.h.load_file("import3d.hoc")

    def createCell( self, cellDirName, cellTypeName ):
        cellRoot = os.path.join( self.modelRoot, cellDirName )
        cellRoot = os.path.abspath( cellRoot )
        cellLoaded = self.loadedCells.get( cellDirName, False )
        curDir = os.getcwd()
        os.chdir( cellRoot )
        if not cellLoaded:
            print( "Loading cell data from %s" % cellRoot )
            # Load main cell template, which will 
            # load biophysics and morphology
            templateFile = os.path.join( cellRoot, "template.hoc" )
            neuron.h.load_file( templateFile )
        newCell = pyCell( cellTypeName, caller="neurpy" )
        os.chdir( curDir )
        return newCell

    def generateGUI( self, synapses=False ):
        return NeurGUI( synapses )
