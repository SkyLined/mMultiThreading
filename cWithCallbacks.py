try: # mDebugOutput use is Optional
  from mDebugOutput import ShowDebugOutput, fShowDebugOutput;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  ShowDebugOutput = fShowDebugOutput = lambda x: x; # NOP

gbDebugOutput = False;
gbFireDebugOutput = False;

class cWithCallbacks(object):
  def fasGetEventNames(oSelf):
    return list(getattr(oSelf, "_cWithCallbacks__dafCallbacks_by_sEventName", {}).keys());
  
  def __fbCheckIsKnownEventName(oSelf, sEventName, bIgnoreMissingEventNames = False):
    mDebugOutput_HideInCallStack = True; # Errors are often easier to read if this function is left out of the stack.
    if sEventName in oSelf.__dafCallbacks_by_sEventName:
      return True;
    assert bIgnoreMissingEventNames, \
        "event %s for class %s not in list of known events (%s)" % (
          repr(sEventName),
          repr(oSelf.__class__.__name__),
          ", ".join([repr(sEventName) for sEventName in oSelf.__dafCallbacks_by_sEventName.keys()]),
        );
    return False;
  
  def fAddEvents(oSelf, *asEventNames):
    mDebugOutput_HideInCallStack = True; # Errors are often easier to read if this function is left out of the stack.
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
  
  def fAddCallbacks(oSelf, dfCallback_by_sEventName, bFireOnce = False, bIgnoreMissingEventNames = False):
    mDebugOutput_HideInCallStack = True; # Errors are often easier to read if this function is left out of the stack.
    for (sEventName, fCallback) in dfCallback_by_sEventName.items():
      oSelf.fAddCallback(sEventName, fCallback, bFireOnce = bFireOnce, bIgnoreMissingEventNames = bIgnoreMissingEventNames);
  def fAddCallback(oSelf, sEventName, fCallback, bFireOnce = False, bIgnoreMissingEventNames = False):
    mDebugOutput_HideInCallStack = True; # Errors are often easier to read if this function is left out of the stack.
    # Use "bIgnoreMissingEventNames" with caution: misspelled names may go unnoticed!
    if oSelf.__fbCheckIsKnownEventName(sEventName, bIgnoreMissingEventNames = bIgnoreMissingEventNames):
      dafCallbacks_by_sEventName = oSelf.__dafFireOnceCallbacks_by_sEventName if bFireOnce else oSelf.__dafCallbacks_by_sEventName;
      dafCallbacks_by_sEventName[sEventName].append(fCallback);
      fShowDebugOutput("New callback for %s: %s%s" % (sEventName, repr(fCallback), " (fire once)" if bFireOnce else ""));
  
  def fRemoveCallback(oSelf, sEventName, fCallback, bFireOnce = False, bIgnoreMissingEventNames = False):
    mDebugOutput_HideInCallStack = True; # Errors are often easier to read if this function is left out of the stack.
    assert fbRemoveCallback(sEventName, fCallback, bFireOnce = bFireOnce, bIgnoreMissingEventNames = bIgnoreMissingEventNames), \
        "%sallback for %s not found: %s" % ("Fire-once c" if bFireOnce else "C", repr(sEventName), repr(fCallback));
  def fbRemoveCallback(oSelf, sEventName, fCallback, bFireOnce = False, bIgnoreMissingEventNames = False):
    mDebugOutput_HideInCallStack = True; # Errors are often easier to read if this function is left out of the stack.
    # Use "bIgnoreMissingEventNames" with caution: misspelled names may go unnoticed!
    if not oSelf.__fbCheckIsKnownEventName(sEventName, bIgnoreMissingEventNames = bIgnoreMissingEventNames):
      return False;
    dafCallbacks_by_sEventName = oSelf.__dafCallbacks_by_sEventName if bFireOnce else oSelf.__dafFireOnceCallbacks_by_sEventName;
    atfCallbacks = dafCallbacks_by_sEventName[sEventName];
    try:
      atfCallbacks.remove(fCallback);
    except ValueError:
      fShowDebugOutput("%sallback for %s not found: %s" % ("Fire-once c" if bFireOnce else "C", sEventName, repr(fCallback)));
      return False;
    else:
      fShowDebugOutput("%sallback for %s removed: %s" % ("Fire-once c" if bFireOnce else "C", sEventName, repr(fCallback)));
      return True;
  
  def fbFireCallbacks(oSelf, sEventName, *txArguments, **dxArguments):
    mDebugOutput_HideInCallStack = True; # Errors are often easier to read if this function is left out of the stack.
    oSelf.__fbCheckIsKnownEventName(sEventName);
    atfFireOnceCallbacks = oSelf.__dafFireOnceCallbacks_by_sEventName[sEventName];
    atfCallbacks = oSelf.__dafCallbacks_by_sEventName[sEventName] + atfFireOnceCallbacks;
    if not atfCallbacks:
      fShowDebugOutput("Event %s fired without callbacks." % sEventName);
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
  
  fFireCallbacks = fbFireCallbacks; # One may not care about the result

