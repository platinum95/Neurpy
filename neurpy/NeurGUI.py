import neuron
from neuron import gui

class NeurGUI( object ):
    def __init__( self, recordSection, enableSynapses=False ):
        self.xres = 1200
        self.yres = 800
        self.xstart = 50
        self.ystart = 0
        self.mainhbox = None
        self.plotvbox = None
        self.synapsevbox = None
        self.shapehbox = None
        self.synapsevbox_size = None
        self.shapehbox = None
        self.sP = None
        self.rP = None
        self.synapse_plot = None
        self.synapsesEnabled = enableSynapses
        self.recSec = recordSection
        self.pwmcnt = neuron.h.PWManager[0].count


    def createMainWindow( self ):
        self.mainhbox = neuron.h.HBox(3)
        self.mainhbox.intercept(1)

        self.mainhbox.adjuster(200)
        self.createRuncontrol()

        self.mainhbox.adjuster(700)
        self.createPlottingPanel()

        self.mainhbox.adjuster(250)
        #TODO - Fix synapses and uncomment this
        self.createSynapsePanel()

        self.mainhbox.adjuster(250)
        self.mainhbox.intercept(0)
        self.mainhbox.full_request(1)
        self.mainhbox.map( "Main", self.xstart, self.ystart, self.xres, self.yres )


    def createPlottingPanel( self ):
        self.plotvbox = neuron.h.VBox()
        self.plotvbox.intercept(1)

        self.plotvbox.adjuster(300)
        self.createShapePanel()
        
        self.plotvbox.adjuster(500)

        self.rP = RingPlot( self.recSec )                                                         

        self.plotvbox.intercept(0)    
        self.mainhbox.full_request(1) 
        self.plotvbox.map("Plotting", 0, 0, -1, -1)
        neuron.h.fast_flush_list.append( self.rP )

    def cleanup( self ):
        for i in range( len( neuron.h.graphList ) ):
            neuron.h.graphList[ i ].remove_all()

        neuron.h.flush_list.remove_all()
        neuron.h.fast_flush_list.remove_all()

        self.rP.cleanup()
        neuron.h.fast_flush_list.append( self.rP )
        neuron.h.fast_flush_list.append( self.sP )                                       

        neuron.h.doNotify()
        neuron.h.PWManager
#        for i in range( self.pwmcnt, int( neuron.h.PWManager[0].count-1 ) ):
#            neuron.h.PWManager[0].close(i)
#            neuron.h.doNotify()

        neuron.h.stoprun = 0
