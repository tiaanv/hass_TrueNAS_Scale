"""Constants for TrueNAS Scale 26 Integration."""

DOMAIN = "truenas_scale"

CONF_HOST = "host"
CONF_API_KEY = "api_key"
CONF_USERNAME = "username"
CONF_PORT = "port"
CONF_SSL = "ssl"
CONF_VERIFY_SSL = "verify_ssl"

DEFAULT_PORT = 443
DEFAULT_SSL = True
DEFAULT_VERIFY_SSL = False
DEFAULT_USERNAME = "root"

DATA_SYSTEM_INFO = "system_info"
DATA_POOLS = "pools"
DATA_DATASETS = "datasets"
DATA_DISKS = "disks"
DATA_DISK_TEMPS = "disk_temperatures"
DATA_SERVICES = "services"
DATA_APPS = "apps"
DATA_ALERTS = "alerts"
DATA_REALTIME = "realtime"
DATA_INTERFACES = "interfaces"
DATA_VMS = "vms"

UPDATE_INTERVAL_SECONDS = 15
