import ctypes
import threading
def _async_raise(tid:int, exctype:BaseException):
        """raises the exception, performs cleanup if needed"""
        try:
            tid = ctypes.c_long(tid)
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                tid, ctypes.py_object(exctype))
            if res == 0:
                # pass
                raise ValueError("invalid thread id")
            elif res != 1:
                # """if it returns a number greater than one, you're in trouble,
                # and you should call it again with exc=NULL to revert the effect"""
                ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
                raise SystemError("PyThreadState_SetAsyncExc failed")
        except Exception as err:
            print(err)
def kill_thread(thread:threading.Thread):
    _async_raise(thread.ident,SystemExit)
def kill_threads(threads:list[threading.Thread]):
    for thread in threads:
        _async_raise(thread.ident,SystemExit)
def debug_thread(thread:threading.Thread,error:Exception):
    _async_raise(thread.ident,error)