from PyInstaller.compat import is_darwin
from PyInstaller.utils.hooks import (
    eval_statement, exec_statement, logger)
logger.info('######removing unused mpl-backend ######')
excl_backend_names = eval_statement('import matplotlib; print(matplotlib.rcsetup.all_backends)')

excl_backend_names.remove('WX')
excl_backend_names.remove('WXAgg')

print("Entering custom hook for matplotlib-backends")
excl_module_names=[]
for backend_name in excl_backend_names:
    module_name = 'matplotlib.backends.backend_%s' % backend_name.lower()
    excl_module_names.append(module_name)
    logger.info('##  Matplotlib backend "%s": removed' %  module_name)
logger.info('###### end mpl-backend removal #########')
excludedimports = excl_module_names