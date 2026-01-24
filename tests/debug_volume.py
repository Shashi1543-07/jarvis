try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    print("Pycaw imported.")
    
    # 1. Inspect GetSpeakers
    device = AudioUtilities.GetSpeakers()
    print(f"Device type: {type(device)}")
    print(f"Device dir: {dir(device)}")
    
    # 2. Try to activate on the device wrapper if it has an attribute
    # Some versions wrap it. Check for 'activate', 'interface', 'real_device'
    
    from comtypes import CLSCTX_ALL
    
    interface = None
    
    if hasattr(device, 'Activate'):
        print("Has Activate method.")
        interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    elif hasattr(device, 'interface'):
        print("Using .interface attribute")
        interface = device.interface.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    else:
        print("Attempting to find alternate activation...")
        # Try GetAllDevices
        devices = AudioUtilities.GetAllDevices()
        for d in devices:
            print(f"Found device: {d}")
            # Try to get default speakers this way
            
    if interface:
        from ctypes import cast, POINTER
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        print(f"Current volume: {volume.GetMasterVolumeLevelScalar()}")
        
except Exception as e:
    print(f"Error: {e}")
