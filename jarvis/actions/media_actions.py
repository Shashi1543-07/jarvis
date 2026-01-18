from core.os.media_master import MediaMaster

def play_music():
    """Toggles play/pause"""
    mm = MediaMaster()
    return mm.play_pause()

def pause_music():
    """Toggles play/pause"""
    mm = MediaMaster()
    return mm.play_pause()

def resume_music():
    """Alias for play_music"""
    return play_music()

def stop_music():
    """Stops music playback"""
    mm = MediaMaster()
    return mm.stop()

def next_track():
    """Skips to the next track"""
    mm = MediaMaster()
    return mm.next_track()

def previous_track():
    """Goes to the previous track"""
    mm = MediaMaster()
    return mm.prev_track()

def volume_up(steps=5):
    """Increases system volume"""
    mm = MediaMaster()
    return mm.volume_up(steps)

def volume_down(steps=5):
    """Decreases system volume"""
    mm = MediaMaster()
    return mm.volume_down(steps)
