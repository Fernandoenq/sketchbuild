import ctypes, sys

print("Python:", sys.version)

class SUModelRef(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]

CALLBACK = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.POINTER(SUModelRef),
    ctypes.c_char_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_int),
)

def py_impl(model_ptr, buf, length, status_ptr):
    print("dentro do callback, length=", length)
    status_ptr[0] = 0
    return 0

cb = CALLBACK(py_impl)
cb.argtypes = [
    ctypes.POINTER(SUModelRef),
    ctypes.c_char_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_int),
]
cb.restype = ctypes.c_int

model = SUModelRef()
status = ctypes.c_int(-1)
data = b"\x00\x01\x02\x03" * 100

print("chamando...")
r = cb(ctypes.byref(model), data, len(data), ctypes.byref(status))
print("retornou:", r, "status:", status.value)
