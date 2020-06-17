from fTestDependencies import fTestDependencies;
fTestDependencies();

from mDebugOutput import fEnableDebugOutputForClass, fEnableDebugOutputForModule, fTerminateWithException;
try:
  # Tests are yet to be added.
  pass;
except Exception as oException:
  fTerminateWithException(oException);