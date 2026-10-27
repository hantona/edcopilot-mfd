import platform

# A windows specific replacement for open that doesn't prevent others from writing to or replacing the file
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
    import msvcrt
    import os

    # Windows API constants
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    FILE_SHARE_DELETE = 0x00000004
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]


    def open_shared_read(filepath, *, encoding='utf-8'):
        # Open the file allowing other processes to read, write, and delete it
        handle = kernel32.CreateFileW(
            str(filepath),
            GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            None,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            None
        )

        if handle == INVALID_HANDLE_VALUE:
            raise ctypes.WinError(ctypes.get_last_error())

        # Convert the Windows HANDLE to a C runtime file descriptor
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY)

        # Return a standard Python file object (closing it closes the underlying handle)
        return os.fdopen(fd, 'r', encoding=encoding)

else:
    def open_shared_read(filepath, *, encoding='utf-8'):
        return open(filepath, encoding=encoding)
