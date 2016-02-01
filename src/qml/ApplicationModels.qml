// import QtQuick 2.5
// import QtQml.Models 2.2
//
// Item {
//
//     property variant jobs: DelegateModel {
//         model: currentProject.proxy
//         delegate: Rectangle { width: parent.width }
//         Component.onCompleted: currentJob = items.get(0).model
//     }
//
//     property variant projects: DelegateModel {
//         model: _applicationModel.projects
//         delegate: Rectangle { width: parent.width }
//         Component.onCompleted: currentProject = items.get(0).model
//     }
//
// }
