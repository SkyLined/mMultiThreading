try: # mDebugOutput use is Optional
  from mDebugOutput import *;
except: # Do nothing if not available.
  ShowDebugOutput = lambda fxFunction: fxFunction;
  fShowDebugOutput = lambda sMessage: None;
  fEnableDebugOutputForModule = lambda mModule: None;
  fEnableDebugOutputForClass = lambda cClass: None;
  fEnableAllDebugOutput = lambda: None;
  cCallStack = fTerminateWithException = fTerminateWithConsoleOutput = None;

gbDebugOutput = False;
gbFireDebugOutput = False;

class cWithCallbacks(object):
  def fasGetEventNames(oSelf):
    return getattr(oSelf, "_cWithCallbacks__dafCallbacks_by_sEventName", {}).keys();
    
  def fAddEvents(oSelf, *asEventNames):
    # Might be called multiple times by sub-classes.
    if not hasattr(oSelf, "_cWithCallbacks__dafCallbacks_by_sEventName"):
      oSelf.__dafCallbacks_by_sEventName = {};
      oSelf.__dafFireOnceCallbacks_by_sEventName = {};
    for sEventName in asEventNames:
      assert sEventName not in oSelf.__dafCallbacks_by_sEventName, \
          "The event %s appears to be defined twice" % repr(sEventName);
      oSelf.__dafCallbacks_by_sEventName[sEventName] = [];
      oSelf.__dafFireOnceCallbacks_by_sEventName[sEventName] = [];
    fShowDebugOutput("new events: %s" % ", ".join(asEventNames));
  
  def fAddCallback(oSelf, sEventName, fCallback, bFireOnce = False):
    assert sEventName in oSelf.__dafCallbacks_by_sEventName, \
        "event %s not in list of known events (%s)" % (
          repr(sEventName),
          ", ".join([repr(sEventName) for sEventName in oSelf.__dafCallbacks_by_sEventName.keys()])
        );
    dafCallbacks_by_sEventName = oSelf.__dafFireOnceCallbacks_by_sEventName if bFireOnce else oSelf.__dafCallbacks_by_sEventName;
    dafCallbacks_by_sEventName[sEventName].append(fCallback);
    fShowDebugOutput("New callback for %s: %s%s" % (sEventName, repr(fCallback), " (fire once)" if bFireOnce else ""));
  
  def fbRemoveCallback(oSelf, sEventName, fCallback):
    assert sEventName in oSelf.__dafCallbacks_by_sEventName, \
        "event %s not in list of known events (%s)" % (
          repr(sEventName),
          ", ".join([repr(sEventName) for sEventName in oSelf.__dafCallbacks_by_sEventName.keys()])
        );
    if fCallback in oSelf.__dafCallbacks_by_sEventName:
      oSelf.__dafCallbacks_by_sEventName.remove(fCallback);
      fShowDebugOutput("Regular callback for %s removed: %s" % (sEventName, repr(fCallback)));
      return True;
    if fCallback in oSelf.__dafFireOnceCallbacks_by_sEventName:
      oSelf.__dafFireOnceCallbacks_by_sEventName.remove(fCallback);
      fShowDebugOutput("Fire-once callback for %s removed: %s" % (sEventName, repr(fCallback)));
      return True;
    fShowDebugOutput("Callback not found");
    return False;
  
  def fRemoveCallback(oSelf, sEventName, fCallback):
    oSelf.fbRemoveCallback(sEventName, fCallback)
  
  def fbFireCallbacks(oSelf, sEventName, *txArguments, **dxArguments):
    assert sEventName in oSelf.__dafCallbacks_by_sEventName, \
        "event %s not in list of known events (%s)" % (
          repr(sEventName),
          ", ".join([repr(sEventName) for sEventName in oSelf.__dafCallbacks_by_sEventName.keys()])
        );
    atfFireOnceCallbacks = oSelf.__dafFireOnceCallbacks_by_sEventName[sEventName];
    atfCallbacks = oSelf.__dafCallbacks_by_sEventName[sEventName] + atfFireOnceCallbacks;
    if not atfCallbacks:
      fShowDebugOutput("Fired %s event without callbacks." % sEventName);
      return False;
    fShowDebugOutput("Firing %s event for %d callbacks." % (sEventName, len(atfCallbacks)));
    if txArguments or dxArguments:
      asArguments = (
        [repr(xArgument) for xArgument in txArguments] +
        ["%s:%s" % (repr(xKey), repr(xValue)) for (xKey, xValue) in dxArguments.items()]
      );
      fShowDebugOutput("  Arguments: %s." % ", ".join(asArguments));
    for fCallback in atfCallbacks:
      bFireOnce = fCallback in atfFireOnceCallbacks;
      fShowDebugOutput("  -> %s%s" % (repr(fCallback), " (fire once)" if bFireOnce else ""));
      fCallback(oSelf, *txArguments, **dxArguments);
      if bFireOnce:
        atfFireOnceCallbacks.remove(fCallback);
    return True;

  def fFireCallbacks(oSelf, sEventName, *txArguments, **dxArguments):
    oSelf.fbFireCallbacks(sEventName, *txArguments, **dxArguments);

