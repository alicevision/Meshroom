.pragma library

function randomLabel(index, entryType) {
    var tag = ["Atlas", "Comet", "Echo", "Nimbus", "Quartz", "Vector"]
    return entryType + " " + tag[index % tag.length] + " #" + (index + 1)
}
