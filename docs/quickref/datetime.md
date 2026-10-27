# datetime, date, zoneinfo

```python
from datetime import date, datetime, timedelta, UTC
from zoneinfo import ZoneInfo

date(2026, 10, 26)                    # calendar day, no time
datetime.now(UTC)                     # AWARE (has tzinfo) ✅
datetime.now()                        # NAIVE local time ⚠️
date.fromisoformat("2026-10-26")
datetime.fromisoformat("2026-10-26T09:00:00-04:00")
dt.isoformat()   dt.date()   dt.strftime("%b %d %H:%M")
```

**Arithmetic:**
```python
dt + timedelta(days=1, hours=2)
(end - start).total_seconds()
d1 < d2                               # comparison works for date and datetime
```

**Time zones:**
```python
ny = ZoneInfo("America/New_York")
local = datetime(2026, 11, 1, 9, 0, tzinfo=ny)   # 9am wall clock in NY (DST handled)
local.astimezone(UTC)                            # same instant, shown in UTC
local.replace(tzinfo=None)                       # strip tz (changes nothing about the clock time!)
```

⚠️ Naive and aware datetimes can't be compared (TypeError).
⚠️ "Same day" depends on whose time zone: convert to the zone first, then take `.date()`.
⚠️ `datetime` is a subclass of `date`; `date` vs `datetime` comparisons raise.
