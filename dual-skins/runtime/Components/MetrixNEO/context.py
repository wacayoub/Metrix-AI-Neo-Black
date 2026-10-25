"""Read the context selection without substituting the currently playing channel."""


def context_selection(screen):
    if screen is None:
        return None, None
    csel = getattr(screen, "csel", None)
    reference = csel.getCurrentSelection() if csel is not None else None
    if reference is None:
        service = getattr(screen, "serviceRef", None)
        reference = getattr(service, "ref", None)
    if reference is None:
        return None, getattr(screen, "event", None)
    from enigma import eServiceCenter
    info = eServiceCenter.getInstance().info(reference)
    return reference, info.getEvent(reference) if info else None
