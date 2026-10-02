.pragma library

// A Plugin has a rootPath (installed on disk), a PluginRecord (downloadable-only) does not.
function isInstalled(plugin) {
    return plugin !== null && typeof plugin.rootPath !== "undefined"
}

// Installed plugins show where they live on disk, downloadable ones show their source URL.
function pluginPath(plugin) {
    if (plugin === null)
        return ""
    return isInstalled(plugin) ? plugin.rootPath : plugin.url
}
