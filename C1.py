##CHI_BIO_PROGRAM
#Optogenetic Integral Control Program
from threading import Thread, Lock
def main(M,sysData,api):
    integral=0.0 #Integral in integral controller
    green=0.0 #Intensity of Green actuation 
    red=0.0 #Intensity of red actuation.
    GFPNow=sysData[M]['FP1']['Emit1']
    GFPTarget=sysData[M]['Custom']['Status'] #This is the controller setpoint.
    error=GFPTarget-GFPNow
    if error>0.0075:
        green=1.0
        red=0.0
        sysData[M]['Custom']['param3']=0.0 
    elif error<-0.0075:
        green=0.0
        red=1.0
        sysData[M]['Custom']['param3']=0.0
    else:
        red=1.0
        balance=float(Params[0]) #our guess at green light level to get 50% expression.
        KI=float(Params[1])
        KP=float(Params[2])
        integral=sysData[M]['Custom']['param3']+error*KI
        green=balance+KP*error+integral
        sysData[M]['Custom']['param3']=integral
    GreenThread=Thread(target = api.CustomLEDCycle, args=(M,'LEDD',green))
    GreenThread.setDaemon(True)
    GreenThread.start();
    RedThread=Thread(target = api.CustomLEDCycle, args=(M,'LEDF',red))
    RedThread.setDaemon(True)
    RedThread.start();
    sysData[M]['Custom']['param1']=green
    sysData[M]['Custom']['param2']=red
    api.addTerminal(M,'Program = C1 green= ' + str(green)+ ' red= ' + str(red) + ' integral= ' + str(integral))
