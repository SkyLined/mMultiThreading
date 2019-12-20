import threading;
from mDebugOutput import cWithDebugOutput, fsToString;
from .cLock import cLock;

class cThread(cWithDebugOutput):
  __oThread_by_uId = {};
  
  @staticmethod
  def foGetCurrent():
    return cThread.__oThread_by_uId.get(threading.currentThread().ident);
  
  def __init__(oSelf, fMain, *txArguments, **dxArguments):
    oSelf.__fMain = fMain;
    oSelf.__txArguments = txArguments;
    oSelf.__dxArguments = dxArguments;
    oSelf.__bVital = True;
    oSelf.__uId = None;
    oSelf.__bStarted = False;
    oSelf.__bRunning = False;
    oSelf.__bTerminated = False;
    oSelf.__oTerminatedLock = cLock("cThread.__oTerminatedLock", bLocked = True);
  
  @property
  def bVital(oSelf):
    return oSelf.__bVital;
  
  @property
  def bStarted(oSelf):
    return oSelf.__bStarted;
  
  @property
  def bRunning(oSelf):
    return oSelf.__bRunning;
  
  @property
  def bTerminated(oSelf):
    return oSelf.__bTerminated;
  
  @property
  def uId(oSelf):
    return oSelf.__uId;
  
  def fStart(oSelf, bVital = None):
    if bVital is not None:
      oSelf.__bVital = bVital;
    oSelf.__bStarted = True;
    oSelf.__oPythonThread = threading.Thread(target = oSelf.__fMainWrapper);
    oSelf.__oPythonThread.daemon = not oSelf.__bVital;
    oSelf.__oPythonThread.start();
  
  def fWait(oSelf):
    oSelf.__oPythonThread.join();
  
  def __fMainWrapper(oSelf):
    oSelf.__bRunning = True;
    oSelf.__uId = oSelf.__oPythonThread.ident;
    cThread.__oThread_by_uId[oSelf.__uId] = oSelf;
    oSelf.__oPythonThread.name = oSelf.fsToString();
    oSelf.fEnterFunctionOutput();
    try:
      oSelf.__fMain(*oSelf.__txArguments, **oSelf.__dxArguments);
    except Exception as oException:
      oSelf.fFatalExceptionOutput(oException);
    else:
      oSelf.fExitFunctionOutput();
    finally:
      oSelf.__bRunning = False;
      oSelf.__bTerminated = True;
      del cThread.__oThread_by_uId[oSelf.__uId];
      oSelf.__oTerminatedLock.fRelease();
  
  def fsToString(oSelf):
    if hasattr(oSelf.__fMain, "im_self"):
      oMainSelf = getattr(oSelf.__fMain, "im_self");
      sMain = "%s.%s" % (fsToString(oMainSelf, 80), oSelf.__fMain.__name__);
    elif hasattr(oSelf.__fMain, "im_class"):
      cMainClass = getattr(oSelf.__fMain, "im_class");
      sMain = "%s.%s" % (cMainClass.__name__, oSelf.__fMain.__name__);
    else:
      sMain = oSelf.__fMain.__name__;
    return "%s{%s}" % (oSelf.__class__.__name__, ", ".join([s for s in [
      sMain,
      "not started" if not oSelf.__bStarted else None,
      "#%d" % oSelf.__uId if oSelf.__uId is not None else None,
      "running" if oSelf.__bRunning else None,
      "terminated" if oSelf.__bTerminated else None,
    ] if s]));