#        cell.synapses.reset_synapses()

    
    def restart( self ):
        self.cleanup()
        #self.createStimulus()
        #cell.synapses.update_synapses(synapse_plot)
        print( "Running simulation" )
        neuron.h.fast_flush_list.append( self.rP )
        neuron.h.cvode_active(0)
        neuron.h.run()
    
    def stop( self ):
        neuron.h.stoprun = 1
    
    def setStep( self, val ):
        neuron.h.stepcurrent = neuron.h.stepcurrent1


    def createRuncontrol( self ):                                      
        neuron.h.xpanel("RunControl", 0)                                                     
        neuron.h.xbutton("Init & Run", self.restart )                                           
        neuron.h.xbutton("Stop", self.stop )                                                 
        neuron.h.xvalue("Total time", "tstop")                                                 
        neuron.h.xvalue("Sim Time","t", 0,"", 0, 1 )                                 
        neuron.h.xvalue("Real Time","realtime", 0,"", 0, 1 )                                 
        neuron.h.xbutton("Quit","quit()")
        
        neuron.h.xlabel("Step current")
        neuron.h.xradiobutton("No step","stepcurrent=\"none\"", 1)                                                                                
        neuron.h.xradiobutton("Step current 1","stepcurrent=\"stepcurrent1\"")            
        neuron.h.xradiobutton("Step current 2","stepcurrent=\"stepcurrent2\"")               
        neuron.h.xradiobutton("Step current 3","stepcurrent=\"stepcurrent3\"")               
        neuron.h.xpanel(1498, 0)

    def createShapePanel( self ):
        self.shapehbox = neuron.h.HBox()
        self.shapehbox.intercept(1)

        self.shapehbox.adjuster(350)
        self.sP = neuron.h.PlotShape(0)                                                       
        self.sP.variable("soma", "v(0.5)")                                               
        self.sP.view(-594.956, -98.0373, 1260.25, 1188.42, 573, 0, 505.92, 592)         
        self.sP.exec_menu("Shape Plot")                                                  

        self.shapehbox.adjuster(350)                                    
        self.synapse_plot = neuron.h.Shape(0)
        self.synapse_plot.view(-594.956, -98.0373, 1260.25, 1188.42, 49, 0, 500.16, 592)
    
        self.shapehbox.intercept(0)    
        self.shapehbox.full_request(1) 
        self.plotvbox.full_request(1) 
        self.mainhbox.full_request(1) 
        self.shapehbox.map("Shapes", 1104, 0, -1, -1)

    def synToggle( self, pre_mtype_id ):
        print( "Toggle synapse %i" % pre_mtype_id )

        synapses = self.stimCell.synapses

        varnameTog = "active_pre_mtype_tog_%i" % pre_mtype_id
        varnameFreq = "active_pre_mtype_frq_%i" % pre_mtype_id

        setVarOp = "synapses.active_pre_mtypes.x[ pre_mtype_id ] = self.%s" % varnameTog
        setVarFreqOp = "synapses.pre_mtype_freqs.x[ pre_mtype_id ] = self.%s" % varnameFreq

        exec( setVarOp )
        exec( setVarFreqOp )
        
        self.stimCell.synapses.update_synapses( self.synapse_plot )

    def createSynapsePanel( self ):
        # Preliminary translation to Python, not actually functioning yet
        # TODO - Fix this

        self.synapsevbox = neuron.h.HBox()
        self.synapsevbox.intercept( 1 )
        neuron.h.xpanel("Synapses")
        neuron.h.xlabel("Presyn m-types")
        synapses = self.stimCell.synapses

        for i in range( len( synapses.pre_mtypes ) ):
            pre_mtype_id = int( synapses.pre_mtypes.x[ i ] )
            pre_mtype_freqs = synapses.pre_mtype_freqs
            pre_mtype_name = synapses.id_mtype_map.o( pre_mtype_id ).s
            active_pre_mtypes = synapses.active_pre_mtypes
            cur_pre_mtype = active_pre_mtypes.x[ pre_mtype_id ]
            varname = "active_pre_mtype_tog_%i" % pre_mtype_id
            setVarOp = "self.%s = synapses.active_pre_mtypes.x[ pre_mtype_id ]" % varname
            exec( setVarOp )
            neuron.h.xstatebutton( pre_mtype_name,
                                   ( self, varname ),
                                   ( self.synToggle, pre_mtype_id ) )

        neuron.h.xpanel( 100, 0 )

        neuron.h.xpanel("Freq")
        neuron.h.xlabel("Frequency (Hz)")
        neuron.h( "objref mainCell, synPlot" )
        neuron.h.mainCell = self.stimCell
        neuron.h.synPlot = self.synapse_plot
        self.x = 10
        self.rx = neuron.h.ref( 10 )
        for i in range( len( synapses.pre_mtypes ) ):
            pre_mtype_id = int( synapses.pre_mtypes.x[ i ] )
            pre_mtype_freqs = synapses.pre_mtype_freqs
            pre_mtype_name = synapses.id_mtype_map.o( pre_mtype_id ).s
            active_pre_mtypes = synapses.active_pre_mtypes
            pre_mtype_freqs._ref_x[ pre_mtype_id ]
            varname = "active_pre_mtype_frq_%i" % pre_mtype_id
            setVarOp = "self.%s = synapses.pre_mtype_freqs.x[ pre_mtype_id ]" % varname
            exec( setVarOp )
            neuron.h.xvalue( "", ( self, varname ), 0, ( self.synToggle, pre_mtype_id ), 1 )

        neuron.h.xpanel( 100, 0 )

        self.synapsevbox.intercept(0)

        self.showSynapsePanel()
 

    def showSynapsePanel( self ):
        if self.synapsesEnabled:
            self.synapsevbox.map("Presynaptic activity", 0, 0, -1, -1)
        else:
            self.synapsevbox.unmap()



class RingPlot( object ):
    def __init__( self, recordSection ):
        self.g = None
        self.clipped_voltage = None
        self.g = None
        self.clipped_voltage = None
        self.clipped_time = None
        self.voltage = None
        self.time = None
        self.max_vec = None
        self.recSec = recordSection

        # Generate graph
        self.g = neuron.h.Graph(0)

        # Horizontal width of the plot (in ms)
        self.clip_size = 3000.0

        # Record voltage
        self.voltage = neuron.h.Vector(10000)
        self.voltage.record( self.recSec(0.5)._ref_v )

        # Record time
        self.time = neuron.h.Vector(10000)
        self.time.record( neuron.h._ref_t )

        # Vector that will contain the clipped data
        self.clipped_voltage = neuron.h.Vector()
        self.clipped_time = neuron.h.Vector()

        # Set up location and size of window
        self.g.view(0, -90, 3000, 120, 50, 650, 1007.04, 450)

    # View count of the graph 
    def view_count( self ):
        return self.g.view_count()

    # Fast flush the plot
    def fastflush( self ):
        self.update()
        return self.g.flush()
    
    # Flush the plot
    def flush( self ):
        self.update()
        return self.g.flush()

    # Update the plot
    def update( self ):
        # Set clipping region (in ms)
        self.clip_size = 3000.0
        t = neuron.h._ref_t
        # Time at right side of clipping region
        right_t = t

        # Time at left side of clipping region
        # Wait until time reaches clip_size to start scrolling
        left_t = 0.0
        if t >= self.clip_size:
             left_t = t - self.clip_size
        else:
             left_t = 0.0
    
        dt = neuron.h.dt
        # Calculate clipped vectors
        self.clipped_voltage.copy( self.voltage, 0, left_t/dt, right_t/dt-1 )
        self.clipped_time.copy( self.time, 0, left_t/dt, right_t/dt-1 )
        self.clipped_time.sub( left_t )

        # Erase previous plot
        self.g.erase()
        # Plot clipped vectors
        self.clipped_voltage.plot( self.g, self.clipped_time )

    # Clean up the plot
    def cleanup( self ):
        # Vector that will contain the clipped data
        self.clipped_voltage = neuron.h.Vector()
        self.clipped_time = neuron.h.Vector()