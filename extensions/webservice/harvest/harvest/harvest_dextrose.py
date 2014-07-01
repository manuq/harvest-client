is_dextrose = None
dextrose_version = None
try:
    import ceibal.laptops
except ImportError:
    is_dextrose = False
else:
    is_dextrose = True

if is_dextrose:
    xo = ceibal.laptops.XO()
    build = xo._build
    if "Version-b" in build:
        dextrose_version = "dextrose4"
    elif "Version-a" in build:
        dextrose_version = "dextrose3"

if dextrose_version == "dextrose3":
    import gconf
else:
    from gi.repository import GConf

def get_gconf_default_client():
    if dextrose_version == "dextrose3":
        return gconf.client_get_default()
    else:
        return GConf.Client.get_default()

def get_serial_number():
    xo = ceibal.laptops.XO()
    return xo._sn
