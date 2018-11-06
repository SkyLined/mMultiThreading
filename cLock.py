import os, Queue, threading, traceback;
from mDebugOutput import cWithDebugOutput;

def fsGetCallersCaller():
  uThreadId = threading.currentThread().ident;
  (sFileName, uLineNumber, sFunctionName, sSource) = traceback.extract_stack(limit = 4)[0];
  return "%s @ %s/%d thread #%d" % (sFunctionName, os.path.dirname(sFileName), uLineNumber, uThreadId);

class cLock(cWithDebugOutput):
  def __init__(oSelf, sDescription = None, uSize = 1, bLocked = False):
    oSelf.__sDescription = sDescription or id(oSelf);
    oSelf.__uSize = uSize;
    oSelf.__oQueue = Queue.Queue(uSize);
    oSelf.__sLastAcquireCaller = None;
    if bLocked:
      for u in xrange(uSize):
        oSelf.__oQueue.put(fsGetCallersCaller());
  
  @property
  def bLocked(oSelf):
    return oSelf.__oQueue.full();
  
  @property
  def sLockedBy(oSelf):
    return oSelf.__sLastAcquireCaller;
  
  def fAcquire(oSelf):
    oSelf.fEnterFunctionOutput();
    try:
      oSelf.__oQueue.put(oSelf.__sLastAcquireCaller);
      oSelf.__sLastAcquireCaller = fsGetCallersCaller(); # Race condition, but this is for debug purpose only, so not worth complicating things to get it right.
      return oSelf.fExitFunctionOutput();
    except Exception as oException:
      oSelf.fxRaiseExceptionOutput(oException);
      raise;
  
  def fbAcquire(oSelf, nTimeoutInSeconds = 0):
    # Fast path to reduce debug output
    if not nTimeoutInSeconds and oSelf.__oQueue.full(): return False;
    oSelf.fEnterFunctionOutput(nTimeoutInSeconds = nTimeoutInSeconds);
    try:
      try:
        oSelf.__oQueue.put(oSelf.__sLastAcquireCaller, True, float(nTimeoutInSeconds));
      except Queue.Full:
        return oSelf.fxExitFunctionOutput(False);
      oSelf.__sLastAcquireCaller = fsGetCallersCaller(); # Race condition, but this is for debug purpose only, so not worth complicating things to get it right.
      return oSelf.fxExitFunctionOutput(True);
    except Exception as oException:
      oSelf.fxRaiseExceptionOutput(oException);
      raise;
  
  def fRelease(oSelf):
    oSelf.fEnterFunctionOutput();
    try:
      oSelf.__sLastAcquireCaller = oSelf.__oQueue.get(False, 0);
      return oSelf.fExitFunctionOutput();
    except Exception as oException:
      oSelf.fxRaiseExceptionOutput(oException);
      raise;

  def fbRelease(oSelf):
    # Fast path to reduce debug output
    if oSelf.__oQueue.empty(): return False;
    oSelf.fEnterFunctionOutput();
    try:
      try:
        oSelf.__sLastAcquireCaller = oSelf.__oQueue.get(False, 0);
      except Queue.Empty:
        return oSelf.fxExitFunctionOutput(False, "Not locked");
      return oSelf.fxExitFunctionOutput(True, "Unlocked");
    except Exception as oException:
      oSelf.fxRaiseExceptionOutput(oException);
      raise;

  def fWait(oSelf):
    # If the lock is locked, wait for it to be unlocked by trying to lock it ourselves. Once locked, unlock it again.
    oSelf.fEnterFunctionOutput();
    try:
      if oSelf.bLocked:
        oSelf.__oQueue.put(0);
        oSelf.__oQueue.get(False, 0);
      return oSelf.fExitFunctionOutput();
    except Exception as oException:
      oSelf.fxRaiseExceptionOutput(oException);
      raise;

  def fbWait(oSelf, nTimeoutInSeconds = None):
    # Wait for the lock to be unlocked by trying to lock it with a timeout. If we locked it, unlock it again.
    # Returns True of the lock was unlocked during the call.
    oSelf.fEnterFunctionOutput(nTimeoutInSeconds = nTimeoutInSeconds);
    try:
      try:
        oSelf.__oQueue.put(0, True, float(nTimeoutInSeconds));
      except Queue.Full:
        return oSelf.fxExitFunctionOutput(False);
        oSelf.__oQueue.get(False, 0);
      return oSelf.fxExitFunctionOutput(True);
    except Exception as oException:
      oSelf.fxRaiseExceptionOutput(oException);
      raise;
  
  def fsToString(oSelf):
    return "%s{%s (%s)}" % (
      oSelf.__class__.__name__,
      oSelf.__sDescription,
      ("locked by %s" % oSelf.__sLastAcquireCaller) if oSelf.__oQueue.full() else
        "unlocked" if oSelf.__oQueue.empty() else
        "%d/%d (last acquired by %s)" % (oSelf.__oQueue.qsize(), oSelf.__uSize, oSelf.__sLastAcquireCaller),
    );