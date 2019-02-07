#!/usr/bin/env python3

'''
Script to create a file in every cell data folder which contains the
name of the cell template as it appears in the HOC code so that it
can be loaded automatically by Python.
'''


import sys
import os
import re

OUTPUT_FILENAME = 'cellname.txt'

def dealWithCell( root, templatePath ):
    templateStr = None
    with open( templatePath, 'r' ) as tmplFile:
        for line in tmplFile:
            if( re.search( r"^begintemplate.*", line ) ):
                line = re.sub( r"(.*begintemplate)|[\r\n]|[ ]", '', line )
                templateStr = line.strip()
                break
    if not templateStr:
        print( "Warning! Could not find template name for %s" % templatePath )
        return
    
    outputPath = os.path.join( root, OUTPUT_FILENAME )
    with open( outputPath, 'w' ) as outFile:
        outFile.write( templateStr )


def recurseFolders( rootDir ):
    # Check for the cell template file
    dirListing = [ sub for sub in os.listdir( rootDir ) ]
    templateFiles = [ os.path.join( rootDir, tmpl ) for tmpl in dirListing if re.search( r'template\.hoc', tmpl ) and os.path.isfile( os.path.join( rootDir, tmpl ) ) ]
    if templateFiles:
        if len( templateFiles ) != 1:
            print( "More than 1 template file? Wat" )
        dealWithCell( rootDir, templateFiles[ 0 ] )    
        
    else:
        dirs = [ os.path.join( rootDir, dir ) for dir in dirListing if os.path.isdir( os.path.join( rootDir, dir ) ) ]
        for dir in dirs:
            recurseFolders( dir )



modelBasePath = '../modelBase/'
if( len( sys.argv ) > 1 ):
    modelBasePath = sys.argv[ 1 ]

modelBaseDir = os.path.dirname( modelBasePath )



recurseFolders( modelBaseDir )