import os, Queue, threading, time, threading, traceback;

from mDebugOutput import cCallStack, ShowDebugOutput, fShowDebugOutput, fTerminateWithDeadlock, fTerminateWithConsoleOutput;
from cWithCallbacks import cWithCallbacks;

def fsGetCallersCaller(uThreadId):
  uThreadId = threading.currentThread().ident;
  (sFileName, uLineNumber, sFunctionName, sSource) = traceback.extract_stack(limit = 4)[0];
  return "%s @ %s/%d thread #%d" % (sFunctionName, os.path.dirname(sFileName), uLineNumber, uThreadId);

guErrorNormalColor = 0x0F07;
guErrorHighlightColor = 0x0F07;

class cLock(cWithCallbacks):
  @classmethod
  @ShowDebugOutput
  def faoWaitUntilLocksAreUnlocked(oSelf, aoLocks, nzTimeoutInSeconds):
    oAtLeastOneLockIsUnLockedLock = cLock("faoWaitUntilLocksAreUnlockedLock", bLocked = True);
    def fReleaseAtLeastOneLockIsUnLockedLock():
      oAtLeastOneLockIsUnLockedLock.fbRelease();
    for oLock in aoLocks:
      oLock.fAddCallback("unlocked", lambda oLock: fReleaseAtLeastOneLockIsUnLockedLock());
      if not oLock.bLocked:
        fReleaseAtLeastOneLockIsUnLockedLock();
    oAtLeastOneLockIsUnLockedLock.fbWait(nzTimeoutInSeconds);
    return [
      oLock
      for oLock in aoLocks
      if not oLock.bLocked
    ];
    
  def __init__(oSelf, szDescription = None, uSize = 1, bLocked = False, nzDeadlockTimeoutInSeconds = None):
    oSelf.__sDescription = szDescription or str(id(oSelf));
    oSelf.__uSize = uSize;
    oSelf.__oQueue = Queue.Queue(uSize);
    oSelf.__oQueuePutLock = Queue.Queue(1);
    if nzDeadlockTimeoutInSeconds is not None:
      assert isinstance(nzDeadlockTimeoutInSeconds, (int, long, float)) and nzDeadlockTimeoutInSeconds >=0, \
          "Invalid timeout value %s" % repr(nTimeoutInSeconds);
    oSelf.__nzDeadlockTimeoutInSeconds = nzDeadlockTimeoutInSeconds;
    oSelf.fAddEvents("locked", "unlocked");
    if bLocked:
      oSelf.__oLastAcquireCallStack = cCallStack.foFromThisFunctionsCaller();
      for u in xrange(uSize):
        oSelf.__oQueue.put(oSelf.__oLastAcquireCallStack);
    else:
      oSelf.__oLastAcquireCallStack = None;
  
  @property
  def bLocked(oSelf):
    return oSelf.__oQueue.full();
  
  @property
  def sLockedBy(oSelf):
    if oSelf.__oQueue.full():
      oStack = oSelf.__oLastAcquireCallStack;
      if oStack:
        return "%s in thread %d/0x%X" % (oStack.oTopFrame.sCallDescription, oStack.uThreadId, oStack.uThreadId);
    return None;
  
  @ShowDebugOutput
  def fAcquire(oSelf):
    assert oSelf.__nzDeadlockTimeoutInSeconds is not None, \
        "Cannot acquire a lock without a timeout if no deadlock timeout is provided."
    oCallStack = cCallStack.foFromThisFunctionsCaller();
    if not oSelf.__fbAcquire(oCallStack, oSelf.__nzDeadlockTimeoutInSeconds):
      if oSelf.__oLastAcquireCallStack and oSelf.__oLastAcquireCallStack.uThreadId == oCallStack.uThreadId:
        oSelf.__fTerminateWithSingleThreadDeadlock(oCallStack);
      oSelf.__fTerminateWithMultiThreadDeadlock(oCallStack);
  
  @ShowDebugOutput
  def fbAcquire(oSelf, nTimeoutInSeconds = 0):
    oCallStack = cCallStack.foFromThisFunctionsCaller();
    return oSelf.__fbAcquire(oCallStack, nTimeoutInSeconds);
  
  def __fbAcquire(oSelf, oCallStack, nTimeoutInSeconds):
    if nTimeoutInSeconds is not None:
      assert isinstance(nTimeoutInSeconds, (int, long, float)) and nTimeoutInSeconds >=0, \
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
          oSelf.__oQueue.put(oSelf.__oLastAcquireCallStack, nRemainingTimeoutInSeconds > 0, nRemainingTimeoutInSeconds);
        except Queue.Full:
          if nTimeoutInSeconds > 0:
            fShowDebugOutput("Not acquired becuase waiting for locked to become unlocked timed out.");
          else:
            fShowDebugOutput("Not acquired because already locked.");
          return False;
        oSelf.__oLastAcquireCallStack = oCallStack;
        fShowDebugOutput("Acquired.");
        oSelf.fFireCallbacks("locked");
        return True;
      finally:
        oSelf.__oQueuePutLock.get(False, 0);
    except Queue.Full:
      fShowDebugOutput("Not acquired because busy.");
      return False;
  
  def __fTerminateWithSingleThreadDeadlock(oSelf, oCallStack):
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
          guErrorNormalColor, "Thread: ", guErrorHighlightColor, "%d/0x%X" % (oCallStack.uThreadId, oCallStack.uThreadId),
          guErrorNormalColor, " (", guErrorHighlightColor, oCallStack.sThreadName or "<unnamed>", guErrorNormalColor, ")!",
        ],
      ],
      oCallStack
    );
  def __fTerminateWithMultiThreadDeadlock(oSelf, oCallStack):
    oSelf.__fTerminateWithConsoleOutput(
      "Deadlock detected",
      [
        [
          guErrorHighlightColor, "Cannot acquire lock within ", guErrorHighlightColor,
          "%f" % oSelf.__nzDeadlockTimeoutInSeconds, guErrorNormalColor, " seconds!",
        ],
        [
          guErrorNormalColor, "Lock: ", guErrorHighlightColor, str(oSelf),
        ],
        [
          guErrorNormalColor, "Currently locked by thread: ", guErrorHighlightColor,
          "%d/0x%X" % (oSelf.__oLastAcquireCallStack.uThreadId, oSelf.__oLastAcquireCallStack.uThreadId),
          guErrorNormalColor, " (", guErrorHighlightColor, oCallStack.sThreadName or "<unnamed>", guErrorNormalColor, ")!",
        ],
        [
          guErrorNormalColor, "Attempted to be locked by thread: ", guErrorHighlightColor,
          "%d/0x%X" % (oCallStack.uThreadId, oCallStack.uThreadId),
          guErrorNormalColor, " (", guErrorHighlightColor, oCallStack.sThreadName or "<unnamed>", guErrorNormalColor, ")!",
        ],
      ],
      oCallStack
    );
  def __fTerminateWithConsoleOutput(oSelf, sMessage, aasConsoleOutputLines, oCallStack):
    fTerminateWithConsoleOutput(
      sMessage,
      aasConsoleOutputLines + [
        [],
        [
          guErrorNormalColor, "Stack at the time the lock was last acquired:",
        ]
      ] + oSelf.__oLastAcquireCallStack.faasCreateConsoleOutput(bAddHeader = False) + [
        [],
        [
          guErrorNormalColor, "Stack when the thread attempted to acquired the lock a second time:",
        ]
      ] + oCallStack.faasCreateConsoleOutput(bAddHeader = False)
    );
  
  @ShowDebugOutput
  def fRelease(oSelf):
    fShowDebugOutput("Unlocking %s..." % oSelf);
    try:
      oSelf.__oLastAcquireCallStack = oSelf.__oQueue.get(False, 0);
    except Queue.Empty:
      raise AssertionError("Cannot release lock %s because it is not locked!" % oSelf);
    oSelf.fFireCallbacks("unlocked");

  @ShowDebugOutput
  def fbRelease(oSelf):
    fShowDebugOutput("Attempting to unlock %s if locked..." % oSelf);
    try:
      oSelf.__oLastAcquireCallStack = oSelf.__oQueue.get(False, 0);
    except Queue.Empty:
      fShowDebugOutput("Not locked");
      return False;
    fShowDebugOutput("Unlocked");
    oSelf.fFireCallbacks("unlocked");
    return True;

  @ShowDebugOutput
  def fbIsLockedByCurrentThread(oSelf):
    oCallStack = oSelf.__oLastAcquireCallStack;
    return oCallStack and oCallStack.uThreadId == threading.currentThread().ident;

  @ShowDebugOutput
  def fbWait(oSelf, nTimeoutInSeconds):
    assert isinstance(nTimeoutInSeconds, (int, long, float)) and nTimeoutInSeconds >= 0, \
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
    except Queue.Full:
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
    oStack = oSelf.__oLastAcquireCallStack;
    sLastAcquireCaller = (
      "%s @ %s in thread %d/0x%X" % (oStack.oTopFrame.sCallDescription, oStack.oTopFrame.sLastExecutedCodeLocation, oStack.uThreadId, oStack.uThreadId) \
          if oStack else None
    );
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
