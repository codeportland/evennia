from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.application.service import Service

from evennia.contrib.gamedir_client.client import EvenniaGameDirClient
from evennia.utils import logger

# How many seconds to wait before triggering the first EGD check-in.
_FIRST_UPDATE_DELAY = 10
# How often to sync to the server
_CLIENT_UPDATE_RATE = 60 * 30


class EvenniaGameDirService(Service):
    """
    Twisted Service that contains a LoopingCall for sending details on a
    game to the Evennia Game Directory.
    """
    name = 'GameDirectoryClient'

    def __init__(self):
        self.client = EvenniaGameDirClient(
            on_bad_request=self._die_on_bad_request)
        self.loop = LoopingCall(self.client.send_game_details)

    def startService(self):
        super(EvenniaGameDirService, self).startService()
        # TODO: Check to make sure that the client is configured.
        # Start the loop, but only after a short delay. This allows the
        # portal and the server time to sync up as far as total player counts.
        # Prevents always reporting a count of 0.
        reactor.callLater(
            _FIRST_UPDATE_DELAY, self.loop.start, _CLIENT_UPDATE_RATE)

    def stopService(self):
        if self.running == 0:
            # @reload errors if we've stopped this service.
            return
        super(EvenniaGameDirService, self).stopService()
        self.loop.stop()

    def _die_on_bad_request(self):
        """
        If it becomes apparent that our configuration is generating improperly
        formed messages to EGD, we don't want to keep sending bad messages.
        Stop the service so we're not wasting resources.
        """
        logger.log_infomsg(
            "Shutting down Evennia Game Directory client service due to "
            "invalid configuration.")
        self.stopService()