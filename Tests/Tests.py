import os, sys;
sModulePath = os.path.dirname(__file__);
sys.path = [sModulePath] + [sPath for sPath in sys.path if sPath.lower() != sModulePath.lower()];

from fTestDependencies import fTestDependencies;
fTestDependencies("--automatically-fix-dependencies" in sys.argv);
sys.argv = [s for s in sys.argv if s != "--automatically-fix-dependencies"];

try: # mDebugOutput use is Optional
  import mDebugOutput as m0DebugOutput;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  m0DebugOutput = None;

guExitCodeInternalError = 1; # Use standard value;
try:
  try:
    from mConsole import oConsole;
  except:
    import sys, threading;
    oConsoleLock = threading.Lock();
    class oConsole(object):
      @staticmethod
      def fOutput(*txArguments, **dxArguments):
        sOutput = "";
        for x in txArguments:
          if isinstance(x, str):
            sOutput += x;
        sPadding = dxArguments.get("sPadding");
        if sPadding:
          sOutput.ljust(120, sPadding);
        oConsoleLock.acquire();
        print(sOutput);
        sys.stdout.flush();
        oConsoleLock.release();
      @staticmethod
      def fStatus(*txArguments, **dxArguments):
        pass;
  
  # Tests are yet to be added.
  from mMultiThreading import cLock;
  oLock1 = cLock();
  oLock2 = cLock();
  assert oLock2.fbAcquire(), \
      "Cannot acquire lock";
  assert not oLock2.fbAcquire(), \
      "Lock acquired twice!?";
  aoUnlockedLocks = cLock.faoWaitUntilLocksAreUnlocked(
    aoLocks = [
      oLock1,
      oLock2,
    ],
    n0TimeoutInSeconds = 0,
  );
  assert aoUnlockedLocks == [oLock1], \
      "Expected [oLock1] got %s" % (repr(aoUnlockedLocks),);
  assert oLock1.fbAcquire(), \
      "Cannot acquire lock";
  assert not oLock1.fbAcquire(), \
      "Lock acquired twice!?";
  aoUnlockedLocks = cLock.faoWaitUntilLocksAreUnlocked(
    aoLocks = [
      oLock1,
      oLock2,
    ],
    n0TimeoutInSeconds = 0.5,
  );
  assert aoUnlockedLocks == [], \
      "Expected [] got %s" % (repr(aoUnlockedLocks),);
  
except Exception as oException:
  if m0DebugOutput:
    m0DebugOutput.fTerminateWithException(oException, guExitCodeInternalError, bShowStacksForAllThread = True);
  raise;
