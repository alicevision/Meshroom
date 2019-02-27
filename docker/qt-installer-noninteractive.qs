// Emacs mode hint: -*- mode: JavaScript -*-

function Controller() {
    installer.autoRejectMessageBoxes();
    installer.installationFinished.connect(function() {
        gui.clickButton(buttons.NextButton);
    })

    // Copied from https://bugreports.qt.io/browse/QTIFW-1072?jql=project%20%3D%20QTIFW
    // there are some changes between Qt Online installer 3.0.1 and 3.0.2. Welcome page does some network
    // queries that is why the next button is called too early. 
    var page = gui.pageWidgetByObjectName("WelcomePage")
    page.completeChanged.connect(welcomepageFinished)
}

Controller.prototype.WelcomePageCallback = function() {
    gui.clickButton(buttons.NextButton);
}

welcomepageFinished = function()
{
    //completeChange() -function is called also when other pages visible
    //Make sure that next button is clicked only when in welcome page
    if(gui.currentPageWidget().objectName == "WelcomePage") {
        gui.clickButton( buttons.NextButton);   
    }
}

Controller.prototype.CredentialsPageCallback = function() {
    gui.clickButton(buttons.NextButton);
}

Controller.prototype.IntroductionPageCallback = function() {
    gui.clickButton(buttons.NextButton);
}

Controller.prototype.TargetDirectoryPageCallback = function()
{
    gui.currentPageWidget().TargetDirectoryLineEdit.setText("/opt/qt");
    gui.clickButton(buttons.NextButton);
}

Controller.prototype.ComponentSelectionPageCallback = function() {
    var widget = gui.currentPageWidget();

    widget.deselectAll();

    // widget.selectComponent("qt");
    // widget.selectComponent("qt.qt5.5111");
    widget.selectComponent("qt.qt5.5111.gcc_64");
    // widget.selectComponent("qt.qt5.5111.qtscript");
    // widget.selectComponent("qt.qt5.5111.qtscript.gcc_64");
    // widget.selectComponent("qt.qt5.5111.qtwebengine");
    // widget.selectComponent("qt.qt5.5111.qtwebengine.gcc_64");
    // widget.selectComponent("qt.qt5.5111.qtwebglplugin");
    // widget.selectComponent("qt.qt5.5111.qtwebglplugin.gcc_64");
    // widget.selectComponent("qt.tools");

    gui.clickButton(buttons.NextButton);
}

Controller.prototype.LicenseAgreementPageCallback = function() {
    gui.currentPageWidget().AcceptLicenseRadioButton.setChecked(true);
    gui.clickButton(buttons.NextButton);
}

Controller.prototype.StartMenuDirectoryPageCallback = function() {
    gui.clickButton(buttons.NextButton);
}

Controller.prototype.ReadyForInstallationPageCallback = function()
{
    gui.clickButton(buttons.NextButton);
}

Controller.prototype.FinishedPageCallback = function() {
    var checkBoxForm = gui.currentPageWidget().LaunchQtCreatorCheckBoxForm
    if (checkBoxForm && checkBoxForm.launchQtCreatorCheckBox) {
        checkBoxForm.launchQtCreatorCheckBox.checked = false;
    }
    gui.clickButton(buttons.FinishButton);
}

