import threading;
from mDebugOutput import cCallStack, ShowDebugOutput, fShowDebugOutput, fTerminateWithException;
from mDebugOutput.mColors import *;
from .cLock import cLock;

goThreadCounterLock = threading.Lock();
guThreadCounter = 0;
def fuCountNewThreadAndReturnIndex():
  global goThreadCounterLock, guThreadCounter;
  goThreadCounterLock.acquire();
  try:
    uThreadIndex = guThreadCounter;
    guThreadCounter += 1;
    return uThreadIndex;
  finally:
    goThreadCounterLock.release();

class cThread(object):
  __oThread_by_uId = {};
  
  @staticmethod
  def foGetCurrent():
    return cThread.__oThread_by_uId.get(threading.currentThread().ident);
  
  @ShowDebugOutput
  def __init__(oSelf, fMain, *txArguments, **dxArguments):
    oSelf.__fMain = fMain;
    oSelf.__oCreateCallStack = cCallStack.foFromThisFunctionsCaller();
    oSelf.__txArguments = txArguments;
    oSelf.__dxArguments = dxArguments;
    oSelf.__bVital = True;
    oSelf.__uId = None;
    oSelf.__bStarted = False;
    oSelf.__bRunning = False;
    oSelf.__bTerminated = False;
    oSelf.__oTerminatedLock = cLock(
      "cThread.__oTerminatedLock",
      bLocked = True
    );
    if hasattr(fMain, "im_self"):
      oMainSelf = getattr(fMain, "im_self");
      oSelf.sMain = "%s.%s" % (oMainSelf.__class__.__name__, fMain.__name__);
      oSelf.sMainId = "%s#%X.%s" % (oMainSelf.__class__.__name__, id(oMainSelf), fMain.__name__);
    elif hasattr(fMain, "im_class"):
      cMainClass = getattr(fMain, "im_class");
      oSelf.sMain = oSelf.sMainId = "%s.%s" % (cMainClass.__name__, fMain.__name__);
    else:
      oSelf.sMain = oSelf.sMainId = fMain.__name__;
    oSelf.uIndex = fuCountNewThreadAndReturnIndex();
  
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
  
  @ShowDebugOutput
  def fStart(oSelf, bVital = None):
    if bVital is not None:
      oSelf.__bVital = bVital;
    oSelf.__bStarted = True;
    oSelf.__oPythonThread = threading.Thread(
      target = oSelf.__fMainWrapper,
      name = oSelf.sMainId,
    );
    oSelf.__oPythonThread.daemon = not oSelf.__bVital;
    oSelf.__oPythonThread.start();
  
  @ShowDebugOutput
  def fWait(oSelf):
    oSelf.__oPythonThread.join();
    return not oSelf.__oPythonThread.isAlive();
  
  @ShowDebugOutput
  def fbWait(oSelf, nzTimeoutInSeconds):
    oSelf.__oPythonThread.join(nzTimeoutInSeconds);
    return not oSelf.__oPythonThread.isAlive();
  
  @ShowDebugOutput
  def __fMainWrapper(oSelf):
    oSelf.__bRunning = True;
    oSelf.__uId = oSelf.__oPythonThread.ident;
    cThread.__oThread_by_uId[oSelf.__uId] = oSelf;
    oSelf.__oPythonThread.name = str(oSelf);
    try:
      oSelf.__fMain(*oSelf.__txArguments, **oSelf.__dxArguments);
    except Exception as oException:
      fTerminateWithException(
        oException,
        aasAdditionalConsoleOutputLines = [
          [
            guStackHeaderColor, "This thread was created in thread ", guStackHeaderHighlightColor, "%d/0x%X" % (oSelf.__oCreateCallStack.uThreadId, oSelf.__oCreateCallStack.uThreadId),
            guStackHeaderColor, " (", guStackHeaderHighlightColor, oSelf.__oCreateCallStack.sThreadName or "<unnamed>", guStackHeaderColor, ")",
            guStackHeaderColor, " with the following stack:",
          ],
        ] + oSelf.__oCreateCallStack.faasCreateConsoleOutput(bAddHeader = False)
      );
    oSelf.__bRunning = False;
    oSelf.__bTerminated = True;
    del cThread.__oThread_by_uId[oSelf.__uId];
    oSelf.__oTerminatedLock.fRelease();
  
  def fasGetDetails(oSelf):
    # This is done without a property lock, so race-conditions exist and it
    # approximates the real values.
    return [s for s in [
      "main = %s" % oSelf.sMain,
      "not started" if not oSelf.__bStarted else None,
      "#%d" % oSelf.__uId if oSelf.__uId is not None else None,
      "running" if oSelf.__bRunning else None,
      "terminated" if oSelf.__bTerminated else None,
    ] if s];
  
  def __repr__(oSelf):
    sModuleName = ".".join(oSelf.__class__.__module__.split(".")[:-1]);
    return "<%s.%s#%X|%s>" % (sModuleName, oSelf.__class__.__name__, id(oSelf), "|".join(oSelf.fasGetDetails()));
  
  def __str__(oSelf):
    return "%s#%X{%s}" % (oSelf.__class__.__name__, id(oSelf), ", ".join(oSelf.fasGetDetails()));
