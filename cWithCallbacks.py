gbDebugOutput = False;
gbFireDebugOutput = False;

class cWithCallbacks(object):
  def fAddEvents(oSelf, *asEventNames):
    if gbDebugOutput and hasattr(oSelf, "fEnterFunctionOutput"):
      oSelf.fEnterFunctionOutput(asEventNames = asEventNames);
    # Might be called multiple times by sub-classes.
    if not hasattr(oSelf, "_cWithCallbacks__dafCallbacks_by_sEventName"):
      oSelf.__dafCallbacks_by_sEventName = {};
    for sEventName in asEventNames:
      assert sEventName not in oSelf.__dafCallbacks_by_sEventName, \
          "The event %s appears to be defined twice" % repr(sEventName);
      oSelf.__dafCallbacks_by_sEventName[sEventName] = [];
    if gbDebugOutput and hasattr(oSelf, "fStatusOutput"):
      oSelf.fStatusOutput("known events: %s" % ", ".join([repr(sEventName) for sEventName in oSelf.__dafCallbacks_by_sEventName.keys()]));
    if gbDebugOutput and hasattr(oSelf, "fxExitFunctionOutput"):
      oSelf.fExitFunctionOutput();
  
  def fAddCallback(oSelf, sEventName, fCallback):
    if gbDebugOutput and hasattr(oSelf, "fEnterFunctionOutput"):
      oSelf.fEnterFunctionOutput(sEventName = sEventName, fCallback = fCallback);
    assert sEventName in oSelf.__dafCallbacks_by_sEventName, \
        "Unknown event name %s" % repr(sEventName);
    oSelf.__dafCallbacks_by_sEventName[sEventName].append(fCallback);
    if gbDebugOutput and hasattr(oSelf, "fxExitFunctionOutput"):
      oSelf.fExitFunctionOutput();
  
  def fbRemoveCallback(oSelf, sEventName, fCallback):
    if gbDebugOutput and hasattr(oSelf, "fEnterFunctionOutput"):
      oSelf.fEnterFunctionOutput(sEventName = sEventName, fCallback = fCallback);
    assert sEventName in oSelf.__dafCallbacks_by_sEventName, \
        "Unknown event name %s" % repr(sEventName);
    if fCallback in oSelf.__dafCallbacks_by_sEventName[sEventName]:
      oSelf.__dafCallbacks_by_sEventName[sEventName].remove(fCallback);
      bResult = True;
    else:
      bResult = False;
    if gbDebugOutput and hasattr(oSelf, "fxExitFunctionOutput"):
      return oSelf.fxExitFunctionOutput(bResult);
    return bResult;
  
  def fFireCallbacks(oSelf, sEventName, *axArguments, **dxArguments):
    if (gbDebugOutput or gbFireDebugOutput) and hasattr(oSelf, "fEnterFunctionOutput"):
      oSelf.fEnterFunctionOutput(sEventName = sEventName, axArguments = axArguments, dxArguments = dxArguments);
    assert sEventName in oSelf.__dafCallbacks_by_sEventName, \
        "event %s not in list of known events (%s)" % (repr(sEventName), ", ".join([repr(sEventName) for sEventName in oSelf.__dafCallbacks_by_sEventName.keys()]));
    afCallbacks = oSelf.__dafCallbacks_by_sEventName[sEventName];
    for fCallback in afCallbacks:
      fCallback(oSelf, *axArguments, **dxArguments);
    if (gbDebugOutput or gbFireDebugOutput) and hasattr(oSelf, "fxExitFunctionOutput"):
      oSelf.fExitFunctionOutput("Fired %d callbacks" % len(afCallbacks));
  