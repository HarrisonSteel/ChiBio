
function getSysData(){
    
    
    $.ajax({
           type: "GET",
           url: '/getSysdata/',
           dataType: "json",
           
           success:function(data){
               updateData(data);
           }

            }); 
    
   
}

var charts = [];


function updateData(data){
        
        var running = Boolean(data.Experiment.ON); //True if Experiment is running.
		
		
		 	
		
         
				
		  
        // Update Terminal        
        document.getElementById("termI").innerHTML=data.Terminal.text;
        
        //Update Output Indicators
        document.getElementById("LEDADefault").innerHTML=data.LEDA.default.toFixed(3);
        document.getElementById("LEDACurrent").innerHTML=data.LEDA.target.toFixed(3);
        document.getElementById("LEDBDefault").innerHTML=data.LEDB.default.toFixed(3);
        document.getElementById("LEDBCurrent").innerHTML=data.LEDB.target.toFixed(3);
        document.getElementById("LEDCDefault").innerHTML=data.LEDC.default.toFixed(3);
        document.getElementById("LEDCCurrent").innerHTML=data.LEDC.target.toFixed(3);
        document.getElementById("LEDDDefault").innerHTML=data.LEDD.default.toFixed(3);
        document.getElementById("LEDDCurrent").innerHTML=data.LEDD.target.toFixed(3);
        document.getElementById("LEDEDefault").innerHTML=data.LEDE.default.toFixed(3);
        document.getElementById("LEDECurrent").innerHTML=data.LEDE.target.toFixed(3);
        document.getElementById("LEDFDefault").innerHTML=data.LEDF.default.toFixed(3);
        document.getElementById("LEDFCurrent").innerHTML=data.LEDF.target.toFixed(3);
        document.getElementById("LEDGDefault").innerHTML=data.LEDG.default.toFixed(3);
        document.getElementById("LEDGCurrent").innerHTML=data.LEDG.target.toFixed(3);
        
        document.getElementById("UVDefault").innerHTML=data.UV.default.toFixed(3);
        document.getElementById("UVCurrent").innerHTML=data.UV.target.toFixed(3);
        
        
        document.getElementById("LASER650Default").innerHTML=data.LASER650.default.toFixed(3);
        document.getElementById("LASER650Current").innerHTML=data.LASER650.target.toFixed(3);
        
        document.getElementById("Pump1Current").innerHTML=data.Pump1.target.toFixed(3);
        document.getElementById("Pump2Current").innerHTML=data.Pump2.target.toFixed(3);
        
        document.getElementById("Pump3Current").innerHTML=data.Pump3.target.toFixed(3);
        document.getElementById("Pump4Current").innerHTML=data.Pump4.target.toFixed(3);
        
        
        document.getElementById("StirCurrent").innerHTML=data.Stir.target.toFixed(3);
        document.getElementById("LightCurrent").innerHTML=data.Light.Excite;
        document.getElementById("CustomStatus").innerHTML=data.Custom.Status.toFixed(3);
        
         
        document.getElementById("StartTime").innerHTML = data.Experiment.startTime;
        
        
        
        document.getElementById("410nmSense").innerHTML = data.AS7341.spectrum.nm410.toFixed(0);
        document.getElementById("440nmSense").innerHTML = data.AS7341.spectrum.nm440.toFixed(0);
        document.getElementById("470nmSense").innerHTML = data.AS7341.spectrum.nm470.toFixed(0);
        document.getElementById("510nmSense").innerHTML = data.AS7341.spectrum.nm510.toFixed(0);
        document.getElementById("550nmSense").innerHTML = data.AS7341.spectrum.nm550.toFixed(0);
        document.getElementById("583nmSense").innerHTML = data.AS7341.spectrum.nm583.toFixed(0);
        document.getElementById("620nmSense").innerHTML = data.AS7341.spectrum.nm620.toFixed(0);
        document.getElementById("670nmSense").innerHTML = data.AS7341.spectrum.nm670.toFixed(0);
        document.getElementById("ClearSense").innerHTML = data.AS7341.spectrum.CLEAR.toFixed(0);
        
        document.getElementById("FPBase1Value").innerHTML = data.FP1.Base.toFixed(0);
        document.getElementById("FPEmit1AValue").innerHTML = data.FP1.Emit1.toFixed(3);
        document.getElementById("FPEmit1BValue").innerHTML = data.FP1.Emit2.toFixed(3);
        
        document.getElementById("FPBase2Value").innerHTML = data.FP2.Base.toFixed(0);
        document.getElementById("FPEmit2AValue").innerHTML = data.FP2.Emit1.toFixed(3);
        document.getElementById("FPEmit2BValue").innerHTML = data.FP2.Emit2.toFixed(3);
        
        document.getElementById("FPBase3Value").innerHTML = data.FP3.Base.toFixed(0);
        document.getElementById("FPEmit3AValue").innerHTML = data.FP3.Emit1.toFixed(3);
        document.getElementById("FPEmit3BValue").innerHTML = data.FP3.Emit2.toFixed(3);
        
        
        document.getElementById("TName").innerHTML = "Device: " + data.UIDevice
        document.getElementById("TempCurrent").innerHTML = data.ThermometerExternal.current.toFixed(3);
        document.getElementById("TempCurrent2").innerHTML = data.ThermometerInternal.current.toFixed(3);
        document.getElementById("TempCurrent3").innerHTML = data.ThermometerIR.current.toFixed(3);
        document.getElementById("ThermostatTarget").innerHTML=data.Thermostat.target.toFixed(3);
        
        
        document.getElementById("ODCurrent").innerHTML = data.OD.current.toFixed(3);
        
        document.getElementById("OD0Current").innerHTML = data.OD0.target.toFixed(0);
        document.getElementById("ODRaw").innerHTML = data.OD0.raw.toFixed(0);
        
        document.getElementById("VolumeCurrent").innerHTML = data.Volume.target.toFixed(3);
        
        document.getElementById("ODTarget").innerHTML = data.OD.target.toFixed(3);
        
           
        // Do Experiment-dependent things
       
        
        if (running){
             document.getElementById("ExperimentRunningIndicator").setAttribute("class", "btn btn-success")
             document.getElementById("ExperimentRunningIndicator").innerHTML= "&nbsp &nbsp &nbsp   Running   &nbsp &nbsp &nbsp"
        } else {
             document.getElementById("ExperimentRunningIndicator").setAttribute("class", "btn btn-danger")
             document.getElementById("ExperimentRunningIndicator").innerHTML=  "&nbsp &nbsp &nbsp   Stopped   &nbsp &nbsp &nbsp"
        }
        


        document.getElementById("ExperimentStart").disabled = running;
        document.getElementById("ExperimentReset").disabled = running;
        document.getElementById("ExperimentStop").disabled = !running;
        
        var measuring = Boolean(data.OD.Measuring); //True if we are measuring things

        
        
        document.getElementById("LEDASwitch").disabled = (measuring );
        document.getElementById("LEDBSwitch").disabled = (measuring );
        document.getElementById("LEDCSwitch").disabled = (measuring );
        document.getElementById("LEDDSwitch").disabled = (measuring );
        document.getElementById("LEDESwitch").disabled = (measuring );
        document.getElementById("LEDFSwitch").disabled = (measuring );
        document.getElementById("LEDGSwitch").disabled = (measuring );
        document.getElementById("LASER650Switch").disabled = (measuring );
        
        document.getElementById("GetSpectrum").disabled = (measuring );
        
        document.getElementById("TempMeasure").disabled = (measuring );
        document.getElementById("TempMeasure2").disabled = (measuring );
        document.getElementById("TempMeasure3").disabled = (measuring );
        document.getElementById("ODMeasure").disabled = (measuring );
        
        
        
        //document.getElementById("LEDASet").disabled = (data.LEDA.ON==1);
        //document.getElementById("LEDBSet").disabled = (data.LEDB.ON==1);
        //document.getElementById("LEDCSet").disabled = (data.LEDC.ON==1);
        //document.getElementById("LEDDSet").disabled = (data.LEDD.ON==1);
        //document.getElementById("LEDESet").disabled = (data.LEDE.ON==1);
        //document.getElementById("LEDFSet").disabled = (data.LEDF.ON==1);
        //document.getElementById("LEDGSet").disabled = (data.LEDG.ON==1);
        
        //document.getElementById("UVSet").disabled = (data.UV.ON==1);
        
        //document.getElementById("LASER650Set").disabled = (data.LASER650.ON==1);
        
        
        
        
    
    
    
        
        
         if (data.LEDA.ON==1.0){
             document.getElementById("LEDASwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("LEDASwitch").setAttribute("style", "")
        }
        
        
        if (data.LEDB.ON==1){
             document.getElementById("LEDBSwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("LEDBSwitch").setAttribute("style", "")
        }
        
        if (data.LEDC.ON==1){
             document.getElementById("LEDCSwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("LEDCSwitch").setAttribute("style", "")
        }
        if (data.LEDD.ON==1){
             document.getElementById("LEDDSwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("LEDDSwitch").setAttribute("style", "")
        }
        if (data.LEDE.ON==1){
             document.getElementById("LEDESwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("LEDESwitch").setAttribute("style", "")
        }
        if (data.LEDF.ON==1){
             document.getElementById("LEDFSwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("LEDFSwitch").setAttribute("style", "")
        }
        if (data.LEDG.ON==1){
             document.getElementById("LEDGSwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("LEDGSwitch").setAttribute("style", "")
        }
        
        
         if (data.UV.ON==1){
             document.getElementById("UVSwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("UVSwitch").setAttribute("style", "")
        }
        
        
        if (data.FP1.ON==1){
             document.getElementById("FP1Switch").setAttribute("style", "border-style:inset;background-color:lightblue")
             document.getElementById("FPExcite1").disabled = 1
             document.getElementById("FPBase1").disabled = 1
             document.getElementById("FPEmit1A").disabled = 1
             document.getElementById("FPEmit1B").disabled = 1
             document.getElementById("FPGain1").disabled = 1
        } else {
             document.getElementById("FP1Switch").setAttribute("style", "")
             document.getElementById("FPExcite1").disabled = 0
             document.getElementById("FPBase1").disabled = 0
             document.getElementById("FPEmit1A").disabled = 0
             document.getElementById("FPEmit1B").disabled = 0
             document.getElementById("FPGain1").disabled = 0
        }
        
        if (data.FP2.ON==1){
             document.getElementById("FP2Switch").setAttribute("style", "border-style:inset;background-color:lightblue")
             document.getElementById("FPExcite2").disabled = 1
             document.getElementById("FPBase2").disabled = 1
             document.getElementById("FPEmit2A").disabled = 1
             document.getElementById("FPEmit2B").disabled = 1
             document.getElementById("FPGain2").disabled = 1
        } else {
             document.getElementById("FP2Switch").setAttribute("style", "")
             document.getElementById("FPExcite2").disabled = 0
             document.getElementById("FPBase2").disabled = 0
             document.getElementById("FPEmit2A").disabled = 0
             document.getElementById("FPEmit2B").disabled = 0
             document.getElementById("FPGain2").disabled = 0
        }
        
        if (data.FP3.ON==1){
             document.getElementById("FP3Switch").setAttribute("style", "border-style:inset;background-color:lightblue")
             document.getElementById("FPExcite3").disabled = 1
             document.getElementById("FPBase3").disabled = 1
             document.getElementById("FPEmit3A").disabled = 1
             document.getElementById("FPEmit3B").disabled = 1
             document.getElementById("FPGain3").disabled = 1
        } else {
             document.getElementById("FP3Switch").setAttribute("style", "")
             document.getElementById("FPExcite3").disabled = 0
             document.getElementById("FPBase3").disabled = 0
             document.getElementById("FPEmit3A").disabled = 0
             document.getElementById("FPEmit3B").disabled = 0
             document.getElementById("FPGain3").disabled = 0
        }
        
        
      
        
         if (data.LASER650.ON==1){
             document.getElementById("LASER650Switch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("LASER650Switch").setAttribute("style", "")
        }
        
         if (data.Thermostat.ON==1){
             document.getElementById("ThermostatSwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("ThermostatSwitch").setAttribute("style", "")
        }
       
        if (data.Pump1.ON==1){
             document.getElementById("Pump1Switch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("Pump1Switch").setAttribute("style", "")
        }
        
        if (data.Pump2.ON==1){
             document.getElementById("Pump2Switch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("Pump2Switch").setAttribute("style", "")
        }
        
         if (data.Pump3.ON==1){
             document.getElementById("Pump3Switch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("Pump3Switch").setAttribute("style", "")
        }
        
         if (data.Pump4.ON==1){
             document.getElementById("Pump4Switch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("Pump4Switch").setAttribute("style", "")
        }
        
         if (data.Stir.ON==1){
             document.getElementById("StirSwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("StirSwitch").setAttribute("style", "")
        }
        
         if (data.Light.ON==1){
             document.getElementById("LightSwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("LightSwitch").setAttribute("style", "")
        }
        
         if (data.Custom.ON==1){
             document.getElementById("CustomSwitch").setAttribute("style", "border-style:inset;background-color:lightblue")
             
        } else {
             document.getElementById("CustomSwitch").setAttribute("style", "")
        }
        
        
        if (data.presentDevices.M0 ==0) {
            document.getElementById("Device0").disabled= Boolean(1)
        
        } else if (data.UIDevice=='M0'){
            document.getElementById("Device0").disabled= Boolean(0)
            document.getElementById("Device0").setAttribute("style", "border-style:inset;background-color:LimeGreen")
             
        } else {
            document.getElementById("Device0").disabled= Boolean(0)
            document.getElementById("Device0").setAttribute("style", "")
        }
        
        
        
        if (data.presentDevices.M1 ==0) {
            document.getElementById("Device1").disabled= Boolean(1)
        
        } else if (data.UIDevice=='M1'){
            document.getElementById("Device1").disabled= Boolean(0)
            document.getElementById("Device1").setAttribute("style", "border-style:inset;background-color:LimeGreen")
             
        } else {
            document.getElementById("Device1").disabled= Boolean(0)
            document.getElementById("Device1").setAttribute("style", "")
        }
        
        
        
        if (data.presentDevices.M2 ==0) {
            document.getElementById("Device2").disabled= Boolean(1)
        
        } else if (data.UIDevice=='M2'){
            document.getElementById("Device2").disabled= Boolean(0)
            document.getElementById("Device2").setAttribute("style", "border-style:inset;background-color:LimeGreen")
             
        } else {
            document.getElementById("Device2").disabled= Boolean(0)
            document.getElementById("Device2").setAttribute("style", "")
        }
        
        
        
        if (data.presentDevices.M3 ==0) {
            document.getElementById("Device3").disabled= Boolean(1)
        
        } else if (data.UIDevice=='M3'){
            document.getElementById("Device3").disabled= Boolean(0)
            document.getElementById("Device3").setAttribute("style", "border-style:inset;background-color:LimeGreen")
             
        } else {
            document.getElementById("Device3").disabled= Boolean(0)
            document.getElementById("Device3").setAttribute("style", "")
        }
        
        
        
        if (data.presentDevices.M4 ==0) {
            document.getElementById("Device4").disabled= Boolean(1)
        
        } else if (data.UIDevice=='M4'){
            document.getElementById("Device4").disabled= Boolean(0)
            document.getElementById("Device4").setAttribute("style", "border-style:inset;background-color:LimeGreen")
             
        } else {
            document.getElementById("Device4").disabled= Boolean(0)
            document.getElementById("Device4").setAttribute("style", "")
        }
        
        
        
        if (data.presentDevices.M5 ==0) {
            document.getElementById("Device5").disabled= Boolean(1)
        
        } else if (data.UIDevice=='M5'){
            document.getElementById("Device5").disabled= Boolean(0)
            document.getElementById("Device5").setAttribute("style", "border-style:inset;background-color:LimeGreen")
             
        } else {
            document.getElementById("Device5").disabled= Boolean(0)
            document.getElementById("Device5").setAttribute("style", "")
        }
        
        
        if (data.presentDevices.M6 ==0) {
            document.getElementById("Device6").disabled= Boolean(1)
        
        } else if (data.UIDevice=='M6'){
            document.getElementById("Device6").disabled= Boolean(0)
            document.getElementById("Device6").setAttribute("style", "border-style:inset;background-color:LimeGreen")
             
        } else {
            document.getElementById("Device6").disabled= Boolean(0)
            document.getElementById("Device6").setAttribute("style", "")
        }
        
        if (data.presentDevices.M7 ==0) {
            document.getElementById("Device7").disabled= Boolean(1)
        
        } else if (data.UIDevice=='M7'){
            document.getElementById("Device7").disabled= Boolean(0)
            document.getElementById("Device7").setAttribute("style", "border-style:inset;background-color:LimeGreen")
             
        } else {
            document.getElementById("Device7").disabled= Boolean(0)
            document.getElementById("Device7").setAttribute("style", "")
        }
        
        
        
        
        
        var TurbidostatOn = Boolean(data.OD.ON); //True if we are regulating OD

        document.getElementById("Pump1Switch").disabled = (TurbidostatOn);
        document.getElementById("Pump1Set").disabled = (TurbidostatOn);
        document.getElementById("Pump2Switch").disabled = (TurbidostatOn);
        document.getElementById("Pump2Set").disabled = (TurbidostatOn);
         if (TurbidostatOn){
             document.getElementById("ODRegulate").setAttribute("style", "border-style:inset;background-color:lightblue")
        } else {
             document.getElementById("ODRegulate").setAttribute("style", "")
        }
        document.getElementById("ODRegulate").disabled = !Boolean(data.Experiment.ON)
        
        
         if (data.Zigzag.ON==1){
             document.getElementById("Zigzag").setAttribute("style", "border-style:inset;background-color:lightblue")
        } else {
             document.getElementById("Zigzag").setAttribute("style", "")
        }
        document.getElementById("Zigzag").disabled = !TurbidostatOn
             
               
       // Following if statement is for things that should be done only when changing betwix devices.
        if (document.getElementById("FPRefresh").value != data.UIDevice){
            document.getElementById("FPRefresh").value = data.UIDevice
            
            document.getElementById("FPExcite1").value = data.FP1.LED
            document.getElementById("FPBase1").value = data.FP1.BaseBand
            document.getElementById("FPEmit1A").value = data.FP1.Emit1Band
            document.getElementById("FPEmit1B").value = data.FP1.Emit2Band
            document.getElementById("FPGain1").value = data.FP1.Gain
            
            document.getElementById("FPExcite2").value = data.FP2.LED
            document.getElementById("FPBase2").value = data.FP2.BaseBand
            document.getElementById("FPEmit2A").value = data.FP2.Emit1Band
            document.getElementById("FPEmit2B").value = data.FP2.Emit2Band
            document.getElementById("FPGain2").value = data.FP2.Gain
            
            document.getElementById("FPExcite3").value = data.FP3.LED
            document.getElementById("FPBase3").value = data.FP3.BaseBand
            document.getElementById("FPEmit3A").value = data.FP3.Emit1Band
            document.getElementById("FPEmit3B").value = data.FP3.Emit2Band
            document.getElementById("FPGain3").value = data.FP3.Gain
        }
              
        // Now to draw the charts
        if( document.getElementById("GraphReplot").value!== data.time.record.length || document.getElementById("FPRefresh").innerHTML != data.UIDevice){
		  

          document.getElementById("GraphReplot").value=data.time.record.length;
          document.getElementById("FPRefresh").innerHTML = data.UIDevice

          var x =data.time.record.toString()
          var y=data.OD.record.toString()
          //drawChart(x,x,'cat','dog');
          drawChart2(2,1,data.time.record.toString(),data.OD.record.toString(),data.OD.targetrecord.toString(),"","","","",'Time (h)','Optical Density','OD,Target')
          drawChart2(4,2,data.time.record.toString(),data.ThermometerIR.record.toString(),data.Thermostat.record.toString(),data.ThermometerInternal.record.toString(),data.ThermometerExternal.record.toString(),"","",'Time (h)','Temperature (C)','Culture Temperature,Target,Internal Air, External Air')
          drawChart2(1,3,data.time.record.toString(),data.Pump1.record.toString(),"" ,"","","","",'Time (h)','Pump Rate','Pump 1 (Input),')
		  
			  
		
          //drawChart2(2,3,data.time.record.toString(),data.Pump1.record.toString(),data.Pump2.record.toString()  ,"","","","",'Time (h)','Pump Rate','Pump 1, Pump 2')
          //data.Pump2.record.toString()   <-- removed from above line.
          
          
          
          if(document.getElementById("FPEmit1B").value=="OFF"){
                drawChart2(1,4,data.time.record.toString(),data.FP1.Emit1Record.toString(),"","","","","",'Time (h)','Normalised FP Emission','Emission Band 1')
              
          } else{
                drawChart2(2,4,data.time.record.toString(),data.FP1.Emit1Record.toString(),data.FP1.Emit2Record.toString(),"","","","",'Time (h)','Normalised FP Emission','Emission Band 1, Emission Band 2')    
          }
          
            if(document.getElementById("FPEmit2B").value=="OFF"){
                drawChart2(1,5,data.time.record.toString(),data.FP2.Emit1Record.toString(),"","","","","",'Time (h)','Normalised FP Emission','Emission Band 1')
              
          } else{
            drawChart2(2,5,data.time.record.toString(),data.FP2.Emit1Record.toString(),data.FP2.Emit2Record.toString(),"","","","",'Time (h)','Normalised FP Emission','Emission Band 1, Emission Band 2')
          }
          
           if(document.getElementById("FPEmit3B").value=="OFF"){
                drawChart2(1,6,data.time.record.toString(),data.FP3.Emit1Record.toString(),"","","","","",'Time (h)','Normalised FP Emission','Emission Band 1')
              
          } else{
            drawChart2(2,6,data.time.record.toString(),data.FP3.Emit1Record.toString(),data.FP3.Emit2Record.toString(),"","","","",'Time (h)','Normalised FP Emission','Emission Band 1, Emission Band 2')
          }
		  
		  
		    if (data.Zigzag.ON==1){
		  drawChart2(1,7,data.time.record.toString(),data.GrowthRate.record.toString(),"" ,"","","","",'Time (h)','Growth Rate','Growth Rate,')
		  }
		  

        }
        

}






function drawChart2(num,plotID,data_x,data_y1,data_y2,data_y3,data_y4,data_y5,data_y6,xlabel,ylabel,DataNames) {
    var data = new google.visualization.DataTable();
    
    data.addColumn('number', xlabel);
    DataNames=DataNames.split(",")
    var ToPlot=data_x.split(",").map(Number);
    
    Array.prototype.zip = function (arr) {
         return this.map(function (e, i) {
            return [e, arr[i]];
         })
      };
     
     
     var myarray=new Array(ToPlot.length)
     for (i=0; i < ToPlot.length; i++){
        myarray[i]=new Array(num+1)
        myarray[i][0]=ToPlot[i]/3600.0;
     }
     
    for (var i=0;i<num;i++){
      data.addColumn('number', DataNames[i]);
      var yin = eval("data_y"+ (i+1))
      var data_y=yin.split(",").map(Number);
      for (j=0; j < ToPlot.length; j++){
           myarray[j][i+1]=data_y[j];
      }
      //ToPlot=ToPlot.zip(data_y);
    }
    
      
      data.addRows(myarray)
      
    
     var options = {
        height: 400,
            
        hAxis: {
         title: xlabel
        },
        vAxis: {
         title: ylabel
        },
        legend: {position: 'top', alignment: 'end'},
        chartArea: {width: '80%'}
      };
      
      if (charts[plotID] === undefined || charts[plotID] === null) {
          charts[plotID] = new google.visualization.LineChart(document.getElementById('chart_div'+plotID));
   } else {
          charts[plotID].clearChart(); //We are doing this (clearing the chart each iteration) to avoid a memory leak in Google Charts!
   }
   
   


    charts[plotID].draw(data, options);
	
	data={};




      
    
   
    

}



