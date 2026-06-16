"""
Save callback for Meshroom.

When the environment variable MR_ASK_TEMPLATE_BEFORE_SAVING is set to "1",
this module registers a "save" callback that returns information about whether
the user should be asked to choose between saving as a template or a standard save.

The callback returns a dictionary:
    {"askTemplate": True}

This result is used by the QML save dialog to decide whether to present
a choice dialog to the user.
"""

import os
import logging

from meshroom.core.callbacks import registerCallback

logger = logging.getLogger(__name__)


def _saveCallback(*args, **kwargs):
    """
    Save callback that signals the UI should ask the user whether to save
    as a template or as a standard project file.

    Returns:
        dict: {"askTemplate": True} to indicate the system should present
              the template-or-save choice to the user.
    """
    return {"askTemplate": True}


def registerSaveCallback():
    """
    Register the save callback if the environment variable
    MR_ASK_TEMPLATE_BEFORE_SAVING is set to "1".
    """
    if os.environ.get("MR_ASK_TEMPLATE_BEFORE_SAVING", "0") == "1":
        registerCallback("save", _saveCallback)
        logger.info("Save callback registered (MR_ASK_TEMPLATE_BEFORE_SAVING=1).")
    else:
        logger.debug("Save callback not registered (MR_ASK_TEMPLATE_BEFORE_SAVING is not set to 1).")
