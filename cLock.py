import os, queue, threading, time, threading, traceback;

try: # mDebugOutput use is Optional
  from mDebugOutput import ShowDebugOutput, fShowDebugOutput, cCallStack as c0CallStack;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  ShowDebugOutput = fShowDebugOutput = lambda x: x; # NOP
  c0CallStack = None;

from .cWithCallbacks import cWithCallbacks;

def fsGetCallersCaller(uThreadId):
  uThreadId = threading.currentThread().ident;
  (sFileName, uLineNumber, sFunctionName, sSource) = traceback.extract_stack(limit = 4)[0];
  return "%s @ %s/%d thread #%d" % (sFunctionName, os.path.dirname(sFileName), uLineNumber, uThreadId);

guErrorNormalColor = 0x0F07;
guErrorHighlightColor = 0x0F07;

class cLock(cWithCallbacks):
  @classmethod
  @ShowDebugOutput
  def faoWaitUntilLocksAreUnlocked(oSelf, aoLocks, n0TimeoutInSeconds = None):
    oAtLeastOneLockIsUnlockedLock = cLock("faoWaitUntilLocksAreUnlockedLock", bLocked = True);
    def fHandleUnlock(oLock):
      oAtLeastOneLockIsUnlockedLock.fbRelease();
    for oLock in aoLocks:
      if not oLock.bLocked:
        oAtLeastOneLockIsUnlockedLock.fbRelease();
      else:
        oLock.fAddCallback("unlocked", fHandleUnlock);
    oAtLeastOneLockIsUnlockedLock.fbWait(n0TimeoutInSeconds);
    return [
      oLock
      for oLock in aoLocks
      if not oLock.bLocked
    ];
    
  def __init__(oSelf, s0Description = None, uSize = 1, bLocked = False, n0DeadlockTimeoutInSeconds = None):
    oSelf.__sDescription = s0Description or str(id(oSelf));
    oSelf.__uSize = uSize;
    oSelf.__oQueue = queue.Queue(uSize);
    oSelf.__oQueuePutLock = queue.Queue(1);
    if n0DeadlockTimeoutInSeconds is not None:
      assert isinstance(n0DeadlockTimeoutInSeconds, (int, float)) and n0DeadlockTimeoutInSeconds >=0, \
          "Invalid timeout value %s" % repr(nTimeoutInSeconds);
    oSelf.__n0DeadlockTimeoutInSeconds = n0DeadlockTimeoutInSeconds;
    oSelf.fAddEvents("locked", "unlocked");
    if bLocked:
      oSelf.__xLastAcquireCallStackOrThreadId = c0CallStack.foForThisFunctionsCaller() if c0CallStack else threading.current_thread().ident;
      for u in range(uSize):
        oSelf.__oQueue.put(oSelf.__xLastAcquireCallStackOrThreadId);
    else:
      oSelf.__xLastAcquireCallStackOrThreadId = None;
  
  @property
  def bLocked(oSelf):
    return oSelf.__oQueue.full();
  
  @property
  def sLockedBy(oSelf):
    if oSelf.__oQueue.full():
      xStackOrThreadId = oSelf.__xLastAcquireCallStackOrThreadId;
      if c0CallStack:
        return "%s in thread %d/0x%X" % (xStackOrThreadId.oTopFrame.sCallDescription, xStackOrThreadId.uThreadId, xStackOrThreadId.uThreadId);
      else:
        return "thread %d/0x%X" % (xStackOrThreadId, xStackOrThreadId);
    return None;
  
  @ShowDebugOutput
  def fAcquire(oSelf):
    assert oSelf.__n0DeadlockTimeoutInSeconds is not None, \
        "Cannot acquire a lock without a timeout if no deadlock timeout is provided."
    xCallStackOrThreadId = c0CallStack.foForThisFunctionsCaller() if c0CallStack else threading.current_thread().ident;
    if not oSelf.__fbAcquire(xCallStackOrThreadId, oSelf.__n0DeadlockTimeoutInSeconds):
      xLastAcquireCallStackOrThreadId = oSelf.__xLastAcquireCallStackOrThreadId;
      if (
        xLastAcquireCallStackOrThreadId is not None and (
          xLastAcquireCallStackOrThreadId.uThreadId == xCallStackOrThreadId.uThreadId if c0CallStack
          else xLastAcquireCallStackOrThreadId == xCallStackOrThreadId
        )
      ):
        oSelf.__fTerminateWithSingleThreadDeadlock(xLastAcquireCallStackOrThreadId);
      oSelf.__fTerminateWithMultiThreadDeadlock(xLastAcquireCallStackOrThreadId);
  
  @ShowDebugOutput
  def fbAcquire(oSelf, nTimeoutInSeconds = 0):
    xCallStackOrThreadId = c0CallStack.foForThisFunctionsCaller() if c0CallStack else threading.current_thread().ident;
    return oSelf.__fbAcquire(xCallStackOrThreadId, nTimeoutInSeconds);
  
  def __fbAcquire(oSelf, xCallStackOrThreadId, nTimeoutInSeconds):
    if nTimeoutInSeconds is not None:
      assert isinstance(nTimeoutInSeconds, (int, float)) and nTimeoutInSeconds >=0, \
          "Invalid timeout value %s" % repr(nTimeoutInSeconds);
      fShowDebugOutput("Attempting to lock %s for up to %f seconds..." % (oSelf, nTimeoutInSeconds));
    else:
      fShowDebugOutput("Attempting to lock %s..." % oSelf);
    nEndTime = time.time() + nTimeoutInSeconds;
    try:
      oSelf.__oQueuePutLock.put(0, nTimeoutInSeconds > 0, nTimeoutInSeconds);
      try:
        nRemainingTimeoutInSeconds = max(0, nEndTime - time.time());
        try:
          oSelf.__oQueue.put(oSelf.__xLastAcquireCallStackOrThreadId, nRemainingTimeoutInSeconds > 0, nRemainingTimeoutInSeconds);
        except queue.Full:
          if nTimeoutInSeconds > 0:
            fShowDebugOutput("Not acquired becuase waiting for locked to become unlocked timed out.");
          else:
            fShowDebugOutput("Not acquired because already locked.");
          return False;
        oSelf.__xLastAcquireCallStackOrThreadId = xCallStackOrThreadId;
        fShowDebugOutput("Acquired.");
        oSelf.fFireCallbacks("locked");
        return True;
      finally:
        oSelf.__oQueuePutLock.get(False, 0);
    except queue.Full:
      fShowDebugOutput("Not acquired because busy.");
      return False;
  
  def __fTerminateWithSingleThreadDeadlock(oSelf, xCallStackOrThreadId):
    oSelf.__fTerminateWithConsoleOutput(
      "Attempt to acquire lock twice in a single thread",
      [
        [
          guErrorHighlightColor, "Cannot acquire the same lock twice from the same thread!",
        ],
        [
          guErrorNormalColor, "Lock: ", guErrorHighlightColor, str(oSelf),
        ],
        [
          guErrorNormalColor, "Thread: ",
          guErrorHighlightColor, "%d/0x%X" % (xCallStackOrThreadId.uThreadId, xCallStackOrThreadId.uThreadId),
          guErrorNormalColor, " (",
          guErrorHighlightColor, xCallStackOrThreadId.sThreadName or "<unnamed>",
          guErrorNormalColor, ")!",
        ] if cClassStack else [
          guErrorNormalColor, "Thread: ",
          guErrorHighlightColor, "%d/0x%X" % (xCallStackOrThreadId, xCallStackOrThreadId,
          guErrorNormalColor, "!"),
        ],
      ],
      xCallStackOrThreadId
    );
  def __fTerminateWithMultiThreadDeadlock(oSelf, xCallStackOrThreadId):
    oSelf.__fTerminateWithConsoleOutput(
      "Deadlock detected",
      [
        [
          guErrorHighlightColor, "Cannot acquire lock within ", guErrorHighlightColor,
          "%f" % oSelf.__n0DeadlockTimeoutInSeconds, guErrorNormalColor, " seconds!",
        ],
        [
          guErrorNormalColor, "Lock: ", guErrorHighlightColor, str(oSelf),
        ],
        [
          guErrorNormalColor, "Currently locked by thread: ",
          guErrorHighlightColor, "%d/0x%X" % (oSelf.__xLastAcquireCallStackOrThreadId.uThreadId, oSelf.__xLastAcquireCallStackOrThreadId.uThreadId),
          guErrorNormalColor, " (",
          guErrorHighlightColor, oSelf.__xLastAcquireCallStackOrThreadId.sThreadName or "<unnamed>",
          guErrorNormalColor, ")!",
        ] if c0CallStack else [
          guErrorNormalColor, "Currently locked by thread: ",
          guErrorHighlightColor, "%d/0x%X" % (oSelf.__xLastAcquireCallStackOrThreadId, oSelf.__xLastAcquireCallStackOrThreadId),
          guErrorNormalColor, "!",
        ],
        [
          guErrorNormalColor, "Attempted to be locked by thread: ",
          guErrorHighlightColor, "%d/0x%X" % (xCallStackOrThreadId.uThreadId, xCallStackOrThreadId.uThreadId),
          guErrorNormalColor, " (",
          guErrorHighlightColor, xCallStackOrThreadId.sThreadName or "<unnamed>",
          guErrorNormalColor, ")!",
        ] if c0CallStack else [
          guErrorNormalColor, "Attempted to be locked by thread: ",
          guErrorHighlightColor, "%d/0x%X" % (xCallStackOrThreadId, xCallStackOrThreadId),
          guErrorNormalColor, "!",
        ],
      ],
      xCallStackOrThreadId
    );
  def __fTerminateWithConsoleOutput(oSelf, sMessage, aasConsoleOutputLines, xCallStackOrThreadId):
    assert fTerminateWithConsoleOutput, \
        "\n".join( # Strip all color codes and just output the text:
          [sMessage] + [
            "".join([
              sConsoleOutput for sConsoleOutput in asConsoleOutputLine
              if isinstance(sConsoleOutput, str)
            ])
            for asConsoleOutputLine in aasConsoleOutputLines
          ]
        );
    fTerminateWithConsoleOutput(
      sMessage,
      aasConsoleOutputLines + (
        [
          [],
          [
            guErrorNormalColor, "Stack at the time the lock was last acquired:",
          ]
        ] + oSelf.__xLastAcquireCallStackOrThreadId.faasCreateConsoleOutput(bAddHeader = False) + [
          [],
          [
            guErrorNormalColor, "Stack when the thread attempted to acquired the lock a second time:",
          ]
        ] + xCallStackOrThreadId.faasCreateConsoleOutput(bAddHeader = False)
      ) if c0CallStack else []
    );
  
  @ShowDebugOutput
  def fRelease(oSelf):
    fShowDebugOutput("Unlocking %s..." % oSelf);
    try:
      oSelf.__xLastAcquireCallStackOrThreadId = oSelf.__oQueue.get(False, 0);
    except queue.Empty:
      raise AssertionError("Cannot release lock %s because it is not locked!" % oSelf);
    oSelf.fFireCallbacks("unlocked");

  @ShowDebugOutput
  def fbRelease(oSelf):
    fShowDebugOutput("Attempting to unlock %s if locked..." % oSelf);
    try:
      oSelf.__xLastAcquireCallStackOrThreadId = oSelf.__oQueue.get(False, 0);
    except queue.Empty:
      fShowDebugOutput("Not locked");
      return False;
    fShowDebugOutput("Unlocked");
    oSelf.fFireCallbacks("unlocked");
    return True;

  @ShowDebugOutput
  def fbIsLockedByCurrentThread(oSelf):
    xCallStackOrThreadId = oSelf.__xLastAcquireCallStackOrThreadId;
    return (
      (xCallStackOrThreadId.uThreadId if c0CallStack else xCallStackOrThreadId) == threading.currentThread().ident
    ) if xCallStackOrThreadId else False;

  @ShowDebugOutput
  def fbWait(oSelf, nTimeoutInSeconds):
    assert isinstance(nTimeoutInSeconds, (int, float)) and nTimeoutInSeconds >= 0, \
        "Invalid timeout value %s" % repr(nTimeoutInSeconds);
    # Wait for the lock to be unlocked by trying to lock it with a timeout. If we locked it, unlock it again.
    # Returns True of the lock was unlocked during the call.
    fShowDebugOutput("Waiting for %s up to %d seconds..." % (oSelf, nTimeoutInSeconds));
    nEndTime = time.time() + nTimeoutInSeconds;
    try:
      oSelf.__oQueuePutLock.put(0, True, nTimeoutInSeconds);
      try:
        nRemainingTimeoutInSeconds = nEndTime - time.time();
        if nRemainingTimeoutInSeconds < 0:
          fShowDebugOutput("Timeout");
          return False;
        oSelf.__oQueue.put(0, True, float(nRemainingTimeoutInSeconds));
        oSelf.__oQueue.get(False, 0);
      finally:
        oSelf.__oQueuePutLock.get(False, 0);
    except queue.Full:
      return False;
    return True;
  
  @ShowDebugOutput
  def fWait(oSelf):
    # Wait for the lock to be unlocked by trying to lock it. After we locked it, unlock it again.
    oSelf.__oQueuePutLock.put(0, True);
    try:
      oSelf.__oQueue.put(0, True);
      oSelf.__oQueue.get(False, 0);
    finally:
      oSelf.__oQueuePutLock.get(False, 0);
  
  def fasGetDetails(oSelf):
    # This is done without a property lock, so race-conditions exist and it
    # approximates the real values.
    uAcquiredCount = oSelf.__oQueue.qsize();
    xCallStackOrThreadId = oSelf.__xLastAcquireCallStackOrThreadId;
    sLastAcquireCaller = (
      (
        "%s @ %s in thread %d/0x%X" % (
          xCallStackOrThreadId.oTopFrame.sCallDescription, xCallStackOrThreadId.oTopFrame.sLastExecutedCodeLocation,
          xCallStackOrThreadId.uThreadId, xCallStackOrThreadId.uThreadId
        )
      ) if c0CallStack else (
        "thread %d/0x%X" % (xCallStackOrThreadId, xCallStackOrThreadId)
      )
    ) if xCallStackOrThreadId else None;
    return [s for s in [
      oSelf.__sDescription,
      ("locked by %s" % sLastAcquireCaller) if uAcquiredCount == oSelf.__uSize else
          "unlocked" if uAcquiredCount == 0 else 
          ("%d/%d (last acquired by %s)" % (uAcquiredCount, oSelf.__uSize, sLastAcquireCaller)),
    ] if s];
  
  def __repr__(oSelf):
    sModuleName = ".".join(oSelf.__class__.__module__.split(".")[:-1]);
    return "<%s.%s#%X|%s>" % (sModuleName, oSelf.__class__.__name__, id(oSelf), "|".join(oSelf.fasGetDetails()));
  
  def __str__(oSelf):
    return "%s#%X{%s}" % (oSelf.__class__.__name__, id(oSelf), ", ".join(oSelf.fasGetDetails()));
