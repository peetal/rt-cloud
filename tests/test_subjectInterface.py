import pytest
from tests.backgroundTestServers import BackgroundTestServers
from rtCommon.clientInterface import ClientInterface
from rtCommon.errors import ValidationError


class TestSubjectInterface:
    serversForTests = None

    def setup_class(cls):
        cls.serversForTests = BackgroundTestServers()

    def teardown_class(cls):
        cls.serversForTests.stopServers()

    # Local subjectInterface test
    def test_localSubjectInterface(self):
        """Test SubjectInterface when instantiated in local mode"""
        TestSubjectInterface.serversForTests.stopServers()
        TestSubjectInterface.serversForTests.startServers(subjectRemote=False, dataRemote=True)
        runSubjectFeedbackTest(isRemote=False)

    # Remote subjectInterface test
    def test_remoteSubjectInterface(self):
        """Test SubjectInterface when instantiated in local mode"""
        # Use a remote (RPC) client to the subjectInterface
        TestSubjectInterface.serversForTests.stopServers()
        TestSubjectInterface.serversForTests.startServers(subjectRemote=True, dataRemote=False)
        runSubjectFeedbackTest(isRemote=True)


def runSubjectFeedbackTest(isRemote):
    clientInterface = ClientInterface()
    subjInterface = clientInterface.subjInterface
    print(f'subjInterface remote: {subjInterface.isRemote}, {subjInterface.isRunningRemote()}')
    assert subjInterface.isRunningRemote() == isRemote

    runId = 3
    for trId in range(1, 10):
        value = 20 + trId
        onsetTimeDelayMs = trId + 4
        subjInterface.setResult(runId, trId, value, onsetTimeDelayMs)

    for i in range(1, 10):
        feedbackMsg = subjInterface.dequeueResult(block=False, timeout=1)
        assert feedbackMsg['runId'] == runId
        assert feedbackMsg['trId'] == i
        assert feedbackMsg['value'] == 20 + i
        assert feedbackMsg['onsetTimeDelayMs'] == i + 4

    subjInterface.setResult(1, 2, 3, 3.1)
    feedbackMsg = subjInterface.dequeueResult(block=False, timeout=1)
    assert feedbackMsg['onsetTimeDelayMs']  == 3.1

    with pytest.raises((ValidationError, Exception)):
        # Try setting a negative onsetTimeDelay
        subjInterface.setResult(1, 2, 3, -1)