import threading;

try: # mDebugOutput use is Optional
  from mDebugOutput import ShowDebugOutput, fShowDebugOutput, cCallStack as c0CallStack, fTerminateWithException as f0TerminateWithException;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  ShowDebugOutput = fShowDebugOutput = lambda x: x; # NOP
  c0CallStack = f0TerminateWithException = None;

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
  uExitCodeInternalError = 1; # Default value, can be modified on the entire cThread class or specific instances.
  __oThread_by_uId = {};
  
  @staticmethod
  def foGetCurrent():
    return cThread.__oThread_by_uId.get(threading.currentThread().ident);
  
  @ShowDebugOutput
  def __init__(oSelf, fMain, *txArguments, **dxArguments):
    oSelf.__fMain = fMain;
    oSelf.__oCreateCallStack = c0CallStack.foForThisFunctionsCaller() if c0CallStack else None;
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
    if oSelf.__oPythonThread.is_alive():
      oSelf.__oPythonThread.join();
  
  @ShowDebugOutput
  def fbWait(oSelf, n0TimeoutInSeconds):
    if oSelf.__oPythonThread.is_alive():
      oSelf.__oPythonThread.join(n0TimeoutInSeconds);
    return not oSelf.__oPythonThread.is_alive();
  
  @ShowDebugOutput
  def __fMainWrapper(oSelf):
    oSelf.__bRunning = True;
    oSelf.__uId = oSelf.__oPythonThread.ident;
    cThread.__oThread_by_uId[oSelf.__uId] = oSelf;
    oSelf.__oPythonThread.name = str(oSelf);
    try:
      oSelf.__fMain(*oSelf.__txArguments, **oSelf.__dxArguments);
    except Exception as oException:
      if f0TerminateWithException:
        f0TerminateWithException(
          oException,
          oSelf.uExitCodeInternalError,
          a0asAdditionalConsoleOutputLines = [
            [
              0x0F07, "This thread was created in thread ",
              0x0F0F, "%d/0x%X" % (oSelf.__oCreateCallStack.u0ThreadId, oSelf.__oCreateCallStack.u0ThreadId),
              0x0F07, " (",
              0x0F0F, oSelf.__oCreateCallStack.s0ThreadName or "<unnamed>",
              0x0F07, ") with the following stack:",
            ] if oSelf.__oCreateCallStack.u0ThreadId is not None else [
              0x0F07, "This thread was created in an unknown thread with the following stack:",
            ],
          ] + oSelf.__oCreateCallStack.faasCreateConsoleOutput(bAddHeader = False)
        );
      raise;
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
