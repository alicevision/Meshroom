import os

# Enable local plugin management for all the plugin tests.
# The local plugin services (install, update, uninstall) refuse to run when "MESHROOM_LOCAL_PLUGINS" is disabled.
os.environ["MESHROOM_LOCAL_PLUGINS"] = "True"
