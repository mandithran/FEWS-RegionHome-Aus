def round_hours(dt, resolutionInHours):
    """round_hours(datetime, resolutionInHours) => datetime rounded to lower interval
    Works for hour resolution up to a day (e.g. cannot round to nearest week).
    """
    from datetime import datetime, timedelta
    # First zero out minutes, seconds and micros
    dtTrunc = dt.replace(minute=0,second=0, microsecond=0)
    # Figure out how many minutes we are past the last interval
    excessHours = (dtTrunc.hour) % resolutionInHours
    # Subtract off the excess minutes to get the last interval
    return dtTrunc + timedelta(hours=-excessHours)

def retrieveSurgeFile():
    return("Hello surge...")